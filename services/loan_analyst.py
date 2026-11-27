"""
AI Loan Analyst Service for LoanSense AI.
Provides grounded, advisory underwriting memorandums using Google Gemini with RAG policy grounding.
Adheres strictly to human-in-the-loop governance: GenAI responses are advisory only and never autonomously approve or reject loans.
"""

import os
import re
import requests
from typing import Dict, Any, Optional

import config
from rag.retriever import PolicyRetriever
from rag.context_builder import build_underwriting_context


ADVISORY_DISCLAIMER: str = (
    "⚠️ ADVISORY NOTICE: In accordance with institutional policy and banking governance regulations, "
    "this AI Underwriting Assessment is strictly advisory. Machine learning predictions and generative AI "
    "evaluations cannot autonomously approve or reject credit applications. The final lending decision "
    "and underwriting authorization rests exclusively with a designated human loan officer."
)


def _generate_deterministic_memo(
    applicant_data: Dict[str, Any],
    retrieved_rules: list,
    dti: float
) -> Dict[str, Any]:
    """
    Fallback deterministic advisory memo generator used when GEMINI_API_KEY is not configured
    or when external API network calls are unreachable.
    """
    name = applicant_data.get("name", "Applicant")
    score = int(applicant_data.get("credit_score") or 650)
    purpose = applicant_data.get("loan_purpose", "Personal Loan")
    ml_prob_val = applicant_data.get("ml_default_probability")
    ml_prob = float(ml_prob_val) if ml_prob_val is not None else 18.5
    ml_band_val = applicant_data.get("ml_risk_band")
    ml_band = str(ml_band_val) if ml_band_val else ("Low" if ml_prob < 30 else "Medium" if ml_prob < 60 else "High")
    rule_score_val = applicant_data.get("approval_probability")
    rule_score = float(rule_score_val) if rule_score_val is not None else 50.0

    # Determine eligibility flags
    strengths = []
    flags = []
    conditions = []

    if score >= 750:
        strengths.append(f"Strong bureau credit profile with score of {score}.")
    elif score >= 680:
        strengths.append(f"Acceptable prime credit score of {score}.")
    else:
        flags.append(f"Subprime credit score of {score} below standard benchmark (680).")
        conditions.append("Require a creditworthy co-applicant or guarantor.")

    if dti <= 35.0:
        strengths.append(f"Conservative Debt-to-Income ratio of {dti:.1f}% well within the 50% policy threshold.")
    elif dti <= 50.0:
        strengths.append(f"Debt-to-Income ratio of {dti:.1f}% complies with the 50% policy limit.")
    else:
        flags.append(f"Elevated Debt-to-Income ratio of {dti:.1f}% exceeds institutional 50% limit.")
        conditions.append("Reduce requested loan principal or extend tenure to reduce monthly debt burden below 50%.")

    if ml_band == "High" or ml_prob >= 50.0:
        flags.append(f"ML predictive model flags high default likelihood ({ml_prob:.1f}%).")
        conditions.append("Mandatory senior underwriter review required per policy POL-RISK-008.")
    elif ml_band == "Medium":
        flags.append(f"Moderate default probability ({ml_prob:.1f}%) identified by ML risk classifier.")
        conditions.append("Verify 6 months of bank account statements and secondary income documentation.")
    else:
        strengths.append(f"ML predictive classifier indicates low default probability ({ml_prob:.1f}%).")

    conditions.append("Verify KYC documents, current employment, and residential address.")

    memo_text = f"""### 📋 Executive Underwriting Memorandum (Advisory)

**Applicant:** {name} | **Facility:** {purpose} | **DTI Ratio:** {dti:.1f}%

#### 1. Executive Summary
The loan application for **{name}** has been evaluated against institutional credit policies and analytical risk models.
- **Rule-Based Approval Score:** {rule_score:.1f}% / 100
- **ML Default Risk Classification:** {ml_band} ({ml_prob:.1f}%)

#### 2. Key Compensating Strengths
""" + "\n".join([f"- ✅ {s}" for s in (strengths or ["No standout prime compensating factors identified."])]) + f"""

#### 3. Key Risk Factors & Vulnerabilities
""" + "\n".join([f"- ⚠️ {f}" for f in (flags or ["No critical risk violations detected."])]) + f"""

#### 4. Grounded Policy Compliance Summary
- **Primary Governing Clauses:** {', '.join([r.clause_id for r in retrieved_rules[:3]])}
- **Mandatory Requirements:**
""" + "\n".join([f"- 📌 [{r.clause_id}] {r.title}: {r.rule_text[:120]}..." for r in retrieved_rules[:3]]) + f"""

#### 5. Recommended Underwriting Conditions for Loan Officer
""" + "\n".join([f"1. {c}" for c in conditions]) + f"""

---
> {ADVISORY_DISCLAIMER}
"""

    return {
        "status": "success",
        "source": "deterministic_policy_engine",
        "memorandum": memo_text.strip(),
        "disclaimer": ADVISORY_DISCLAIMER,
        "dti_percent": round(dti, 1),
        "retrieved_clauses": [r.clause_id for r in retrieved_rules]
    }


def generate_advisory_underwriting_memo(
    applicant_data: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a grounded advisory underwriting memorandum for a loan application.
    Leverages RAG to retrieve institutional credit policy rules and passes the grounded context
    to Google Gemini.
    """
    key = api_key or config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    # Calculate DTI
    income = float(applicant_data.get("annual_income", 0))
    loan_amount = float(applicant_data.get("loan_amount", 0))
    tenure = int(applicant_data.get("tenure_months", 12))
    interest_rate = float(applicant_data.get("interest_rate", 10.0))
    monthly_income = max(1.0, income / 12.0)
    r = (interest_rate / 1200.0)
    if r > 0 and tenure > 0:
        emi = loan_amount * r * ((1 + r) ** tenure) / (((1 + r) ** tenure) - 1)
    else:
        emi = loan_amount / max(1, tenure)
    dti = (emi / monthly_income) * 100.0

    # 1. RAG Policy Retrieval
    retriever = PolicyRetriever()
    retrieved_rules = retriever.retrieve(
        loan_purpose=applicant_data.get("loan_purpose"),
        credit_score=applicant_data.get("credit_score"),
        dti_percent=dti,
        ml_prob=applicant_data.get("ml_default_probability"),
        top_k=4
    )

    # 2. Build Context
    context = build_underwriting_context(applicant_data, retrieved_rules)

    # 3. Fallback if API key missing
    if not key:
        return _generate_deterministic_memo(applicant_data, retrieved_rules, dti)

    # 4. Prompt Gemini with strict advisory instructions
    system_instruction = (
        "You are an AI Underwriting Assistant for LoanSense AI. "
        "Your task is to draft an objective, grounded Executive Underwriting Memorandum for a licensed human loan officer. "
        "IMPORTANT RULES:\n"
        "1. Your assessment is strictly ADVISORY. You must NEVER autonomously approve or reject the loan.\n"
        "2. Ground your analysis strictly in the provided applicant data and institutional credit policy clauses.\n"
        "3. Provide balanced analysis covering: Executive Summary, Key Compensating Strengths, Risk Flags, Policy Compliance, and Recommended Underwriting Conditions.\n"
        "4. Always conclude with the mandatory advisory disclaimer."
    )

    prompt = f"""{system_instruction}

{context}

Draft the Executive Underwriting Memorandum in clean GitHub-flavored Markdown. 
Conclude with the exact disclaimer:
"{ADVISORY_DISCLAIMER}"
"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        response.raise_for_status()
        res_json = response.json()
        memo_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()

        # Ensure disclaimer is present
        if "ADVISORY" not in memo_text:
            memo_text += f"\n\n---\n> {ADVISORY_DISCLAIMER}"

        return {
            "status": "success",
            "source": "gemini_api",
            "memorandum": memo_text,
            "disclaimer": ADVISORY_DISCLAIMER,
            "dti_percent": round(dti, 1),
            "retrieved_clauses": [r.clause_id for r in retrieved_rules]
        }
    except Exception as err:
        # Graceful fallback to deterministic memo on API error
        memo = _generate_deterministic_memo(applicant_data, retrieved_rules, dti)
        memo["fallback_reason"] = f"Gemini API unavailable: {err}"
        return memo
