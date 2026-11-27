"""
Loan Application module for LoanSense AI.
Provides applicant intake, financial analysis, rule-based scoring, and advisory ML default prediction.
Ensures ML recommendations remain advisory and uses safe atomic inserts for database persistence.
"""

import streamlit as st
import pandas as pd
from db import fetch_all, execute, execute_insert
from calculations import calc_emi, calc_risk_score
from modules.ml_model import predict_loan_default


def render():
    st.markdown("## 📋 Loan Application")
    st.caption("Submit and analyse a new loan application")
    st.divider()

    # ── Form ────────────────────────────────────────────────────
    with st.form("loan_form"):
        st.markdown("#### Applicant Profile")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            loan_amount = st.number_input("Loan Amount (₹)", min_value=10000, max_value=10000000, value=500000, step=10000)
            annual_income = st.number_input("Annual Income (₹)", min_value=100000, max_value=10000000, value=800000, step=10000)
            employment = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business", "Government"])

        with col2:
            purpose = st.selectbox("Loan Purpose", ["Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan", "Business Loan"])
            existing = st.selectbox("Existing Loans", [0, 1, 2, 3])
            property_area = st.selectbox("Property Area", ["Urban", "Semi-Urban", "Rural"])
            email = st.text_input("Email (optional)")

        st.markdown("#### Loan Parameters")
        col3, col4 = st.columns(2)
        with col3:
            credit_score = st.slider("Credit Score", 300, 900, 720)
            tenure = st.slider("Tenure (months)", 6, 240, 36, step=6)
        with col4:
            interest_rate = st.slider("Interest Rate (%)", 6.0, 24.0, 10.5, step=0.5)
            age = st.slider("Applicant Age", 18, 70, 30)

        submitted = st.form_submit_button("🔍 Analyse Loan Application", use_container_width=True)

    # ── Analysis & Advisory Logic ───────────────────────────────
    if submitted:
        if not name:
            st.warning("Please enter applicant name.")
            st.stop()

        # Calculations
        emi = calc_emi(loan_amount, interest_rate, tenure)
        monthly_inc = round(annual_income / 12)
        emi_ratio = round((emi / monthly_inc) * 100, 1)
        risk_score = calc_risk_score(credit_score, emi_ratio, existing, employment)
        total_pay = emi * tenure
        total_int = total_pay - loan_amount

        # ML Model Prediction (Advisory)
        ml_prob, ml_band = predict_loan_default({
            'credit_score': credit_score,
            'annual_income': annual_income,
            'employment_type': employment,
            'existing_loans': existing,
            'loan_amount': loan_amount,
            'loan_purpose': purpose,
            'interest_rate': interest_rate,
            'tenure_months': tenure,
            'age': age
        })

        # All applications enter human review queue; ML never auto-approves or auto-rejects
        advisory_status = "review"

        # Save to session state so it survives reruns when clicking "Save to DB"
        st.session_state.app_result = {
            'name': name,
            'email': email,
            'credit_score': credit_score,
            'annual_income': annual_income,
            'employment': employment,
            'purpose': purpose,
            'existing': existing,
            'property_area': property_area,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'tenure': tenure,
            'age': age,
            'emi': emi,
            'monthly_inc': monthly_inc,
            'emi_ratio': emi_ratio,
            'risk_score': risk_score,
            'status': advisory_status,
            'advisory_status': advisory_status,
            'total_int': total_int,
            'ml_prob': ml_prob,
            'ml_band': ml_band
        }

    if "app_result" in st.session_state:
        res = st.session_state.app_result

        st.divider()
        st.markdown("#### 📊 Financial Analysis")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly EMI", f"₹{res['emi']:,.0f}")
        m2.metric("Monthly Income", f"₹{res['monthly_inc']:,.0f}")
        m3.metric("EMI / Income", f"{res['emi_ratio']}%")
        m4.metric("Total Interest", f"₹{res['total_int']:,.0f}")

        st.divider()
        st.markdown("### 🛡️ Credit Risk Decision Engines (Advisory Guidance)")

        # Clear advisory notice per governance guidelines
        if res['ml_band'] == "Low":
            st.success(f"💡 **ADVISORY RECOMMENDATION: RECOMMENDED FOR APPROVAL** (Low Risk, Default Prob: {res['ml_prob']}%)")
            st.caption("ℹ️ ML assessment is advisory. Final approval or rejection requires authorized officer confirmation.")
        elif res['ml_band'] == "Medium":
            st.warning(f"⚠️ **ADVISORY RECOMMENDATION: REFER FOR OFFICER REVIEW** (Medium Risk, Default Prob: {res['ml_prob']}%)")
            st.caption("ℹ️ Moderate risk detected. Recommended for manual underwriter review.")
        else:
            st.error(f"🛑 **ADVISORY RECOMMENDATION: HIGH RISK WARNING** (High Risk, Default Prob: {res['ml_prob']}%)")
            st.caption("ℹ️ High likelihood of default flagged by ML model. Final action rests with lending authority.")

        st.divider()
        col_rule, col_ml = st.columns(2)

        with col_rule:
            st.markdown("##### ⚙️ Traditional Rule-Based Engine (Educational View)")
            st.markdown(f"**Weighted Approval Score: {res['risk_score']}%**")
            st.progress(res['risk_score'] / 100)

            if res['risk_score'] >= 70:
                st.success(f"Rule Score: ✅ High Quality (Score: {res['risk_score']}%)")
            elif res['risk_score'] >= 45:
                st.warning(f"Rule Score: ⚠️ Moderate Quality (Score: {res['risk_score']}%)")
            else:
                st.error(f"Rule Score: ❌ Elevated Risk (Score: {res['risk_score']}%)")

        with col_ml:
            st.markdown("##### 🤖 Machine Learning Classifier (Advisory Model)")
            st.markdown(f"**Predicted Default Probability: {res['ml_prob']}%**")
            st.progress(res['ml_prob'] / 100)

            if res['ml_band'] == "Low":
                st.success(f"ML Risk Band: 🟢 {res['ml_band']} Risk")
                st.info("Predicts low likelihood of delinquency. Recommended for automated fast-track approval.")
            elif res['ml_band'] == "Medium":
                st.warning(f"ML Risk Band: 🟡 {res['ml_band']} Risk")
                st.info("Detects moderate default factors. Escalation recommended.")
            else:
                st.error(f"ML Risk Band: 🔴 {res['ml_band']} Risk")
                st.info("Flags significant default risk indicators. Rejection or collateral review advised.")

        # ── AI Underwriting Analyst (Advisory Grounding) ─────────
        with st.expander("🤖 Generate Advisory AI Underwriting Memorandum", expanded=False):
            st.caption("Grounds applicant attributes against institutional credit policy clauses via RAG.")
            if st.button("Generate Memorandum Now", key="btn_generate_app_memo"):
                from services.loan_analyst import generate_advisory_underwriting_memo
                with st.spinner("Generating policy-grounded underwriting memorandum..."):
                    memo_res = generate_advisory_underwriting_memo({
                        "name": res['name'],
                        "credit_score": res['credit_score'],
                        "annual_income": res['annual_income'],
                        "employment_type": res['employment'],
                        "existing_loans": res['existing'],
                        "loan_amount": res['loan_amount'],
                        "loan_purpose": res['purpose'],
                        "tenure_months": res['tenure'],
                        "interest_rate": res['interest_rate'],
                        "approval_probability": res['risk_score'],
                        "ml_default_probability": res['ml_prob'],
                        "ml_risk_band": res['ml_band']
                    })
                st.markdown(memo_res['memorandum'])

        # ── Save to DB with Officer Confirmation ─────────────────
        st.divider()
        if st.session_state.role in ["admin", "officer"]:
            st.markdown("##### ✍️ Loan Officer Decision & Persistence")
            decision_options = ["approved", "review", "rejected", "pending"]
            default_idx = decision_options.index(res.get('advisory_status', 'pending')) if res.get('advisory_status') in decision_options else 3

            officer_decision = st.selectbox(
                "Confirm Final Application Status (Officer Authorization):",
                decision_options,
                index=default_idx,
                format_func=lambda x: f"{x.upper()} (Advisory was: {res.get('advisory_status', '').upper()})" if x == res.get('advisory_status') else x.upper()
            )

            if st.button("💾 Save Application to Database", use_container_width=True):
                try:
                    # Safe atomic insert using execute_insert to avoid race conditions
                    borrower_id = execute_insert("""
                        INSERT INTO borrowers
                            (full_name, email, credit_score, annual_income,
                             employment_type, property_area, existing_loans)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (res['name'], res['email'], res['credit_score'], res['annual_income'],
                          res['employment'], res['property_area'], res['existing']))

                    # Insert application with both rule-based score and ML advisory probability
                    execute("""
                        INSERT INTO loan_applications
                            (borrower_id, reviewed_by, loan_amount, loan_purpose,
                             interest_rate, tenure_months, status, approval_probability,
                             ml_default_probability, ml_risk_band)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (borrower_id, None, res['loan_amount'], res['purpose'],
                          res['interest_rate'], res['tenure'], officer_decision, res['risk_score'],
                          res['ml_prob'], res['ml_band']))

                    st.success(f"Application saved successfully with status: {officer_decision.upper()}!")
                    del st.session_state.app_result
                    st.rerun()
                except Exception as e:
                    st.error(f"DB Error: {e}")
        else:
            st.caption("🔒 Viewer role cannot save or authorize applications.")


if __name__ == "__main__":
    render()
