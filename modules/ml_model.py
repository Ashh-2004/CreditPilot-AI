import os
import sys
import pandas as pd
import joblib

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'xgboost_model.joblib')

def predict_loan_default(loan_data: dict) -> tuple[float, str]:
    """
    Takes borrower and application features and predicts default probability and risk band.
    
    Args:
        loan_data (dict): Dictionary with keys:
            - credit_score (int)
            - annual_income (float)
            - employment_type (str)
            - existing_loans (int)
            - loan_amount (float)
            - loan_purpose (str)
            - interest_rate (float)
            - tenure_months (int)
            - age (int)
            
    Returns:
        tuple (probability, risk_band):
            - probability: float (0.0 to 100.0)
            - risk_band: str ('Low', 'Medium', 'High')
    """
    # 1. Ensure the model exists, train it if missing
    if not os.path.exists(MODEL_PATH):
        print("Model file not found. Running training script...")
        import subprocess
        try:
            script_path = os.path.join(os.path.dirname(__file__), '..', 'train_model.py')
            subprocess.run([sys.executable, script_path], check=True)
        except Exception as e:
            print(f"Error auto-training model: {e}")
            # Fallback to rules-based proxy default probability if training fails
            return _fallback_prediction(loan_data)
            
    # 2. Load model
    try:
        pipeline = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"Error loading model: {e}")
        return _fallback_prediction(loan_data)
        
    # 3. Format input data as DataFrame matching training features
    df_input = pd.DataFrame([{
        'credit_score': int(loan_data['credit_score']),
        'annual_income': float(loan_data['annual_income']),
        'employment_type': str(loan_data['employment_type']),
        'existing_loans': int(loan_data['existing_loans']),
        'loan_amount': float(loan_data['loan_amount']),
        'loan_purpose': str(loan_data['loan_purpose']),
        'interest_rate': float(loan_data['interest_rate']),
        'tenure_months': int(loan_data['tenure_months']),
        'age': int(loan_data['age'])
    }])
    
    # 4. Predict probability
    try:
        # predict_proba returns [prob_non_default, prob_default]
        default_prob = pipeline.predict_proba(df_input)[0][1]
        default_prob_pct = round(float(default_prob) * 100, 2)
    except Exception as e:
        print(f"Prediction failed: {e}")
        return _fallback_prediction(loan_data)
        
    # 5. Determine risk band
    if default_prob_pct < 30.0:
        risk_band = 'Low'
    elif default_prob_pct < 60.0:
        risk_band = 'Medium'
    else:
        risk_band = 'High'
        
    return default_prob_pct, risk_band

def _fallback_prediction(loan_data: dict) -> tuple[float, str]:
    """Fallback proxy scoring logic if ML model is unavailable."""
    # Score 0 to 100 (where 100 is high approval probability, i.e. low risk)
    # We convert it to default probability: default_prob = 100 - approval_prob
    from calculations import calc_risk_score
    
    # Calculate EMI and EMI ratio
    from calculations import calc_emi
    emi = calc_emi(loan_data['loan_amount'], loan_data['interest_rate'], loan_data['tenure_months'])
    monthly_inc = loan_data['annual_income'] / 12
    emi_ratio = round((emi / monthly_inc) * 100, 1)
    
    approval_score = calc_risk_score(
        loan_data['credit_score'], 
        emi_ratio, 
        loan_data['existing_loans'], 
        loan_data['employment_type']
    )
    
    default_prob = max(0.0, min(100.0, 100.0 - approval_score))
    
    if default_prob < 30.0:
        risk_band = 'Low'
    elif default_prob < 60.0:
        risk_band = 'Medium'
    else:
        risk_band = 'High'
        
    return round(default_prob, 2), risk_band
