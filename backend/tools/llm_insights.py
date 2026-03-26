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

def get_llm_insights(metadata, data_quality, selected):
    system_prompt = """
        You are a senior data analyst.
        You will be given metadata, data quality report, and selected columns for analysis.
        Your task is to provide a comprehensive analysis of the dataset.
        
        Metadata:
        {metadata}

        Data Quality:
        {data_quality}

        Selected Columns:
        {selected}

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
        "metadata": metadata,
        "data_quality": data_quality,
        "selected": selected
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