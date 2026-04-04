# agents/nodes/planner.py
# ─────────────────────────────────────────────────────────────────────────────
# The Planner Node — the only LLM in the graph that makes DECISIONS.
#
# KEY CONCEPT — with_structured_output():
#   In regular LangChain you call llm.invoke() and get back free-form text.
#   You then try to parse it, which is fragile (LLM might say "I'll run the
#   cleaner" instead of a parseable JSON).
#
#   with_structured_output(PlannerDecision) tells the LLM:
#   "You MUST return a JSON object that exactly matches this Pydantic schema.
#    If you don't, the framework retries automatically."
#
#   This turns natural language intent into a typed Python object — safely.
#
# KEY CONCEPT — Node function signature:
#   Every LangGraph node is a plain Python function that:
#     1. Takes the full AgentState dict as input
#     2. Does its work (calls LLM, runs logic, etc.)
#     3. Returns a DICT of ONLY the fields it changed
#   LangGraph merges the returned dict back into the full state automatically.
#   You never return the full state — just your updates.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
import json
from dotenv import load_dotenv
from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq

from agents.state import AgentState

load_dotenv()


# ── Structured Output Schema ──────────────────────────────────────────────────
# This Pydantic model is the CONTRACT the LLM must fulfill.
# Literal["a", "b", "c"] means the field can ONLY be one of those exact values.
# The LLM cannot hallucinate a new action name — it's enforced at the schema level.

class PlannerDecision(BaseModel):
    planned_action: Literal[
        "run_clean",    # Auto-clean the dataset (destructive)
        "run_model",    # Train AutoML ensemble (destructive)
        "predict",      # Predict a single instance using trained model
        "profile",      # Re-run full EDA profiling
        "compare",      # Compare dataset stats before vs after cleaning
        "answer"        # General Q&A — no tool needed, just synthesize from context
    ] = Field(description="The single action to take based on the user's message")

    tool_args: dict = Field(
        default_factory=dict,
        description=(
            "Arguments to pass to the tool. For most tools just pass session_id. "
            "For predict, include feature_values dict with column names and values."
        )
    )

    is_destructive: bool = Field(
        description=(
            "True if this action permanently modifies the session state. "
            "run_clean and run_model are always destructive. "
            "predict, profile, compare, answer are never destructive."
        )
    )

    reasoning: str = Field(
        description="One sentence explaining why you chose this action — used for debugging."
    )


# ── LLM Setup ─────────────────────────────────────────────────────────────────
# Same Groq LLM you already use in llm_insights.py.
# .with_structured_output() wraps it so every .invoke() call returns a
# PlannerDecision object, never raw text.

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",   # Fast + strong reasoning
)

structured_llm = llm.with_structured_output(PlannerDecision)


# ── System Prompt Builder ──────────────────────────────────────────────────────
# We build the prompt dynamically from state fields so the LLM always has
# accurate, real context — not hallucinated column names or target variables.

def build_system_prompt(state: AgentState) -> str:
    meta = state.get("dataset_metadata") or {}
    columns   = meta.get("columns", [])
    target    = meta.get("target_column", "unknown")
    prob_type = meta.get("problem_type", "unknown")
    n_rows    = meta.get("num_rows", "unknown")
    n_cols    = meta.get("num_columns", "unknown")

    # Check if model has been trained (so predict becomes available)
    analysis  = state.get("analysis_cache") or {}
    model_trained = bool(analysis.get("modelling_results"))

    return f"""You are the planning brain of an AI Data Analyst agent.
Your job is to read the user's latest message and decide which single action to take.

## Dataset Context
- Shape: {n_rows} rows × {n_cols} columns
- Columns: {', '.join(columns) if columns else 'not profiled yet'}
- Target variable: {target}
- Problem type: {prob_type}
- Model trained: {'Yes — predict is available' if model_trained else 'No — run_model first'}

## Available Actions
- `run_clean`  — Auto-clean dataset (drop IDs, encode categoricals, impute missing). DESTRUCTIVE.
- `run_model`  — Train AutoML VotingEnsemble with 5-fold CV. DESTRUCTIVE.
- `predict`    — Predict target for a single data point the user describes. Requires trained model.
- `profile`    — Re-run full EDA analysis and refresh insights.
- `compare`    — Show before vs after cleaning statistics.
- `answer`     — Explain, interpret, or answer a question using existing context. No tool needed.

## Rules
1. Only choose `predict` if model_trained = Yes.
2. Always set `tool_args` with at least `{{"session_id": "<session_id>"}}`.
3. For `predict`, add `feature_values` dict with the column values the user mentioned.
4. `run_clean` and `run_model` are always `is_destructive: true`.
5. If unsure, default to `answer` — never guess a destructive action.
6. session_id for this session: {state.get('session_id', '')}
"""


# ── The Planner Node Function ──────────────────────────────────────────────────
# This is what gets registered in graph.py as a node.
# Input : full AgentState
# Output: dict of ONLY the fields this node updates

def planner_node(state: AgentState) -> dict:
    """
    Reads conversation history + dataset context.
    Returns a structured plan: which tool to call, with what args, and whether
    it's destructive (needs human confirmation before executing).
    """
    system_prompt = build_system_prompt(state)

    # Build the message list: system context + full conversation history
    # The LLM sees everything that was said before — this is the memory payoff
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # .invoke() here returns a PlannerDecision object (not raw text)
    # because we used .with_structured_output() above
    decision: PlannerDecision = structured_llm.invoke(messages)

    # Log reasoning to console during development — remove in production
    print(f"[Planner] action={decision.planned_action} | destructive={decision.is_destructive}")
    print(f"[Planner] reasoning: {decision.reasoning}")

    # Return ONLY the fields we're updating — LangGraph merges these into state
    return {
        "planned_action": decision.planned_action,
        "tool_args":      decision.tool_args,
        "is_destructive": decision.is_destructive,
    }
