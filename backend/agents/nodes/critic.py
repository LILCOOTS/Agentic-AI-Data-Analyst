# agents/nodes/critic.py
# ─────────────────────────────────────────────────────────────────────────────
# The Critic Node — validates the plan and gates destructive actions.
#
# KEY CONCEPT — NodeInterrupt:
#   This is NOT a normal Python exception that crashes the program.
#   It's a LangGraph "soft pause" that:
#     1. Saves the entire current graph state to the checkpointer (MemorySaver)
#     2. Returns control back to the caller (/chat endpoint) with the interrupt message
#     3. Waits — doing nothing — until the caller explicitly resumes it
#
#   Resume happens when /chat/confirm is called:
#     graph.invoke(None, config={"configurable": {"thread_id": session_id}})
#     → The None input means "continue from where you paused"
#     → Graph picks up exactly at the Executor node (after Critic)
#
#   This is how LangGraph prevents an AI from autonomously deleting data.
#
# KEY CONCEPT — MemorySaver (referenced here, configured in graph.py):
#   The checkpointer stores the paused graph state in memory, keyed by thread_id.
#   thread_id = session_id in our app (one conversation thread per session).
#   Without a checkpointer, NodeInterrupt has nowhere to save state and fails.
#
# KEY CONCEPT — What else the Critic does:
#   Beyond the pause gate, the Critic does pre-flight validation:
#   - If user asks to predict but no model exists → redirect to "answer" with a hint
#   - If user asks to model but no dataset → redirect to "answer" with a hint
#   This prevents the Executor from crashing on precondition failures.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from langgraph.errors import NodeInterrupt

from agents.state import AgentState
from core.session_manager import session_manager


# ── Confirmation messages shown to the user before destructive actions ─────────
# These are rendered as markdown in the chat panel's confirmation dialog.
CONFIRMATION_MESSAGES: dict[str, str] = {
    "run_clean": (
        "🧹 **I'm about to auto-clean your dataset.**\n\n"
        "**What will happen:**\n"
        "- Drop ID columns (RowNumber, CustomerId, etc.)\n"
        "- Remove high-cardinality text columns (like Surname)\n"
        "- Encode categorical columns (Geography, Gender → numeric)\n"
        "- Impute or drop missing values\n\n"
        "⚠️ This **permanently replaces your working dataset**. "
        "The original is preserved for comparison.\n\n"
        "Confirm to proceed or cancel to stop."
    ),
    "run_model": (
        "🧠 **I'm about to train the AutoML ensemble.**\n\n"
        "**What will happen:**\n"
        "- Train 3 models: Logistic Regression, Random Forest, Gradient Boosting\n"
        "- Run 5-fold cross-validation on all of them\n"
        "- Build a VotingEnsemble from the top performers\n"
        "- Store the fitted model for instant predictions\n\n"
        "⏱️ This takes **30–90 seconds** depending on dataset size.\n\n"
        "Confirm to proceed or cancel to stop."
    ),
}


def critic_node(state: AgentState) -> dict:
    """
    Validates the Planner's decision before the Executor runs.
    - Performs pre-flight checks (is model trained? is dataset uploaded?)
    - For destructive actions: raises NodeInterrupt to pause and ask the user
    - For safe actions: returns empty dict (auto-approved, no state changes needed)
    """
    action     = state.get("planned_action")
    session_id = state.get("session_id")

    # ── Pre-flight Validation ──────────────────────────────────────────────────
    # These checks prevent the Executor from crashing on precondition failures.
    # Instead of an error, we redirect to "answer" with a helpful message.

    try:
        session = session_manager.get_session(session_id)
    except Exception:
        # Session not found — can't do anything, surface a message
        return {
            "planned_action":  "answer",
            "validation_passed": True,
            "final_response": "❌ Session not found. Please upload a new dataset to start.",
        }

    if action == "predict":
        if not session.modelling_results:
            # Predict requested but no model trained yet — redirect gracefully
            return {
                "planned_action":  "answer",
                "validation_passed": True,
                "final_response": (
                    "⚠️ **No trained model found.** I can't make predictions yet.\n\n"
                    "Please say **'train the model'** first and I'll build the AutoML pipeline."
                ),
            }

    if action in ("run_model", "run_clean"):
        if session.working_dataset is None:
            return {
                "planned_action":  "answer",
                "validation_passed": True,
                "final_response": "❌ No dataset found. Please upload a CSV file first.",
            }

    if action == "run_model":
        if not session.analysis_cache:
            return {
                "planned_action":  "answer",
                "validation_passed": True,
                "final_response": (
                    "⚠️ Dataset hasn't been profiled yet. I'll need to run EDA first "
                    "to identify the target column.\n\nSay **'analyze the dataset'** and "
                    "I'll do that, then we can train the model."
                ),
            }

    # ── Destructive Action Gate ────────────────────────────────────────────────
    # If the action permanently modifies the session, pause and ask the user.
    # NodeInterrupt saves all current state to MemorySaver and returns the
    # message to the /chat endpoint. Graph resumes when /chat/confirm is called.
    #
    # KEY CONCEPT — Why we check `confirmed` here:
    #   When NodeInterrupt is raised, LangGraph saves state with next=["critic"].
    #   On resume (after user clicks Confirm), the graph REPLAYS the Critic node.
    #   Without this check the Critic would raise NodeInterrupt again — infinite loop.
    #   /chat/confirm calls agent.update_state({"confirmed": True}) BEFORE resuming,
    #   so this check sees True on the replay and skips the interrupt cleanly.
    #   We immediately reset confirmed → False so it doesn't bleed into future turns.

    if state.get("is_destructive") and action in CONFIRMATION_MESSAGES:
        if state.get("confirmed"):
            # User clicked Confirm → skip the interrupt on this replay run
            print(f"[Critic] Confirmed — proceeding to Executor: {action}")
            return {"confirmed": False}   # reset for next turn

        print(f"[Critic] Pausing for human confirmation: {action}")
        raise NodeInterrupt(CONFIRMATION_MESSAGES[action])

    # ── Safe Action — Auto-approved ────────────────────────────────────────────
    # profile, predict, compare, answer — no confirmation needed.
    print(f"[Critic] Auto-approved safe action: {action}")
    return {}   # Return empty dict — LangGraph merges nothing, state unchanged

