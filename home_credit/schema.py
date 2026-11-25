"""
Home Credit Default Risk canonical schema definitions.
Defines column lists, data types, target definitions, and table manifests for Home Credit data.
"""

from typing import List, Dict

# Target variable definition in Home Credit
TARGET_COLUMN = "TARGET"
ID_COLUMN = "SK_ID_CURR"

# Table manifests for Kaggle Home Credit dataset
REQUIRED_TABLES: List[str] = [
    "application_train.csv",
]

HISTORICAL_TABLES: List[str] = [
    "bureau.csv",
    "bureau_balance.csv",
    "previous_application.csv",
    "POS_CASH_balance.csv",
    "credit_card_balance.csv",
    "installments_payments.csv",
]

OPTIONAL_TABLES: List[str] = [
    "application_test.csv",
    "HomeCredit_columns_description.csv",
    "sample_submission.csv",
]

# Canonical feature groups for Home Credit application data
NUMERIC_FEATURES: List[str] = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "DAYS_BIRTH",           # Negative days from loan application
    "DAYS_EMPLOYED",        # Negative days employed
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
    "EXT_SOURCE_1",         # Normalized external credit score 1
    "EXT_SOURCE_2",         # Normalized external credit score 2
    "EXT_SOURCE_3",         # Normalized external credit score 3
    "REGION_RATING_CLIENT",
    "REGION_RATING_CLIENT_W_CITY",
]

CATEGORICAL_FEATURES: List[str] = [
    "NAME_CONTRACT_TYPE",     # Cash loans, Revolving loans
    "CODE_GENDER",            # M, F, XNA
    "FLAG_OWN_CAR",           # Y, N
    "FLAG_OWN_REALTY",        # Y, N
    "NAME_INCOME_TYPE",       # Working, State servant, Commercial associate, Pensioner
    "NAME_EDUCATION_TYPE",    # Higher education, Secondary / secondary special, etc.
    "NAME_FAMILY_STATUS",     # Married, Single / not married, Civil marriage, etc.
    "NAME_HOUSING_TYPE",      # House / apartment, With parents, Municipal apartment, etc.
]

HISTORICAL_FEATURES: List[str] = [
    "BUREAU_LOAN_COUNT",
    "BUREAU_DAYS_CREDIT_MAX",
    "BUREAU_AMT_CREDIT_SUM_SUM",
    "BUREAU_AMT_CREDIT_SUM_DEBT_SUM",
    "BUREAU_DEBT_CREDIT_RATIO",
    "PREV_APP_COUNT",
    "PREV_REFUSED_COUNT",
    "PREV_APPROVED_COUNT",
    "PREV_REFUSAL_RATE",
    "PREV_AMT_CREDIT_MAX",
    "INSTAL_COUNT",
    "INSTAL_LATE_COUNT",
    "INSTAL_LATE_RATIO",
    "INSTAL_DPD_MAX",
    "POS_DPD_MAX",
    "CC_BALANCE_MAX",
]

ALL_BASE_FEATURES: List[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def validate_home_credit_record(record: Dict) -> bool:
    """
    Validates that a dictionary contains valid Home Credit schema keys.
    """
    for col in ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY"]:
        if col not in record:
            return False
        if record[col] is not None and record[col] < 0:
            return False
    return True
