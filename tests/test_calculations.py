"""
Tests for financial formulas and analytical algorithms in calculations.py.
"""

import pytest
from calculations import (
    calc_emi,
    calc_risk_score,
    calc_amortization_schedule,
    calc_stress_test_impact
)


class TestEmiCalculation:
    """Test standard reducing balance EMI formula."""

    def test_standard_emi(self):
        # Principal: 500,000, Rate: 10.5% p.a., Tenure: 36 months
        emi = calc_emi(500000, 10.5, 36)
        # Expected EMI: approx 16254.67
        assert 16200 < emi < 16300
        assert isinstance(emi, float)

    def test_zero_interest_rate(self):
        # Principal: 120,000, Rate: 0%, Tenure: 12 months
        emi = calc_emi(120000, 0, 12)
        assert emi == 10000.0

    def test_single_month_tenure(self):
        emi = calc_emi(10000, 12.0, 1)
        # 10000 + 1 month interest (100) = 10100
        assert emi == 10100.0


class TestRiskScoreCalculation:
    """Test traditional rule-based scoring engine."""

    def test_perfect_borrower_score(self):
        # Excellent credit (750+ -> 35), low EMI ratio (<30 -> 30), 0 existing loans (20), Govt employee (15)
        score = calc_risk_score(credit_score=800, emi_ratio=20.0, existing_loans=0, employment="Government")
        assert score == 100

    def test_high_risk_borrower_score(self):
        # Poor credit (<650 -> 5), high EMI ratio (>=50 -> 0), 3 existing loans (0), Self-Employed (8)
        score = calc_risk_score(credit_score=500, emi_ratio=55.0, existing_loans=3, employment="Self-Employed")
        assert score == 13

    def test_moderate_salaried_borrower(self):
        # Credit: 710 -> 25, EMI ratio: 35 -> 20, existing: 1 -> 12, employment: Salaried -> 15 => Total 72
        score = calc_risk_score(credit_score=710, emi_ratio=35.0, existing_loans=1, employment="Salaried")
        assert score == 72

    def test_score_does_not_exceed_100(self):
        score = calc_risk_score(credit_score=900, emi_ratio=10.0, existing_loans=0, employment="Government")
        assert score <= 100


class TestAmortizationPrepayment:
    """Test amortization schedule and accelerated prepayment analytics."""

    def test_standard_amortization_schedule_no_prepayment(self):
        res = calc_amortization_schedule(
            principal=300000,
            annual_rate=10.0,
            tenure_months=36,
            monthly_prepayment=0.0
        )
        assert len(res["schedule"]) == 36
        assert res["actual_tenure_months"] == 36
        assert res["tenure_months_saved"] == 0
        assert res["interest_saved"] == 0.0
        assert res["schedule"][-1]["closing_balance"] == 0.0

    def test_accelerated_monthly_prepayment(self):
        # ₹500,000 at 9.0% for 60 months with ₹2,000 extra per month
        base_res = calc_amortization_schedule(500000, 9.0, 60, monthly_prepayment=0.0)
        accel_res = calc_amortization_schedule(500000, 9.0, 60, monthly_prepayment=2000.0)

        assert accel_res["actual_tenure_months"] < 60
        assert accel_res["tenure_months_saved"] > 0
        assert accel_res["interest_saved"] > 0.0
        assert accel_res["total_interest"] < base_res["total_interest"]

    def test_lump_sum_prepayment_saves_interest(self):
        res = calc_amortization_schedule(
            principal=1000000,
            annual_rate=8.5,
            tenure_months=120,
            monthly_prepayment=0.0,
            lump_sum_prepayment=150000,
            lump_sum_month=12
        )
        assert res["tenure_months_saved"] >= 12
        assert res["interest_saved"] > 50000.0


class TestStressTesting:
    """Test macro-prudential portfolio stress testing calculations."""

    def test_stress_test_impact_rate_and_income_shock(self):
        res = calc_stress_test_impact(
            baseline_exposure=100000000,  # ₹10 Cr
            baseline_npa_rate=2.5,
            rate_shock_bps=200,          # +2.0% interest rate
            income_shock_pct=15.0        # -15% income contraction
        )
        assert res["stressed_npa_rate"] > res["baseline_npa_rate"]
        assert res["npa_surge_pct"] > 0.0
        assert res["stressed_npa_amount"] > res["baseline_npa_amount"]
        assert res["incremental_capital_at_risk"] > 0.0

    def test_zero_shock_matches_baseline(self):
        res = calc_stress_test_impact(
            baseline_exposure=50000000,
            baseline_npa_rate=3.0,
            rate_shock_bps=0,
            income_shock_pct=0.0
        )
        assert res["stressed_npa_rate"] == 3.0
        assert res["npa_surge_pct"] == 0.0
        assert res["incremental_capital_at_risk"] == 0.0
