"""
Automated Integration Tests for LoanSense AI FastAPI Backend.
Validates all REST endpoints: Auth, Portfolio, Applications, EMI, Risk, Home Credit, and AI Underwriting.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LoanSense AI API"


def test_api_portfolio_get():
    res = client.get("/api/portfolio")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "charts" in data
    assert "applications" in data
    assert "total_applications" in data["kpis"]
    assert len(data["applications"]) > 0


def test_api_portfolio_filtering():
    res = client.get("/api/portfolio?purpose=Home%20Loan&status_filter=approved")
    assert res.status_code == 200
    data = res.json()
    for app_item in data["applications"]:
        assert app_item["loan_purpose"] == "Home Loan"
        assert app_item["status"] == "approved"


def test_api_calculate_risk_advisory():
    payload = {
        "name": "Kiran Kumar",
        "loan_amount": 500000.0,
        "annual_income": 900000.0,
        "employment_type": "Salaried",
        "property_area": "Urban",
        "existing_loans": 1,
        "tenure_months": 36,
        "interest_rate": 10.5,
        "loan_purpose": "Personal Loan",
        "credit_score": 750
    }
    res = client.post("/api/applications/calculate-risk", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "emi" in data
    assert "risk_score" in data
    assert "ml_prob" in data
    assert "ml_band" in data
    assert "advisory_status" in data
    assert "ADVISORY NOTICE" in data["disclaimer"]


def test_api_emi_calculation_with_prepayment():
    payload = {
        "principal": 1000000.0,
        "annual_rate": 8.5,
        "tenure_months": 120,
        "processing_fee_pct": 1.0,
        "monthly_prepayment": 2000.0,
        "lump_sum_prepayment": 50000.0,
        "lump_sum_month": 12
    }
    res = client.post("/api/emi/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["base_emi"] > 0
    assert data["interest_saved"] > 0
    assert data["tenure_months_saved"] > 0
    assert len(data["accelerated_schedule"]) > 0


def test_api_risk_summary():
    res = client.get("/api/risk/summary?min_dpd=10&max_score=700")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "delinquency_watchlist" in data
    assert "supervised_models" in data


def test_api_stress_test():
    payload = {
        "baseline_exposure_cr": 300.0,
        "baseline_npa_rate": 3.0,
        "rate_shock_bps": 200,
        "income_shock_pct": 15.0
    }
    res = client.post("/api/risk/stress-test", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["stressed_npa_rate"] > 3.0
    assert data["npa_surge_pct"] > 0
    assert data["incremental_capital_at_risk_cr"] > 0


def test_api_home_credit_evaluation():
    res = client.get("/api/home-credit/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert "evaluation_report" in data
    assert "calibration_report" in data
    assert "shap_summary" in data


def test_api_home_credit_predict():
    payload = {
        "AMT_INCOME_TOTAL": 250000.0,
        "AMT_CREDIT": 500000.0,
        "AMT_ANNUITY": 25000.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "Y",
        "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 0,
        "DAYS_BIRTH": -15000,
        "DAYS_EMPLOYED": -3000,
        "EXT_SOURCE_1": 0.65,
        "EXT_SOURCE_2": 0.70,
        "EXT_SOURCE_3": 0.75,
        "INSTAL_LATE_RATIO": 0.0
    }
    res = client.post("/api/home-credit/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "calibrated_default_probability" in data
    assert "risk_band" in data
    assert "risk_drivers" in data
    assert "safety_drivers" in data
    assert "ADVISORY NOTICE" in data["disclaimer"]


def test_api_underwrite_advisory():
    applicant = {
        "name": "Sunita Patil",
        "annual_income": 800000.0,
        "credit_score": 710,
        "employment_type": "Salaried",
        "existing_loans": 1,
        "loan_amount": 1200000.0,
        "loan_purpose": "Home Loan",
        "tenure_months": 180,
        "interest_rate": 8.75,
        "approval_probability": 75.0,
        "ml_default_probability": 15.0,
        "ml_risk_band": "Low"
    }
    res = client.post("/api/ai/underwrite", json=applicant)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "memorandum" in data
    assert "ADVISORY" in data["disclaimer"]


def test_api_policy_query():
    req = {
        "query": "What is the maximum allowed DTI for salaried borrowers?",
        "credit_score": 720,
        "dti_percent": 42.0,
        "loan_purpose": "Home Loan"
    }
    res = client.post("/api/ai/policy-query", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "clauses" in data
    assert len(data["clauses"]) > 0
    assert "synthesis" in data
    assert "ADVISORY" in data["disclaimer"]
