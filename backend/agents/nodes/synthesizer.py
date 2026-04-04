# agents/nodes/synthesizer.py
# ─────────────────────────────────────────────────────────────────────────────
# The Synthesizer Node — the only output-facing LLM in the graph.
#
# KEY CONCEPT — How streaming works (two levels):
#   Level 1 (this node): calls llm.invoke() — gets the full response at once.
#   Level 2 (graph.py):  the /chat endpoint calls graph.astream_events() which
#                        intercepts ALL LangChain LLM calls happening inside
#                        nodes and emits token-by-token events automatically.
#
#   You don't need special code HERE for streaming. When astream_events() is
#   running the graph, any llm.invoke() call inside a node automatically fires
#   "on_chat_model_stream" events that the /chat endpoint can forward as SSE.
#
# KEY CONCEPT — How Synthesizer completes the memory circle:
#   Every node that writes a response MUST add it to state["messages"] as an
#   AIMessage. That's how the conversation history stays complete.
#
#   state["messages"] = [...HumanMessage("train model"), AIMessage("Done! ✅...")]
#                                                         ↑ added by Synthesizer
#
#   Next turn, the Planner reads ALL messages and has full conversation context.
#   Without this, the agent would forget every response it ever gave.
#
# KEY CONCEPT — Pre-baked responses (from Critic pre-flight redirects):
#   When the Critic catches a precondition failure (no model, no dataset, etc.)
#   it sets final_response directly and the executor never runs.
#   The Synthesizer detects this with:
#       pre_baked AND tool never ran ("status" not "success"/"error")
#   → skips the LLM, returns the pre-baked message directly.
#   This saves latency and avoids hallucinating a response for error cases.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
import json

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from agents.state import AgentState

load_dotenv()

# ── LLM Setup ─────────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
)
chain = llm | StrOutputParser()


# ── Context Formatters ─────────────────────────────────────────────────────────
# These convert raw tool_output dicts into clean human-readable summaries
# that go into the system prompt. We never dump raw JSON to the LLM —
# structured formatting reduces hallucination risk significantly.

def _format_model_result(output: dict) -> str:
    prob_type  = output.get("problem_type", "unknown")
    target     = output.get("target_column", "the target")
    best       = output.get("best_model", "unknown").replace("_", " ")
    metric     = output.get("metric_name", "metric")
    value      = output.get("metric_value")
    cv_mean    = output.get("cv_score_mean")
    cv_std     = output.get("cv_score_std")
    extra      = output.get("extra_metrics", {})
    top_feats  = output.get("top_features", [])

    feat_lines = "\n".join(
        f"  - {f['feature']}: {f['importance']*100:.1f}%"
        for f in top_feats[:5]
    ) if top_feats else "  - (not available)"

    extra_str = "\n".join(
        f"  - {k.replace('_',' ').title()}: {v:.4f}" for k, v in extra.items()
    ) if extra else ""

    return f"""
AutoML Pipeline Results:
- Problem type: {prob_type}
- Target column: {target}
- Best base model: {best}
- Primary metric ({metric}): {value}
- Cross-validation: {cv_mean} ± {cv_std}
{extra_str}
Top 5 features by importance:
{feat_lines}
"""


def _format_clean_result(output: dict) -> str:
    rows_b = output.get("rows_before", "?")
    rows_a = output.get("rows_after", "?")
    cols_b = output.get("cols_before", "?")
    cols_a = output.get("cols_after", "?")
    n_acts = output.get("actions_applied", 0)
    log    = output.get("cleaning_log", [])

    log_lines = "\n".join(
        f"  - {l.get('column', '?')}: {l.get('action', '?')} ({l.get('status', '')})"
        for l in log[:5]
    )

    return f"""
Cleaning Results:
- Rows: {rows_b} → {rows_a}
- Columns: {cols_b} → {cols_a}
- Actions applied: {n_acts}
Sample actions:
{log_lines}
"""


def _format_predict_result(output: dict) -> str:
    return f"""
Prediction Result:
- Predicted value: {output.get('prediction')}
- Confidence: {f"{output.get('confidence', 0)*100:.1f}%" if output.get('confidence') else 'N/A'}
- Target probability: {f"{output.get('target_prob', 0)*100:.1f}%" if output.get('target_prob') else 'N/A'}
- Interpretation: {output.get('interpretation', '')}
"""


def _format_profile_result(output: dict) -> str:
    findings = "\n".join(f"  - {f}" for f in output.get("key_findings", [])[:3])
    ranking  = "\n".join(
        f"  - {r['feature']}: {r['correlation']*100:.1f}%"
        for r in output.get("correlation_ranking", [])[:5]
    )
    return f"""
EDA Profile Results:
- Summary: {output.get('summary', '')}
- Target: {output.get('target_column')} ({output.get('problem_type')})
Key findings:
{findings}
Top correlated features:
{ranking}
"""


def _format_compare_result(output: dict) -> str:
    orig  = output.get("original", {})
    clean = output.get("cleaned", {})
    removed = output.get("cols_removed", [])
    added   = output.get("cols_added", [])
    return f"""
Before/After Comparison:
- Original:  {orig.get('rows')} rows × {orig.get('cols')} cols, {orig.get('missing_cells')} missing cells
- Cleaned:   {clean.get('rows')} rows × {clean.get('cols')} cols, {clean.get('missing_cells')} missing cells
- Columns removed: {', '.join(removed) if removed else 'none'}
- Columns added (dummies): {len(added)} new columns
"""


FORMATTERS = {
    "run_model": _format_model_result,
    "run_clean": _format_clean_result,
    "predict":   _format_predict_result,
    "profile":   _format_profile_result,
    "compare":   _format_compare_result,
}


# ── The Synthesizer Node Function ──────────────────────────────────────────────

def synthesizer_node(state: AgentState) -> dict:
    """
    Converts tool output into a human-readable markdown response.
    Adds the AI response to messages (completing the memory circle).
    Handles pre-baked error messages from Critic without an LLM call.
    Handles graceful fallback when retry_count maxed out.
    """
    tool_output = state.get("tool_output") or {}
    action      = state.get("planned_action", "answer")
    retry_count = state.get("retry_count", 0)

    # ── Case 1: Pre-baked message (Critic validation redirect) ────────────────
    # Executor never ran a real tool, Critic already wrote the response.
    tool_ran = tool_output.get("status") in ("success", "error")
    pre_baked = state.get("final_response")

    if pre_baked and not tool_ran:
        print(f"[Synthesizer] Using pre-baked response (no tool ran)")
        return {
            "messages":       [AIMessage(content=pre_baked)],
            "final_response": pre_baked,
        }

    # ── Case 2: Tool errored and retries exhausted ────────────────────────────
    if tool_output.get("status") == "error" and retry_count >= 2:
        err_msg = tool_output.get("error", "Unknown error")
        fallback = (
            f"⚠️ **I ran into an issue after {retry_count} attempts.**\n\n"
            f"Error: `{err_msg}`\n\n"
            "Please check that your dataset is uploaded and properly profiled, "
            "then try again. If the issue persists, try re-uploading the CSV."
        )
        return {
            "messages":       [AIMessage(content=fallback)],
            "final_response": fallback,
        }

    # ── Case 3: Normal synthesis — format tool output and call LLM ───────────
    meta        = state.get("dataset_metadata") or {}
    target      = meta.get("target_column", "the target")
    prob_type   = meta.get("problem_type", "unknown")

    # Format tool output using the appropriate formatter
    formatter = FORMATTERS.get(action)
    tool_context = formatter(tool_output) if formatter else (
        "No tool was run. Answer directly from the conversation context."
    )

    system_prompt = f"""You are a friendly, expert AI Data Analyst assistant embedded in a web dashboard.
You have just run an analysis tool and received structured results. Your job is to communicate
these results clearly to the user in markdown format.

## Dataset Context
- Target variable: {target}
- Problem type: {prob_type}

## Tool Result
{tool_context}

## Response Rules
1. Use the EXACT numbers from the Tool Result — never make up or round metrics.
2. Use markdown: **bold** for key numbers, bullet points for lists, headers for sections.
3. Explain what the numbers mean in plain English (non-technical users should understand).
4. End with a clear, specific suggestion for the next logical step.
5. Be concise — 150–300 words maximum. No waffle.
6. If the tool returned an error, acknowledge it and suggest a remedy.
"""

    messages = [SystemMessage(content=system_prompt)] + list(state.get("messages", []))

    print(f"[Synthesizer] Generating response for action={action}")
    response = chain.invoke(messages)

    return {
        "messages":       [AIMessage(content=response)],
        "final_response": response,
    }
