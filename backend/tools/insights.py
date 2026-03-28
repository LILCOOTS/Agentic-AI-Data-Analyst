from tools.llm_insights import get_llm_insights
import pandas as pd
# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS — column-specific, not generic
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendations(metadata, data_quality, selected_columns):
    recommendations = []

    # Keys live under missing_report (nested), not at the top level
    missing_report = data_quality.get("missing_report", {})

    # High missing → name the columns
    for col in missing_report.get("high_missing_columns", []):
        pct = metadata["missing_summary"]["per_column"].get(col, {}).get("missing_percentage", 0)
        recommendations.append(
            f"Drop '{col}' — {pct:.1f}% of values are missing, making it unreliable for modelling."
        )

    # Moderate missing → imputation suggestion
    for col in missing_report.get("moderate_missing_columns", []):
        pct = metadata["missing_summary"]["per_column"].get(col, {}).get("missing_percentage", 0)
        recommendations.append(
            f"Impute '{col}' ({pct:.1f}% missing) using median or model-based imputation."
        )

    # Skewed selected columns — per-column recommendation
    for col in selected_columns.get("skewed_columns", []):
        if col not in metadata["numerical_summary"]:
            continue
        skew = metadata["numerical_summary"][col]["skewness"]
        recommendations.append(
            f"Apply log1p transformation to '{col}' (skewness = {skew:.2f}) "
            f"to reduce right-tail distortion and improve linear model performance."
        )

    # ID columns
    for col in data_quality.get("id_like_columns", []):
        recommendations.append(
            f"Remove '{col}' — it appears to be an ID column and will not generalise to unseen data."
        )

    # High cardinality categoricals
    for col in data_quality.get("high_cardinality_columns", []):
        n = metadata["unique_counts"].get(col, "?")
        recommendations.append(
            f"Encode or exclude '{col}' — it has {n} unique values (high cardinality) "
            f"which can cause overfitting with naive encoding."
        )

    # Constant columns only (unique == 1)
    for col in data_quality.get("low_variance_columns", []):
        recommendations.append(
            f"Drop '{col}' — it is a constant column (single unique value) with zero predictive signal."
        )

    # Target present → positive cue
    target = selected_columns.get("target_column")
    if target:
        problem = selected_columns.get("problem_type", "supervised learning")
        recommendations.append(
            f"Target variable '{target}' identified for {problem}. "
            f"Ensure it is not leaked into feature engineering steps."
        )

    return recommendations


# ─────────────────────────────────────────────────────────────────────────────
# GENERAL INSIGHTS — narrative summary, not a count sentence
# ─────────────────────────────────────────────────────────────────────────────

def generate_general_insights(metadata, data_quality, selected_columns=None):
    insights = {
        "summary": "",
        "missing": [],
        "skewness": [],
        "correlation": [],
        "target": ""
    }

    # ── Narrative summary ──────────────────────────────────────────────────
    target = (selected_columns or {}).get("target_column")
    problem = (selected_columns or {}).get("problem_type", "regression")
    num_count = len(metadata["column_types"]["numerical"])
    cat_count = len(metadata["column_types"]["categorical"])

    parts = [
        f"The dataset has {metadata['num_rows']:,} rows and {metadata['num_columns']} columns "
        f"({num_count} numerical, {cat_count} categorical)."
    ]
    if target:
        parts.append(f"'{target}' is identified as the target variable for {problem}.")
    if data_quality["missing_report"]["high_missing_columns"]:
        n = len(data_quality["missing_report"]["high_missing_columns"])
        parts.append(f"{n} column(s) have >50% missing values and are candidates for removal.")
    if data_quality["high_skew_columns"]:
        n = len(data_quality["high_skew_columns"])
        parts.append(f"{n} numerical feature(s) are highly skewed — log transformation is recommended.")

    insights["summary"] = " ".join(parts)

    # ── Missing details ────────────────────────────────────────────────────
    for col in data_quality["missing_report"]["high_missing_columns"]:
        pct = metadata["missing_summary"]["per_column"][col]["missing_percentage"]
        insights["missing"].append(
            f"'{col}' has {pct:.1f}% missing — recommended to drop."
        )
    for col in data_quality["missing_report"]["moderate_missing_columns"]:
        pct = metadata["missing_summary"]["per_column"][col]["missing_percentage"]
        insights["missing"].append(
            f"'{col}' has {pct:.1f}% missing — consider imputation."
        )

    # ── Skewness — only selected columns, not all ─────────────────────────
    selected_skewed = (
        selected_columns.get("skewed_columns", [])
        if selected_columns
        else data_quality["high_skew_columns"]
    )
    for col in selected_skewed:
        if col not in metadata["numerical_summary"]:
            continue
        skew = metadata["numerical_summary"][col]["skewness"]
        insights["skewness"].append(
            f"'{col}' is highly skewed (skewness = {skew:.2f}) — "
            f"log1p transformation will stabilise variance and reduce model bias."
        )

    # ── Target ─────────────────────────────────────────────────────────────
    if target:
        insights["target"] = f"'{target}' is the regression target (selected from candidate targets)."
    elif data_quality["candidate_targets"]:
        t = data_quality["candidate_targets"][0]
        insights["target"] = f"'{t}' is a candidate target variable."

    return insights


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATION INSIGHTS — label strength only when warranted
# ─────────────────────────────────────────────────────────────────────────────

def generate_correlation_insights(correlation_pairs, df):
    insights = []

    for col1, col2 in correlation_pairs:
        temp_df = df[[col1, col2]].dropna()

        if temp_df[col1].nunique() <= 1 or temp_df[col2].nunique() <= 1:
            continue

        corr = temp_df.corr().iloc[0, 1]

        if abs(corr) < 0.3:
            continue

        if abs(corr) > 0.7:
            strength = "very strong"
        elif abs(corr) > 0.4:
            strength = "strong"
        elif abs(corr) > 0.2:
            strength = "moderate"
        else:
            strength = "weak"

        direction = "positive" if corr > 0 else "negative"

        insights.append(
            f"'{col1}' and '{col2}' have a {strength} {direction} correlation "
            f"(r = {corr:.2f}) — multicollinearity risk if both are used as features."
        )

    return insights


# ─────────────────────────────────────────────────────────────────────────────
# KEY FINDINGS — numeric, correlation-strength-aware
# ─────────────────────────────────────────────────────────────────────────────

def generate_key_findings(df, target, numerical_cols):
    if not target or target not in df.columns:
        return []

    if not pd.api.types.is_numeric_dtype(df[target]):
        return []

    correlations = {}

    for col in numerical_cols:
        if col == target:
            continue
        temp_df = df[[col, target]].dropna()
        if temp_df[col].nunique() <= 1:
            continue
        corr = temp_df.corr().iloc[0, 1]
        correlations[col] = corr

    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

    findings = []
    for col, corr in sorted_corr[:3]:
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            label = "very strongly correlated"
        elif abs_corr >= 0.4:
            label = "strongly correlated"
        elif abs_corr >= 0.2:
            label = "moderately correlated"
        else:
            label = "weakly correlated"

        direction = "positively" if corr > 0 else "negatively"

        findings.append(
            f"'{col}' is {label} {direction} with '{target}' (r = {corr:.2f}), "
            f"indicating {'high' if abs_corr >= 0.4 else 'limited'} predictive importance."
        )

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE IMPORTANCE — sorted ranking vs target
# ─────────────────────────────────────────────────────────────────────────────

def generate_correlation_ranking(df, target, numerical_cols):
    if not target or target not in df.columns:
        return []

    if not pd.api.types.is_numeric_dtype(df[target]):
        return []

    importance = []

    for col in numerical_cols:
        if col == target:
            continue
        temp = df[[col, target]].dropna()
        if temp[col].nunique() <= 1:
            continue
        corr = round(float(temp.corr().iloc[0, 1]), 3)
        importance.append({"feature": col, "correlation": corr})

    importance.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return importance


# ─────────────────────────────────────────────────────────────────────────────
# TARGET INSIGHTS — numerical + categorical breakdown
# ─────────────────────────────────────────────────────────────────────────────

def generate_target_insights(df, target_column, numerical_cols, categorical_cols):
    insights = []

    if not target_column or target_column not in df.columns:
        return insights

    # Numerical vs Target
    correlations = {}
    if pd.api.types.is_numeric_dtype(df[target_column]):
        for col in numerical_cols:
            if col == target_column:
                continue
            temp_df = df[[col, target_column]].dropna()
            if temp_df[col].nunique() <= 1:
                continue
            corr = temp_df.corr().iloc[0, 1]
            correlations[col] = corr

    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

    for col, corr in sorted_corr[:5]:
        if abs(corr) < 0.2:
            continue
        direction = "positively" if corr > 0 else "negatively"
        if abs(corr) >= 0.7:
            signal = "very strong"
        elif abs(corr) >= 0.4:
            signal = "strong"
        elif abs(corr) >= 0.2:
            signal = "moderate"
        else:
            signal = "weak"
        insights.append(
            f"'{col}' is {direction} related to '{target_column}' "
            f"(r = {corr:.2f}) — {signal} signal."
        )
        if len(insights) == 5:
            break

    # Categorical vs Target
    for col in categorical_cols[:3]:
        if col not in df.columns:
            continue
        temp_df = df[[col, target_column]].dropna()
        if temp_df[col].nunique() > 20:
            continue

        grouped = temp_df.groupby(col)[target_column].mean().sort_values(ascending=False)
        if len(grouped) < 2:
            continue

        top_cat = grouped.index[0]
        bot_cat = grouped.index[-1]
        top_mean = grouped.iloc[0]
        bot_mean = grouped.iloc[-1]

        insights.append(
            f"'{target_column}' varies across '{col}': "
            f"avg {top_mean:,.1f} for '{top_cat}' vs {bot_mean:,.1f} for '{bot_cat}' — "
            f"this categorical split is predictive."
        )

    return insights


# ─────────────────────────────────────────────────────────────────────────────
# MASTER ASSEMBLER
# ─────────────────────────────────────────────────────────────────────────────

def generate_all_insights(df, metadata, data_quality, selected_columns):

    general       = generate_general_insights(metadata, data_quality, selected_columns)
    key_findings  = generate_key_findings(df, selected_columns["target_column"], selected_columns["numerical_columns"])
    correlation   = generate_correlation_insights(selected_columns["correlation_pairs"], df)
    target_insights = generate_target_insights(
        df,
        selected_columns["target_column"],
        selected_columns["numerical_columns"],
        selected_columns["categorical_columns"]
    )
    correlation_ranking = generate_correlation_ranking(
        df,
        selected_columns["target_column"],
        selected_columns["numerical_columns"]
    )
    # Top 5 most impactful recommendations only
    recommendations = generate_recommendations(metadata, data_quality, selected_columns)[:5]

    # ── Risk flags ────────────────────────────────────────────────────────
    risk_flags = []
    if data_quality["missing_report"]["high_missing_columns"]:
        cols = ", ".join(f"'{c}'" for c in data_quality["missing_report"]["high_missing_columns"])
        risk_flags.append(f"High missing values detected in: {cols}.")
    if data_quality["high_skew_columns"]:
        cols = ", ".join(f"'{c}'" for c in data_quality["high_skew_columns"])
        risk_flags.append(f"Highly skewed features: {cols} — may distort distance-based and linear models.")
    if data_quality["id_like_columns"]:
        cols = ", ".join(f"'{c}'" for c in data_quality["id_like_columns"])
        risk_flags.append(f"ID-like columns detected ({cols}) — must be excluded from training.")

    try:
        llm_insights = get_llm_insights(metadata, data_quality, selected_columns)
    except Exception as e:
        llm_insights = str(e)

    return {
        "general":            general,
        "key_findings":       key_findings,
        "correlation_ranking": correlation_ranking,
        "correlation":        correlation,
        "target_analysis":    target_insights,
        "risk_flags":         risk_flags,
        "recommendations":    recommendations,
        "llm":                llm_insights
    }