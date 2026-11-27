"""
Rigorous evaluation and probability calibration module for Home Credit Default Risk.
Computes ROC-AUC, PR-AUC, Brier score, and calibration curves using stratified validation.
All outputs carry explicit synthetic-data disclaimers.
"""

from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    brier_score_loss,
)

SYNTHETIC_DATA_DISCLAIMER = (
    "DISCLAIMER: All metrics are computed on a synthetic sample strictly conforming to the Home Credit schema. "
    "These metrics must NOT be presented as actual Home Credit Kaggle competition performance until the official "
    "competition dataset is ingested."
)


def compute_comprehensive_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Computes a full suite of classification and calibration metrics:
    - ROC-AUC
    - PR-AUC (Average Precision)
    - Accuracy, Precision, Recall, F1
    - Brier Score Loss (probabilistic calibration error)
    - Confusion Matrix [[TN, FP], [FN, TP]]
    """
    y_pred = (y_prob >= threshold).astype(int)

    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier_score = float(brier_score_loss(y_true, y_prob))
    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "brier_score": round(brier_score, 4),
        "confusion_matrix": cm,
    }


def evaluate_with_stratified_cv(
    pipeline_factory,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Performs k-fold Stratified Cross-Validation on the training set.
    Ensures fold isolation without touching the held-out test set.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    cv_roc_auc = []
    cv_pr_auc = []
    cv_f1 = []
    cv_brier = []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
        X_fold_train, X_fold_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_fold_train, y_fold_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model = pipeline_factory()
        model.fit(X_fold_train, y_fold_train)

        probs = model.predict_proba(X_fold_val)[:, 1]

        cv_roc_auc.append(roc_auc_score(y_fold_val, probs))
        cv_pr_auc.append(average_precision_score(y_fold_val, probs))
        cv_f1.append(f1_score(y_fold_val, (probs >= 0.5).astype(int), zero_division=0))
        cv_brier.append(brier_score_loss(y_fold_val, probs))

    return {
        "n_splits": n_splits,
        "cv_roc_auc_mean": round(float(np.mean(cv_roc_auc)), 4),
        "cv_roc_auc_std": round(float(np.std(cv_roc_auc)), 4),
        "cv_pr_auc_mean": round(float(np.mean(cv_pr_auc)), 4),
        "cv_pr_auc_std": round(float(np.std(cv_pr_auc)), 4),
        "cv_f1_mean": round(float(np.mean(cv_f1)), 4),
        "cv_brier_mean": round(float(np.mean(cv_brier)), 4),
    }


def calibrate_and_evaluate_curves(
    uncalibrated_pipeline,
    pipeline_factory,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    method: str = "sigmoid",
    cv: int = 3
) -> Tuple[Any, Dict[str, Any]]:
    """
    Calibrates model default probabilities using CalibratedClassifierCV.
    Calculates calibration curves (reliability diagrams) before and after calibration.
    Returns (calibrated_model, calibration_metrics).
    """
    # 1. Uncalibrated test evaluation
    uncalibrated_probs = uncalibrated_pipeline.predict_proba(X_test)[:, 1]
    uncal_brier = float(brier_score_loss(y_test, uncalibrated_probs))

    prob_true_uncal, prob_pred_uncal = calibration_curve(
        y_test, uncalibrated_probs, n_bins=10, strategy="uniform"
    )

    # 2. Fit probability calibrator using cross-validation on training data
    calibrated_model = CalibratedClassifierCV(
        estimator=pipeline_factory(),
        method=method,
        cv=cv
    )
    calibrated_model.fit(X_train, y_train)

    calibrated_probs = calibrated_model.predict_proba(X_test)[:, 1]
    cal_brier = float(brier_score_loss(y_test, calibrated_probs))

    prob_true_cal, prob_pred_cal = calibration_curve(
        y_test, calibrated_probs, n_bins=10, strategy="uniform"
    )

    calibration_report = {
        "calibration_method": method,
        "uncalibrated_brier_score": round(uncal_brier, 4),
        "calibrated_brier_score": round(cal_brier, 4),
        "brier_improvement_percent": round(max(0.0, (uncal_brier - cal_brier) / max(1e-6, uncal_brier) * 100), 2),
        "uncalibrated_curve": {
            "mean_predicted_probability": [round(float(x), 4) for x in prob_pred_uncal],
            "fraction_of_positives": [round(float(x), 4) for x in prob_true_uncal],
        },
        "calibrated_curve": {
            "mean_predicted_probability": [round(float(x), 4) for x in prob_pred_cal],
            "fraction_of_positives": [round(float(x), 4) for x in prob_true_cal],
        },
        "disclaimer": SYNTHETIC_DATA_DISCLAIMER
    }

    return calibrated_model, calibration_report
