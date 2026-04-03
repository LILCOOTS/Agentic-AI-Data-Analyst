# agents/state.py
# ─────────────────────────────────────────────────────────────────────────────
# The Agent State — the shared memory dictionary every node reads from
# and writes back to. Think of it as the agent's working memory for one
# full conversation session.
#
# KEY CONCEPT — add_messages:
#   In LangChain, you manually manage message history. In LangGraph,
#   `Annotated[List[BaseMessage], add_messages]` tells the graph runtime:
#   "Never overwrite this field — always APPEND to it."
#   This is what gives the agent persistent conversation memory across turns.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Annotated, List, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages        # The append-only reducer
from langchain_core.messages import BaseMessage         # Parent class for all message types


class AgentState(TypedDict):
    # ── Conversation History ──────────────────────────────────────────────────
    # add_messages is the REDUCER — it appends, never overwrites.
    # HumanMessage("clean my data") + AIMessage("Cleaned ✅") build up here.
    messages: Annotated[List[BaseMessage], add_messages]

    # ── Session Context (injected once per /chat session open) ────────────────
    # session_id ties the agent to the user's uploaded dataset in SessionManager
    session_id: str

    # dataset_metadata gives the LLM awareness of column names, types, target
    # so it never has to guess — it reads from actual profiling output
    dataset_metadata: Optional[dict]

    # analysis_cache holds the last full EDA run so the Reflector can
    # cross-check LLM claims against real numbers (e.g., "correlation is 0.29")
    analysis_cache: Optional[dict]

    # ── Planning Fields (written by Planner, read by Critic + Executor) ───────
    # planned_action is the tool the Planner decided to invoke:
    #   "run_clean" | "run_model" | "predict" | "profile" | "compare" | "answer"
    planned_action: Optional[str]

    # tool_args are the arguments the Planner wants to pass to the tool:
    #   e.g. {"session_id": "abc-123"} for most tools
    #        {"feature_values": {"Age": 45, "Balance": 120000}} for predict
    tool_args: Optional[dict]

    # is_destructive flags actions that PERMANENTLY change the session state
    # (cleaning mutates working_dataset, modeling overwrites modelling_results)
    # When True, the Critic sends the plan to the UI and waits for confirmation.
    is_destructive: bool

    # ── Execution Fields (written by Executor, read by Reflector) ─────────────
    # tool_output holds the raw JSON dict the Python function returned
    tool_output: Optional[dict]

    # ── Reflection Fields (written by Reflector) ──────────────────────────────
    # validation_passed is the Reflector's verdict — True means Synthesizer
    # can proceed, False triggers a retry (up to retry_count max)
    validation_passed: bool

    # retry_count tracks how many times Executor → Reflector has looped
    # Safety cap: after 2 retries, Synthesizer gets a graceful fallback message
    retry_count: int

    # ── Response (written by Synthesizer) ─────────────────────────────────────
    # final_response is the markdown string streamed back to the chat panel
    final_response: Optional[str]
