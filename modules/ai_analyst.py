"""
AI Loan Analyst module for LoanSense AI.
Provides grounded, advisory credit underwriting assessments powered by Google Gemini and RAG policy retrieval.
Underwriting assessments are strictly advisory to support human loan officers.
"""

import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

import config
from db import fetch_all
from services.loan_analyst import generate_advisory_underwriting_memo, ADVISORY_DISCLAIMER
from rag.retriever import PolicyRetriever

load_dotenv(override=True)


def render():
    st.markdown("## 🤖 AI Loan Analyst (RAG Underwriting Assistant)")
    st.caption("Generate institutional underwriting memorandums grounded in credit policy guidelines and analytical ML models.")
    st.divider()

    st.info(
        "ℹ️ **Human-in-the-Loop Policy**: AI underwriting assessments are strictly advisory. "
        "All approval, conditional, or rejection decisions require designated human loan officer authorization."
    )

    tab_db, tab_custom = st.tabs(["📁 Analyze Existing Application", "🧪 Underwriting Scenario Simulator"])

    # ── Tab 1: Analyze DB Application ───────────────────────────
    with tab_db:
        st.markdown("#### Select Application from Portfolio")
        try:
            apps = fetch_all("""
                SELECT
                    a.application_id,
                    b.full_name,
                    b.credit_score,
                    b.annual_income,
                    b.employment_type,
                    b.existing_loans,
                    a.loan_amount,
                    a.loan_purpose,
                    a.tenure_months,
                    a.interest_rate,
                    a.status,
                    a.approval_probability,
                    a.ml_default_probability,
                    a.ml_risk_band
                FROM loan_applications a
                JOIN borrowers b ON a.borrower_id = b.borrower_id
                ORDER BY a.application_id DESC
                LIMIT 50
            """)
        except Exception as e:
            st.warning(f"Unable to load applications from database: {e}")
            apps = []

        if not apps:
            st.info("No applications found in the database. You can test using the 'Underwriting Scenario Simulator' tab.")
        else:
            app_options = {
                f"App #{app['application_id']} - {app['full_name']} (₹{float(app['loan_amount']):,.0f} {app['loan_purpose']} | Status: {app['status'].upper()})": app
                for app in apps
            }
            selected_label = st.selectbox("Choose application to review:", list(app_options.keys()))
            selected_app = app_options[selected_label]

            # Display quick profile snapshot
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Credit Score", selected_app['credit_score'])
            col2.metric("Annual Income", f"₹{float(selected_app['annual_income']):,.0f}")
            col3.metric("Loan Amount", f"₹{float(selected_app['loan_amount']):,.0f}")
            col4.metric("ML Risk Band", selected_app['ml_risk_band'] or "N/A")

            if st.button("🔍 Generate AI Underwriting Memo", key="btn_analyst_db", use_container_width=True):
                with st.spinner("Retrieving governing credit policies & generating advisory memorandum..."):
                    applicant_payload = {
                        "name": selected_app['full_name'],
                        "credit_score": selected_app['credit_score'],
                        "annual_income": float(selected_app['annual_income']),
                        "employment_type": selected_app['employment_type'],
                        "existing_loans": selected_app['existing_loans'],
                        "loan_amount": float(selected_app['loan_amount']),
                        "loan_purpose": selected_app['loan_purpose'],
                        "tenure_months": selected_app['tenure_months'],
                        "interest_rate": float(selected_app['interest_rate']),
                        "approval_probability": float(selected_app['approval_probability'] or 50.0),
                        "ml_default_probability": float(selected_app['ml_default_probability'] or 20.0),
                        "ml_risk_band": selected_app['ml_risk_band'] or "Low"
                    }
                    memo_result = generate_advisory_underwriting_memo(applicant_payload)

                st.success(f"Memorandum generated via {memo_result['source']} (DTI: {memo_result['dti_percent']}%)")
                st.markdown(memo_result['memorandum'])

    # ── Tab 2: Custom Scenario Simulator ────────────────────────
    with tab_custom:
        st.markdown("#### Hypothetical Application Underwriting Review")
        c1, c2 = st.columns(2)
        with c1:
            sim_name = st.text_input("Applicant Name", "Priya Sharma")
            sim_score = st.slider("Credit Bureau Score", 300, 900, 675)
            sim_income = st.number_input("Annual Income (₹)", min_value=100000, max_value=20000000, value=950000, step=50000)
            sim_emp = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business", "Government"])
            sim_existing = st.number_input("Existing Active Loans", min_value=0, max_value=10, value=2)

        with c2:
            sim_purpose = st.selectbox("Loan Purpose", ["Home Loan", "Personal Loan", "Business Loan", "Vehicle Loan", "Education Loan"])
            sim_amount = st.number_input("Requested Loan Amount (₹)", min_value=50000, max_value=50000000, value=3500000, step=50000)
            sim_tenure = st.number_input("Tenure (Months)", min_value=6, max_value=360, value=240, step=6)
            sim_rate = st.number_input("Proposed Interest Rate (% p.a.)", min_value=5.0, max_value=30.0, value=8.5, step=0.25)
            sim_ml_prob = st.slider("Simulated ML Default Risk (%)", 1.0, 99.0, 22.0)

        # Retrievable policy preview
        retriever = PolicyRetriever()
        preview_rules = retriever.retrieve(
            loan_purpose=sim_purpose,
            credit_score=sim_score,
            ml_prob=sim_ml_prob,
            top_k=3
        )
        with st.expander("📌 Preview Governing Credit Policy Rules (RAG Context)"):
            for r in preview_rules:
                st.markdown(f"**[{r.clause_id}] {r.title}** ({r.category})")
                st.caption(f"{r.rule_text}")

        if st.button("🚀 Run Scenario Underwriting Analysis", key="btn_analyst_sim", use_container_width=True):
            with st.spinner("Analyzing profile against policy guidelines..."):
                sim_band = "High" if sim_ml_prob >= 50 else ("Medium" if sim_ml_prob >= 25 else "Low")
                applicant_payload = {
                    "name": sim_name,
                    "credit_score": sim_score,
                    "annual_income": float(sim_income),
                    "employment_type": sim_emp,
                    "existing_loans": sim_existing,
                    "loan_amount": float(sim_amount),
                    "loan_purpose": sim_purpose,
                    "tenure_months": int(sim_tenure),
                    "interest_rate": float(sim_rate),
                    "approval_probability": 70.0,
                    "ml_default_probability": float(sim_ml_prob),
                    "ml_risk_band": sim_band
                }
                memo_result = generate_advisory_underwriting_memo(applicant_payload)

            st.success(f"Assessment complete (Engine: {memo_result['source']} | DTI: {memo_result['dti_percent']}%)")
            st.markdown(memo_result['memorandum'])


if __name__ == "__main__":
    render()
