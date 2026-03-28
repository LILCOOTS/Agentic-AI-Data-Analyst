import pandas as pd
import numpy as np
import re

"""
analyze_data_quality(metadata)
│
├── detect_high_missing()
├── detect_id_columns()
├── detect_high_skew()
├── detect_low_variance()
├── detect_high_cardinality()
├── detect_candidate_targets()
"""

# class AnalyzeDataQuality:
#     def __init__(self, metadata: dict):
#         self.metadata  = metadata
#         self.issues = []

def detect_high_missing(metadata, threshold_high=0.5, threshold_med=0.01):
    high_missing = []
    moderate_missing = []

    for col, info in metadata["missing_summary"]["per_column"].items():
        missing_pct = info["missing_percentage"] / 100

        if missing_pct >= threshold_high:
            high_missing.append(col)

        elif missing_pct >= threshold_med:
            moderate_missing.append(col)

    return {
        "high_missing_columns": high_missing,
        "moderate_missing_columns": moderate_missing
    }

def detect_id_columns(metadata):
    """
    A column is ID-like only if:
      1. Every value is unique (unique == num_rows), AND
      2. It is an integer column  OR  its name contains id-like keywords.
    Float/continuous columns (Temperature, Pressure, etc.) are NEVER IDs
    even if every value happens to be unique.
    """
    id_like = []
    num_rows   = metadata["num_rows"]
    unique_counts = metadata["unique_counts"]
    numerical  = set(metadata["column_types"]["numerical"])

    ID_KEYWORDS = {"id", "index", "key", "code", "no", "num", "number", "seq", "uuid", "ref"}

    for col, unique in unique_counts.items():
        if unique != num_rows:
            continue

        # Convert CamelCase to snake_case first, then lower and replace spaces/dashes
        name_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', col)
        name_lower = name_snake.lower().replace(" ", "_").replace("-", "_")
        name_is_id = any(kw in name_lower.split("_") or name_lower.startswith(kw) for kw in ID_KEYWORDS)

        # Float numerical columns are measurement data, never IDs
        is_float_numerical = col in numerical and not name_is_id

        if is_float_numerical:
            continue  # Temperature (°C), Pressure (kPa) etc. — skip

        id_like.append(col)

    return id_like

def detect_high_skew(metadata, skew_threshold=2):
    skewed = []
    unique_counts   = metadata["unique_counts"]
    numerical_summary = metadata["numerical_summary"]

    for col, stats in numerical_summary.items():
        # Skip binary columns — skewness is meaningless for 0/1 flags
        if unique_counts.get(col, 99) == 2 and stats.get("min", -1) == 0 and stats.get("max", -1) == 1:
            continue
        if abs(stats["skewness"]) > skew_threshold:
            skewed.append(col)

    return skewed

def detect_low_variance(metadata):
    """Flag only truly constant columns (unique == 1). Low ratio ≠ useless."""
    low_variance = []

    unique_counts = metadata["unique_counts"]

    for col, unique in unique_counts.items():
        if unique == 1:          # constant column — zero predictive signal
            low_variance.append(col)

    return low_variance

def detect_high_cardinality(metadata, threshold=50):
    high_card = []

    categorical_summary = metadata["categorical_summary"]

    for col, info in categorical_summary.items():
        if info["unique_count"] > threshold:
            high_card.append(col)

    return high_card

def detect_candidate_targets(metadata):
    """
    Smart-filter target candidates to 3-5 meaningful columns.
    Regression: continuous numerical, high unique ratio, not ID/year/binary/zero-inflated.
    Classification: categorical with 2-10 balanced classes.
    """
    num_rows      = metadata["num_rows"]
    unique_counts = metadata["unique_counts"]
    numerical_cols = set(metadata["column_types"]["numerical"])
    categorical_cols = set(metadata["column_types"]["categorical"])
    num_summary   = metadata.get("numerical_summary", {})
    cat_summary   = metadata.get("categorical_summary", {})

    scored = []  # (col, score, problem_type)

    # ── Regression candidates ─────────────────────────────────────────────
    for col in numerical_cols:
        unique = unique_counts.get(col, 0)
        stats  = num_summary.get(col, {})

        # Must have meaningful variety (>5% of rows are unique)
        if unique < num_rows * 0.05:
            continue

        # Skip zero-inflated columns (median == 0, mostly zeros)
        if stats.get("median", 1) == 0 and stats.get("mean", 1) / max(stats.get("max", 1), 1) < 0.15:
            continue

        # Skip year-like columns (min > 1800 and max < 2100 and all integers)
        if stats.get("min", 0) > 1800 and stats.get("max", 9999) < 2100:
            continue

        # Score: unique ratio × std (rewards continuous, spread-out columns)
        unique_ratio = unique / num_rows
        std = stats.get("std", 0)
        score = unique_ratio * std

        scored.append((col, score, "regression"))

    # ── Classification candidates ─────────────────────────────────────────
    # First, check categorical columns
    for col in categorical_cols:
        unique = unique_counts.get(col, 0)
        if unique < 2 or unique > 10:
            continue

        # Check class balance: majority class should be < 90% of rows
        top_values = cat_summary.get(col, {}).get("top_values", {})
        if top_values:
            max_class_count = max(top_values.values())
            if max_class_count / num_rows > 0.90:
                continue  # too imbalanced — not a useful target

        # Score: closer to balanced = higher score
        balance_score = unique / 10  # more classes = more interesting
        scored.append((col, balance_score, "classification"))

    # Also check numerical columns for binary outcomes (like Exited = 0/1)
    for col in numerical_cols:
        unique = unique_counts.get(col, 0)
        if unique == 2:
            # Check balance:
            stats = num_summary.get(col, {})
            # If min=0 and max=1, mean represents the proportion of 1s
            if stats.get("min", -1) == 0 and stats.get("max", -1) == 1:
                prop = stats.get("mean", 0)
                if prop < 0.05 or prop > 0.95:
                    continue # highly imbalanced
            # Score binary classification targets very favorably
            scored.append((col, 1.0, "classification"))


    # ── Sort by score, return top 5 ───────────────────────────────────────
    final_scored = []
    semantic_keywords = ["target", "label", "exited", "churn", "price", "status"]
    
    for col, score, ptype in scored:
        name_lower = col.lower()
        if any(kw in name_lower for kw in semantic_keywords):
            score += 10.0  # Massive boost to force it to the top
        final_scored.append((col, score, ptype))

    final_scored.sort(key=lambda x: x[1], reverse=True)
    return [col for col, _, _ in final_scored[:5]]

def analyze_data_quality(metadata: dict) -> dict:
    missing_report = detect_high_missing(metadata)
    id_columns = detect_id_columns(metadata)
    skew_columns = detect_high_skew(metadata)
    low_variance = detect_low_variance(metadata)
    high_cardinality = detect_high_cardinality(metadata)
    candidate_targets = detect_candidate_targets(metadata)

    return {
        "missing_report": missing_report,
        "id_like_columns": id_columns,
        "high_skew_columns": skew_columns,
        "low_variance_columns": low_variance,
        "high_cardinality_columns": high_cardinality,
        "candidate_targets": candidate_targets
    }

