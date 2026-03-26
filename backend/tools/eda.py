"""
eda.py
│
├── select_columns(metadata)
├── generate_univariate_analysis(df)
├── generate_bivariate_analysis(df)
├── generate_correlation(df)
├── generate_target_analysis(df)
├── generate_summary(metadata, data_quality)

"""

import numpy as np
import plotly.express as px
import pandas as pd
from tools.insights import generate_all_insights
from tools.llm_insights import get_llm_insights, get_llm_target_selection

def select_columns(df, metadata, data_quality, top_k=5, forced_target: str = None):
    numerical_cols = metadata["column_types"]["numerical"]
    categorical_cols = metadata["column_types"]["categorical"]

    id_cols = set(data_quality["id_like_columns"])
    high_missing = set(data_quality["missing_report"]["high_missing_columns"])
    moderate_missing = set(data_quality["missing_report"]["moderate_missing_columns"])

    # Step 1: Filter columns
    filtered_numerical = [
        col for col in numerical_cols
        if col not in id_cols and col not in high_missing
    ]

    filtered_categorical = [
        col for col in categorical_cols
        if col not in high_missing
    ]

    # Step 2: Rank numerical by std (variance proxy)
    std_map = {
        col: metadata["numerical_summary"][col]["std"]
        for col in filtered_numerical
    }

    sorted_numerical = sorted(
        std_map,
        key=std_map.get,
        reverse=True
    )

    top_numerical = sorted_numerical[:top_k]

    # Step 3: Select categorical (filter low-variance: unique > 2 required)
    selected_categorical = []
    for col in filtered_categorical:
        unique = metadata["unique_counts"][col]
        if 3 <= unique <= min(20, int(0.1 * len(df))):
            selected_categorical.append(col)

    selected_categorical = selected_categorical[:top_k]

    # Step 4: Target detection (FIXED)

    candidate_targets = data_quality["candidate_targets"]

    target_column = None
    problem_type = None

    numerical_candidates = [
        col for col in candidate_targets 
        if col in numerical_cols and col not in id_cols
    ]

    categorical_candidates = [
        col for col in candidate_targets 
        if col in categorical_cols
    ]

    # ── Phase 3: User override ────────────────────────────────────────────
    if forced_target and forced_target in metadata["columns"]:
        target_column = forced_target
        problem_type  = "regression" if forced_target in numerical_cols else "classification"

    # ── Phase 2: LLM target selection ────────────────────────────────────
    elif candidate_targets:
        llm_result    = get_llm_target_selection(candidate_targets, metadata)
        target_column = llm_result.get("target_column")
        problem_type  = llm_result.get("problem_type", "regression")

    # ── Fallback: max(std) if candidates empty ────────────────────────────
    elif numerical_candidates:
        target_column = max(
            numerical_candidates,
            key=lambda col: metadata["numerical_summary"].get(col, {}).get("std", 0)
        )
        problem_type = "regression"
    elif categorical_candidates:
        target_column = categorical_candidates[0]
        problem_type  = "classification"

    if target_column:
        if target_column in top_numerical:
            top_numerical.remove(target_column)
        if target_column in selected_categorical:
            selected_categorical.remove(target_column)

    # Step 5: Correlation pairs
    correlation_pairs = []

    if len(top_numerical) >= 2:
        corr_cols = top_numerical.copy()

        if target_column and target_column not in corr_cols:
            corr_cols.append(target_column)
            
        corr = df[corr_cols].corr().abs()

        pairs = []

        for i in range(len(top_numerical)):
            for j in range(i + 1, len(top_numerical)):
                col1 = top_numerical[i]
                col2 = top_numerical[j]

                score = corr.loc[col1, col2]
                pairs.append((col1, col2, score))

        # sort by strongest correlation
        pairs = sorted(pairs, key=lambda x: x[2], reverse=True)

        # take top 3 pairs
        correlation_pairs = [(p[0], p[1]) for p in pairs[:3]]

    # Step 6: Skewed columns
    skewed_columns = [
        col for col in data_quality["high_skew_columns"]
        if col in top_numerical
    ]

    return {
        "numerical_columns": top_numerical,
        "categorical_columns": selected_categorical,
        "target_column": target_column,
        "problem_type": problem_type,
        "correlation_pairs": correlation_pairs,
        "skewed_columns": skewed_columns
    }

def _make_histogram(values: pd.Series, title: str, x_label: str) -> str:
    """Compute bins with numpy, render with go.Bar — lowest-level, guaranteed rendering."""
    import plotly.graph_objects as go

    # Force numeric — catches object-dtype columns that sneak through
    clean = pd.to_numeric(values, errors="coerce").dropna()

    if clean.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (no data)")
        return fig.to_json()

    counts, edges = np.histogram(clean, bins=50)
    centers = (edges[:-1] + edges[1:]) / 2   # float64 bin midpoints

    skew = round(float(clean.skew()), 2)
    kurt = round(float(clean.kurt()), 2)

    fig = go.Figure(data=[
        go.Bar(
            x=centers,
            y=counts,
            marker_color="#636EFA",
            name=x_label,
        )
    ])
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title="Count",
        annotations=[dict(
            x=0.98, y=0.97, xref="paper", yref="paper",
            text=f"skew={skew}  kurt={kurt}",
            showarrow=False, font=dict(size=11),
            align="right"
        )]
    )
    return fig.to_json()


def generate_univariate_analysis(df, selected):
    plots = []
    skewed = set(selected.get("skewed_columns", []))

    # Numerical → pre-computed histogram (always renders)
    for col in selected["numerical_columns"]:
        series = df[col]
        plots.append(_make_histogram(series, f"Distribution of {col}", col))

        # Log-transformed view for skewed columns
        if col in skewed:
            log_series = np.log1p(series.clip(lower=0))
            plots.append(_make_histogram(log_series, f"Distribution of {col} (log-transformed)", f"log1p({col})"))

    # Categorical → bar chart (unchanged — already works)
    for col in selected["categorical_columns"]:
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(counts, x=col, y="count", title=f"{col} Distribution")
        plots.append(fig.to_json())

    return plots

def generate_bivariate_analysis(df, selected):
    plots = []

    for col1, col2 in selected["correlation_pairs"][:3]:
        # Filter weak correlations before plotting
        corr_val = round(float(df[[col1, col2]].dropna().corr().iloc[0, 1]), 3)
        if abs(corr_val) < 0.3:
            continue

        try:
            fig = px.scatter(
                df, x=col1, y=col2,
                trendline="ols",
                title=f"{col1} vs {col2}"
            )
        except Exception:
            fig = px.scatter(df, x=col1, y=col2, title=f"{col1} vs {col2}")

        direction = "positive" if corr_val > 0 else "negative"
        fig.update_layout(
            annotations=[dict(
                x=0.5, y=1.07, xref="paper", yref="paper",
                text=f"r = {corr_val:+.3f}  ({direction} correlation)",
                showarrow=False, font=dict(size=13)
            )]
        )
        plots.append(fig.to_json())

    return plots

def generate_correlation(df, selected):
    num_cols = selected["numerical_columns"]

    # if less than 2 numerical columns, no correlation matrix
    if len(num_cols) < 2:
        return None

    corr = df[num_cols].corr()

    fig = px.imshow(
        corr,
        text_auto=True,
        title="Correlation Matrix"
    )

    return fig.to_json()

def generate_target_analysis(df, selected):
    target = selected["target_column"]
    problem_type = selected["problem_type"]

    if not target:
        return []

    plots = []

    # Regression
    if problem_type == "regression":

        cols = selected["numerical_columns"]

        # Ensure target is included safely
        if target not in cols:
            cols = cols + [target]

        # Drop rows with NaN (VERY IMPORTANT)
        temp_df = df[cols].dropna()

        if target not in temp_df.columns:
            return []

        corr_series = temp_df.corr()[target].drop(target)

        # 🔥 Ensure index is valid column names
        corr_series = corr_series.sort_values(ascending=False)

        top_features = list(corr_series.index[:3])

        for col in top_features:
            if col not in df.columns:
                continue

            corr_value = round(df[col].corr(df[target]), 3)

            try:
                fig = px.scatter(
                    df, x=col, y=target,
                    trendline="ols",
                    title=f"{col} vs {target} (r = {corr_value})"
                )
            except Exception:
                # statsmodels not installed — fall back to plain scatter
                fig = px.scatter(
                    df, x=col, y=target,
                    title=f"{col} vs {target} (r = {corr_value})"
                )

            fig.add_annotation(
                text=f"r = {corr_value}",
                xref="paper", yref="paper",
                x=0.05, y=0.95, showarrow=False,
                font=dict(size=13)
            )

            plots.append(fig.to_json())

    # Classification
    elif problem_type == "classification":
        for col in selected["numerical_columns"]:
            fig = px.box(df, x=target, y=col,
                         title=f"{col} by {target}")
            plots.append(fig.to_json())

    return plots 

def run_full_analysis(df, metadata, data_quality, forced_target: str = None):
    # Step 1: Select columns
    selected = select_columns(df, metadata, data_quality, forced_target=forced_target)

    # Step 2: Generate plots
    univariate = generate_univariate_analysis(df, selected)
    bivariate = generate_bivariate_analysis(df, selected)
    correlation = generate_correlation(df, selected)
    target_analysis = generate_target_analysis(df, selected)

    # Step 3: Generate all insights (includes feature_importance + recommendations)
    insights = generate_all_insights(df, metadata, data_quality, selected)

    return {
        "selected_columns": selected,
        "eda": {
            "univariate": univariate,
            "bivariate": bivariate,
            "correlation": correlation,
            "target_analysis": target_analysis
        },
        "insights": insights
    }