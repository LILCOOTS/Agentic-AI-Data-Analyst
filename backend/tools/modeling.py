import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    HistGradientBoostingRegressor, HistGradientBoostingClassifier,
    StackingRegressor, StackingClassifier
)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, f1_score,
    mean_squared_error, r2_score,
    roc_auc_score, average_precision_score
)


def run_modeling(df: pd.DataFrame, target_col: str, problem_type: str) -> dict:
    """
    Run baseline model, return feature importance + metrics.
    No hardcoded assumptions — works on any cleaned dataset.
    """

    # ── Guard: target must exist after cleaning ──────────────────────────
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset after cleaning.")

    # ── Separate features / target ────────────────────────────────────────
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # ── Leakage guard: drop columns nearly identical to the target ─────────
    # Any column with |corr| > 0.98 with y is almost certainly a leak or redundant
    num_X = X.select_dtypes(include="number")
    if not num_X.empty:
        corr_with_target = num_X.corrwith(y).abs()
        leaky_cols = corr_with_target[corr_with_target > 0.98].index.tolist()
        if leaky_cols:
            X = X.drop(columns=leaky_cols)

    # ── Encode remaining categoricals ────────────────────────────────────
    # drop_first=True avoids dummy-variable trap
    X = pd.get_dummies(X, drop_first=True)

    # ── Drop any remaining NaN rows (safety net) ─────────────────────────
    valid = X.notna().all(axis=1) & y.notna()
    X, y = X[valid], y[valid]

    if len(X) < 10:
        raise ValueError("Not enough valid rows to train a model after cleaning.")

    # ── Target scaling for regression (if skewed) ──────────────────────────
    is_log_transformed = False
    if problem_type == "regression" and abs(y.skew()) > 0.5 and y.min() >= 0:
        y = np.log1p(y)
        is_log_transformed = True

    # ── Train / test split ────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Feature scaling (required for Logistic, helps Linear too) ─────────
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    # ── Model selection ───────────────────────────────────────────────────
    if problem_type == "classification":
        base_models = [
            ("rf", RandomForestClassifier(n_estimators=100, random_state=42)),
            ("hgb", HistGradientBoostingClassifier(random_state=42)),
            ("logreg", LogisticRegression(max_iter=1000, solver="lbfgs"))
        ]
        meta_model = LogisticRegression(max_iter=1000, solver="lbfgs")
        model = StackingClassifier(estimators=base_models, final_estimator=meta_model, cv=5)
    else:
        base_models = [
            ("rf", RandomForestRegressor(n_estimators=100, random_state=42)),
            ("hgb", HistGradientBoostingRegressor(random_state=42)),
            ("ridge", Ridge())
        ]
        meta_model = Ridge()
        model = StackingRegressor(estimators=base_models, final_estimator=meta_model, cv=5)

    model.fit(X_train_sc, y_train)
    y_pred = model.predict(X_test_sc)

    # ── Metrics ───────────────────────────────────────────────────────────
    if problem_type == "classification":
        metric_name  = "accuracy"
        metric_value = round(float(accuracy_score(y_test, y_pred)), 4)
        
        # Calculate robust performance metrics natively for classification
        try:
            y_prob = model.predict_proba(X_test)
            # Handle multi-class vs binary
            if len(np.unique(y_train)) == 2:
                roc_auc = roc_auc_score(y_test, y_prob[:, 1])
                pr_auc = average_precision_score(y_test, y_prob[:, 1])
            else:
                roc_auc = roc_auc_score(y_test, y_prob, multi_class="ovo")
                pr_auc = 0.0 # PR-AUC natively harder for multi-class without binarization
        except Exception:
            roc_auc, pr_auc = 0.0, 0.0

        extra = {
            "f1_score": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
            "roc_auc": round(float(roc_auc), 4),
            "pr_auc": round(float(pr_auc), 4)
        }
    else:
        if is_log_transformed:
            # Inverse transform to report original scale RMSE
            y_test_orig = np.expm1(y_test)
            y_pred_orig = np.expm1(y_pred)
        else:
            y_test_orig = y_test
            y_pred_orig = y_pred

        rmse         = float(np.sqrt(mean_squared_error(y_test_orig, y_pred_orig)))
        r2           = float(r2_score(y_test_orig, y_pred_orig))
        metric_name  = "rmse"
        metric_value = round(rmse, 4)
        extra        = {"r2_score": round(r2, 4)}

    # ── Feature importance ────────────────────────────────────────────────
    # We extract absolute feature importance directly from the Random Forest
    # base estimator inside the trained stack, yielding powerful non-linear importance.
    rf_estimator = model.named_estimators_["rf"]
    importance = rf_estimator.feature_importances_

    feature_importance = (
        pd.DataFrame({"feature": X.columns, "importance": importance})
        .sort_values("importance", ascending=False)
        .head(20)                                 # top 20 — enough for display + LLM
        .reset_index(drop=True)
    )

    return {
        "problem_type": problem_type,
        "model_architecture": "StackingEnsemble (RandomForest + HistGradientBoosting + Linear)",
        "metric_name":  metric_name,
        "metric_value": metric_value,
        "extra_metrics": extra,
        "rows_trained":  int(len(X_train)),
        "rows_tested":   int(len(X_test)),
        "n_features":    int(X.shape[1]),
        "feature_importance_source": "RandomForest (Level 0 Base Estimator)",
        # Plain list of dicts — JSON-serializable, no DataFrame
        "feature_importance": feature_importance.to_dict(orient="records"),
    }