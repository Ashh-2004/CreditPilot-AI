"""
Tests for Home Credit Frontend Integration (Phase 5.1).
Validates artifact loading, feature preprocessing alignment, calibrated predictions,
SHAP local attribution, missing-artifact handling, and Indian borrower model isolation.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from home_credit.inference import (
    load_home_credit_artifacts,
    prepare_home_credit_input_row,
    predict_home_credit_risk,
    explain_home_credit_applicant
)


def test_load_home_credit_artifacts_success():
    artifacts = load_home_credit_artifacts()
    assert artifacts["is_loaded"] is True
    assert artifacts["calibrated_model"] is not None
    assert artifacts["uncalibrated_pipeline"] is not None
    assert artifacts["evaluation_report"] is not None
    assert artifacts["calibration_report"] is not None
    assert artifacts["shap_summary"] is not None
    assert len(artifacts["missing_files"]) == 0


def test_load_home_credit_artifacts_missing_directory(tmp_path):
    empty_dir = tmp_path / "empty_models"
    empty_dir.mkdir()
    artifacts = load_home_credit_artifacts(artifact_dir=empty_dir)
    assert artifacts["is_loaded"] is False
    assert len(artifacts["missing_files"]) >= 2


def test_prepare_home_credit_input_row_alignment():
    artifacts = load_home_credit_artifacts()
    expected_cols = list(artifacts["uncalibrated_pipeline"].named_steps["preprocessor"].feature_names_in_)
    assert len(expected_cols) == 142

    raw_input = {
        "AMT_INCOME_TOTAL": 250000.0,
        "AMT_CREDIT": 500000.0,
        "AMT_ANNUITY": 25000.0,
        "DAYS_BIRTH": -14600,
        "DAYS_EMPLOYED": -2920,
        "EXT_SOURCE_1": 0.65,
        "EXT_SOURCE_2": 0.70,
        "EXT_SOURCE_3": 0.75,
        "INSTAL_LATE_RATIO": 0.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "F"
    }

    df_row = prepare_home_credit_input_row(raw_input, expected_cols)
    assert df_row.shape == (1, 142)
    assert list(df_row.columns) == expected_cols

    # Verify domain ratios
    assert df_row["CREDIT_INCOME_PERCENT"].iloc[0] == 2.0
    assert df_row["ANNUITY_INCOME_PERCENT"].iloc[0] == 0.10
    assert df_row["CREDIT_TERM"].iloc[0] == 20.0
    assert round(df_row["DAYS_EMPLOYED_PERCENT"].iloc[0], 2) == 0.20
    assert round(df_row["EXT_SOURCES_MEAN"].iloc[0], 2) == 0.70


def test_predict_home_credit_risk_prime_vs_subprime():
    artifacts = load_home_credit_artifacts()

    prime_input = {
        "AMT_INCOME_TOTAL": 300000.0,
        "AMT_CREDIT": 400000.0,
        "AMT_ANNUITY": 20000.0,
        "DAYS_BIRTH": -16000,
        "DAYS_EMPLOYED": -4000,
        "EXT_SOURCE_1": 0.75,
        "EXT_SOURCE_2": 0.72,
        "EXT_SOURCE_3": 0.80,
        "INSTAL_LATE_RATIO": 0.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "F"
    }

    subprime_input = {
        "AMT_INCOME_TOTAL": 100000.0,
        "AMT_CREDIT": 700000.0,
        "AMT_ANNUITY": 35000.0,
        "DAYS_BIRTH": -9000,
        "DAYS_EMPLOYED": -300,
        "EXT_SOURCE_1": 0.15,
        "EXT_SOURCE_2": 0.18,
        "EXT_SOURCE_3": 0.12,
        "INSTAL_LATE_RATIO": 0.45,
        "INSTAL_DPD_MAX": 60.0,
        "PREV_REFUSAL_RATE": 0.60,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "M"
    }

    res_prime = predict_home_credit_risk(prime_input, artifacts)
    res_subprime = predict_home_credit_risk(subprime_input, artifacts)

    assert res_prime["status"] == "success"
    assert res_subprime["status"] == "success"

    # Subprime default probability should be substantially higher than prime
    assert res_subprime["calibrated_default_probability"] > res_prime["calibrated_default_probability"]
    assert res_prime["risk_band"] in ("Low", "Medium")
    assert res_subprime["risk_band"] in ("Medium", "High")


def test_explain_home_credit_applicant_attribution():
    artifacts = load_home_credit_artifacts()
    expected_cols = list(artifacts["uncalibrated_pipeline"].named_steps["preprocessor"].feature_names_in_)

    raw_input = {
        "AMT_INCOME_TOTAL": 150000.0,
        "AMT_CREDIT": 500000.0,
        "AMT_ANNUITY": 25000.0,
        "EXT_SOURCE_1": 0.70,
        "EXT_SOURCE_2": 0.75,
        "EXT_SOURCE_3": 0.80,
        "INSTAL_LATE_RATIO": 0.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "M"
    }

    df_row = prepare_home_credit_input_row(raw_input, expected_cols)
    explanation = explain_home_credit_applicant(df_row, artifacts)

    assert explanation["status"] == "success"
    assert "risk_drivers" in explanation
    assert "safety_drivers" in explanation


def test_indian_borrower_workflow_complete_isolation():
    # 1. Verify Indian retail borrower model exists and is distinct
    indian_model_path = Path("models/xgboost_model.joblib")
    assert indian_model_path.exists()

    # 2. Verify modules/application.py imports predict_loan_default from modules.ml_model
    with open("modules/application.py", "r") as f:
        app_code = f.read()
    assert "from modules.ml_model import predict_loan_default" in app_code
    assert "models/home_credit" not in app_code

    # 3. Verify modules/ml_model.py loads models/xgboost_model.joblib
    with open("modules/ml_model.py", "r") as f:
        ml_code = f.read()
    assert "xgboost_model.joblib" in ml_code
    assert "models/home_credit" not in ml_code

    # 3. Verify Indian schema features in modules/application.py
    assert "credit_score" in app_code
    assert "annual_income" in app_code
    assert "property_area" in app_code
