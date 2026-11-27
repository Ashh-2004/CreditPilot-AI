"""
Tests for AI Loan Analyst service and advisory governance.
"""

import pytest
from services.loan_analyst import generate_advisory_underwriting_memo, ADVISORY_DISCLAIMER


def test_deterministic_memo_fallback_without_api_key():
    applicant = {
        "name": "Rajesh Patel",
        "annual_income": 600000,
        "credit_score": 580,
        "employment_type": "Self-Employed",
        "existing_loans": 3,
        "loan_amount": 500000,
        "loan_purpose": "Personal Loan",
        "tenure_months": 36,
        "interest_rate": 14.5,
        "approval_probability": 40.0,
        "ml_default_probability": 58.0,
        "ml_risk_band": "High"
    }

    # Pass api_key="" to trigger deterministic fallback
    result = generate_advisory_underwriting_memo(applicant, api_key="")

    assert result["status"] == "success"
    assert result["source"] == "deterministic_policy_engine"
    assert "Rajesh Patel" in result["memorandum"]
    assert ADVISORY_DISCLAIMER in result["memorandum"]
    assert "Subprime credit score" in result["memorandum"]
    assert len(result["retrieved_clauses"]) > 0


def test_memo_contains_strict_advisory_disclaimer():
    applicant = {
        "name": "Meera Joshi",
        "annual_income": 1500000,
        "credit_score": 790,
        "employment_type": "Salaried",
        "existing_loans": 0,
        "loan_amount": 1000000,
        "loan_purpose": "Home Loan",
        "tenure_months": 120,
        "interest_rate": 8.0,
        "approval_probability": 90.0,
        "ml_default_probability": 5.0,
        "ml_risk_band": "Low"
    }

    result = generate_advisory_underwriting_memo(applicant, api_key="")
    assert "ADVISORY" in result["disclaimer"]
    assert "human loan officer" in result["disclaimer"]
