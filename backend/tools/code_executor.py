# tools/code_executor.py
# ─────────────────────────────────────────────────────────────────────────────
# The Code Execution Engine — the tool that makes the agent genuinely agentic.
#
# Two-phase architecture:
#
# Phase 1 — Code Generation (optional):
#   If the user sends a natural language query ("how many French customers?"),
#   this module calls the LLM to write the pandas code for that query.
#   The LLM gets real column names, dtypes, and sample values as context
#   so it writes code that actually works on THIS dataset.
#
# Phase 2 — Safe Execution:
#   The generated (or user-provided) code runs inside a restricted Python
#   sandbox. Only pandas (pd), numpy (np), and a safe subset of builtins
#   are available. No os, sys, open, subprocess — nothing destructive.
#   df is injected as a READ-ONLY COPY — the agent cannot corrupt the session.
#
# Safety layers:
#   1. Static pattern blocking — rejects code containing os/sys/open/exec etc.
#   2. Restricted __builtins__ — removes dangerous built-ins at exec time
#   3. Read-only DataFrame copy — even if sandbox escapes, original is safe
#   4. 10 second timeout (via threading) — prevents infinite loops
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
import io
import re
import contextlib
import threading
from typing import Any

import pandas as pd
import numpy as np
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# ── LLM for code generation ───────────────────────────────────────────────────
_codegen_llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
)

# ── Blocked patterns — reject before exec ─────────────────────────────────────
_BLOCKED_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+sys\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+shutil\b",
    r"\bimport\s+pathlib\b",
    r"\bopen\s*\(",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"__import__",
    r"__builtins__",
    r"__class__",
    r"\bcompile\s*\(",
    r"\bglobals\s*\(",
    r"\blocals\s*\(",
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
]
_BLOCKED_RE = re.compile("|".join(_BLOCKED_PATTERNS), re.IGNORECASE)


def _is_safe(code: str) -> tuple[bool, str]:
    """Returns (True, '') if safe, (False, reason) if not."""
    match = _BLOCKED_RE.search(code)
    if match:
        return False, f"Blocked pattern detected: `{match.group()}`"
    return True, ""


# ── Safe builtins whitelist ────────────────────────────────────────────────────
_SAFE_BUILTINS = {
    "print": print,
    "len":   len,   "range": range,  "enumerate": enumerate,
    "zip":   zip,   "list":  list,   "dict":  dict,   "set":  set,
    "str":   str,   "int":   int,    "float": float,  "bool": bool,
    "round": round, "abs":   abs,    "sum":   sum,
    "min":   min,   "max":   max,    "sorted": sorted,
    "isinstance": isinstance, "type": type, "hasattr": hasattr,
    "True":  True,  "False": False,  "None":  None,
}


# ── Code Generation ───────────────────────────────────────────────────────────

def _build_context(df: pd.DataFrame) -> str:
    """Give the LLM real column names, dtypes, and example values."""
    lines = ["DataFrame 'df' — available columns:", ""]
    for col in df.columns:
        dtype = str(df[col].dtype)
        if df[col].dtype == object:
            sample = df[col].dropna().unique()[:4].tolist()
        else:
            sample = [round(df[col].min(), 2), round(df[col].median(), 2), round(df[col].max(), 2)]
        lines.append(f"  - {col} ({dtype}): sample values = {sample}")
    lines.append(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
    return "\n".join(lines)


def generate_code(query: str, df: pd.DataFrame, raw_df: pd.DataFrame | None = None) -> str:
    """
    Ask the LLM to write pandas code that answers the user's question.
    Returns raw Python code string ready for execution.
    """
    context = _build_context(df)
    raw_context = _build_context(raw_df) if raw_df is not None else "(same as df — no cleaning done yet)"

    prompt = f"""You are a Python/pandas expert. Write code to answer the question below.

Two DataFrames are available:

1. `df` — the WORKING dataset (may be cleaned/encoded if cleaning has been applied):
{context}

2. `df_raw` — the ORIGINAL uploaded dataset (always has human-readable values like country names):
{raw_context}

Guidelines on which to use:
- For EXPLORATION (counts, filters by country/name, profiles, distributions): prefer `df_raw`
  because it has readable column values (e.g. Geography='Germany', not Geography_Germany=1)
- For MODEL-RELEVANT analysis (features used in training, cleaned values): use `df`
- You can use both in the same query if needed

Available variables (pre-injected, do NOT import):
  df      — working/cleaned DataFrame
  df_raw  — original raw DataFrame
  pd      — pandas
  np      — numpy

Rules:
  1. Store your final answer in a variable called `result`.
  2. result can be a number, string, DataFrame, Series, or list.
  3. Use print() for intermediate steps if helpful — output is captured.
  4. Do NOT use import statements — everything is pre-loaded.
  5. Write ONLY executable Python code. No explanations, no markdown fences.

Question: {query}

Code:"""

    response = _codegen_llm.invoke(prompt)
    code = response.content.strip()

    # Strip ```python ... ``` fences if the LLM added them
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\n?", "", code)
        code = re.sub(r"\n?```$", "", code)

    return code.strip()


# ── Safe Execution ─────────────────────────────────────────────────────────────

def _exec_with_timeout(code: str, safe_globals: dict, local_vars: dict, timeout: int = 10):
    """Run exec() in a separate thread with a timeout."""
    exc_holder = [None]

    def target():
        try:
            exec(code, safe_globals, local_vars)
        except Exception as e:
            exc_holder[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        raise TimeoutError(f"Code execution timed out after {timeout}s (infinite loop?)")
    if exc_holder[0]:
        raise exc_holder[0]


def safe_exec(code: str, df: pd.DataFrame, raw_df: pd.DataFrame | None = None) -> dict:
    """
    Execute code in a restricted sandbox.
    df      = working/cleaned dataset
    raw_df  = original uploaded dataset (injected as df_raw)
    """
    ok, reason = _is_safe(code)
    if not ok:
        return {
            "status": "error",
            "error":  f"Code blocked by safety filter: {reason}",
            "code_executed": code,
        }

    safe_globals = {
        "__builtins__": _SAFE_BUILTINS,
        "df":     df.copy(),
        "df_raw": raw_df.copy() if raw_df is not None else df.copy(),
        "pd":  pd,
        "np":  np,
    }
    local_vars: dict[str, Any] = {}
    stdout_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture):
            _exec_with_timeout(code, safe_globals, local_vars, timeout=10)
    except TimeoutError as e:
        return {"status": "error", "error": str(e), "code_executed": code}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}", "code_executed": code}

    stdout_output = stdout_capture.getvalue().strip()
    result = local_vars.get("result")

    # Serialize result to a JSON-safe representation
    if isinstance(result, pd.DataFrame):
        result_str  = result.to_string(max_rows=25)
        result_type = "dataframe"
        shape       = list(result.shape)
    elif isinstance(result, pd.Series):
        result_str  = result.to_string(max_rows=25)
        result_type = "series"
        shape       = [len(result)]
    elif result is not None:
        result_str  = str(result)
        result_type = type(result).__name__
        shape       = None
    else:
        result_str  = stdout_output or "(no result returned)"
        result_type = "stdout"
        shape       = None

    return {
        "status":       "success",
        "result_type":  result_type,
        "result":       result_str,
        "shape":        shape,
        "stdout":       stdout_output,
        "code_executed": code,
    }


# ── Public entry point ─────────────────────────────────────────────────────────

def run_query(query: str, df: pd.DataFrame, raw_df: pd.DataFrame | None = None) -> dict:
    """
    Full pipeline: generate pandas code from NL query, then execute it safely.
    df     = working dataset (cleaned if cleaning has been run)
    raw_df = original upload (always human-readable column values)
    """
    try:
        code = generate_code(query, df, raw_df)
    except Exception as e:
        return {"status": "error", "error": f"Code generation failed: {e}", "code_executed": ""}

    return safe_exec(code, df, raw_df)
