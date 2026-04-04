# agents/nodes/reflector.py
# ─────────────────────────────────────────────────────────────────────────────
# The Reflector Node — output validation and self-correction loop.
#
# KEY CONCEPT — Cycles in LangGraph (what makes it a GRAPH, not a chain):
#   In LangChain, execution flows in one direction: A → B → C → done.
#   In LangGraph, you can create LOOPS: Executor → Reflector → Executor → ...
#
#   This is the graph structure:
#       Executor ──► Reflector ──► Synthesizer   (happy path)
#                        │
#                        └──► Executor           (retry loop, max 2 times)
#
#   The routing decision happens in a CONDITIONAL EDGE function in graph.py:
#       def route_after_reflector(state):
#           if state["validation_passed"]:  return "synthesizer"
#           if state["retry_count"] >= 2:   return "synthesizer"  # forced fallback
#           return "executor"               # loop back
#
#   The Reflector itself only sets validation_passed and retry_count.
#   It doesn't need to know about the graph topology — that's graph.py's job.
#
# KEY CONCEPT — What the Reflector validates (NO LLM involved):
#   The Reflector is pure Python logic. It checks:
#   1. Did the tool return {"status": "error"}? → fail or retry
#   2. Are numeric metrics in sane ranges? (accuracy 0–1, rmse > 0)
#   3. Are required fields present in the output?
#   4. Is the output consistent with what the Planner intended?
#
#   Why not use the LLM to validate? Because LLMs can hallucinate validation
#   results. "Yes this looks correct" from an LLM is not a check.
#   Deterministic Python bounds-checking is always trustworthy.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from agents.state import AgentState


# ── Validation Rules ──────────────────────────────────────────────────────────
# Each validator takes tool_output and returns (passed: bool, reason: str).
# reason is logged for debugging; on failure it becomes part of the retry context.

def _validate_model_output(output: dict) -> tuple[bool, str]:
    """Validate AutoML tool output — metrics must be sane numbers."""
    metric = output.get("metric_value")
    cv     = output.get("cv_score_mean")

    if metric is None or cv is None:
        return False, "Missing metric_value or cv_score_mean in model output."

    prob_type = output.get("problem_type", "classification")
    if prob_type == "classification":
        if not (0.0 <= float(metric) <= 1.0):
            return False, f"Accuracy {metric} out of valid range [0, 1]."
        if not (0.0 <= float(cv) <= 1.0):
            return False, f"CV score {cv} out of valid range [0, 1]."
    else:
        if float(metric) < 0:
            return False, f"RMSE {metric} cannot be negative."

    top_features = output.get("top_features", [])
    if not top_features:
        return False, "No feature importance data returned."

    return True, "Model output valid."


def _validate_clean_output(output: dict) -> tuple[bool, str]:
    """Validate cleaning tool output — row/col counts must be positive integers."""
    rows_after = output.get("rows_after")
    cols_after = output.get("cols_after")

    if rows_after is None or cols_after is None:
        return False, "Missing rows_after or cols_after in cleaning output."
    if int(rows_after) == 0:
        return False, "Cleaning removed ALL rows — something went wrong."
    if int(cols_after) == 0:
        return False, "Cleaning removed ALL columns — something went wrong."

    return True, "Cleaning output valid."


def _validate_predict_output(output: dict) -> tuple[bool, str]:
    """Validate prediction output — must have a prediction value."""
    prediction = output.get("prediction")

    if prediction is None:
        return False, "No prediction value returned."
    try:
        float(prediction)
    except (TypeError, ValueError):
        return False, f"Prediction value {prediction!r} is not a valid number."

    return True, "Prediction output valid."


def _validate_profile_output(output: dict) -> tuple[bool, str]:
    """Validate profiling output — must have at least a summary."""
    if not output.get("summary"):
        return False, "Profile output missing summary."
    return True, "Profile output valid."


def _validate_compare_output(output: dict) -> tuple[bool, str]:
    """Validate comparison output — must have both original and cleaned stats."""
    if not output.get("original") or not output.get("cleaned"):
        return False, "Compare output missing original or cleaned stats block."
    return True, "Comparison output valid."


# Action → validator mapping
VALIDATORS = {
    "run_model": _validate_model_output,
    "run_clean": _validate_clean_output,
    "predict":   _validate_predict_output,
    "profile":   _validate_profile_output,
    "compare":   _validate_compare_output,
}


# ── The Reflector Node Function ────────────────────────────────────────────────

def reflector_node(state: AgentState) -> dict:
    """
    Validates the Executor's tool_output against deterministic rules.
    Sets validation_passed = True → Synthesizer runs.
    Sets validation_passed = False + increments retry_count → Executor retries.
    After 2 retries, forces validation_passed = True so Synthesizer can give a
    graceful error message instead of looping forever.
    """
    tool_output = state.get("tool_output") or {}
    action      = state.get("planned_action")
    retry_count = state.get("retry_count", 0)

    # ── Fast-pass cases ────────────────────────────────────────────────────────

    # Tool errored at the Python level → no point retrying unless within limit
    if tool_output.get("status") == "error":
        error_msg = tool_output.get("error", "Unknown error")
        print(f"[Reflector] Tool error: {error_msg} | retry_count={retry_count}")
        if retry_count >= 2:
            # Max retries reached — let Synthesizer give graceful fallback
            return {"validation_passed": True, "retry_count": retry_count}
        return {"validation_passed": False, "retry_count": retry_count + 1}

    # No tool ran (action = "answer") — nothing to validate
    if tool_output.get("status") == "no_tool":
        print("[Reflector] No tool ran — auto-passing.")
        return {"validation_passed": True, "retry_count": 0}

    # ── Validated Checks ───────────────────────────────────────────────────────
    validator = VALIDATORS.get(action)

    if validator is None:
        # Unknown action — pass through, Synthesizer handles it
        print(f"[Reflector] No validator for action={action} — auto-passing.")
        return {"validation_passed": True, "retry_count": retry_count}

    passed, reason = validator(tool_output)
    print(f"[Reflector] Validation {'PASSED' if passed else 'FAILED'}: {reason}")

    if passed:
        return {"validation_passed": True, "retry_count": 0}

    # Validation failed — retry if under limit, else force-pass for graceful fallback
    if retry_count >= 2:
        print("[Reflector] Max retries reached — forcing pass for graceful fallback.")
        return {"validation_passed": True, "retry_count": retry_count}

    return {"validation_passed": False, "retry_count": retry_count + 1}
