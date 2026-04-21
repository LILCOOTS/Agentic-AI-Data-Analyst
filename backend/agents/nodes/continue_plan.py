# agents/nodes/continue_plan.py
# ─────────────────────────────────────────────────────────────────────────────
# The ContinuePlan Node — the "gear shift" for multi-step autonomous pipelines.
#
# KEY CONCEPT — Why this node exists:
#   After Synthesizer finishes step N, the graph checks if plan_steps is
#   non-empty. If it is, instead of going to END, it comes here.
#
#   This node pops the next action from plan_steps, loads it into state
#   (planned_action, is_destructive, tool_args), and resets per-step volatile
#   fields (tool_output, retry_count, validation_passed).
#
#   The graph then routes back to Critic — which means:
#   - Destructive steps (run_clean, run_model) still ask for confirmation
#   - Safe steps (profile, query, compare) run automatically
#   - Reflector still validates every step's output
#   - Synthesizer still streams each step's response separately
#
# KEY CONCEPT — Tool args for plan steps:
#   All pipeline actions (profile, run_clean, run_model, compare) only need
#   {"session_id": ...}. This node auto-generates that.
#   If a plan_step is a "query:..." encoded string, it splits out the query.
#   This covers the common "analyze → clean → model" pipeline patterns.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from agents.state import AgentState

# Actions that permanently modify session state — still require HITL confirmation
_DESTRUCTIVE = {"run_clean", "run_model"}


def continue_plan_node(state: AgentState) -> dict:
    """
    Advances to the next step in a multi-step plan.
    Pops the first item from plan_steps, sets it as planned_action,
    and resets all per-step volatile state fields.

    Called by the graph router after Synthesizer when plan_steps is non-empty.
    """
    steps     = list(state.get("plan_steps") or [])
    session_id = state.get("session_id", "")

    if not steps:
        # Guard: shouldn't happen (router checks first) but safe fallback
        return {"plan_steps": []}

    next_action = steps.pop(0)

    # Handle "query:<text>" encoded steps where the query text is embedded
    tool_args = {"session_id": session_id}
    if next_action.startswith("query:"):
        query_text  = next_action[len("query:"):]
        next_action = "query"
        tool_args["query"] = query_text

    print(f"[ContinuePlan] → next step: '{next_action}' | {len(steps)} step(s) remaining")

    return {
        # Advance the action
        "planned_action":  next_action,
        "is_destructive":  next_action in _DESTRUCTIVE,
        "tool_args":       tool_args,
        "plan_steps":      steps,           # shorter list (one item removed)

        # Reset per-step volatile fields so previous step's state doesn't bleed through
        "tool_output":       None,
        "validation_passed": False,
        "retry_count":       0,
        "confirmed":         False,         # each destructive step needs fresh confirmation
        "final_response":    None,
    }
