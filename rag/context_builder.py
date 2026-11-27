"""
Context Builder for RAG Underwriting Prompts.
Formats applicant details, risk scores, ML predictions, and retrieved policy rules
into a structured, grounded context for Google Gemini.
"""

from typing import Dict, Any, List
from rag.policy_documents import PolicyRule
from rag.retriever import PolicyRetriever


def build_underwriting_context(
    applicant_data: Dict[str, Any],
    retrieved_rules: List[PolicyRule]
) -> str:
    """
    Constructs a grounded underwriting prompt context for the LLM.
    """
    name = applicant_data.get("name", "Applicant")
    income = applicant_data.get("annual_income", 0)
    score = applicant_data.get("credit_score", 0)
    employment = applicant_data.get("employment_type", "Salaried")
    existing_loans = applicant_data.get("existing_loans", 0)
    loan_amount = applicant_data.get("loan_amount", 0)
    purpose = applicant_data.get("loan_purpose", "Personal Loan")
    tenure = applicant_data.get("tenure_months", 12)
    interest_rate = applicant_data.get("interest_rate", 10.0)

    # Risk metrics with safe None fallbacks
    rule_score_val = applicant_data.get("approval_probability")
    rule_score = float(rule_score_val) if rule_score_val is not None else 50.0

    ml_prob_val = applicant_data.get("ml_default_probability")
    ml_prob = float(ml_prob_val) if ml_prob_val is not None else 18.5

    ml_band_val = applicant_data.get("ml_risk_band")
    ml_band = str(ml_band_val) if ml_band_val else ("Low" if ml_prob < 30 else "Moderate" if ml_prob < 60 else "High")

    # Estimated monthly EMI
    monthly_income = max(1.0, income / 12.0)
    # Approximate monthly EMI
    r = (interest_rate / 1200.0)
    if r > 0 and tenure > 0:
        emi = loan_amount * r * ((1 + r) ** tenure) / (((1 + r) ** tenure) - 1)
    else:
        emi = loan_amount / max(1, tenure)
    dti = (emi / monthly_income) * 100.0

    policy_section = "\n".join([
        f"- [{rule.clause_id}] {rule.title} ({rule.category}):\n"
        f"  Rule: {rule.rule_text}\n"
        f"  Underwriting Guidance: {rule.guidance}"
        for rule in retrieved_rules
    ])

    context = f"""
===================================================================
LOAN APPLICATION UNDERWRITING FILE
===================================================================

[1] APPLICANT FINANCIAL PROFILE:
- Full Name: {name}
- Employment Type: {employment}
- Stated Annual Income: ₹{income:,.2f} (Monthly: ₹{monthly_income:,.2f})
- Credit Bureau Score: {score} (Range: 300-900)
- Existing Active Loans: {existing_loans}

[2] PROPOSED CREDIT FACILITY:
- Loan Purpose: {purpose}
- Requested Loan Amount: ₹{loan_amount:,.2f}
- Proposed Interest Rate: {interest_rate:.2f}% p.a.
- Proposed Tenure: {tenure} months
- Estimated Monthly EMI: ₹{emi:,.2f}
- Estimated Debt-to-Income (DTI / FOIR): {dti:.1f}%

[3] ANALYTICAL RISK METRICS:
- Traditional Rule-Based Approval Score: {rule_score:.1f}% / 100
- ML Classifier Default Probability: {ml_prob:.1f}%
- ML Risk Tier: {ml_band}

[4] RELEVANT INSTITUTIONAL CREDIT POLICY CLAUSES (RAG Grounding):
{policy_section}
===================================================================
"""
    return context.strip()
