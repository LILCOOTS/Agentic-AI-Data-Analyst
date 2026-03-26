import pandas as pd
import numpy as np


def apply_cleaning(df: pd.DataFrame, actions: list) -> tuple[pd.DataFrame, list]:
    """
    Apply cleaning actions in order. Returns (cleaned_df, cleaning_log).
    Actions must be pre-ordered: drops → imputation → dedup → transforms.
    """
    dfc = df.copy()
    log = []

    for item in actions:
        col    = item.get("column")
        action = item.get("action")  # NOTE: use 'item' not 'action' to avoid variable shadowing

        # Safety: skip if column was already dropped by a prior action
        if col is not None and col not in dfc.columns:
            log.append({"column": col, "action": action, "status": "skipped — already removed"})
            continue

        try:
            if action == "drop_column":
                dfc = dfc.drop(columns=[col])
                log.append({"column": col, "action": action, "status": "done"})

            elif action == "impute_with_mean":
                n = dfc[col].isna().sum()
                dfc[col] = dfc[col].fillna(dfc[col].mean())
                log.append({"column": col, "action": action, "status": f"filled {n} nulls"})

            elif action == "impute_with_median":
                n = dfc[col].isna().sum()
                dfc[col] = dfc[col].fillna(dfc[col].median())
                log.append({"column": col, "action": action, "status": f"filled {n} nulls"})

            elif action == "impute_with_mode":
                n = dfc[col].isna().sum()
                mode_val = dfc[col].mode()
                if not mode_val.empty:
                    dfc[col] = dfc[col].fillna(mode_val[0])
                log.append({"column": col, "action": action, "status": f"filled {n} nulls"})

            elif action == "drop_duplicates":
                before = len(dfc)
                dfc = dfc.drop_duplicates()
                removed = before - len(dfc)
                log.append({"column": None, "action": action, "status": f"removed {removed} duplicate rows"})

            elif action == "fill_with_none":
                n = dfc[col].isna().sum()
                dfc[col] = dfc[col].fillna("None")
                log.append({"column": col, "action": action, "status": f"filled {n} NaNs with 'None'"})

            elif action == "add_binary_indicator":
                indicator_col = f"{col}_present"
                dfc[indicator_col] = (dfc[col] > 0).astype(int)
                dfc = dfc.drop(columns=[col])
                log.append({"column": col, "action": action, "status": f"created '{indicator_col}' (0/1), dropped original"})

            elif action == "transform":
                method = item.get("method", "log1p")
                if method == "log1p":
                    if dfc[col].min() < 0:
                        log.append({"column": col, "action": action, "status": "skipped — negative values"})
                        continue
                    dfc[col] = np.log1p(dfc[col])
                    log.append({"column": col, "action": action, "status": "log1p applied"})
                else:
                    log.append({"column": col, "action": action, "status": f"unknown method '{method}' — skipped"})

            else:
                log.append({"column": col, "action": action, "status": "unknown action — skipped"})

        except Exception as e:
            log.append({"column": col, "action": action, "status": f"error: {str(e)}"})

    return dfc, log