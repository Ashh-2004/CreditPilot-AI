"""
Automated tests for Home Credit model evaluation, calibration, and SHAP explainability.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer

from home_credit.evaluation import (
    compute_comprehensive_metrics,
    evaluate_with_stratified_cv,
    calibrate_and_evaluate_curves,
    SYNTHETIC_DATA_DISCLAIMER,
)
from home_credit.explainability import HomeCreditExplainer
from home_credit.ingestion import load_or_create_home_credit_dataset
from home_credit.feature_engineering import compute_domain_features


def test_comprehensive_metrics_calculation():
    """Verify calculation of ROC-AUC, PR-AUC, Brier score, and classification metrics."""
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])

    metrics = compute_comprehensive_metrics(y_true, y_prob, threshold=0.5)

    assert metrics["roc_auc"] == 1.0
    assert metrics["pr_auc"] == 1.0
    assert metrics["accuracy"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["brier_score"] < 0.1
    assert metrics["confusion_matrix"] == [[3, 0], [0, 3]]


def test_stratified_cv_execution():
    """Verify stratified cross-validation produces mean and std statistics."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(60, 4), columns=["f1", "f2", "f3", "f4"])
    y = pd.Series(np.random.choice([0, 1], size=60, p=[0.8, 0.2]))

    def dummy_factory():
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression()),
        ])

    cv_results = evaluate_with_stratified_cv(dummy_factory, X, y, n_splits=3, random_state=42)

    assert cv_results["n_splits"] == 3
    assert 0.0 <= cv_results["cv_roc_auc_mean"] <= 1.0
    assert cv_results["cv_roc_auc_std"] >= 0.0
    assert "cv_brier_mean" in cv_results


def test_probability_calibration_and_curves():
    """Verify probability calibration and reliability curve generation."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(100, 3), columns=["f1", "f2", "f3"])
    y = pd.Series(np.random.choice([0, 1], size=100, p=[0.85, 0.15]))

    def pipe_factory():
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression()),
        ])

    fitted_pipe = pipe_factory()
    fitted_pipe.fit(X[:70], y[:70])

    cal_model, cal_report = calibrate_and_evaluate_curves(
        fitted_pipe, pipe_factory, X[:70], y[:70], X[70:], y[70:], method="sigmoid", cv=2
    )

    assert hasattr(cal_model, "predict_proba")
    assert "uncalibrated_brier_score" in cal_report
    assert "calibrated_brier_score" in cal_report
    assert "uncalibrated_curve" in cal_report
    assert "calibrated_curve" in cal_report
    assert cal_report["disclaimer"] == SYNTHETIC_DATA_DISCLAIMER


def test_shap_explainer_global_and_individual():
    """Verify SHAP global ranking and individual applicant explanation."""
    df_raw = load_or_create_home_credit_dataset(sample_size=120, random_seed=42)
    df = compute_domain_features(df_raw)

    drop_cols = ["TARGET", "SK_ID_CURR"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df["TARGET"]

    num_cols = X.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]

    preprocessor = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_cols),
    ], remainder="drop")

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=500)),
    ])
    pipe.fit(X[:80], y[:80])

    explainer = HomeCreditExplainer(pipe, background_data=X[:80], max_background_samples=30)

    # 1. Test Global Importance
    global_imp = explainer.compute_global_importance(X[80:], max_eval_samples=40)
    assert "top_features" in global_imp
    assert len(global_imp["top_features"]) > 0
    assert global_imp["top_features"][0]["mean_abs_shap"] >= global_imp["top_features"][-1]["mean_abs_shap"]

    # 2. Test Individual Explanation
    individual_exp = explainer.explain_individual_prediction(X.iloc[[85]])
    assert "predicted_default_probability" in individual_exp
    assert "risk_drivers" in individual_exp
    assert "safety_drivers" in individual_exp
    assert individual_exp["disclaimer"] == SYNTHETIC_DATA_DISCLAIMER


def test_synthetic_provenance_labeling():
    """Verify synthetic data disclaimer is explicitly attached to evaluation output."""
    assert "synthetic sample" in SYNTHETIC_DATA_DISCLAIMER.lower()
    assert "not be presented as actual home credit kaggle competition performance" in SYNTHETIC_DATA_DISCLAIMER.lower()
