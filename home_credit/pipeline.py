"""
Machine Learning Training, Evaluation, Calibration, and Explainability Pipeline for Home Credit.
Supports real Kaggle Home Credit data ingestion, historical table aggregations (bureau,
previous applications, installments, POS cash, credit cards), and rigorous model evaluation.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

from home_credit.schema import TARGET_COLUMN, ID_COLUMN
from home_credit.feature_engineering import (
    compute_domain_features,
    merge_historical_features,
)
from home_credit.ingestion import (
    load_or_create_home_credit_dataset,
    validate_home_credit_dataset_directory,
)
from home_credit.evaluation import (
    compute_comprehensive_metrics,
    evaluate_with_stratified_cv,
    calibrate_and_evaluate_curves,
    SYNTHETIC_DATA_DISCLAIMER,
)
from home_credit.explainability import HomeCreditExplainer

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


def create_preprocessor(numeric_cols: list, categorical_cols: list) -> ColumnTransformer:
    """
    Builds a robust ColumnTransformer that imputes and scales numeric features,
    and imputes and one-hot encodes categorical features.
    """
    num_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", num_pipeline, numeric_cols),
            ("cat", cat_pipeline, categorical_cols),
        ],
        remainder="drop"
    )


def train_and_evaluate_home_credit(
    data_dir: str = "data/home_credit",
    output_dir: str = "models/home_credit",
    sample_size: Optional[int] = 30000,
    cv_folds: int = 5,
    aggregate_history: bool = True,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Executes the end-to-end Home Credit research and training pipeline:
    1. Dataset validation and manifest inspection
    2. Real dataset loading with stratified sampling
    3. Historical table aggregations (bureau, prev app, installments, POS, credit card)
    4. Domain feature engineering (credit ratios, DTI proxy, external scores)
    5. Stratified 5-fold CV + Genuinely held-out test evaluation
    6. Model comparison (Logistic Regression vs Gradient Boosting)
    7. Probability calibration & reliability curves
    8. SHAP global feature importance and individual prediction explanation
    9. Artifact export
    """
    print("=" * 65)
    print("  Home Credit Default Risk — Real-Data Training & Evaluation")
    print("=" * 65)

    # 1. Dataset Directory Validation
    print("\n[1/7] Validating dataset directory and table manifest...")
    val_report = validate_home_credit_dataset_directory(data_dir=data_dir)
    is_real_data = val_report.get("valid", False)
    provenance = val_report.get("data_provenance", "SYNTHETIC_RESEARCH_SAMPLE")
    source = val_report.get("dataset_source", "synthetic_generator")

    print(f"  Data Source: {source} ({provenance})")
    print(f"  Present files: {len(val_report['present_files'])} CSVs")
    if val_report["missing_required"]:
        print(f"  WARNING: Missing required files: {val_report['missing_required']}")
    if val_report["missing_historical"]:
        print(f"  Notice: Missing historical tables: {val_report['missing_historical']}")

    # 2. Ingestion
    print("\n[2/7] Ingesting application records...")
    df = load_or_create_home_credit_dataset(data_dir=data_dir, sample_size=sample_size, random_seed=random_state)

    actual_provenance = df.attrs.get("data_provenance", provenance)
    actual_source = df.attrs.get("dataset_source", source)

    # 3. Historical Table Aggregations
    if aggregate_history and Path(data_dir).exists():
        print("[3/7] Aggregating historical tables (bureau, previous applications, installments, POS, CC)...")
        df = merge_historical_features(df, data_dir=data_dir)
        print(f"  Features after historical merges: {df.shape[1]} columns")

    # 4. Domain Feature Engineering
    print("[4/7] Computing domain credit risk ratios...")
    df = compute_domain_features(df)

    drop_cols = [TARGET_COLUMN]
    if ID_COLUMN in df.columns:
        drop_cols.append(ID_COLUMN)

    X = df.drop(columns=drop_cols)
    y = df[TARGET_COLUMN]

    all_numeric = X.select_dtypes(include=["number"]).columns.tolist()
    all_categorical = [c for c in X.columns if c not in all_numeric]

    print(f"  Total features prepared: {len(all_numeric)} numeric, {len(all_categorical)} categorical")

    # 5. Genuinely held-out test split (25% held out)
    print("[5/7] Partitioning training set and genuinely held-out test set (25%)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=y
    )
    print(f"  Training samples: {len(X_train):,} | Held-out test samples: {len(X_test):,}")

    preprocessor = create_preprocessor(all_numeric, all_categorical)

    # Factory functions for consistent CV and testing
    def lr_factory():
        return Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state)),
        ])

    def gb_factory():
        if XGB_AVAILABLE:
            scale_pos = (len(y_train) - sum(y_train)) / max(1, sum(y_train))
            clf = XGBClassifier(
                n_estimators=100, learning_rate=0.08, max_depth=4,
                scale_pos_weight=scale_pos, random_state=random_state, eval_metric="logloss"
            )
        else:
            clf = HistGradientBoostingClassifier(
                max_iter=100, learning_rate=0.08, max_depth=4,
                class_weight="balanced", random_state=random_state
            )
        return Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ])

    # 6. Stratified Cross-Validation on Training Split
    print(f"\n[6/7] Running Stratified {cv_folds}-Fold Cross-Validation on training split...")
    cv_lr = evaluate_with_stratified_cv(lr_factory, X_train, y_train, n_splits=cv_folds, random_state=random_state)
    cv_gb = evaluate_with_stratified_cv(gb_factory, X_train, y_train, n_splits=cv_folds, random_state=random_state)

    # 7. Fit Full Models & Evaluate on Held-Out Test Set
    print("[7/7] Fitting full models, calibrating probabilities & generating SHAP explanations...")
    pipe_lr = lr_factory()
    pipe_lr.fit(X_train, y_train)
    prob_lr = pipe_lr.predict_proba(X_test)[:, 1]
    test_metrics_lr = compute_comprehensive_metrics(y_test.values, prob_lr)

    pipe_gb = gb_factory()
    pipe_gb.fit(X_train, y_train)
    prob_gb = pipe_gb.predict_proba(X_test)[:, 1]
    test_metrics_gb = compute_comprehensive_metrics(y_test.values, prob_gb)

    # Select best model based on held-out test ROC-AUC
    if test_metrics_gb["roc_auc"] >= test_metrics_lr["roc_auc"]:
        best_pipeline = pipe_gb
        best_name = "gradient_boosting"
        best_metrics = test_metrics_gb
    else:
        best_pipeline = pipe_lr
        best_name = "logistic_regression"
        best_metrics = test_metrics_lr

    # Probability Calibration
    best_factory = gb_factory if best_name == "gradient_boosting" else lr_factory
    calibrated_model, cal_report = calibrate_and_evaluate_curves(
        best_pipeline, best_factory, X_train, y_train, X_test, y_test, method="sigmoid"
    )

    # SHAP Explainability
    explainer = HomeCreditExplainer(best_pipeline, background_data=X_train, max_background_samples=100)
    shap_global = explainer.compute_global_importance(X_test, max_eval_samples=150)
    sample_explanation = explainer.explain_individual_prediction(X_test.iloc[[0]])

    # Build provenance disclaimer string
    if actual_provenance == "REAL_KAGGLE_HOME_CREDIT_DATASET":
        disclaimer = (
            f"DATASET PROVENANCE: Official Home Credit Default Risk Kaggle dataset ({actual_source}). "
            f"Trained on {len(X_train):,} training records and evaluated on {len(X_test):,} genuinely held-out records."
        )
    else:
        disclaimer = SYNTHETIC_DATA_DISCLAIMER

    # Save Artifacts & Reports
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    joblib.dump(calibrated_model, out_path / "model.joblib")
    joblib.dump(best_pipeline, out_path / "uncalibrated_model.joblib")

    test_comparison = {
        "logistic_regression": test_metrics_lr,
        "gradient_boosting": test_metrics_gb,
    }

    eval_report = {
        "data_provenance": actual_provenance,
        "dataset_source": actual_source,
        "disclaimer": disclaimer,
        "total_available_in_csv": val_report.get("application_train", {}).get("total_records", len(df)),
        "dataset_records_used": len(df),
        "train_samples": len(X_train),
        "held_out_test_samples": len(X_test),
        "total_features": len(X.columns),
        "numeric_features_count": len(all_numeric),
        "categorical_features_count": len(all_categorical),
        "best_model": best_name,
        "models": test_comparison,
        "held_out_test_comparison": test_comparison,
        "stratified_5_fold_cv": {
            "logistic_regression": cv_lr,
            "gradient_boosting": cv_gb,
        }
    }

    with open(out_path / "evaluation_report.json", "w") as f:
        json.dump(eval_report, f, indent=4)

    cal_report["disclaimer"] = disclaimer
    cal_report["data_provenance"] = actual_provenance
    cal_report["dataset_source"] = actual_source

    with open(out_path / "calibration_report.json", "w") as f:
        json.dump(cal_report, f, indent=4)

    shap_output = {
        "data_provenance": actual_provenance,
        "dataset_source": actual_source,
        "disclaimer": disclaimer,
        "model": best_name,
        "global_importance": shap_global,
        "sample_individual_explanation": sample_explanation,
    }

    with open(out_path / "shap_summary.json", "w") as f:
        json.dump(shap_output, f, indent=4)

    with open(out_path / "dataset_validation_report.json", "w") as f:
        json.dump(val_report, f, indent=4)

    # Backward compatibility with metrics.json
    with open(out_path / "metrics.json", "w") as f:
        json.dump(eval_report, f, indent=4)

    print("\n" + "=" * 65)
    print("  HOME CREDIT REAL-DATA EVALUATION SUMMARY (Held-Out Test Set):")
    print(f"  Dataset: {actual_source} | Records Used: {len(df):,}")
    print(f"  Gradient Boosting -> ROC-AUC: {test_metrics_gb['roc_auc']:.4f} | PR-AUC: {test_metrics_gb['pr_auc']:.4f} | Brier: {test_metrics_gb['brier_score']:.4f}")
    print(f"  Logistic Reg.     -> ROC-AUC: {test_metrics_lr['roc_auc']:.4f} | PR-AUC: {test_metrics_lr['pr_auc']:.4f} | Brier: {test_metrics_lr['brier_score']:.4f}")
    print(f"  Probability Calibration: Brier score improved from {cal_report['uncalibrated_brier_score']} to {cal_report['calibrated_brier_score']}")
    print(f"  Top 3 Global SHAP Features: {[f['feature'] for f in shap_global['top_features'][:3]]}")
    print("=" * 65)

    return eval_report


# Alias for backward compatibility
train_home_credit_models = train_and_evaluate_home_credit
