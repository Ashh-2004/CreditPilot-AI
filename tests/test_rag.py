"""
Tests for RAG Policy Knowledge Base and Context Builder.
"""

import pytest
from rag.policy_documents import POLICY_RULES, PolicyRule
from rag.retriever import PolicyRetriever
from rag.context_builder import build_underwriting_context


def test_policy_rules_loaded():
    assert len(POLICY_RULES) >= 8
    clause_ids = [r.clause_id for r in POLICY_RULES]
    assert "POL-ELIG-001" in clause_ids
    assert "POL-COMP-009" in clause_ids


def test_retriever_loan_purpose():
    retriever = PolicyRetriever()
    results = retriever.retrieve(loan_purpose="Home Loan", top_k=4)
    result_ids = [r.clause_id for r in results]
    assert "POL-PURP-003" in result_ids  # Home Loan policy


def test_retriever_subprime_score_trigger():
    retriever = PolicyRetriever()
    results = retriever.retrieve(credit_score=580, top_k=3)
    result_ids = [r.clause_id for r in results]
    assert "POL-ELIG-001" in result_ids


def test_retriever_high_ml_risk_trigger():
    retriever = PolicyRetriever()
    results = retriever.retrieve(ml_prob=65.0, top_k=3)
    result_ids = [r.clause_id for r in results]
    assert "POL-RISK-008" in result_ids


def test_context_builder_generates_valid_text():
    applicant = {
        "name": "Arun Kumar",
        "annual_income": 1200000,
        "credit_score": 740,
        "employment_type": "Salaried",
        "existing_loans": 1,
        "loan_amount": 2500000,
        "loan_purpose": "Home Loan",
        "tenure_months": 240,
        "interest_rate": 8.5,
        "approval_probability": 85.0,
        "ml_default_probability": 12.0,
        "ml_risk_band": "Low"
    }

    retriever = PolicyRetriever()
    rules = retriever.retrieve(loan_purpose="Home Loan", credit_score=740, top_k=3)

    context = build_underwriting_context(applicant, rules)
    assert "Arun Kumar" in context
    assert "Home Loan" in context
    assert "Estimated Debt-to-Income" in context
    assert "POL-PURP-003" in context or "POL-ELIG-001" in context
