"""
Institutional Credit Underwriting Policy Rules for LoanSense AI.
Provides grounded credit policy documents and underwriting standards.
"""

from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class PolicyRule:
    clause_id: str
    title: str
    category: str  # 'ELIGIBILITY', 'DEBT_BURDEN', 'PURPOSE_SPECIFIC', 'RISK_MITIGATION', 'REGULATORY'
    applicable_purposes: Set[str]
    min_credit_score: Optional[int]
    max_dti_percent: Optional[float]
    rule_text: str
    guidance: str


POLICY_RULES: List[PolicyRule] = [
    PolicyRule(
        clause_id="POL-ELIG-001",
        title="Minimum Bureau Credit Score Thresholds",
        category="ELIGIBILITY",
        applicable_purposes={"Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan", "Business Loan"},
        min_credit_score=600,
        max_dti_percent=None,
        rule_text="Applicants with a credit score below 600 represent subprime credit risk. Standard unsecured loans are ineligible. Secured facilities require minimum 30% equity/margin or creditworthy guarantor.",
        guidance="Applicants scoring between 600-699 require secondary income verification. Scores >= 700 qualify for prime underwriting."
    ),
    PolicyRule(
        clause_id="POL-DTI-002",
        title="Maximum Debt-to-Income / FOIR Standards",
        category="DEBT_BURDEN",
        applicable_purposes={"Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan", "Business Loan"},
        min_credit_score=None,
        max_dti_percent=50.0,
        rule_text="Total monthly debt service (existing EMI obligations + proposed new EMI) must not exceed 50% of verified gross monthly income for salaried applicants, and 45% for self-employed/business applicants.",
        guidance="If DTI exceeds 50%, loan amount must be curtailed, tenure extended (within purpose caps), or existing high-cost personal loans consolidated."
    ),
    PolicyRule(
        clause_id="POL-PURP-003",
        title="Home Loan Underwriting & LTV Limits",
        category="PURPOSE_SPECIFIC",
        applicable_purposes={"Home Loan"},
        min_credit_score=650,
        max_dti_percent=55.0,
        rule_text="Maximum tenor for Home Loans is 360 months (30 years) or retirement age (whichever is earlier). Maximum Loan-to-Value (LTV) is 80% for loans above 30 Lakhs, and 85% for loans up to 30 Lakhs. Property must hold clear marketable title.",
        guidance="First-time home buyers with clean bureau history can be granted an interest concession of 25 bps."
    ),
    PolicyRule(
        clause_id="POL-PURP-004",
        title="Personal Loan Unsecured Credit Guidelines",
        category="PURPOSE_SPECIFIC",
        applicable_purposes={"Personal Loan"},
        min_credit_score=680,
        max_dti_percent=45.0,
        rule_text="Personal loans are strictly unsecured. Maximum tenor is capped at 60 months. Applicants with 3 or more existing active unsecured loans are ineligible without prior debt payoff.",
        guidance="Risk-based pricing applies: Credit score 680-720 incurs a +1.50% margin premium over base rate."
    ),
    PolicyRule(
        clause_id="POL-PURP-005",
        title="Business Loan Underwriting Standards",
        category="PURPOSE_SPECIFIC",
        applicable_purposes={"Business Loan"},
        min_credit_score=700,
        max_dti_percent=40.0,
        rule_text="Business loan applicants must demonstrate minimum 24 months continuous profitable operations and GST filing compliance. Working capital loans require hypothecation of current assets and personal guarantee of promoters.",
        guidance="For ticket sizes exceeding 25 Lakhs, audited financial statements for preceding 2 fiscal years are mandatory."
    ),
    PolicyRule(
        clause_id="POL-PURP-006",
        title="Vehicle Loan Collateralization & Margin",
        category="PURPOSE_SPECIFIC",
        applicable_purposes={"Vehicle Loan"},
        min_credit_score=620,
        max_dti_percent=50.0,
        rule_text="Vehicle loans require primary hypothecation of the financed asset registered with the Regional Transport Authority. Maximum tenor is 84 months for new vehicles and 48 months for pre-owned.",
        guidance="Minimum down payment is 15% for new vehicles and 30% for used vehicles."
    ),
    PolicyRule(
        clause_id="POL-PURP-007",
        title="Education Loan Underwriting & Moratorium",
        category="PURPOSE_SPECIFIC",
        applicable_purposes={"Education Loan"},
        min_credit_score=620,
        max_dti_percent=None,
        rule_text="Education loans for professional/STEM degrees permit a course-period moratorium plus 12 months grace period. A parent or legal guardian must act as co-borrower. Loans above 7.5 Lakhs require tangible collateral security.",
        guidance="Accredited tier-1 universities qualify for interest rate subsidy during the moratorium period."
    ),
    PolicyRule(
        clause_id="POL-RISK-008",
        title="Machine Learning & Risk Tier Escalation",
        category="RISK_MITIGATION",
        applicable_purposes={"Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan", "Business Loan"},
        min_credit_score=None,
        max_dti_percent=None,
        rule_text="When an advisory ML model predicts a Default Probability >= 50% or classifies an applicant into 'High' risk band, the application must be escalated for senior underwriter review. Fast-track automated routing is forbidden.",
        guidance="The underwriter must document compensating factors (e.g. liquid asset reserves, high collateral coverage, stable employment) before overriding an elevated ML risk score."
    ),
    PolicyRule(
        clause_id="POL-COMP-009",
        title="Fair Lending & Human-in-the-Loop Governance",
        category="REGULATORY",
        applicable_purposes={"Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan", "Business Loan"},
        min_credit_score=None,
        max_dti_percent=None,
        rule_text="In compliance with banking regulations, all automated risk scores, ML classifications, and AI generative summaries are strictly advisory. No application may be autonomously approved or rejected by an automated system without affirmative human loan officer sign-off.",
        guidance="Adverse lending decisions must clearly specify objective underwriting grounds (e.g., inadequate disposable income, adverse bureau tradelines) in the institutional audit log."
    )
]
