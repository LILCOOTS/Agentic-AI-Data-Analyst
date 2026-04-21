# agents/graph.py
# ─────────────────────────────────────────────────────────────────────────────
# The Graph — wires every node together into a compiled, runnable agent.
#
# KEY CONCEPT — StateGraph:
#   A StateGraph takes your TypedDict (AgentState) as its "schema".
#   Every node gets a copy of the full state, modifies what it owns,
#   and returns a dict of ONLY the changed fields.
#   The graph runtime merges those changes back automatically.
#
# KEY CONCEPT — Fixed edges vs Conditional edges:
#   Fixed edge:       A →always→ B            (add_edge)
#   Conditional edge: A →maybe→ B or C        (add_conditional_edges)
#                     decided by a routing FUNCTION that reads state
#
#   Routing functions are plain Python — no LLM, no uncertainty.
#   That's what makes LangGraph safe: routing is always deterministic.
#
# KEY CONCEPT — MemorySaver (checkpointer):
#   Without a checkpointer, NodeInterrupt has nowhere to save state.
#   MemorySaver keeps all graph states in memory, keyed by thread_id.
#   thread_id = session_id in our app (one thread per user session).
#
#   Every invoke() call reads from and writes to the checkpointer.
#   This means conversation history persists between HTTP requests — the
#   graph "remembers" across calls as long as the server is running.
#
# KEY CONCEPT — How to read this graph topology:
#
#   START
#     │
#   Planner ──────────────────────────────────┐
#     │                                        │ (always fixed edge)
#   Critic                                     │
#     │                                        │
#     ├─ validation_passed=True ──► Synthesizer│ (Critic redirected)
#     │                                        │
#     └─ else ──────────────────► Executor ───-┘
#                                    │
#                                 Reflector
#                                    │
#                                    ├─ validation_passed=True ──► Synthesizer
#                                    │
#                                    └─ retry_count < 2 ──────────► Executor (CYCLE)
#                                                                        ↑────┘
#   Synthesizer ──► END
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import AgentState
from agents.nodes.planner       import planner_node
from agents.nodes.critic        import critic_node
from agents.nodes.executor      import executor_node
from agents.nodes.reflector     import reflector_node
from agents.nodes.synthesizer   import synthesizer_node
from agents.nodes.continue_plan import continue_plan_node


# ── Routing Functions ─────────────────────────────────────────────────────────
# These are the "traffic directors" of the graph.
# They receive the CURRENT state and return the name of the NEXT node.
# They must be deterministic — no LLM, no randomness.

def route_after_critic(state: AgentState) -> str:
    """
    After Critic runs:
    - If Critic set validation_passed=True (precondition failure redirect)
      → go directly to Synthesizer with the pre-baked response.
    - Otherwise → go to Executor (safe action approved OR destructive action
      was confirmed by human after NodeInterrupt resume).
    """
    if state.get("validation_passed") is True:
        return "synthesizer"
    return "executor"


def route_after_reflector(state: AgentState) -> str:
    """
    After Reflector runs:
    - If output is valid (or max retries reached) → Synthesizer.
    - If output invalid and retries remain → loop back to Executor.

    The Reflector already sets validation_passed=True when retry_count>=2
    (forced pass for graceful fallback), so we only need one check here.
    """
    if state.get("validation_passed"):
        return "synthesizer"
    return "executor"   # ← This is the CYCLE — what makes it a graph, not a chain


def route_after_synthesizer(state: AgentState) -> str:
    """
    After Synthesizer runs:
    - If plan_steps is non-empty → ContinuePlan (advance multi-step pipeline).
    - Otherwise → END (conversation turn complete).
    """
    remaining = state.get("plan_steps") or []
    if remaining:
        print(f"[Router] Plan has {len(remaining)} step(s) remaining — continuing.")
        return "continue_plan"
    return END


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_graph() -> tuple:
    """
    Constructs and compiles the LangGraph StateGraph.
    Returns (compiled_agent, memory) — memory is kept for inspection/testing.
    """
    # ── Checkpointer ──────────────────────────────────────────────────────────
    # MemorySaver stores paused graph states in a Python dict.
    # Required for NodeInterrupt to save state between HTTP requests.
    # In production, swap with AsyncRedisSaver or SqliteSaver for persistence.
    memory = MemorySaver()

    # ── Build ──────────────────────────────────────────────────────────────────
    builder = StateGraph(AgentState)

    # Register every node — name (str) + function
    builder.add_node("planner",       planner_node)
    builder.add_node("critic",        critic_node)
    builder.add_node("executor",      executor_node)
    builder.add_node("reflector",     reflector_node)
    builder.add_node("synthesizer",   synthesizer_node)
    builder.add_node("continue_plan", continue_plan_node)   # ⭐ multi-step

    # ── Fixed Edges ──────────────────────────────────────────────────────
    builder.add_edge(START,           "planner")    # every invocation starts at Planner
    builder.add_edge("planner",       "critic")     # Planner always goes to Critic
    builder.add_edge("executor",      "reflector")  # Executor always goes to Reflector
    builder.add_edge("continue_plan", "critic")     # after advancing, go back to Critic

    # ── Conditional Edges ──────────────────────────────────────────────────────
    # Critic → Executor or Synthesizer
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "executor":    "executor",
            "synthesizer": "synthesizer",
        }
    )

    # Reflector → Synthesizer or Executor (the retry CYCLE)
    builder.add_conditional_edges(
        "reflector",
        route_after_reflector,
        {
            "executor":    "executor",    # ← loop back
            "synthesizer": "synthesizer",
        }
    )

    # Synthesizer → END or ContinuePlan (the multi-step LOOP)
    builder.add_conditional_edges(
        "synthesizer",
        route_after_synthesizer,
        {
            "continue_plan": "continue_plan",   # ← advance to next plan step
            END:              END,
        }
    )

    # ── Compile ────────────────────────────────────────────────────────────────
    # checkpointer=memory  → enables NodeInterrupt + persistent thread memory
    # interrupt_before is NOT needed here because our Critic raises NodeInterrupt
    # FROM INSIDE the node rather than using a compile-time static interrupt.
    agent = builder.compile(checkpointer=memory)

    return agent, memory


# ── Singleton ─────────────────────────────────────────────────────────────────
# Build once at import time — same pattern as session_manager.
# Both the /chat and /chat/confirm endpoints import this same agent object.
agent, memory = build_graph()


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_thread_config(session_id: str) -> dict:
    """
    Returns the LangGraph config dict for a given session.
    thread_id ties this invoke() call to a specific conversation history
    in the MemorySaver. Always pass this config when calling agent.invoke()
    or agent.astream_events().
    """
    return {"configurable": {"thread_id": session_id}}


def create_initial_state(
    session_id: str,
    user_message: str,
    dataset_metadata: dict | None = None,
    analysis_cache: dict | None = None,
) -> dict:
    """
    Factory function for the initial state dict on the FIRST message of a session.
    Subsequent messages don't need this — the graph reads from the checkpointer.

    Required fields with non-Optional types need explicit defaults:
    - is_destructive, validation_passed, confirmed, retry_count
    """
    from langchain_core.messages import HumanMessage

    return {
        "messages":         [HumanMessage(content=user_message)],
        "session_id":       session_id,
        "dataset_metadata": dataset_metadata,
        "analysis_cache":   analysis_cache,
        "planned_action":   None,
        "tool_args":        None,
        "is_destructive":   False,
        "tool_output":      None,
        "validation_passed": False,
        "retry_count":      0,
        "confirmed":        False,
        "final_response":   None,
        "plan_steps":       [],
    }


def create_followup_state(user_message: str) -> dict:
    """
    For subsequent messages in the SAME session, we only need to inject
    the new HumanMessage — the graph reads all other state from the checkpointer.
    Reset volatile fields so the previous turn's values don't bleed through.
    """
    from langchain_core.messages import HumanMessage

    return {
        "messages":          [HumanMessage(content=user_message)],
        "planned_action":    None,
        "tool_args":         None,
        "is_destructive":    False,
        "tool_output":       None,
        "validation_passed": False,
        "retry_count":       0,
        "confirmed":         False,
        "final_response":    None,
        "plan_steps":        [],
    }
