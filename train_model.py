import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Try importing XGBoost, if not installed yet we can print an error (it will be installed by the pip command)
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

# Standard EMI Calculator matching calculations.py
def calc_emi(principal, annual_rate, tenure_months):
    r = annual_rate / 100 / 12
    n = tenure_months
    if r == 0:
        return round(principal / n, 2)
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return round(emi, 2)

def generate_synthetic_dataset(num_samples=10000, random_seed=42):
    """
    Generates a realistic synthetic loan default dataset mapping to LoanIQ features.
    Saves it to data/loan_dataset.csv.
    """
    np.random.seed(random_seed)
    
    print(f"Generating {num_samples} simulated loan records...")
    
    # 1. Generate applicant and loan features
    cs_choices = np.random.choice([0, 1, 2], size=num_samples, p=[0.15, 0.35, 0.50])
    credit_scores = np.array([
        np.random.randint(300, 599) if c == 0 else
        np.random.randint(600, 699) if c == 1 else
        np.random.randint(700, 900)
        for c in cs_choices
    ])
    
    # Generate random arrays for annual income
    inc_choices = np.random.choice([0, 1, 2], size=num_samples, p=[0.30, 0.50, 0.20])
    annual_incomes = np.array([
        np.random.randint(250000, 500000) if c == 0 else
        np.random.randint(500001, 1200000) if c == 1 else
        np.random.randint(1200001, 3500000)
        for c in inc_choices
    ])
    
    employment_types = np.random.choice(
        ['Salaried', 'Self-Employed', 'Business', 'Government'],
        size=num_samples,
        p=[0.4, 0.25, 0.2, 0.15]
    )
    
    existing_loans = np.random.choice(
        [0, 1, 2, 3],
        size=num_samples,
        p=[0.5, 0.3, 0.15, 0.05]
    )
    
    loan_purposes = np.random.choice(
        ['Home Loan', 'Personal Loan', 'Education Loan', 'Vehicle Loan', 'Business Loan'],
        size=num_samples,
        p=[0.3, 0.25, 0.15, 0.15, 0.15]
    )
    
    # Loan amount depends on purpose ranges
    loan_amounts = []
    interest_rates = []
    tenures = []
    
    loan_configs = {
        'Home Loan': {'amt_range': (1500000, 7500000), 'rate_range': (8.0, 10.5), 'tenure_range': (120, 240)},
        'Business Loan': {'amt_range': (500000, 3000000), 'rate_range': (11.0, 15.5), 'tenure_range': (12, 60)},
        'Vehicle Loan': {'amt_range': (300000, 1500000), 'rate_range': (9.0, 12.0), 'tenure_range': (36, 84)},
        'Education Loan': {'amt_range': (200000, 1200000), 'rate_range': (8.5, 11.5), 'tenure_range': (36, 120)},
        'Personal Loan': {'amt_range': (50000, 500000), 'rate_range': (12.0, 18.0), 'tenure_range': (12, 48)}
    }
    
    for i in range(num_samples):
        cfg = loan_configs[loan_purposes[i]]
        amt = round(np.random.randint(*cfg['amt_range']), -4)
        rate = round(np.random.uniform(*cfg['rate_range']), 2)
        tenure = round(np.random.randint(*cfg['tenure_range']), -1)
        if tenure == 0:
            tenure = 12
        loan_amounts.append(amt)
        interest_rates.append(rate)
        tenures.append(tenure)
        
    loan_amounts = np.array(loan_amounts)
    interest_rates = np.array(interest_rates)
    tenures = np.array(tenures)
    
    ages = np.random.randint(22, 60, size=num_samples)
    
    # 2. Compute probabilities and generate default labels
    defaults = []
    true_probs = []
    
    for i in range(num_samples):
        # Base default prob
        prob = 0.25
        
        # Credit score factor
        cs = credit_scores[i]
        if cs < 550:
            prob += 0.35
        elif cs < 650:
            prob += 0.20
        elif cs >= 750:
            prob -= 0.15
            
        # EMI ratio factor
        emi = calc_emi(loan_amounts[i], interest_rates[i], tenures[i])
        monthly_inc = annual_incomes[i] / 12
        emi_ratio = emi / monthly_inc
        if emi_ratio >= 0.50:
            prob += 0.25
        elif emi_ratio >= 0.35:
            prob += 0.10
        elif emi_ratio < 0.20:
            prob -= 0.08
            
        # Existing loans
        ex = existing_loans[i]
        if ex >= 2:
            prob += 0.10
        elif ex == 0:
            prob -= 0.05
            
        # Employment
        emp = employment_types[i]
        if emp in ['Self-Employed', 'Business']:
            prob += 0.06
        elif emp == 'Government':
            prob -= 0.06
            
        # Age factor
        age = ages[i]
        if age < 28:
            prob += 0.05
        elif age > 48:
            prob -= 0.04
            
        # Bounding probability
        prob = np.clip(prob, 0.01, 0.99)
        true_probs.append(prob)
        
        # Target variable (defaulted or not)
        default_label = np.random.binomial(1, prob)
        defaults.append(default_label)
        
    df = pd.DataFrame({
        'credit_score': credit_scores,
        'annual_income': annual_incomes,
        'employment_type': employment_types,
        'existing_loans': existing_loans,
        'loan_amount': loan_amounts,
        'loan_purpose': loan_purposes,
        'interest_rate': interest_rates,
        'tenure_months': tenures,
        'age': ages,
        'default_probability': true_probs,
        'default': defaults
    })
    
    # Create data directory if not exists
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/loan_dataset.csv', index=False)
    print("Dataset saved to data/loan_dataset.csv")
    return df

def train_and_evaluate_models():
    # Load dataset
    if not os.path.exists('data/loan_dataset.csv'):
        df = generate_synthetic_dataset()
    else:
        df = pd.read_csv('data/loan_dataset.csv')
        
    # Prepare features and target
    X = df.drop(columns=['default_probability', 'default'])
    y = df['default']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define preprocessing pipelines
    numeric_features = ['credit_score', 'annual_income', 'existing_loans', 'loan_amount', 'interest_rate', 'tenure_months', 'age']
    categorical_features = ['employment_type', 'loan_purpose']
    
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # ── 1. Train Baseline: Logistic Regression ────────────────────
    print("Training Baseline Model: Logistic Regression...")
    lr_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(max_iter=1000, random_state=42))
    ])
    lr_pipeline.fit(X_train, y_train)
    
    # Evaluate Baseline
    y_pred_lr = lr_pipeline.predict(X_test)
    y_prob_lr = lr_pipeline.predict_proba(X_test)[:, 1]
    
    cm_lr = confusion_matrix(y_test, y_pred_lr)
    lr_metrics = {
        'accuracy': round(accuracy_score(y_test, y_pred_lr), 4),
        'precision': round(precision_score(y_test, y_pred_lr), 4),
        'recall': round(recall_score(y_test, y_pred_lr), 4),
        'f1': round(f1_score(y_test, y_pred_lr), 4),
        'confusion_matrix': cm_lr.tolist() # [[TN, FP], [FN, TP]]
    }
    
    # ── 2. Train Challenger: XGBoost ─────────────────────────────
    global XGB_AVAILABLE
    if XGB_AVAILABLE:
        print("Training Challenger Model: XGBoost Classifier...")
        xgb_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', XGBClassifier(
                n_estimators=100, 
                max_depth=5, 
                learning_rate=0.1, 
                random_state=42, 
                use_label_encoder=False,
                eval_metric='logloss'
            ))
        ])
        xgb_pipeline.fit(X_train, y_train)
        
        # Evaluate Challenger
        y_pred_xgb = xgb_pipeline.predict(X_test)
        y_prob_xgb = xgb_pipeline.predict_proba(X_test)[:, 1]
        
        cm_xgb = confusion_matrix(y_test, y_pred_xgb)
        xgb_metrics = {
            'accuracy': round(accuracy_score(y_test, y_pred_xgb), 4),
            'precision': round(precision_score(y_test, y_pred_xgb), 4),
            'recall': round(recall_score(y_test, y_pred_xgb), 4),
            'f1': round(f1_score(y_test, y_pred_xgb), 4),
            'confusion_matrix': cm_xgb.tolist()
        }
        
        # We will save the XGBoost pipeline as the primary model
        best_pipeline = xgb_pipeline
        print(f"XGBoost F1-score: {xgb_metrics['f1']:.4f} vs. Logistic Regression F1-score: {lr_metrics['f1']:.4f}")
    else:
        print("XGBoost is not installed or import failed. Using Logistic Regression as best pipeline.")
        best_pipeline = lr_pipeline
        xgb_metrics = lr_metrics.copy()
        xgb_metrics['f1'] = 0.0 # Placeholder indicating it wasn't run
        
    # Create models directory
    os.makedirs('models', exist_ok=True)
    
    # Save best pipeline
    joblib.dump(best_pipeline, 'models/xgboost_model.joblib')
    print("Primary model pipeline saved to models/xgboost_model.joblib")
    
    # Save metrics JSON
    metrics_payload = {
        'logistic_regression': lr_metrics,
        'xgboost': xgb_metrics,
        'best_model': 'xgboost' if XGB_AVAILABLE else 'logistic_regression'
    }
    
    with open('models/model_metrics.json', 'w') as f:
        json.dump(metrics_payload, f, indent=4)
    print("Evaluation metrics saved to models/model_metrics.json")
    
    print("\n--- MODEL TRAINING REPORT ---")
    print(f"Dataset Size: {len(df)} records (Train: {len(X_train)}, Test: {len(X_test)})")
    print(f"Logistic Regression: Accuracy={lr_metrics['accuracy']:.4f}, Precision={lr_metrics['precision']:.4f}, Recall={lr_metrics['recall']:.4f}, F1={lr_metrics['f1']:.4f}")
    if XGB_AVAILABLE:
        print(f"XGBoost Classifier:  Accuracy={xgb_metrics['accuracy']:.4f}, Precision={xgb_metrics['precision']:.4f}, Recall={xgb_metrics['recall']:.4f}, F1={xgb_metrics['f1']:.4f}")
    print("-----------------------------")

if __name__ == '__main__':
    train_and_evaluate_models()
