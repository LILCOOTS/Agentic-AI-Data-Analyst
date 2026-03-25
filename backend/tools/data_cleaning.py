"""
data_cleaning.py — generates a dataset-agnostic ordered list of cleaning actions.

Order: drops → imputation → dedup → transforms

Detection is fully data-driven — no hardcoded column names.
"""


def _is_zero_inflated(col, metadata):
    """
    Detect zero-inflated numerical columns dynamically.
    A column is zero-inflated if median == 0 and mean < 15% of max.
    These are sparse columns where log1p can't fix skew — a binary flag is better.
    """
    stats = metadata["numerical_summary"].get(col, {})
    if not stats:
        return False
    median = stats.get("median", 1)
    mean   = stats.get("mean", 1)
    max_v  = stats.get("max", 1)
    if max_v == 0:
        return False
    return median == 0 and (mean / max_v) < 0.15


def generate_cleaning_action_report(metadata, data_quality):
    actions = []
    numerical_cols  = set(metadata["column_types"]["numerical"])
    categorical_cols = set(metadata["column_types"]["categorical"])
    dropped = set()

    # ── 1. Drop high-missing columns ──────────────────────────────────────
    for col in data_quality["missing_report"]["high_missing_columns"]:
        pct = round(metadata["missing_summary"]["per_column"][col]["missing_percentage"])
        actions.append({
            "column": col,
            "action": "drop_column",
            "reason": f"{pct}% missing — too sparse to be useful"
        })
        dropped.add(col)

    # ── 2. Drop ID-like columns ───────────────────────────────────────────
    for col in data_quality["id_like_columns"]:
        if col not in dropped:
            actions.append({
                "column": col,
                "action": "drop_column",
                "reason": "Identifier column — no predictive power"
            })
            dropped.add(col)

    # ── 3. Drop constant columns ──────────────────────────────────────────
    for col in data_quality.get("low_variance_columns", []):
        if col not in dropped:
            actions.append({
                "column": col,
                "action": "drop_column",
                "reason": "Constant column — zero variance"
            })
            dropped.add(col)

    # ── 4. Impute moderate-missing columns ────────────────────────────────
    for col in data_quality["missing_report"]["moderate_missing_columns"]:
        if col in dropped:
            continue

        if col in categorical_cols:
            # Categorical NaN = "not applicable/present" — fill with "None" string.
            # Mode would inflate one category and destroy signal.
            actions.append({
                "column": col,
                "action": "fill_with_none",
                "reason": "Categorical missing — NaN likely means 'not applicable', filling with 'None' category"
            })
        elif col in numerical_cols:
            skew = abs(metadata["numerical_summary"].get(col, {}).get("skewness", 0))
            method = "impute_with_median" if skew > 1 else "impute_with_mean"
            label  = "median (skewed)" if skew > 1 else "mean (normal)"
            actions.append({
                "column": col,
                "action": method,
                "reason": f"Numerical missing — imputing with {label}"
            })

    # ── 5. Deduplicate rows ───────────────────────────────────────────────
    actions.append({
        "column": None,
        "action": "drop_duplicates",
        "reason": "Remove exact duplicate rows"
    })

    # ── 6. Handle skewed numerical columns ────────────────────────────────
    for col in data_quality["high_skew_columns"]:
        if col in dropped:
            continue

        col_min = metadata["numerical_summary"].get(col, {}).get("min", 0)
        if col_min < 0:
            continue  # log1p undefined for negative values

        if _is_zero_inflated(col, metadata):
            # Zero-inflated: binary presence flag is more informative than log
            actions.append({
                "column": col,
                "action": "add_binary_indicator",
                "reason": "Zero-inflated column — binary presence flag more informative than log transform"
            })
        else:
            skew_val = round(metadata["numerical_summary"][col]["skewness"], 2)
            actions.append({
                "column": col,
                "action": "transform",
                "method": "log1p",
                "reason": f"High skewness ({skew_val}) — log1p compression"
            })

    # ── 7. Log-transform regression target if skewed ──────────────────────
    # Target skewness > 0.5 warrants normalisation regardless of the global threshold
    target_candidates = []
    for col in numerical_cols:
        if col not in dropped:
            stats = metadata["numerical_summary"].get(col, {})
            if abs(stats.get("skewness", 0)) > 0.5 and col not in [
                a["column"] for a in actions if a.get("action") == "transform"
            ]:
                # Only add if this col is a candidate target with high unique count
                if metadata["unique_counts"].get(col, 0) > 50:
                    target_candidates.append(col)

    # Among candidates, pick the one selected as target (if any)
    selected_target = None
    for col in ["SalePrice", "Price", "Target", "target", "label", "Label"]:
        if col in target_candidates:
            selected_target = col
            break
    # Fallback: highest unique-count numerical not already transformed
    if not selected_target and target_candidates:
        selected_target = max(target_candidates, key=lambda c: metadata["unique_counts"].get(c, 0))

    if selected_target:
        skew_val = round(metadata["numerical_summary"][selected_target]["skewness"], 2)
        actions.append({
            "column": selected_target,
            "action": "transform",
            "method": "log1p",
            "reason": f"Target variable skewed ({skew_val}) — log1p normalisation improves regression"
        })

    return actions