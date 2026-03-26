import os
import json
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

grok_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(api_key=grok_api_key, model_name="openai/gpt-oss-120b")
output_parser = StrOutputParser()

def build_compact_context(metadata, data_quality, selected):
    compact = {
        "dataset_shape": f"{metadata.get('num_rows', 0)} rows, {metadata.get('num_columns', 0)} cols",
        "target": selected.get("target_column"),
        "problem_type": selected.get("problem_type"),
        "selected_features": selected.get("numerical_columns", []) + selected.get("categorical_columns", []),
        "key_issues": {
            "high_missing": data_quality.get("missing_report", {}).get("high_missing_columns", []),
            "skewed": data_quality.get("high_skew_columns", []),
            "correlation_pairs": selected.get("correlation_pairs", [])
        }
    }
    
    stats = {}
    num_summary = metadata.get("numerical_summary", {})
    cat_summary = metadata.get("categorical_summary", {})
    
    for col in compact["selected_features"] + ([compact["target"]] if compact["target"] else []):
        if col in num_summary:
            s = num_summary[col]
            stats[col] = f"num(mean={round(s.get('mean',0),1)}, std={round(s.get('std',0),1)}, skew={round(s.get('skewness',0),1)})"
        elif col in cat_summary:
            stats[col] = f"cat(unique={cat_summary[col].get('unique_count')})"
            
    compact["feature_stats"] = stats
    return json.dumps(compact)


def get_llm_insights(metadata, data_quality, selected):
    system_prompt = """
        You are a senior data analyst.
        You will be given a compact summary of a dataset.
        Your task is to provide a comprehensive analysis of the dataset.
        
        Compact Context:
        {compact_context}

        Provide:
            1. Key insights
            2. Data issues
            3. Modelling suggestions
            4. Business interpretation
        
        Keep it clear and concise.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Generate insights based on the above information.")
    ])

    chain = prompt | llm | output_parser
    return chain.invoke({
        "compact_context": build_compact_context(metadata, data_quality, selected)
    })



def get_llm_target_selection(candidates: list, metadata: dict) -> dict:
    """
    Phase 2: Ask LLM to pick the most appropriate target column from a
    short list of smart-filtered candidates. Returns:
      {"target_column": str, "problem_type": "regression"|"classification", "reason": str}
    Falls back to candidates[0] if LLM fails or returns invalid JSON.
    """
    # Build a compact summary of each candidate for the LLM
    candidate_stats = []
    num_summary = metadata.get("numerical_summary", {})
    cat_summary = metadata.get("categorical_summary", {})
    unique_counts = metadata.get("unique_counts", {})

    for col in candidates:
        if col in num_summary:
            s = num_summary[col]
            candidate_stats.append(
                f"{col} (numerical): unique={unique_counts.get(col)}, "
                f"mean={round(s.get('mean',0),2)}, std={round(s.get('std',0),2)}, "
                f"min={s.get('min')}, max={s.get('max')}, skew={round(s.get('skewness',0),2)}"
            )
        elif col in cat_summary:
            top = list(cat_summary[col].get("top_values", {}).keys())[:3]
            candidate_stats.append(
                f"{col} (categorical): unique={unique_counts.get(col)}, top classes={top}"
            )

    candidates_text = "\n".join(candidate_stats)

    system_prompt = """You are a machine learning expert. 
Given a list of candidate target columns from a dataset, select the one most suitable as the target/label for supervised learning.

Candidates:
{candidates}

All column names in dataset: {all_columns}

Reply with ONLY a JSON object on one line, no markdown:
{{"target_column": "<column_name>", "problem_type": "regression", "reason": "<one sentence>"}} 
or
{{"target_column": "<column_name>", "problem_type": "classification", "reason": "<one sentence>"}}"""

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "Pick the target.")])
    chain = prompt | llm | output_parser

    try:
        raw = chain.invoke({
            "candidates": candidates_text,
            "all_columns": ", ".join(metadata.get("columns", []))
        })
        # Strip markdown fences if model wraps in ```json
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)
        # Validate the returned column is actually in candidates
        if result.get("target_column") in candidates:
            return result
    except Exception:
        pass

    # Fallback: return first candidate, infer problem_type from dtype
    fallback_col = candidates[0]
    fallback_type = "regression" if fallback_col in metadata.get("column_types", {}).get("numerical", []) else "classification"
    return {"target_column": fallback_col, "problem_type": fallback_type, "reason": "LLM fallback — first ranked candidate"}