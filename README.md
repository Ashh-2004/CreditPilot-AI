# 🏦 CreditPilot AI — Institutional Lending & Risk Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19%20%2B%20TypeScript-61DAFB.svg)](https://react.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-blue.svg)](https://www.mysql.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CreditPilot AI** is an institutional **decision-support prototype** for bank lending intelligence, explainable credit risk modeling, portfolio monitoring, and policy-grounded AI underwriting.

> [!IMPORTANT]
> **Human-in-the-Loop Governance:** All machine learning risk scores, calibrated probabilities, and AI-generated underwriting memoranda in CreditPilot AI are strictly **advisory**. The system never autonomously approves or rejects loan applications; binding lending decisions require explicit human loan officer authorization.

---

## ✨ Key Capabilities

- 🔐 **Admin-Governed Role-Based Access Control (RBAC)**
  - `bcrypt`-hashed authentication with **Admin**, **Officer**, and **Viewer** roles.
  - Public self-registration is disabled; only authenticated **Administrators** can provision or remove user accounts via the **User Admin** console (`/api/admin/users`).

- 🤖 **Calibrated Credit Risk Modeling & SHAP Explainability**
  - **Home Credit Default Risk Pipeline (`home_credit/`)**: Trained on **18,750** records and evaluated on **6,250** held-out records from the official Home Credit Kaggle dataset (`142` features: `126` numeric, `16` categorical).
  - **Honest Held-Out Performance (`models/home_credit/evaluation_report.json`)**:
    - Gradient Boosting: **ROC-AUC `0.7407`**, PR-AUC `0.2355`, Brier Score `0.1710` (calibrated).
    - Logistic Regression baseline: **ROC-AUC `0.7305`**, PR-AUC `0.2235`, Brier Score `0.1974`.
  - Includes per-applicant SHAP feature attributions (`home_credit/explainability.py`).
  - *Note:* The legacy domestic Indian quick-score heuristic/synthetic baseline (`modules/ml_model.py`) is retained solely for rapid prototype simulation and should not be interpreted as real-world default accuracy.

- 📑 **RAG-Grounded AI Underwriting & Policy Assistant (`rag/`, `services/loan_analyst.py`)**
  - Retrieves institutional credit policy clauses (DTI caps, bureau score tiers, escalation rules) and synthesizes structured Executive Underwriting Memoranda via Google Gemini 2.5 Flash, with a deterministic policy-engine fallback when offline.

- 🛡️ **Hardened Natural Language to SQL Analytics (`sql_guard.py`)**
  - Translates plain-English portfolio questions into read-only MySQL `SELECT` queries.
  - Enforces `sqlparse` AST validation, table allowlisting, sensitive column blocking (e.g., `password_hash`), single-statement checks, `LIMIT` clamping, and read-only execution (`db.fetch_all_read_only`).

- 📊 **Live Portfolio, Delinquency Watchlist & Macro Stress Testing**
  - Derives KPIs, sector/purpose breakdowns, and delinquency watchlists directly from `loaniq_db` MySQL tables (`0` / empty-state shown when no records match, without fake fallback numbers).
  - Interactive EMI & Prepayment Amortization Simulator (`calculations.py`).

---

## 🛠️ Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Tailwind CSS, Vite |
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **Legacy Prototype UI** | Streamlit (`app.py`) |
| **Machine Learning** | Scikit-Learn (Gradient Boosting, Logistic Regression, Calibration), Joblib, SHAP |
| **Generative AI & RAG** | Google Gemini API, Custom Institutional Policy Retriever |
| **Database & Security** | MySQL (`mysql-connector-python` pooling), `sqlparse` AST guard, `bcrypt` |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** (for the React frontend)
- **MySQL Server** running locally

### 2. Clone the Repository

```bash
git clone https://github.com/Ashh-2004/CreditPilot-AI.git
cd CreditPilot-AI
```

### 3. Set Up a Virtual Environment

```bash
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate environment (Linux/macOS)
# source .venv/bin/activate
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials (never commit `.env`):

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=loaniq_db

GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Initialize & Seed Database
1. Run `Create tables.sql` in MySQL to create `loaniq_db` and all tables.
2. Seed the database with initial users and sample portfolio records:
   ```bash
   python sql/seed.py
   ```

### 6. Install Dependencies & Run
```bash
# Backend dependencies
pip install -r requirements.txt

# Start FastAPI backend (serves API + built frontend at http://127.0.0.1:8000)
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# (Optional) Run React dev server with hot reload at http://localhost:5173
npm --prefix frontend install
npm --prefix frontend run dev -- --port 5173
```

---

## 👥 Default Seeded Credentials (`sql/seed.py`)

Running `python sql/seed.py` creates the following accounts in `loaniq_db.users`:

| Role | Username | Default Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access + User Admin provisioning |
| **Officer** | `officer` | `off123` | Applications, EMI, AI Analyst, SQL Assistant, Portfolio, Risk |
| **Officer** | `officer2` | `off456` | Applications, EMI, AI Analyst, SQL Assistant, Portfolio, Risk |
| **Viewer** | `viewer` | `view123` | Read-only Overview, Portfolio, Risk Intelligence, SQL Assistant |

*(In development mode, `main.py` also accepts `admin / admin` and `officer / password` as convenience fallbacks when DB seeding hasn't been run yet.)*

---

## 🧪 Running Tests

```bash
pytest
npm --prefix frontend run build
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [Issues page](https://github.com/Ashh-2004/CreditPilot-AI/issues).
