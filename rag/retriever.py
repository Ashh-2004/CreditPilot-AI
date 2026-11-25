"""
Policy Retriever for RAG Credit Underwriting in LoanSense AI.
Indexes institutional underwriting policy rules and retrieves relevant clauses
based on applicant financial parameters, loan purpose, and risk scores.
"""

from typing import List, Dict, Any, Optional
from rag.policy_documents import POLICY_RULES, PolicyRule


class PolicyRetriever:
    """
    In-memory credit underwriting policy retriever.
    Performs deterministic and semantic-relevance matching of credit rules.
    """

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        self.rules = rules or POLICY_RULES

    def retrieve(
        self,
        loan_purpose: Optional[str] = None,
        credit_score: Optional[int] = None,
        dti_percent: Optional[float] = None,
        ml_prob: Optional[float] = None,
        query: Optional[str] = None,
        top_k: int = 4
    ) -> List[PolicyRule]:
        """
        Retrieves the most pertinent policy clauses for a given applicant profile or query.
        """
        scored_rules: List[tuple[float, PolicyRule]] = []

        query_terms = set(query.lower().split()) if query else set()

        for rule in self.rules:
            score = 0.0

            # 1. Purpose relevance
            if loan_purpose and (loan_purpose in rule.applicable_purposes or "ALL" in rule.applicable_purposes):
                score += 3.0

            # 2. Credit score threshold trigger
            if credit_score is not None:
                if credit_score < 600 and rule.clause_id in ("POL-ELIG-001", "POL-RISK-008"):
                    score += 5.0
                elif credit_score < 650 and rule.category == "ELIGIBILITY":
                    score += 3.0

            # 3. DTI threshold trigger
            if dti_percent is not None and dti_percent > 45.0 and rule.category == "DEBT_BURDEN":
                score += 4.0

            # 4. ML risk escalation trigger
            if ml_prob is not None and ml_prob >= 40.0 and rule.clause_id == "POL-RISK-008":
                score += 5.0

            # 5. Always include regulatory compliance clause baseline
            if rule.clause_id == "POL-COMP-009":
                score += 2.0

            # 6. Keyword overlap matching if query string provided
            if query_terms:
                rule_text_lower = f"{rule.title} {rule.rule_text} {rule.guidance}".lower()
                matches = sum(1 for term in query_terms if term in rule_text_lower)
                score += matches * 1.5

            scored_rules.append((score, rule))

        # Sort descending by score
        scored_rules.sort(key=lambda x: x[0], reverse=True)

        return [r for _, r in scored_rules[:top_k]]
