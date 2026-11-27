# app.py — CreditPilot AI Streamlit Application Entrypoint & Router

import streamlit as st
from auth import verify_credentials
from db import fetch_all
from modules import (
    application,
    portfolio,
    emi_calculator,
    risk_analysis,
    ai_query,
    ai_analyst,
    home_credit_analysis,
)

st.set_page_config(page_title="CreditPilot AI", layout="wide", page_icon="🏦")

# ── Dark theme CSS ──────────────────────────────────────────
st.markdown("""<style>
  .stApp { background-color: #0d1117; color: #e6e6e6; }
  header[data-testid="stHeader"] { background-color: #0d1117 !important; }
  section[data-testid="stSidebar"] { background-color: #0a0f14; }
  .stButton > button {
    background-color: #c9a227; color: #0a0f14;
    font-weight: 600; border: none; border-radius: 6px;
  }
  .stTextInput > div > input, .stSelectbox > div, .stTextArea > div > textarea {
    background-color: #111820; border: 1px solid #1e2a35; color: #e6e6e6;
  }
</style>""", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# ── Role → allowed pages ────────────────────────────────────
ROLE_PAGES = {
    "admin":   ["Application", "Portfolio", "EMI Calculator", "Risk Analysis", "AI Query Assistant", "AI Loan Analyst", "Home Credit Risk Analysis"],
    "officer": ["Application", "EMI Calculator", "AI Query Assistant", "AI Loan Analyst", "Home Credit Risk Analysis"],
    "viewer":  ["Portfolio", "Risk Analysis", "Home Credit Risk Analysis"],
}

# ── Page Dispatcher Map ─────────────────────────────────────
PAGE_ROUTERS = {
    "Application": application.render,
    "Portfolio": portfolio.render,
    "EMI Calculator": emi_calculator.render,
    "Risk Analysis": risk_analysis.render,
    "AI Query Assistant": ai_query.render,
    "AI Loan Analyst": ai_analyst.render,
    "Home Credit Risk Analysis": home_credit_analysis.render,
}

# ── Login page ──────────────────────────────────────────────
def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("## 🏦 Credit**Pilot AI**")
        st.markdown("##### Institutional Lending & Risk Intelligence")
        st.divider()

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role     = st.selectbox("Role", ["admin", "officer", "viewer"])

        if st.button("Sign In", use_container_width=True):
            is_valid, message, user = verify_credentials(username, password, expected_role=role)
            if is_valid and user:
                st.session_state.logged_in = True
                st.session_state.username  = user["username"]
                st.session_state.role      = user["role"]
                st.rerun()
            else:
                st.error(message or "Invalid credentials or role mismatch.")

# ── Sidebar (after login) ───────────────────────────────────
def show_sidebar():
    with st.sidebar:
        st.markdown("### Credit**Pilot AI**")
        st.caption("Institutional Lending Intelligence")
        st.divider()

        st.markdown(f"👤 **{st.session_state.username.capitalize()}**")
        st.caption(f"Role: {st.session_state.role.capitalize()}")
        st.divider()

        allowed = ROLE_PAGES.get(st.session_state.role, [])
        page = st.radio("Navigate", allowed)

        st.divider()
        st.caption("Live Portfolio Stats")
        try:
            stats = fetch_all("""
                SELECT
                    SUM(CASE WHEN loan_status = 'active' THEN 1 ELSE 0 END) AS active_loans,
                    COUNT(*) AS total_loans,
                    SUM(CASE WHEN loan_status IN ('npa', 'defaulted') THEN 1 ELSE 0 END) AS npa_loans
                FROM loans
            """)
            row = stats[0] if stats else {}
            active_loans = int(row.get("active_loans") or 0)
            total_loans = int(row.get("total_loans") or 0)
            npa_loans = int(row.get("npa_loans") or 0)
            npa_rate = f"{(npa_loans / total_loans * 100):.1f}%" if total_loans > 0 else "0.0%"
            st.metric("Active Loans", f"{active_loans:,}")
            st.metric("NPA / Default Rate", npa_rate)
        except Exception:
            st.metric("Active Loans", "N/A")
            st.metric("NPA / Default Rate", "N/A")

        if st.button("Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username  = None
            st.session_state.role      = None
            st.rerun()

    return page

# ── Main router ─────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login()
else:
    page = show_sidebar()
    render_func = PAGE_ROUTERS.get(page)
    if render_func:
        render_func()
    else:
        st.error(f"Page '{page}' is not available.")
