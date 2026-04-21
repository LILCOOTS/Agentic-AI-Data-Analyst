# tools/proactive_analyzer.py
# ─────────────────────────────────────────────────────────────────────────────
# Proactive Analysis Engine — runs BEFORE the user asks anything.
#
# After a dataset loads, this module runs 4 targeted pandas queries against
# the live data, collects real numbers, then synthesizes them into a
# "welcome analysis" that surfaces the most interesting/surprising findings.
#
# Key design decisions:
#   1. Uses the same run_query() sandbox as the chat query tool — consistent,
#      safe, and already tested.
#   2. Queries are adaptive — they use actual column names from metadata so
#      they work on ANY dataset, not just the bank churn example.
#   3. Results go to the LLM as structured context, not raw JSON — same
#      pattern as Synthesizer's formatters.
#   4. This function is called ONCE at upload time. It's not part of the
#      LangGraph pipeline — it's a direct async call from the /proactive_analysis
#      endpoint, which streams back to the chat panel.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from tools.code_executor import run_query

load_dotenv()

_llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
)
_chain = _llm | StrOutputParser()


# ── Adaptive Query Builder ─────────────────────────────────────────────────────
# These queries use real column names from metadata — no hardcoding.

def _build_queries(meta: dict) -> list[tuple[str, str]]:
    """
    Returns a list of (label, query_string) pairs tailored to this dataset.
    Each query will be executed via run_query() against the raw DataFrame.
    """
    target     = meta.get("target_column", "")
    columns    = meta.get("columns", [])
    num_cols   = [c for c in columns if c != target]
    cat_cols   = meta.get("categorical_columns", [])

    queries = []

    # 1 — Class/target balance (always useful — reveals imbalance)
    if target:
        queries.append((
            "target_balance",
            f"counts = df_raw['{target}'].value_counts(); "
            f"result = (counts / counts.sum() * 100).round(2).to_dict()"
        ))

    # 2 — Feature separation: which numeric column best separates target classes?
    if target and num_cols:
        safe_cols = [c for c in num_cols[:10]]   # cap at 10 to keep code short
        cols_str = str(safe_cols)
        queries.append((
            "feature_separation",
            f"import pandas as pd\n"
            f"cols = {cols_str}\n"
            f"sep = {{}}\n"
            f"for c in cols:\n"
            f"    try:\n"
            f"        g = df_raw.groupby('{target}')[c].mean()\n"
            f"        sep[c] = round(abs(g.max() - g.min()), 3)\n"
            f"    except: pass\n"
            f"result = dict(sorted(sep.items(), key=lambda x: x[1], reverse=True)[:5])"
        ))

    # 3 — Zero-value check: which columns have suspicious zero concentrations?
    if num_cols:
        safe_cols = str(num_cols[:8])
        queries.append((
            "zero_values",
            f"cols = {safe_cols}\n"
            f"zeros = {{c: round(100 * (df_raw[c] == 0).sum() / len(df_raw), 1) for c in cols if c in df_raw.columns}}\n"
            f"result = {{k: v for k, v in sorted(zeros.items(), key=lambda x: x[1], reverse=True) if v > 5}}"
        ))

    # 4 — Categorical segment analysis: churn rate per category for top cat column
    if target and cat_cols:
        top_cat = cat_cols[0]
        queries.append((
            "segment_churn",
            f"result = df_raw.groupby('{top_cat}')['{target}'].mean().round(4).sort_values(ascending=False).to_dict()"
        ))

    return queries


# ── Run All Proactive Queries ──────────────────────────────────────────────────

def collect_proactive_data(session) -> dict:
    """
    Executes all adaptive queries against the session's raw dataset.
    Returns a dict of {label: result_str} for successful queries.
    """
    meta = session.metadata or {}
    df   = session.raw_dataset

    if df is None:
        return {}

    queries  = _build_queries(meta)
    findings = {}

    for label, code in queries:
        result = run_query(code, df, df)   # both df and df_raw = raw dataset
        if result.get("status") == "success":
            findings[label] = result.get("result", "")

    return findings


# ── Synthesis Prompt ───────────────────────────────────────────────────────────

def _build_synthesis_prompt(meta: dict, findings: dict) -> str:
    target    = meta.get("target_column", "unknown")
    n_rows    = meta.get("num_rows", "?")
    n_cols    = meta.get("num_columns", "?")
    prob_type = meta.get("problem_type", "unknown")

    sections = []
    if "target_balance" in findings:
        sections.append(f"Target variable '{target}' distribution: {findings['target_balance']}")
    if "feature_separation" in findings:
        sections.append(f"Top 5 features by mean-difference between {target} groups: {findings['feature_separation']}")
    if "zero_values" in findings:
        sections.append(f"Columns with >5% zero values: {findings['zero_values']}")
    if "segment_churn" in findings:
        sections.append(f"Target rate by segment: {findings['segment_churn']}")

    data_summary = "\n".join(f"  - {s}" for s in sections) if sections else "  - (no data computed)"

    return f"""You are an expert AI Data Analyst. A user has just uploaded a dataset and is seeing their dashboard for the first time.

## Dataset Overview
- Shape: {n_rows} rows × {n_cols} columns
- Target variable: {target}
- Problem type: {prob_type}

## Computed Statistics (real numbers from the data — use these exactly)
{data_summary}

## Your Task
Write a concise, insightful "welcome analysis" for this user. You MUST:

1. Start with one sentence summarizing what this dataset is about.
2. Give exactly 3 numbered findings that are SURPRISING, SPECIFIC, or ACTIONABLE.
   - Use the EXACT numbers from the Computed Statistics above.
   - Each finding should say what it means for the analysis, not just what the number is.
3. End with ONE concrete suggested question the user should ask next (in backticks).

Format:
- Use **bold** for key numbers/column names
- Keep the whole response under 200 words
- Tone: friendly data analyst, not a generic AI assistant
- Do NOT say "I noticed" or "It appears" — state findings directly

Do NOT make up numbers. Only use what's in Computed Statistics."""


# ── Public Entry Point ─────────────────────────────────────────────────────────

def generate_proactive_insights(session) -> str:
    """
    Synchronous entry point: collect query results → synthesize → return markdown string.
    Called from the /proactive_analysis endpoint (run in threadpool).
    """
    meta     = session.metadata or {}
    findings = collect_proactive_data(session)

    if not findings:
        return "Upload a dataset and run profiling to get AI-powered insights."

    prompt = _build_synthesis_prompt(meta, findings)
    response = _chain.invoke([SystemMessage(content=prompt)])
    return response
