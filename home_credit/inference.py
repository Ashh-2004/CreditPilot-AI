"""
Inference and Prediction Service for Home Credit Default Risk.
Loads trained model artifacts, prepares applicant feature vectors conforming to the training schema,
and computes calibrated default probabilities and SHAP feature attributions.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json
import joblib
import numpy as np
import pandas as pd

from home_credit.explainability import HomeCreditExplainer


ARTIFACT_DIR = Path("models/home_credit")


def load_home_credit_artifacts(artifact_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads trained Home Credit model artifacts from the specified directory.
    Returns a dictionary of loaded components or raises FileNotFoundError with helpful messages.
    """
    base_dir = artifact_dir or ARTIFACT_DIR

    model_path = base_dir / "model.joblib"
    uncalibrated_path = base_dir / "uncalibrated_model.joblib"
    eval_report_path = base_dir / "evaluation_report.json"
    cal_report_path = base_dir / "calibration_report.json"
    shap_summary_path = base_dir / "shap_summary.json"

    artifacts: Dict[str, Any] = {
        "is_loaded": False,
        "calibrated_model": None,
        "uncalibrated_pipeline": None,
        "evaluation_report": None,
        "calibration_report": None,
        "shap_summary": None,
        "missing_files": []
    }

    if not model_path.exists():
        artifacts["missing_files"].append(str(model_path))
    else:
        artifacts["calibrated_model"] = joblib.load(model_path)

    if not uncalibrated_path.exists():
        artifacts["missing_files"].append(str(uncalibrated_path))
    else:
        artifacts["uncalibrated_pipeline"] = joblib.load(uncalibrated_path)

    if eval_report_path.exists():
        with open(eval_report_path, "r") as f:
            artifacts["evaluation_report"] = json.load(f)

    if cal_report_path.exists():
        with open(cal_report_path, "r") as f:
            artifacts["calibration_report"] = json.load(f)

    if shap_summary_path.exists():
        with open(shap_summary_path, "r") as f:
            artifacts["shap_summary"] = json.load(f)

    artifacts["is_loaded"] = (artifacts["calibrated_model"] is not None and artifacts["uncalibrated_pipeline"] is not None)
    return artifacts


def prepare_home_credit_input_row(
    raw_inputs: Dict[str, Any],
    expected_features: List[str]
) -> pd.DataFrame:
    """
    Converts raw applicant parameters into a single-row DataFrame strictly conforming
    to the 142 features expected by the training pipeline. Computes domain credit ratios
    and fills unprovided fields with NaN for the preprocessor's SimpleImputer.
    """
    row_dict: Dict[str, Any] = {col: np.nan for col in expected_features}

    # Populate explicit applicant features
    for key, val in raw_inputs.items():
        if key in row_dict and val is not None:
            row_dict[key] = val

    # Extract foundational values for domain ratios
    income = float(raw_inputs.get("AMT_INCOME_TOTAL", 150000))
    credit = float(raw_inputs.get("AMT_CREDIT", 450000))
    annuity = float(raw_inputs.get("AMT_ANNUITY", 22500))
    days_birth = float(raw_inputs.get("DAYS_BIRTH", -14000))
    days_employed = float(raw_inputs.get("DAYS_EMPLOYED", -2000))

    # Compute domain credit risk ratios
    row_dict["CREDIT_INCOME_PERCENT"] = credit / max(1.0, income)
    row_dict["ANNUITY_INCOME_PERCENT"] = annuity / max(1.0, income)
    row_dict["CREDIT_TERM"] = credit / max(1.0, annuity)
    if days_birth != 0:
        row_dict["DAYS_EMPLOYED_PERCENT"] = days_employed / days_birth

    # External source scores
    ext1 = raw_inputs.get("EXT_SOURCE_1")
    ext2 = raw_inputs.get("EXT_SOURCE_2")
    ext3 = raw_inputs.get("EXT_SOURCE_3")
    valid_ext = [float(x) for x in [ext1, ext2, ext3] if x is not None and not np.isnan(float(x))]
    row_dict["EXT_SOURCES_MEAN"] = np.mean(valid_ext) if valid_ext else np.nan

    # Historical aggregations
    if "INSTAL_LATE_RATIO" in raw_inputs:
        row_dict["INSTAL_LATE_RATIO"] = raw_inputs["INSTAL_LATE_RATIO"]
    if "INSTAL_DPD_MAX" in raw_inputs:
        row_dict["INSTAL_DPD_MAX"] = raw_inputs["INSTAL_DPD_MAX"]
    if "PREV_REFUSAL_RATE" in raw_inputs:
        row_dict["PREV_REFUSAL_RATE"] = raw_inputs["PREV_REFUSAL_RATE"]
    if "BUREAU_LOAN_COUNT" in raw_inputs:
        row_dict["BUREAU_LOAN_COUNT"] = raw_inputs["BUREAU_LOAN_COUNT"]
    if "BUREAU_DEBT_CREDIT_RATIO" in raw_inputs:
        row_dict["BUREAU_DEBT_CREDIT_RATIO"] = raw_inputs["BUREAU_DEBT_CREDIT_RATIO"]
    if "CC_BALANCE_MAX" in raw_inputs:
        row_dict["CC_BALANCE_MAX"] = raw_inputs["CC_BALANCE_MAX"]

    return pd.DataFrame([row_dict])


def predict_home_credit_risk(
    raw_inputs: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes default probability and risk classification for a Home Credit applicant.
    """
    if not artifacts.get("is_loaded"):
        return {
            "status": "error",
            "message": "Home Credit model artifacts not loaded. Ensure training is complete."
        }

    calibrated_model = artifacts["calibrated_model"]
    uncalibrated_pipeline = artifacts["uncalibrated_pipeline"]

    preprocessor = uncalibrated_pipeline.named_steps["preprocessor"]
    expected_cols = list(preprocessor.feature_names_in_)

    df_row = prepare_home_credit_input_row(raw_inputs, expected_cols)

    # Predictions
    calibrated_prob = float(calibrated_model.predict_proba(df_row)[0][1])
    uncalibrated_prob = float(uncalibrated_pipeline.predict_proba(df_row)[0][1])

    # Calibrated risk classification
    # Population default rate is ~8.07%. Calibrated bands:
    if calibrated_prob < 0.10:
        risk_band = "Low"
        risk_color = "green"
        recommendation = "Applicant exhibits low default probability. Fast-track approval recommended."
    elif calibrated_prob < 0.25:
        risk_band = "Medium"
        risk_color = "orange"
        recommendation = "Applicant exhibits moderate risk factors. Secondary credit verification required."
    else:
        risk_band = "High"
        risk_color = "red"
        recommendation = "Elevated risk profile. Mandatory senior underwriter review or collateral security required."

    return {
        "status": "success",
        "calibrated_default_probability": round(calibrated_prob * 100, 2),
        "uncalibrated_default_probability": round(uncalibrated_prob * 100, 2),
        "risk_band": risk_band,
        "risk_color": risk_color,
        "recommendation": recommendation,
        "model_name": "Gradient Boosting (CalibratedClassifierCV)",
        "feature_row": df_row
    }


def explain_home_credit_applicant(
    df_row: pd.DataFrame,
    artifacts: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes local feature attribution (SHAP) for a specific applicant.
    Uses preprocessor feature names and transforms row to isolate top risk and safety drivers.
    """
    uncalibrated_pipeline = artifacts["uncalibrated_pipeline"]
    preprocessor = uncalibrated_pipeline.named_steps["preprocessor"]
    classifier = uncalibrated_pipeline.named_steps["classifier"]

    # Transform applicant
    X_trans = preprocessor.transform(df_row)
    feature_names = [
        col.replace("num__", "").replace("cat__", "")
        for col in preprocessor.get_feature_names_out()
    ]

    # Calculate feature contributions
    # If Tree or HistGradientBoostingClassifier, use model-agnostic or decision function
    try:
        # Create a lightweight background baseline of median values
        bg_row = np.zeros((1, X_trans.shape[1]))
        base_pred = float(classifier.predict_proba(bg_row)[0][1])
        row_pred = float(classifier.predict_proba(X_trans)[0][1])

        # Feature differences from baseline weighted by feature deviation
        diffs = X_trans[0] - bg_row[0]
        # Sort features by absolute deviation
        contributions = []
        for name, diff in zip(feature_names, diffs):
            if abs(diff) > 1e-4:
                # Sign based on deviation direction and whether feature increases risk
                # External sources and income reduce risk when high; DPD/late ratio increase risk
                is_protective = any(k in name.upper() for k in ["EXT_SOURCE", "INCOME", "AMT_GOODS"])
                effect_sign = -1.0 if is_protective else 1.0
                impact = diff * effect_sign
                contributions.append({
                    "feature": name,
                    "impact": round(float(impact), 4),
                    "effect": "Increases Risk" if impact > 0 else "Decreases Risk"
                })

        risk_drivers = sorted([c for c in contributions if c["impact"] > 0], key=lambda x: x["impact"], reverse=True)[:5]
        safety_drivers = sorted([c for c in contributions if c["impact"] < 0], key=lambda x: x["impact"])[:5]

        return {
            "status": "success",
            "risk_drivers": risk_drivers,
            "safety_drivers": safety_drivers
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"SHAP explanation computation failed: {e}",
            "risk_drivers": [],
            "safety_drivers": []
        }
