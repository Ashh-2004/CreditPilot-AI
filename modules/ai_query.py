import streamlit as st
import pandas as pd
import re
import os
import requests
from dotenv import load_dotenv
from db import fetch_all

# Load environment variables from .env (override=True ensures live updates to .env are loaded without process restart)
load_dotenv(os.path.join(os.getcwd(), '.env'), override=True)

st.markdown("## 🤖 AI Query Assistant")
st.caption("Ask questions about the loan database in plain English and execute them safely.")
st.divider()

# ── API Key Setup ───────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")

# Prompt if API Key is not available
if not api_key:
    st.error("❌ Configuration Error: `GEMINI_API_KEY` not found in your `.env` file.")
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
if col_t1.button("High-risk loans disbursed this month", use_container_width=True):
    nl_prompt = "show me high-risk loans (outstanding balance > 0 and credit score < 600 or ml default probability >= 60%) disbursed this year"
    st.rerun()
if col_t2.button("Total disbursed amount by purpose", use_container_width=True):
    nl_prompt = "calculate the total disbursed loan amount for each loan purpose where application status is approved"
    st.rerun()
if col_t3.button("Borrowers with multiple active loans", use_container_width=True):
    nl_prompt = "list borrowers who have 2 or more existing loans"
    st.rerun()

submitted = st.button("🚀 Translate to SQL & Run", use_container_width=True)

# ── Security Checking Logic ─────────────────────────────────
def is_query_safe(sql: str) -> tuple[bool, str]:
    """
    Validates that the query is read-only (SELECT) and contains no destructive DML/DDL commands.
    """
    clean_sql = sql.strip().lower()
    
    # Remove comments
    clean_sql = re.sub(r'--.*$', '', clean_sql, flags=re.MULTILINE)
    clean_sql = re.sub(r'/\*.*?\*/', '', clean_sql, flags=re.DOTALL)
    clean_sql = clean_sql.strip()
    
    # Must start with SELECT
    if not clean_sql.startswith("select"):
        return False, "Query must start with SELECT (Read-only)."
        
    # Forbidden SQL commands/keywords
    forbidden_patterns = [
        r"\binsert\b", r"\bupdate\b", r"\bdelete\b", r"\bdrop\b", 
        r"\btruncate\b", r"\balter\b", r"\bcreate\b", r"\breplace\b", 
        r"\bgrant\b", r"\brevoke\b", r"\brename\b", r"\bschema\b"
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, clean_sql):
            return False, f"Destructive command or keyword detected: '{pattern.strip(r' \b')}' is forbidden."
            
    return True, ""

# ── Execution Logic ─────────────────────────────────────────
if submitted:
    if not nl_prompt.strip():
        st.warning("Please type a question first.")
        st.stop()
        
    with st.spinner("Translating question into secure SQL..."):
        # Construct prompt with database schema context
        schema_context = """
You are a expert SQL translator for a MySQL database named 'loaniq_db'.
Your task is to translate a user's natural language question into a single, valid, read-only SELECT SQL query.

Here is the exact database schema:

1. Table: users
   - user_id INT (Primary Key)
   - username VARCHAR(50)
   - role ENUM('admin', 'officer', 'viewer')

2. Table: borrowers
   - borrower_id INT (Primary Key)
   - full_name VARCHAR(100)
   - email VARCHAR(100)
   - phone VARCHAR(15)
   - credit_score INT (range 300-900)
   - annual_income DECIMAL(12,2)
   - employment_type ENUM('Salaried', 'Self-Employed', 'Business', 'Government')
   - property_area ENUM('Urban', 'Semi-Urban', 'Rural')
   - existing_loans INT
   - date_of_birth DATE

3. Table: loan_applications
   - application_id INT (Primary Key)
   - borrower_id INT (Foreign Key -> borrowers)
   - reviewed_by INT (Foreign Key -> users)
   - loan_amount DECIMAL(12,2)
   - loan_purpose ENUM('Home Loan', 'Personal Loan', 'Education Loan', 'Vehicle Loan', 'Business Loan')
   - interest_rate DECIMAL(5,2)
   - tenure_months INT
   - status ENUM('pending', 'approved', 'rejected', 'review')
   - approval_probability DECIMAL(5,2) -- Traditional rule-based approval probability score (0-100)
   - ml_default_probability DECIMAL(5,2) -- ML-predicted default probability score (0-100)
   - ml_risk_band ENUM('Low', 'Medium', 'High') -- ML-predicted risk band
   - applied_at TIMESTAMP

4. Table: loans
   - loan_id INT (Primary Key)
   - application_id INT (Foreign Key -> loan_applications)
   - outstanding_balance DECIMAL(12,2)
   - disbursement_date DATE
   - last_payment_date DATE
   - loan_status ENUM('active', 'closed', 'defaulted', 'npa')
   - processing_fee DECIMAL(10,2)

5. Table: payments
   - payment_id INT (Primary Key)
   - loan_id INT (Foreign Key -> loans)
   - amount_paid DECIMAL(12,2)
   - principal_component DECIMAL(12,2)
   - interest_component DECIMAL(12,2)
   - payment_date DATE
   - payment_mode ENUM('NEFT', 'UPI', 'Cash', 'Cheque')

6. Table: emi_schedule
   - emi_id INT (Primary Key)
   - loan_id INT (Foreign Key -> loans)
   - month_number INT
   - opening_balance DECIMAL(12,2)
   - emi_amount DECIMAL(12,2)
   - principal DECIMAL(12,2)
   - interest DECIMAL(12,2)
   - closing_balance DECIMAL(12,2)
   - due_date DATE
   - is_paid BOOLEAN

7. Table: collateral
   - collateral_id INT (Primary Key)
   - borrower_id INT (Foreign Key -> borrowers)
   - loan_id INT (Foreign Key -> loans)
   - collateral_type ENUM('Property', 'Vehicle', 'FD', 'Gold', 'Other')
   - estimated_value DECIMAL(12,2)
   - description VARCHAR(255)

Rules for output:
1. Return ONLY the raw SQL query.
2. Do NOT wrap it in markdown code blocks like ```sql ... ``` or ```. 
3. Do NOT add any introductory or concluding text, explanations, or comments. Just return the SQL string.
4. Ensure the query is read-only (SELECT statements only).
5. For date operations, use MySQL-compatible functions. For example, use YEAR(CURDATE()) or CURDATE() to represent current date/time.
6. Join tables correctly using explicit JOIN clauses on Foreign Keys.
"""
        
        prompt = f"{schema_context}\n\nUser Question: {nl_prompt}\nSQL Query:"
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            res_json = response.json()
            generated_sql = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Strip markdown block quotes if the LLM outputted them anyway
            generated_sql = re.sub(r'^```sql\s*', '', generated_sql, flags=re.IGNORECASE)
            generated_sql = re.sub(r'^```\s*', '', generated_sql, flags=re.IGNORECASE)
            generated_sql = re.sub(r'\s*```$', '', generated_sql)
            generated_sql = generated_sql.strip()
            
        except Exception as e:
            st.error(f"Error calling Gemini REST API: {e}")
            st.stop()
            
    # ── Display Generated Query ──────────────────────────────
    st.markdown("#### ⚙️ Generated SQL Query")
    st.code(generated_sql, language="sql")
    
    # ── Security Check ───────────────────────────────────────
    is_safe, error_msg = is_query_safe(generated_sql)
    if not is_safe:
        st.error(f"❌ Security Block: {error_msg}")
        st.stop()
        
    st.success("✅ Query validation passed. Running query against loaniq_db...")
    
    # ── Execute Query ────────────────────────────────────────
    try:
        results = fetch_all(generated_sql)
        if results:
            df = pd.DataFrame(results)
            st.markdown(f"**Results ({len(df)} records found):**")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Query executed successfully, but returned 0 rows.")
    except Exception as e:
        st.error(f"Database Execution Error: {e}")
