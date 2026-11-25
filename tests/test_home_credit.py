"""
Tests for the Home Credit Default Risk pipeline, schema, and feature engineering.
"""

import shutil
from pathlib import Path
import pandas as pd
import pytest

from home_credit.schema import (
    TARGET_COLUMN,
    ID_COLUMN,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    validate_home_credit_record,
)
from home_credit.feature_engineering import compute_domain_features
from home_credit.ingestion import load_or_create_home_credit_dataset
from home_credit.pipeline import train_home_credit_models


def test_schema_record_validation():
    """Verify Home Credit record validation logic."""
    valid_record = {
        "AMT_INCOME_TOTAL": 150000.0,
        "AMT_CREDIT": 450000.0,
        "AMT_ANNUITY": 25000.0,
        "CODE_GENDER": "M",
    }
    assert validate_home_credit_record(valid_record)

    invalid_record = {
        "AMT_INCOME_TOTAL": -500.0,
        "AMT_CREDIT": 450000.0,
        "AMT_ANNUITY": 25000.0,
    }
    assert not validate_home_credit_record(invalid_record)


def test_domain_feature_engineering_calculations():
    """Verify domain ratio computations."""
    df_raw = pd.DataFrame([{
        "AMT_INCOME_TOTAL": 100000.0,
        "AMT_CREDIT": 300000.0,
        "AMT_ANNUITY": 15000.0,
        "DAYS_BIRTH": -10000,
        "DAYS_EMPLOYED": -2000,
        "EXT_SOURCE_1": 0.6,
        "EXT_SOURCE_2": 0.7,
        "EXT_SOURCE_3": 0.8,
    }])

    df_featured = compute_domain_features(df_raw)

    # 1. Credit to income: 300k / 100k = 3.0
    assert df_featured["CREDIT_INCOME_PERCENT"].iloc[0] == pytest.approx(3.0)

    # 2. Annuity to income: 15k / 100k = 0.15
    assert df_featured["ANNUITY_INCOME_PERCENT"].iloc[0] == pytest.approx(0.15)

    # 3. Credit term: 15k / 300k = 0.05
    assert df_featured["CREDIT_TERM"].iloc[0] == pytest.approx(0.05)

    # 4. Ext sources mean: (0.6 + 0.7 + 0.8) / 3 = 0.7
    assert df_featured["EXT_SOURCES_MEAN"].iloc[0] == pytest.approx(0.7)


def test_home_credit_ingestion_shape_and_columns():
    """Verify that dataset ingestion generates expected Home Credit columns."""
    df = load_or_create_home_credit_dataset(sample_size=150, random_seed=99)
    assert len(df) == 150
    assert ID_COLUMN in df.columns
    assert TARGET_COLUMN in df.columns

    for col in ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "DAYS_BIRTH"]:
        assert col in df.columns

    # Verify target distribution (defaults exist)
    assert df[TARGET_COLUMN].isin([0, 1]).all()


def test_home_credit_pipeline_train_and_evaluate(tmp_path):
    """Verify end-to-end training, ROC-AUC calculation, and artifact export."""
    test_out = tmp_path / "models_hc_test"

    results = train_home_credit_models(
        output_dir=str(test_out),
        sample_size=200,
        random_state=123
    )

    assert "models" in results
    assert "gradient_boosting" in results["models"]
    assert "logistic_regression" in results["models"]
    assert "roc_auc" in results["models"]["gradient_boosting"]

    # Verify artifacts exist
    assert (test_out / "model.joblib").exists()
    assert (test_out / "metrics.json").exists()


def test_indian_borrower_workflow_separation():
    """Verify that the original Indian borrower pipeline remains distinct and intact."""
    from modules.ml_model import predict_loan_default

    # Original Indian borrower features
    sample_borrower = {
        'credit_score': 720,
        'annual_income': 800000.0,
        'employment_type': 'Salaried',
        'existing_loans': 1,
        'loan_amount': 500000.0,
        'loan_purpose': 'Home Loan',
        'interest_rate': 10.5,
        'tenure_months': 36,
        'age': 30
    }

    prob, band = predict_loan_default(sample_borrower)
    assert isinstance(prob, float)
    assert band in ["Low", "Medium", "High"]
