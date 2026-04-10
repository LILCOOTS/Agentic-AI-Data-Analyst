# tools/wrapper.py
# ─────────────────────────────────────────────────────────────────────────────
# The Tool Registry — the @tool decorated functions that "open the room"
# for the agent to call existing deterministic tools.
#
# KEY CONCEPT — @tool decorator:
#   In LangChain you already know chains. Tools are different:
#   @tool wraps a Python function so the LLM can SEE it.
#   The function's DOCSTRING becomes the LLM's description of what the tool does.
#   The TYPE HINTS on the arguments tell the LLM what inputs to provide.
#
#   The LLM never executes the function — it just says:
#   "I want to call run_automl_tool with these args."
#   The Executor node then actually calls it. Pure Python. Deterministic.
#
# KEY CONCEPT — Tool Registry (dict pattern):
#   Instead of if/elif chains ("if action == 'run_model': ..."),
#   we map action names to tool functions in a dict.
#   Executor does: TOOL_REGISTRY[planned_action](**tool_args)
#   Clean, extensible — add a new tool by adding one dict entry.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import numpy as np
import pandas as pd
from langchain_core.tools import tool

from core.session_manager import session_manager
from tools.profiling import extract_metadata
from tools.data_quality import analyze_data_quality
from tools.eda import run_full_analysis
from tools.data_cleaning import generate_cleaning_action_report
from tools.apply_cleaning import apply_cleaning
from tools.modeling import run_modeling
from tools.code_executor import run_query, safe_exec


# ── Tool 1: Profile Dataset ───────────────────────────────────────────────────

@tool
def profile_dataset(session_id: str) -> dict:
    """
    Run full EDA profiling on the uploaded dataset.
    Generates statistical summary, correlation analysis, key findings,
    and Plotly chart JSON for all univariate and bivariate plots.
    Use when the user asks to analyze, explore, or understand the dataset.
    """
    session = session_manager.get_session(session_id)
    if session.working_dataset is None:
        return {"error": "No dataset uploaded for this session."}

    results = run_full_analysis(
        session.working_dataset,
        session.metadata,
        session.data_quality
    )
    session.analysis_cache = results
    return {
        "status": "success",
        "summary": results.get("insights", {}).get("general", {}).get("summary", ""),
        "key_findings": results.get("insights", {}).get("key_findings", []),
        "correlation_ranking": results.get("insights", {}).get("correlation_ranking", []),
        "target_column": results.get("selected_columns", {}).get("target_column"),
        "problem_type": results.get("selected_columns", {}).get("problem_type"),
    }


# ── Tool 2: Clean Dataset ─────────────────────────────────────────────────────

@tool
def clean_dataset(session_id: str) -> dict:
    """
    Auto-clean the uploaded dataset.
    Drops ID columns, encodes categorical variables, imputes missing values,
    and removes high-cardinality features. PERMANENTLY modifies the working dataset.
    Use when the user says 'clean', 'preprocess', or 'prepare the data'.
    """
    session = session_manager.get_session(session_id)
    if session.working_dataset is None:
        return {"error": "No dataset found. Upload a CSV first."}

    target_col = None
    if session.analysis_cache and "selected_columns" in session.analysis_cache:
        target_col = session.analysis_cache["selected_columns"].get("target_column")

    actions = generate_cleaning_action_report(
        session.metadata, session.data_quality, target_col=target_col
    )
    cleaned_df, cleaning_log = apply_cleaning(session.raw_dataset, actions)

    session.working_dataset = cleaned_df
    session.metadata = extract_metadata(cleaned_df)
    session.data_quality = analyze_data_quality(session.metadata)
    session.analysis_cache = None   # bust stale cache — data changed

    return {
        "status": "success",
        "rows_before": int(session.raw_dataset.shape[0]),
        "rows_after":  int(cleaned_df.shape[0]),
        "cols_before": int(session.raw_dataset.shape[1]),
        "cols_after":  int(cleaned_df.shape[1]),
        "actions_applied": len([l for l in cleaning_log if l["status"] != "skipped — already removed"]),
        "cleaning_log": cleaning_log[:5],   # top 5 actions for summary
    }


# ── Tool 3: Run AutoML ────────────────────────────────────────────────────────

@tool
def run_automl_tool(session_id: str) -> dict:
    """
    Train an AutoML VotingEnsemble on the working dataset using 5-fold CV.
    Trains Logistic Regression, Random Forest, and Gradient Boosting.
    Returns accuracy, CV score, ROC-AUC, F1, and feature importance.
    Use when the user says 'train', 'model', 'predict', or 'build a classifier'.
    Requires the dataset to have been profiled first (/get_full_analysis).
    """
    session = session_manager.get_session(session_id)
    if session.working_dataset is None:
        return {"error": "No dataset found. Upload a CSV first."}
    if not session.analysis_cache or "selected_columns" not in session.analysis_cache:
        return {"error": "Run profiling first so the agent knows the target column."}

    selected   = session.analysis_cache["selected_columns"]
    target_col = selected.get("target_column")
    prob_type  = selected.get("problem_type")

    results = run_modeling(session.working_dataset, target_col, prob_type)
    session.modelling_results = results  # store fitted model for predict_instance

    top_features = results.get("feature_importance", [])[:5]

    return {
        "status": "success",
        "problem_type":   results["problem_type"],
        "target_column":  target_col,
        "best_model":     results["best_model"],
        "metric_name":    results["metric_name"],
        "metric_value":   results["metric_value"],
        "cv_score_mean":  results["cv_score_mean"],
        "cv_score_std":   results["cv_score_std"],
        "extra_metrics":  results.get("extra_metrics", {}),
        "top_features":   top_features,
        "rows_trained":   results["rows_trained"],
        "rows_tested":    results["rows_tested"],
    }


# ── Tool 4: Predict Instance ──────────────────────────────────────────────────

@tool
def predict_instance(session_id: str, feature_values: dict) -> dict:
    """
    Run a single prediction through the trained model.
    Provide feature_values as a dict of {column_name: value} pairs.
    Example: {"Age": 45, "Balance": 120000, "Geography": "Germany"}
    Use when the user asks 'what would happen if...', 'predict for this person',
    or provides specific feature values and wants a prediction.
    Requires a trained model (run_automl first).
    """
    session = session_manager.get_session(session_id)
    model_results = session.modelling_results
    if not model_results:
        return {"error": "No trained model found. Run the AutoML pipeline first."}

    model   = model_results.get("fitted_model")
    scaler  = model_results.get("fitted_scaler")
    columns = model_results.get("feature_columns")

    if model is None or scaler is None or not columns:
        return {"error": "Fitted model objects not found in session. Re-run modeling."}

    # Build a single-row DataFrame aligned to training column order
    row = {col: 0 for col in columns}   # start with zeros (handles dummies safely)
    for col, val in feature_values.items():
        if col in row:
            row[col] = val
        else:
            # Try matching dummy-encoded columns e.g. Geography_Germany
            for dummy_col in columns:
                if dummy_col.startswith(f"{col}_") and str(val) in dummy_col:
                    row[dummy_col] = 1

    X_input = pd.DataFrame([row])[columns]
    X_scaled = scaler.transform(X_input)

    prob_type = model_results.get("problem_type", "classification")
    if prob_type == "classification":
        prediction = model.predict(X_scaled)[0]
        try:
            probabilities = model.predict_proba(X_scaled)[0]
            confidence = float(max(probabilities))
            churn_prob = float(probabilities[1]) if len(probabilities) > 1 else confidence
        except Exception:
            confidence = None
            churn_prob = None
        return {
            "status":      "success",
            "prediction":  int(prediction),
            "confidence":  round(confidence, 4) if confidence else None,
            "target_prob": round(churn_prob, 4) if churn_prob else None,
            "interpretation": f"Predicted class: {int(prediction)} with {confidence*100:.1f}% confidence"
        }
    else:
        prediction = model.predict(X_scaled)[0]
        if model_results.get("extra_metrics", {}).get("is_log_transformed"):
            prediction = np.expm1(prediction)
        return {
            "status":     "success",
            "prediction": round(float(prediction), 2),
            "interpretation": f"Predicted value: {round(float(prediction), 2)}"
        }


# ── Tool 5: Compare Pre/Post Clean ───────────────────────────────────────────

@tool
def compare_pre_post_clean(session_id: str) -> dict:
    """
    Compare dataset statistics before and after cleaning.
    Shows column count, missing value changes, and shape differences.
    Use when the user asks 'what changed after cleaning?' or 'show the effect of cleaning'.
    """
    session = session_manager.get_session(session_id)
    if session.raw_dataset is None:
        return {"error": "No original dataset found."}
    if session.working_dataset is None:
        return {"error": "No cleaned dataset found. Run cleaning first."}

    raw = session.raw_dataset
    clean = session.working_dataset

    return {
        "status": "success",
        "original":  {"rows": int(raw.shape[0]),   "cols": int(raw.shape[1]),
                      "missing_cells": int(raw.isnull().sum().sum())},
        "cleaned":   {"rows": int(clean.shape[0]), "cols": int(clean.shape[1]),
                      "missing_cells": int(clean.isnull().sum().sum())},
        "cols_removed": list(set(raw.columns) - set(clean.columns)),
        "cols_added":   list(set(clean.columns) - set(raw.columns)),
    }


# ── Tool 6: Execute Code / NL Query ─────────────────────────────────────────────
# THE differentiating tool. Unlike all others, this one does NOT call a
# predefined API endpoint. Instead:
#   1. LLM generates novel pandas code from the user's NL question
#   2. That code runs against the live DataFrame in a safe sandbox
#   3. Any question, any computation, any filter = possible
# No button on the dashboard can replicate this.

@tool
def execute_query_tool(session_id: str, query: str) -> dict:
    """
    Answer any data question by generating and executing pandas code on the
    live dataset. Use for:
      - Counting/filtering: 'how many customers in Germany?', 'find rows where...'
      - Aggregations: 'average balance by geography', 'churn rate per age group'
      - Distribution checks: 'show the distribution of CreditScore'
      - Outlier detection: 'find outliers in Balance'
      - Correlation checks: 'correlation between Age and churn'
      - Any custom computation the user describes
    The agent writes pandas code and executes it safely. Result is real data,
    not a hallucinated answer.
    """
    session = session_manager.get_session(session_id)
    if session.working_dataset is None:
        return {"error": "No dataset found. Upload a CSV first."}

    return run_query(query, session.working_dataset, session.raw_dataset)


# ── Tool Registry ─────────────────────────────────────────────────────────────
# The Executor imports this dict and does: TOOL_REGISTRY[planned_action](**args)
# To add a new tool: write the @tool function above and add one entry here.

TOOL_REGISTRY: dict = {
    "profile":     profile_dataset,
    "run_clean":   clean_dataset,
    "run_model":   run_automl_tool,
    "predict":     predict_instance,
    "compare":     compare_pre_post_clean,
    "query":       execute_query_tool,   # ⭐ the new agentic tool
    # "answer" is NOT in the registry — it routes directly to Synthesizer (no tool needed)
}
