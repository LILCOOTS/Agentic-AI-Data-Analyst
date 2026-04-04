# agents/nodes/executor.py
# ─────────────────────────────────────────────────────────────────────────────
# The Executor Node — pure deterministic dispatch. No LLM involved here.
#
# KEY CONCEPT — What the Executor does:
#   The Planner said: planned_action = "run_clean", tool_args = {"session_id": "abc"}
#   The Executor does exactly one thing:
#       TOOL_REGISTRY["run_clean"](session_id="abc")
#   That's it. No LLM. No decisions. Just Python function dispatch.
#
#   This separation is intentional:
#   - LLM decides WHAT to run  (Planner)
#   - Python decides HOW to run it (Executor)
#   - LangGraph decides IF to run it (Critic gate + conditional edges)
#
# KEY CONCEPT — Why not just call the tool in the Planner?
#   Because we need the Critic to inspect and potentially block the action
#   BEFORE execution. The graph routing is:
#       Planner → Critic (validates) → Executor (runs) → Reflector (checks output)
#   If Planner called the tool itself, the Critic would have nothing to intercept.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from agents.state import AgentState
from tools.wrapper import TOOL_REGISTRY


def executor_node(state: AgentState) -> dict:
    """
    Deterministic tool dispatcher.
    Reads planned_action and tool_args from state.
    Calls the corresponding tool from TOOL_REGISTRY.
    Returns tool_output (raw dict) back to state for the Reflector to verify.
    """
    action    = state.get("planned_action")
    tool_args = state.get("tool_args") or {}

    print(f"[Executor] Running tool: {action} with args: {list(tool_args.keys())}")

    # "answer" skips the executor entirely — Planner routes it straight to Synthesizer
    if action == "answer" or action not in TOOL_REGISTRY:
        return {
            "tool_output":        {"status": "no_tool", "action": action},
            "validation_passed":  True,     # nothing to validate — skip Reflector gate
            "retry_count":        0,
        }

    tool_fn = TOOL_REGISTRY[action]

    try:
        # .invoke() is the LangChain @tool standard call method
        # It handles argument validation and error wrapping automatically
        output = tool_fn.invoke(tool_args)

        print(f"[Executor] Tool succeeded: status={output.get('status', 'unknown')}")

        return {
            "tool_output":       output,
            "validation_passed": False,   # Reflector hasn't checked yet
            "retry_count":       state.get("retry_count", 0),
        }

    except Exception as e:
        # Tool raised an exception — surface it as a structured error
        # Reflector will see this and route to Synthesizer with a graceful message
        print(f"[Executor] Tool failed: {e}")
        return {
            "tool_output": {
                "status": "error",
                "error":  str(e),
                "action": action,
            },
            "validation_passed": False,
            "retry_count":       state.get("retry_count", 0) + 1,
        }
