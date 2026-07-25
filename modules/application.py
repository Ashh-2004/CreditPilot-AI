import streamlit as st
import pandas as pd
from db import fetch_all, execute
from calculations import calc_emi, calc_risk_score

st.markdown("## 📋 Loan Application")
st.caption("Submit and analyse a new loan application")
st.divider()

# ── Form ────────────────────────────────────────────────────
with st.form("loan_form"):
    st.markdown("#### Applicant Profile")
    col1, col2 = st.columns(2)
    with col1:
        name         = st.text_input("Full Name")
        loan_amount  = st.number_input("Loan Amount (₹)", min_value=10000, max_value=10000000, value=500000, step=10000)
        annual_income = st.number_input("Annual Income (₹)", min_value=100000, max_value=10000000, value=800000, step=10000)
        employment   = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business", "Government"])

    with col2:
        purpose      = st.selectbox("Loan Purpose", ["Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan", "Business Loan"])
        existing     = st.selectbox("Existing Loans", [0, 1, 2, 3])
        property_area = st.selectbox("Property Area", ["Urban", "Semi-Urban", "Rural"])
        email        = st.text_input("Email (optional)")

    st.markdown("#### Loan Parameters")
    col3, col4 = st.columns(2)
    with col3:
        credit_score = st.slider("Credit Score", 300, 900, 720)
        tenure       = st.slider("Tenure (months)", 6, 240, 36, step=6)
    with col4:
        interest_rate = st.slider("Interest Rate (%)", 6.0, 24.0, 10.5, step=0.5)
        age           = st.slider("Applicant Age", 18, 70, 30)

    submitted = st.form_submit_button("🔍 Analyse Loan Application", use_container_width=True)

# ── Analysis & Save Logic ───────────────────────────────────
if submitted:
    if not name:
        st.warning("Please enter applicant name.")
        st.stop()

    # Calculations
    emi          = calc_emi(loan_amount, interest_rate, tenure)
    monthly_inc  = round(annual_income / 12)
    emi_ratio    = round((emi / monthly_inc) * 100, 1)
    risk_score   = calc_risk_score(credit_score, emi_ratio, existing, employment)
    total_pay    = emi * tenure
    total_int    = total_pay - loan_amount

    # ML Model Prediction
    from modules.ml_model import predict_loan_default
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

    # Determine status using Machine Learning (not rule-based)
    if ml_band == "Low":
        status = "approved"
    elif ml_band == "Medium":
        status = "review"
    else:
        status = "rejected"

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
        'status': status,
        'total_int': total_int,
        'ml_prob': ml_prob,
        'ml_band': ml_band
    }

if "app_result" in st.session_state:
    res = st.session_state.app_result
    
    st.divider()
    st.markdown("#### 📊 Financial Analysis")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monthly EMI",     f"₹{res['emi']:,.0f}")
    m2.metric("Monthly Income",  f"₹{res['monthly_inc']:,.0f}")
    m3.metric("EMI / Income",    f"{res['emi_ratio']}%")
    m4.metric("Total Interest",  f"₹{res['total_int']:,.0f}")

    st.divider()
    st.markdown("### 🛡️ Credit Risk Decision Engines")
    
    # Clearly highlight that the overall application status is now determined by ML
    if res['status'] == "approved":
        st.success(f"🎉 **OVERALL DECISION: AUTO-APPROVED** — Determined strictly by XGBoost Machine Learning Model ({res['ml_band']} Risk)")
    elif res['status'] == "review":
        st.warning(f"⚠️ **OVERALL DECISION: DEFERRED FOR SENIOR OFFICER REVIEW** — Determined strictly by XGBoost Machine Learning Model ({res['ml_band']} Risk)")
    else:
        st.error(f"❌ **OVERALL DECISION: AUTO-REJECTED** — Determined strictly by XGBoost Machine Learning Model ({res['ml_band']} Risk)")

    st.divider()
    col_rule, col_ml = st.columns(2)
    
    with col_rule:
        st.markdown("##### ⚙️ Traditional Rule-Based Engine (Educational View)")
        st.markdown(f"**Weighted Approval Probability: {res['risk_score']}%**")
        st.progress(res['risk_score'] / 100)
        
        if res['risk_score'] >= 70:
            st.success(f"Rule Suggestion: ✅ Approved (Score: {res['risk_score']}%)")
        elif res['risk_score'] >= 45:
            st.warning(f"Rule Suggestion: ⚠️ Manual Review (Score: {res['risk_score']}%)")
        else:
            st.error(f"Rule Suggestion: ❌ Rejected (Score: {res['risk_score']}%)")
            
    with col_ml:
        st.markdown("##### 🤖 Machine Learning Classifier (Active Decision Maker)")
        st.markdown(f"**Model Default Probability: {res['ml_prob']}%**")
        st.progress(res['ml_prob'] / 100)
        
        if res['ml_band'] == "Low":
            st.success(f"ML Decision: 🟢 Auto-Approve (Band: {res['ml_band']})")
            st.info("XGBoost predicts a low likelihood of default. Loan is auto-approved.")
        elif res['ml_band'] == "Medium":
            st.warning(f"ML Decision: 🟡 Refer for Review (Band: {res['ml_band']})")
            st.info("XGBoost detects moderate default probability. Escalating for manual review.")
        else:
            st.error(f"ML Decision: 🔴 Auto-Reject (Band: {res['ml_band']})")
            st.info("XGBoost flags high likelihood of default. Application is auto-rejected.")

    # ── Save to DB ───────────────────────────────────────────
    st.divider()
    if st.session_state.role in ["admin", "officer"]:
        if st.button("💾 Save Application to Database", use_container_width=True):
            try:
                # Insert borrower
                execute("""
                    INSERT INTO borrowers
                        (full_name, email, credit_score, annual_income,
                         employment_type, property_area, existing_loans)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (res['name'], res['email'], res['credit_score'], res['annual_income'],
                      res['employment'], res['property_area'], res['existing']))

                # Get borrower_id
                rows = fetch_all(
                    "SELECT borrower_id FROM borrowers WHERE full_name=%s ORDER BY borrower_id DESC LIMIT 1",
                    (res['name'],)
                )
                borrower_id = rows[0]["borrower_id"]

                # Insert application with rules-based score AND ML probability/band
                execute("""
                    INSERT INTO loan_applications
                        (borrower_id, reviewed_by, loan_amount, loan_purpose,
                         interest_rate, tenure_months, status, approval_probability,
                         ml_default_probability, ml_risk_band)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (borrower_id, None, res['loan_amount'], res['purpose'],
                      res['interest_rate'], res['tenure'], res['status'], res['risk_score'],
                      res['ml_prob'], res['ml_band']))

                st.success("Application saved successfully!")
                # Clear session state result after saving
                del st.session_state.app_result
                st.rerun()
            except Exception as e:
                st.error(f"DB Error: {e}")
    else:
        st.caption("🔒 Viewer role cannot save applications.")