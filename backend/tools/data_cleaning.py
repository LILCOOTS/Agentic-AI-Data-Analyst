def generate_cleaning_action_report(metadata, data_quality):
    """
    Produce an ordered list of cleaning actions.
    Order matters: drops first → imputation → dedup → transforms last.
    """
    actions = []
    numerical_cols = set(metadata["column_types"]["numerical"])

    # ── 1. Drop high-missing columns ──────────────────────────────────────
    dropped = set()
    for col in data_quality["missing_report"]["high_missing_columns"]:
        actions.append({
            "column": col,
            "action": "drop_column",
            "reason": f">{round(metadata['missing_summary']['per_column'][col]['missing_percentage'])}% missing values"
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

    # ── 3. Drop constant columns (unique == 1) ────────────────────────────
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

        if col in numerical_cols:
            # Use median for skewed columns, mean for normal ones
            skew = abs(metadata["numerical_summary"].get(col, {}).get("skewness", 0))
            method = "impute_with_median" if skew > 1 else "impute_with_mean"
            actions.append({
                "column": col,
                "action": method,
                "reason": f"Moderate missing — {'skewed, using median' if skew > 1 else 'normal, using mean'}"
            })
        else:
            actions.append({
                "column": col,
                "action": "impute_with_mode",
                "reason": "Moderate missing — categorical, using mode"
            })

    # ── 5. Deduplicate rows ───────────────────────────────────────────────
    actions.append({
        "column": None,
        "action": "drop_duplicates",
        "reason": "Remove exact duplicate rows"
    })

    # ── 6. Log-transform skewed numerical columns ─────────────────────────
    for col in data_quality["high_skew_columns"]:
        if col in dropped:
            continue  # skip already-dropped columns
        col_min = metadata["numerical_summary"].get(col, {}).get("min", 0)
        if col_min < 0:
            continue  # log1p undefined for negative values — skip
        actions.append({
            "column": col,
            "action": "transform",
            "method": "log1p",
            "reason": f"High skewness (skew = {round(metadata['numerical_summary'][col]['skewness'], 2)})"
        })

    return actions