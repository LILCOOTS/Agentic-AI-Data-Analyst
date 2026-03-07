import pandas as pd
import numpy as np
from profiling import extract_metadata

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

def detect_high_missing(metadata, threshold_high=0.5, threshold_med=0.2):
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
    id_like = []

    num_rows = metadata["num_rows"]
    unique_counts = metadata["unique_counts"]

    for col, unique in unique_counts.items():
        if unique == num_rows:
            id_like.append(col)

    return id_like

def detect_high_skew(metadata, skew_threshold=2):
    skewed = []

    numerical_summary = metadata["numerical_summary"]

    for col, stats in numerical_summary.items():
        if abs(stats["skewness"]) > skew_threshold:
            skewed.append(col)

    return skewed

def detect_low_variance(metadata):
    low_variance = []

    unique_counts = metadata["unique_counts"]
    num_rows = metadata["num_rows"]

    for col, unique in unique_counts.items():
        if unique <= 1 or (unique / num_rows) < 0.01:
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
    candidates = []

    unique_counts = metadata["unique_counts"]
    numerical_cols = metadata["column_types"]["numerical"]

    for col, unique in unique_counts.items():

        # classification candidate
        if 2 <= unique <= 10:
            candidates.append(col)

        # regression candidate
        if col in numerical_cols and unique > 50:
            candidates.append(col)

    return list(set(candidates))

def analyze_data_quality(metadata: dict) -> dict:
    missing_report = detect_high_missing(metadata)
    id_columns = detect_id_columns(metadata)
    skew_columns = detect_high_skew(metadata)
    low_variance = detect_low_variance(metadata)
    high_cardinality = detect_high_cardinality(metadata)
    candidate_targets = detect_candidate_targets(metadata)

    return {
        "missing_report": missing_report,
        "id_columns": id_columns,
        "skew_columns": skew_columns,
        "low_variance": low_variance,
        "high_cardinality": high_cardinality,
        "candidate_targets": candidate_targets
    }

