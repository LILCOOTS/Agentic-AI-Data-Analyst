# """ Deterministic Insights Generation 
#     |
#     |-- generate_dataset_summary()
#     |-- generate_missing_insights()
#     |-- generate_skewness_insights()
#     |-- generate_target_insight()
#     |-- generate_correlation_insight()
#     |-- generate_all_insights()
# """

# def generate_dataset_summary(metadata):
#     return (
#         f"The dataset contains {metadata['num_rows']} rows and "
#         f"{metadata['num_columns']} columns including "
#         f"{len(metadata['column_types']['numerical'])} numerical and "
#         f"{len(metadata['column_types']['categorical'])} categorical features."
#     )

# def generate_missing_insights(data_quality):
#     insights = []

#     high_missing = data_quality["missing_report"]["high_missing_columns"]
#     moderate_missing = data_quality["missing_report"]["moderate_missing_columns"]

#     if high_missing:
#         insights.append(
#             f"Columns {high_missing} have very high missing values (>50%) and may be dropped."
#         )

#     if moderate_missing:
#         insights.append(
#             f"Columns {moderate_missing} have moderate missing values and may require imputation."
#         )

#     return insights

# def generate_skewness_insights(data_quality):
#     skewed = data_quality["high_skew_columns"]

#     if not skewed:
#         return []

#     return [
#         f"Columns {skewed} are highly skewed and may benefit from log transformation."
#     ]

# def generate_target_insight(selected):
#     target = selected["target_column"]
#     problem_type = selected["problem_type"]

#     if not target:
#         return "No clear target variable detected."

#     if problem_type == "regression":
#         return f"{target} is identified as a regression target."

#     return f"{target} is identified as a classification target."


# def generate_correlation_insight(selected):
#     pairs = selected["correlation_pairs"]

#     if not pairs:
#         return []

#     return [
#         f"Strong relationships observed between {pairs}."
#     ]

# def generate_all_insights(metadata, data_quality, selected):
#     insights = {
#         "summary": generate_dataset_summary(metadata),
#         "missing": generate_missing_insights(data_quality),
#         "skewness": generate_skewness_insights(data_quality),
#         "target": generate_target_insight(selected),
#         "correlation": generate_correlation_insight(selected)
#     }

#     return insights

from tools.llm_insights import get_llm_insights

def generate_general_insights(metadata, data_quality):
    insights = {
        "summary": "",
        "missing": [],
        "skewness": [],
        "correlation": [],
        "target": ""
    }

    # Summary
    insights["summary"] = (
        f"The dataset contains {metadata['num_rows']} rows and "
        f"{metadata['num_columns']} columns including "
        f"{len(metadata['column_types']['numerical'])} numerical and "
        f"{len(metadata['column_types']['categorical'])} categorical features."
    )

    # Missing values (WITH %)
    for col in data_quality["missing_report"]["high_missing_columns"]:
        pct = metadata["missing_summary"]["per_column"][col]["missing_percentage"]
        insights["missing"].append(
            f"{col} has {pct:.2f}% missing values → recommended to drop."
        )

    for col in data_quality["missing_report"]["moderate_missing_columns"]:
        pct = metadata["missing_summary"]["per_column"][col]["missing_percentage"]
        insights["missing"].append(
            f"{col} has {pct:.2f}% missing values → consider imputation."
        )

    # Skewness (WITH VALUES + IMPACT)
    for col in data_quality["high_skew_columns"]:
        skew = metadata["numerical_summary"][col]["skewness"]
        insights["skewness"].append(
            f"{col} is highly skewed (skewness = {skew:.2f}) → may require log transformation to stabilize variance."
        )

    # Target
    if data_quality["candidate_targets"]:
        target = data_quality["candidate_targets"][0]
        insights["target"] = f"{target} is identified as a regression target."

    return insights

def generate_correlation_insights(correlation_pairs, df):
    insights = []

    for col1, col2 in correlation_pairs:
        corr = df[col1].corr(df[col2])

        if abs(corr) > 0.7:
            strength = "strong"
        elif abs(corr) > 0.4:
            strength = "moderate"
        else:
            strength = "weak"

        direction = "positive" if corr > 0 else "negative"

        insights.append(
            f"{col1} and {col2} have {strength} {direction} correlation (r = {corr:.2f}), "
            f"suggesting that changes in {col1} are associated with {col2}."
        )

    return insights

def generate_key_findings(df, target, numerical_cols):
    correlations = {}

    for col in numerical_cols:
        if col == target:
            continue
        correlations[col] = df[col].corr(df[target])

    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

    findings = []

    for col, corr in sorted_corr[:3]:
        findings.append(
            f"{col} is one of the strongest predictors of {target} (correlation = {corr:.2f})."
        )

    return findings

def generate_target_insights(df, target_column, numerical_cols, categorical_cols):
    insights = []

    # Numerical vs Target
    correlations = {}

    for col in numerical_cols:
        if col == target_column:
            continue

        corr = df[col].corr(df[target_column])
        correlations[col] = corr

    # Sort by importance
    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

    for col, corr in sorted_corr[:5]:
        direction = "positive" if corr > 0 else "negative"
        insights.append(
            f"{col} shows {direction} relationship with {target_column} (r = {corr:.2f}), "
            f"indicating it significantly influences the target."
        )

    # Categorical vs Target
    for col in categorical_cols[:3]:
        grouped = df.groupby(col)[target_column].mean().sort_values(ascending=False)

        top_category = grouped.index[0]
        bottom_category = grouped.index[-1]

        insights.append(
            f"{target_column} varies across {col}: highest for '{top_category}' and lowest for '{bottom_category}', "
            f"suggesting strong categorical influence."
        )

    return insights

def generate_all_insights(df, metadata, data_quality, selected_columns):
    
    general = generate_general_insights(metadata, data_quality)

    key_findings = generate_key_findings(df, selected_columns["target_column"], selected_columns["numerical_columns"])

    correlation = generate_correlation_insights(
        selected_columns["correlation_pairs"], df
    )

    target_insights = generate_target_insights(
        df,
        selected_columns["target_column"],
        selected_columns["numerical_columns"],
        selected_columns["categorical_columns"]
    )

    try:
        llm_insights = get_llm_insights(metadata, data_quality, selected_columns)
    except Exception as e:
        llm_insights = str(e)

    return {
        "general": general,
        "key_findings": key_findings,
        "correlation": correlation,
        "target_analysis": target_insights,
        "llm": llm_insights
    }