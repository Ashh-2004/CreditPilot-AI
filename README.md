# 🏦 LoanSense AI — Bank Lending Intelligence System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-green.svg)](https://xgboost.readthedocs.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)](https://ai.google.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-blue.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**LoanSense AI** (formerly LoanIQ) is an enterprise-grade Bank Lending Intelligence and Automated Risk Assessment System built with **Streamlit**, **MySQL**, **XGBoost**, and **Google Gemini AI**. It streamlines loan processing, automates credit risk scoring, monitors portfolio metrics, and enables natural language analytics for banking personnel.

---

## ✨ Features

- 🔐 **Role-Based Access Control (RBAC)**
  - Authenticated login system with encrypted `bcrypt` passwords.
  - Distinct access levels: **Admin**, **Loan Officer**, and **Viewer**.

- 🤖 **ML-Powered Credit Scoring & Risk Prediction**
  - Instant default risk prediction for incoming loan applications using a trained **XGBoost Classifier**.
  - Risk categorization (Low, Medium, High Risk) with feature importance breakdown.

- 💬 **AI Query Assistant (Powered by Google Gemini)**
  - Natural Language to SQL analytics assistant.
  - Ask business questions (e.g., *"What is the average loan amount for self-employed borrowers?"*) and receive automated SQL queries and AI-summarized insights.

- 📊 **Executive Portfolio Dashboard**
  - Real-time monitoring of key banking metrics: Total Disbursements, Active Loans, Default Rates, and NPA (Non-Performing Assets).
  - Interactive Plotly visualizations for loan distributions by sector, employment status, and risk tier.

- 🧮 **Interactive EMI & Amortization Calculator**
  - Calculate loan EMIs, interest breakdowns, and view interactive repayment schedules.

- 📈 **Advanced Risk & NPA Analytics**
  - Debt-to-Income (DTI) distribution, credit score heatmap, and early warning indicator (EWI) tracking for high-risk accounts.

---

## 🛠️ Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend / UI** | Streamlit (Custom Dark Theme) |
| **Data Visualization** | Plotly Express & Plotly Graph Objects, Pandas |
| **Machine Learning** | XGBoost, Scikit-Learn, Joblib |
| **Generative AI** | Google Gemini API (`google-generativeai`) |
| **Database** | MySQL, `mysql-connector-python` |
| **Authentication & Security** | Bcrypt, Streamlit Authenticator |
| **Environment & Package Mgmt** | `python-dotenv`, `uv` / `pip` |

---

## 📁 Repository Structure

```
loaniq/
├── app.py                      # Main Streamlit application entry point & router
├── db.py                       # Database connection module (MySQL pool)
├── train_model.py              # ML model training pipeline (XGBoost)
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
├── Create tables.sql           # Database schema & tables initialization
│
├── modules/                    # Feature modules
│   ├── ai_query.py             # Natural language AI Assistant (Google Gemini)
│   ├── application.py          # Loan Application & Risk Assessment page
│   ├── emi_calculator.py       # Financial & EMI calculation utilities
│   ├── ml_model.py             # ML model loading & inference wrapper
│   ├── portfolio.py            # Portfolio metrics & analytics dashboard
│   └── risk_analysis.py        # Risk analytics & NPA management
│
├── sql/                        # Database scripts & mock data seeders
│   ├── seed.py                 # Mock data generator (Faker)
│   └── update_schema.py        # Schema migration helper
│
├── data/                       # Dataset storage
│   └── loan_dataset.csv        # Synthetic training data
│
└── models/                     # Trained ML artifacts
    ├── xgboost_model.joblib    # Exported XGBoost model artifact
    └── model_metrics.json      # Evaluation metrics (AUC-ROC, F1, Accuracy)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites

- **Python 3.10+**
- **MySQL Server** installed and running
- **Google Gemini API Key** ([Get your API key here](https://aistudio.google.com/))

### 2. Clone the Repository

```bash
git clone https://github.com/Ashh-2004/loansense-AI.git
cd loansense-AI
```

### 3. Set Up Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate environment (Linux/macOS)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database Credentials
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=loaniq

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Initialize & Seed Database

1. Execute `Create tables.sql` in your MySQL workbench or CLI to create the `loaniq` database and required tables.
2. Run the seed script to populate initial users and test data:

```bash
python sql/seed.py
```

### 6. Train the Machine Learning Model (Optional)

A pre-trained model is provided under `models/`. To retrain the model on updated datasets:

```bash
python train_model.py
```

### 7. Run the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 👥 Default Login Credentials

*Seed data creates default test accounts for testing:*

| Role | Username | Default Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access (Application, Portfolio, EMI, Risk, AI Query) |
| **Officer** | `officer1` | `officer123` | Application submission, EMI Calculator, AI Query |
| **Viewer** | `viewer1` | `viewer123` | Portfolio Dashboard, Risk Analysis |

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [Issues page](https://github.com/Ashh-2004/loansense-AI/issues).
