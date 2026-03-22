""" Deterministic Insights Generation 
    |
    |-- generate_dataset_summary()
    |-- generate_missing_insights()
    |-- generate_skewness_insights()
    |-- generate_target_insight()
    |-- generate_correlation_insight()
    |-- generate_all_insights()
"""

def generate_dataset_summary(metadata):
    return (
        f"The dataset contains {metadata['num_rows']} rows and "
        f"{metadata['num_columns']} columns including "
        f"{len(metadata['column_types']['numerical'])} numerical and "
        f"{len(metadata['column_types']['categorical'])} categorical features."
    )

def generate_missing_insights(data_quality):
    insights = []

    high_missing = data_quality["missing_report"]["high_missing_columns"]
    moderate_missing = data_quality["missing_report"]["moderate_missing_columns"]

    if high_missing:
        insights.append(
            f"Columns {high_missing} have very high missing values (>50%) and may be dropped."
        )

    if moderate_missing:
        insights.append(
            f"Columns {moderate_missing} have moderate missing values and may require imputation."
        )

    return insights

def generate_skewness_insights(data_quality):
    skewed = data_quality["high_skew_columns"]

    if not skewed:
        return []

    return [
        f"Columns {skewed} are highly skewed and may benefit from log transformation."
    ]

def generate_target_insight(selected):
    target = selected["target_column"]
    problem_type = selected["problem_type"]

    if not target:
        return "No clear target variable detected."

    if problem_type == "regression":
        return f"{target} is identified as a regression target."

    return f"{target} is identified as a classification target."


def generate_correlation_insight(selected):
    pairs = selected["correlation_pairs"]

    if not pairs:
        return []

    return [
        f"Strong relationships observed between {pairs}."
    ]

def generate_all_insights(metadata, data_quality, selected):
    insights = {
        "summary": generate_dataset_summary(metadata),
        "missing": generate_missing_insights(data_quality),
        "skewness": generate_skewness_insights(data_quality),
        "target": generate_target_insight(selected),
        "correlation": generate_correlation_insight(selected)
    }

    return insights