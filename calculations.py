"""
Financial calculations and analytical algorithms for LoanSense AI.
Includes reducing balance EMI calculations, traditional credit scoring,
amortization schedule generation with prepayment analysis, and portfolio stress testing.
"""

from typing import Dict, Any, List, Tuple


def calc_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Standard reducing balance EMI formula."""
    if tenure_months <= 0:
        return 0.0
    r = annual_rate / 100 / 12
    n = tenure_months
    if r == 0:
        return round(principal / n, 2)
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return round(emi, 2)


def calc_risk_score(credit_score: int, emi_ratio: float,
                    existing_loans: int, employment: str) -> int:
    """
    Returns approval probability 0–100.
    Weights: credit score 35, EMI ratio 30, existing loans 20, employment 15
    """
    score = 0

    # Credit score (35 pts)
    if credit_score >= 750:   score += 35
    elif credit_score >= 700: score += 25
    elif credit_score >= 650: score += 15
    else:                     score += 5

    # EMI/Income ratio (30 pts)
    if emi_ratio < 30:   score += 30
    elif emi_ratio < 40: score += 20
    elif emi_ratio < 50: score += 10
    else:                score += 0

    # Existing loans (20 pts)
    if existing_loans == 0:   score += 20
    elif existing_loans == 1: score += 12
    elif existing_loans == 2: score += 5
    else:                     score += 0

    # Employment type (15 pts)
    if employment in ["Government", "Salaried"]: score += 15
    else:                                         score += 8

    return min(score, 100)


def calc_amortization_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    monthly_prepayment: float = 0.0,
    lump_sum_prepayment: float = 0.0,
    lump_sum_month: int = 0
) -> Dict[str, Any]:
    """
    Generates a full month-by-month reducing balance amortization schedule.
    Supports optional monthly extra prepayments and a one-time lump-sum prepayment.
    Computes total interest saved and tenure reduction compared to baseline.
    """
    if principal <= 0 or tenure_months <= 0:
        return {
            "schedule": [],
            "total_interest": 0.0,
            "total_payment": 0.0,
            "actual_tenure_months": 0,
            "interest_saved": 0.0,
            "tenure_months_saved": 0,
            "baseline_interest": 0.0,
        }

    # Baseline calculations
    base_emi = calc_emi(principal, annual_rate, tenure_months)
    base_total_payment = round(base_emi * tenure_months, 2)
    base_interest = round(base_total_payment - principal, 2)

    r = annual_rate / 100.0 / 12.0
    balance = float(principal)
    schedule: List[Dict[str, Any]] = []
    total_interest_paid = 0.0
    total_principal_paid = 0.0

    for m in range(1, tenure_months + 1):
        if balance <= 0.01:
            break

        interest_comp = round(balance * r, 2)
        scheduled_principal = round(base_emi - interest_comp, 2)

        # Extra prepayments
        extra = monthly_prepayment
        if m == lump_sum_month and lump_sum_prepayment > 0:
            extra += lump_sum_prepayment

        actual_principal = min(balance, scheduled_principal + extra)
        closing_balance = max(0.0, round(balance - actual_principal, 2))
        monthly_total_paid = round(interest_comp + actual_principal, 2)

        total_interest_paid += interest_comp
        total_principal_paid += actual_principal

        schedule.append({
            "month": m,
            "opening_balance": round(balance, 2),
            "interest_component": interest_comp,
            "principal_component": actual_principal,
            "total_payment": monthly_total_paid,
            "closing_balance": closing_balance,
        })

        balance = closing_balance

    actual_tenure = len(schedule)
    if monthly_prepayment == 0.0 and (lump_sum_prepayment == 0.0 or lump_sum_month <= 0):
        interest_saved = 0.0
        tenure_saved = 0
    else:
        interest_saved = max(0.0, round(base_interest - total_interest_paid, 2))
        tenure_saved = max(0, tenure_months - actual_tenure)

    return {
        "schedule": schedule,
        "base_emi": base_emi,
        "total_interest": round(total_interest_paid, 2),
        "total_payment": round(total_principal_paid + total_interest_paid, 2),
        "actual_tenure_months": actual_tenure,
        "interest_saved": interest_saved,
        "tenure_months_saved": tenure_saved,
        "baseline_interest": base_interest,
    }


def calc_stress_test_impact(
    baseline_exposure: float,
    baseline_npa_rate: float,
    rate_shock_bps: int = 150,
    income_shock_pct: float = 10.0
) -> Dict[str, Any]:
    """
    Simulates macro-prudential stress testing on loan portfolio.
    Estimates portfolio default surge, stressed NPA rate, and potential capital provisioning requirement.
    """
    # Sensitivity coefficients based on retail portfolio stress testing conventions
    rate_sensitivity = (rate_shock_bps / 100.0) * 0.45  # each 100 bps adds ~0.45% default migration
    income_sensitivity = (income_shock_pct / 10.0) * 0.65 # each 10% income contraction adds ~0.65% default migration

    stressed_npa_rate = min(35.0, round(baseline_npa_rate + rate_sensitivity + income_sensitivity, 2))
    npa_surge_pct = round(max(0.0, stressed_npa_rate - baseline_npa_rate), 2)

    baseline_npa_amount = round(baseline_exposure * (baseline_npa_rate / 100.0), 2)
    stressed_npa_amount = round(baseline_exposure * (stressed_npa_rate / 100.0), 2)
    incremental_capital_at_risk = round(stressed_npa_amount - baseline_npa_amount, 2)

    return {
        "baseline_npa_rate": baseline_npa_rate,
        "stressed_npa_rate": stressed_npa_rate,
        "npa_surge_pct": npa_surge_pct,
        "baseline_npa_amount": baseline_npa_amount,
        "stressed_npa_amount": stressed_npa_amount,
        "incremental_capital_at_risk": incremental_capital_at_risk,
        "rate_shock_bps": rate_shock_bps,
        "income_shock_pct": income_shock_pct,
    }
