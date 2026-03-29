import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    HistGradientBoostingRegressor, HistGradientBoostingClassifier,
    VotingRegressor, VotingClassifier
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
    # (Since missing values are handled in cleaning, this is purely safety)
    valid_idx = X.notna().all(axis=1) & y.notna()
    X = X[valid_idx]
    y = y[valid_idx]

    if len(X) < 50:
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
        models = {
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
            "gradient_boosting": HistGradientBoostingClassifier(random_state=42),
            "logistic_regression": LogisticRegression(max_iter=1000, solver="lbfgs")
        }
        cv_metric = "roc_auc"
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    else:
        models = {
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "gradient_boosting": HistGradientBoostingRegressor(random_state=42),
            "ridge_regression": Ridge()
        }
        cv_metric = "r2"
        cv = KFold(n_splits=5, shuffle=True, random_state=42)

    # ── Cross Validation ──────────────────────────────────────────────────
    models_performance = {}
    best_model_name = None
    best_score = -float('inf')
    cv_score_mean = 0.0
    cv_score_std = 0.0

    for name, m in models.items():
        # Fallback metric if binary classification roc_auc fails
        metric_to_use = cv_metric
        if problem_type == "classification" and len(np.unique(y_train)) > 2:
            metric_to_use = "accuracy" # multi-class fallback

        try:
            scores = cross_val_score(m, X_train_sc, y_train, cv=cv, scoring=metric_to_use)
            mean_score = float(scores.mean())
            std_score = float(scores.std())
        except Exception:
            mean_score, std_score = 0.0, 0.0
        
        models_performance[name] = round(mean_score, 4)
        
        if mean_score > best_score:
            best_score = mean_score
            best_model_name = name
            cv_score_mean = mean_score
            cv_score_std = std_score

    # ── Retrain Winner & Ensemble ──────────────────────────────────────────
    # Create Voting Ensemble
    if problem_type == "classification":
        # 'soft' voting uses probabilities for better ROC-AUC natively
        ensemble_model = VotingClassifier(
            estimators=[(k, v) for k, v in models.items()],
            voting="soft"
        )
    else:
        ensemble_model = VotingRegressor(
            estimators=[(k, v) for k, v in models.items()]
        )

    ensemble_model.fit(X_train_sc, y_train)
    y_pred = ensemble_model.predict(X_test_sc)

    # ── Metrics ───────────────────────────────────────────────────────────
    if problem_type == "classification":
        metric_name  = "accuracy"
        metric_value = round(float(accuracy_score(y_test, y_pred)), 4)
        
        # Calculate robust performance metrics natively for classification
        try:
            y_prob = ensemble_model.predict_proba(X_test_sc)
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
    rf_estimator = models["random_forest"]
    rf_estimator.fit(X_train_sc, y_train)
    importance = rf_estimator.feature_importances_

    feature_importance = (
        pd.DataFrame({"feature": X.columns, "importance": importance})
        .sort_values("importance", ascending=False)
        .head(20)                                 # top 20 — enough for display + LLM
        .reset_index(drop=True)
    )

    return {
        "problem_type": problem_type,
        "models_performance": models_performance,
        "best_model": best_model_name,
        "model_architecture": "VotingEnsemble (AutoML Base Models Averaged)",
        "metric_name":  metric_name,
        "metric_value": metric_value,
        "cv_score_mean": round(cv_score_mean, 4),
        "cv_score_std": round(cv_score_std, 4),
        "extra_metrics": extra,
        "rows_trained":  int(len(X_train)),
        "rows_tested":   int(len(X_test)),
        "n_features":    int(X.shape[1]),
        "feature_importance_source": "RandomForest",
        "feature_importance": feature_importance.to_dict(orient="records"),
    }