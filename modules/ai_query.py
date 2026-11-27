"""
AI Query Assistant module for LoanSense AI.
Provides natural language to SQL translation using Google Gemini,
hardened against injection via AST SQL parsing (sqlparse), table allowlisting,
read-only execution, query timeouts, and row limit clamping.
"""

import os
import re
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

import config
from db import fetch_all_read_only
from sql_guard import validate_and_sanitize_sql, ALLOWED_TABLES

# Ensure environment variables are loaded
load_dotenv(override=True)


def render():
    st.markdown("## 🤖 AI Query Assistant (Hardened)")
    st.caption("Ask questions about the loan database in plain English and execute read-only queries with AST security validation.")
    st.divider()

    # ── API Key Setup ───────────────────────────────────────────
    api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    if not api_key:
        st.error("❌ Configuration Error: `GEMINI_API_KEY` not found in your environment or `.env` file.")
        st.info("To use the AI Query Assistant, please add `GEMINI_API_KEY=your_key_here` to the `.env` file in your project root and restart the app.")
        st.stop()

    # ── Query Form ──────────────────────────────────────────────
    st.markdown("#### Ask a Question")
    nl_prompt = st.text_area(
        "Query input:",
        placeholder="e.g., Show me all borrowers with a credit score below 600, sorted by credit score descending.",
        height=80
    )

    # Suggested templates for quick testing
    st.caption("**Try these example queries:**")
    col_t1, col_t2, col_t3 = st.columns(3)
    if col_t1.button("High-risk active loans", use_container_width=True):
        nl_prompt = "show me active loans with outstanding balance > 0 where borrowers have credit score < 600"
    if col_t2.button("Total disbursed amount by purpose", use_container_width=True):
        nl_prompt = "calculate total disbursed loan amount for each loan purpose where status is approved"
    if col_t3.button("Borrowers with multiple active loans", use_container_width=True):
        nl_prompt = "list borrowers who have 2 or more existing loans"

    submitted = st.button("🚀 Translate to SQL & Run", use_container_width=True)

    # ── Execution Logic ─────────────────────────────────────────
    if submitted:
        if not nl_prompt.strip():
            st.warning("Please enter a question first.")
            st.stop()

        with st.spinner("Translating question into secure SQL with Google Gemini..."):
            schema_context = f"""
You are an expert SQL translator for a MySQL database named 'loaniq_db'.
Your task is to translate a user's natural language question into a single, valid, read-only SELECT SQL query.

Allowed Tables in loaniq_db:
1. Table: users (user_id INT, username VARCHAR(50), role ENUM('admin', 'officer', 'viewer'))
   * NOTE: DO NOT select password_hash or use SELECT * on users table.
2. Table: borrowers (borrower_id INT, full_name VARCHAR(100), email VARCHAR(100), phone VARCHAR(15), credit_score INT, annual_income DECIMAL(12,2), employment_type ENUM('Salaried', 'Self-Employed', 'Business', 'Government'), property_area ENUM('Urban', 'Semi-Urban', 'Rural'), existing_loans INT, date_of_birth DATE)
3. Table: loan_applications (application_id INT, borrower_id INT, reviewed_by INT, loan_amount DECIMAL(12,2), loan_purpose ENUM('Home Loan', 'Personal Loan', 'Education Loan', 'Vehicle Loan', 'Business Loan'), interest_rate DECIMAL(5,2), tenure_months INT, status ENUM('pending', 'approved', 'rejected', 'review'), approval_probability DECIMAL(5,2), ml_default_probability DECIMAL(5,2), ml_risk_band ENUM('Low', 'Medium', 'High'), applied_at TIMESTAMP)
4. Table: loans (loan_id INT, application_id INT, outstanding_balance DECIMAL(12,2), disbursement_date DATE, last_payment_date DATE, loan_status ENUM('active', 'closed', 'defaulted', 'npa'), processing_fee DECIMAL(10,2))
5. Table: payments (payment_id INT, loan_id INT, amount_paid DECIMAL(12,2), principal_component DECIMAL(12,2), interest_component DECIMAL(12,2), payment_date DATE, payment_mode ENUM('NEFT', 'UPI', 'Cash', 'Cheque'))
6. Table: emi_schedule (emi_id INT, loan_id INT, month_number INT, opening_balance DECIMAL(12,2), emi_amount DECIMAL(12,2), principal DECIMAL(12,2), interest DECIMAL(12,2), closing_balance DECIMAL(12,2), due_date DATE, is_paid BOOLEAN)
7. Table: collateral (collateral_id INT, borrower_id INT, loan_id INT, collateral_type ENUM('Property', 'Vehicle', 'FD', 'Gold', 'Other'), estimated_value DECIMAL(12,2), description VARCHAR(255))

STRICT SECURITY RULES:
1. Return ONLY raw SQL. Do not include markdown code blocks (```sql ... ```), explanations, or comments.
2. Read-only SELECT statements only. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE.
3. Only reference allowed tables: {', '.join(sorted(list(ALLOWED_TABLES)))}.
4. Never generate stacked/multiple queries separated by semicolons.
5. Use MySQL functions (e.g. CURDATE(), YEAR(CURDATE())).
6. Always include explicit JOIN clauses.
"""

            prompt = f"{schema_context}\n\nUser Question: {nl_prompt}\nSQL Query:"

            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
                response.raise_for_status()
                res_json = response.json()
                raw_sql = res_json['candidates'][0]['content']['parts'][0]['text'].strip()

                # Clean markdown code blocks if returned
                raw_sql = re.sub(r'^```sql\s*', '', raw_sql, flags=re.IGNORECASE)
                raw_sql = re.sub(r'^```\s*', '', raw_sql, flags=re.IGNORECASE)
                raw_sql = re.sub(r'\s*```$', '', raw_sql)
                raw_sql = raw_sql.strip()

            except Exception as e:
                st.error(f"Error communicating with Gemini API: {e}")
                st.stop()

        # ── AST Security & Policy Validation ─────────────────────
        st.markdown("#### ⚙️ Generated & Sanitized SQL Query")
        is_safe, sanitized_or_err, detail = validate_and_sanitize_sql(raw_sql)

        if not is_safe:
            st.error(f"❌ Security Block: {sanitized_or_err} ({detail})")
            st.code(raw_sql, language="sql")
            st.stop()

        st.code(sanitized_or_err, language="sql")
        st.caption("🛡️ Verified: Read-only SELECT, Table allowlist matched, Row limit enforced (max 100 rows).")

        # ── Execute Safe Read-Only Query ─────────────────────────
        try:
            results = fetch_all_read_only(sanitized_or_err, timeout_seconds=10, max_rows=100)
            if results:
                df = pd.DataFrame(results)
                st.markdown(f"**Results ({len(df)} records returned, query timeout=10s, max_rows=100):**")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Query executed successfully, but returned 0 rows.")
        except Exception as e:
            st.error(f"Database Execution Error: {e}")


if __name__ == "__main__":
    render()
