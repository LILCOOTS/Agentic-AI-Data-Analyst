"""
This module is used to extract metadata from a pandas DataFrame.

metadata = {
    "num_rows": int,
    "num_columns": int,
    "columns": list[str],

    "column_types": {
        "numerical": list[str],
        "categorical": list[str],
        "datetime": list[str],
        "boolean": list[str],
        "text": list[str],
    },

    "missing_summary": {
        "total_missing": int,
        "per_column": {
            column_name: {
                "missing_count": int,
                "missing_percentage": float
            }
        }
    },

    "unique_counts": {
        column_name: int
    },

    "numerical_summary": {
        column_name: {
            "mean": float,
            "std": float,
            "min": float,
            "max": float,
            "median": float,
            "skewness": float
        }
    },

    "categorical_summary": {
        column_name: {
            "top_values": dict,
            "unique_count": int
        }
    }
}

"""

import pandas as pd
import numpy as np

def extract_metadata(df: pd.DataFrame) -> dict:
    metadata = {}

    metadata["num_rows"] = df.shape[0]
    metadata["num_columns"] = df.shape[1]
    metadata["columns"] = df.columns.tolist()

    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
    boolean_cols = df.select_dtypes(include=["bool"]).columns.tolist()
    text_cols = []
    for col in categorical_cols:
        if df[col].nunique() > 50:
            text_cols.append(col)

    metadata["column_types"] = {
        "numerical": numerical_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
        "boolean": boolean_cols,
        "text": text_cols
    }

    missing_info = {}
    total_missing = int(df.isnull().sum().sum())

    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        missing_percentage = float((missing_count / len(df)) * 100)

        missing_info[col] = {
            "missing_count": missing_count,
            "missing_percentage": round(missing_percentage, 2)
        }

    metadata["missing_summary"] = {
        "total_missing": total_missing,
        "per_column": missing_info
    }

    unique_counts = {}
    for col in df.columns:
        unique_counts[col] = int(df[col].nunique())

    metadata["unique_counts"] = unique_counts

    numerical_summary = {}
    for col in numerical_cols:
        numerical_summary[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "median": float(df[col].median()),
            "skewness": float(df[col].skew())
        }

    metadata["numerical_summary"] = numerical_summary

    categorical_summary = {}
    for col in categorical_cols:
        top_values = df[col].value_counts().head(5).to_dict()
        categorical_summary[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": top_values
        }

    metadata["categorical_summary"] = categorical_summary

    return metadata