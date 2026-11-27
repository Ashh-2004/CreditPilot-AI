"""
Domain feature engineering and historical table aggregations for Home Credit Default Risk.
Extracts:
1. Application domain ratios (DTI proxy, credit-to-income, credit term, employment-to-age, external scores)
2. Bureau credit history aggregations (loan counts, debt-to-credit ratio, recent credit inquiries)
3. Previous Home Credit application aggregations (refusal rates, max approved credit)
4. Repayment installment behavior (late payment frequency, max DPD, underpayments)
5. POS CASH & Credit Card delinquency metrics
"""

from pathlib import Path
from typing import Optional, Set
import numpy as np
import pandas as pd


def compute_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes standard Home Credit domain-specific financial features:
    1. CREDIT_INCOME_PERCENT: Ratio of credit amount to borrower income
    2. ANNUITY_INCOME_PERCENT: Ratio of loan annuity to borrower income (DTI proxy)
    3. CREDIT_TERM: Loan payment term estimate (AMT_ANNUITY / AMT_CREDIT)
    4. DAYS_EMPLOYED_PERCENT: Proportion of life spent employed
    5. EXT_SOURCES_MEAN: Average of available external bureau scores (EXT_SOURCE_1, 2, 3)
    6. EXT_SOURCES_STD: Dispersion of available external bureau scores
    """
    df = df.copy()

    # Avoid division by zero
    income = df["AMT_INCOME_TOTAL"].replace(0, np.nan)
    credit = df["AMT_CREDIT"].replace(0, np.nan)

    # 1. Credit to income ratio
    df["CREDIT_INCOME_PERCENT"] = df["AMT_CREDIT"] / income

    # 2. Annuity to income ratio (Debt Burden / DTI proxy)
    df["ANNUITY_INCOME_PERCENT"] = df["AMT_ANNUITY"] / income

    # 3. Credit term proxy
    df["CREDIT_TERM"] = df["AMT_ANNUITY"] / credit

    # 4. Employment to age ratio (DAYS_EMPLOYED and DAYS_BIRTH are negative integers in Home Credit)
    if "DAYS_EMPLOYED" in df.columns and "DAYS_BIRTH" in df.columns:
        birth = df["DAYS_BIRTH"].replace(0, np.nan)
        # 365243 is a known anomaly flag in Home Credit for retired/unemployed
        employed_clean = df["DAYS_EMPLOYED"].replace(365243, np.nan)
        df["DAYS_EMPLOYED_PERCENT"] = employed_clean / birth

    # 5. External source combinations (key predictors in Home Credit)
    ext_cols = [col for col in ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"] if col in df.columns]
    if ext_cols:
        df["EXT_SOURCES_MEAN"] = df[ext_cols].mean(axis=1)
        df["EXT_SOURCES_STD"] = df[ext_cols].std(axis=1).fillna(0)

    return df


def aggregate_bureau(data_dir: Path, sk_ids: Optional[Set[int]] = None) -> Optional[pd.DataFrame]:
    """Aggregates Credit Bureau (bureau.csv) history per borrower."""
    path = data_dir / "bureau.csv"
    if not path.exists():
        return None

    usecols = ["SK_ID_CURR", "DAYS_CREDIT", "AMT_CREDIT_SUM", "AMT_CREDIT_SUM_DEBT"]
    bureau = pd.read_csv(path, usecols=usecols)
    if sk_ids is not None:
        bureau = bureau[bureau["SK_ID_CURR"].isin(sk_ids)].copy()

    if bureau.empty:
        return None

    bureau_agg = bureau.groupby("SK_ID_CURR").agg(
        BUREAU_LOAN_COUNT=("DAYS_CREDIT", "count"),
        BUREAU_DAYS_CREDIT_MAX=("DAYS_CREDIT", "max"),
        BUREAU_AMT_CREDIT_SUM_SUM=("AMT_CREDIT_SUM", "sum"),
        BUREAU_AMT_CREDIT_SUM_DEBT_SUM=("AMT_CREDIT_SUM_DEBT", "sum"),
    ).reset_index()

    bureau_agg["BUREAU_DEBT_CREDIT_RATIO"] = (
        bureau_agg["BUREAU_AMT_CREDIT_SUM_DEBT_SUM"]
        / bureau_agg["BUREAU_AMT_CREDIT_SUM_SUM"].replace(0, np.nan)
    )
    return bureau_agg


def aggregate_previous_applications(data_dir: Path, sk_ids: Optional[Set[int]] = None) -> Optional[pd.DataFrame]:
    """Aggregates previous Home Credit loan applications (previous_application.csv)."""
    path = data_dir / "previous_application.csv"
    if not path.exists():
        return None

    usecols = ["SK_ID_CURR", "NAME_CONTRACT_STATUS", "AMT_CREDIT"]
    prev = pd.read_csv(path, usecols=usecols)
    if sk_ids is not None:
        prev = prev[prev["SK_ID_CURR"].isin(sk_ids)].copy()

    if prev.empty:
        return None

    prev["IS_REFUSED"] = (prev["NAME_CONTRACT_STATUS"] == "Refused").astype(int)
    prev["IS_APPROVED"] = (prev["NAME_CONTRACT_STATUS"] == "Approved").astype(int)

    prev_agg = prev.groupby("SK_ID_CURR").agg(
        PREV_APP_COUNT=("NAME_CONTRACT_STATUS", "count"),
        PREV_REFUSED_COUNT=("IS_REFUSED", "sum"),
        PREV_APPROVED_COUNT=("IS_APPROVED", "sum"),
        PREV_AMT_CREDIT_MAX=("AMT_CREDIT", "max"),
    ).reset_index()

    prev_agg["PREV_REFUSAL_RATE"] = prev_agg["PREV_REFUSED_COUNT"] / prev_agg["PREV_APP_COUNT"].replace(0, np.nan)
    return prev_agg


def aggregate_installments(data_dir: Path, sk_ids: Optional[Set[int]] = None) -> Optional[pd.DataFrame]:
    """Aggregates historical repayment installments behavior (installments_payments.csv)."""
    path = data_dir / "installments_payments.csv"
    if not path.exists():
        return None

    usecols = ["SK_ID_CURR", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT", "AMT_INSTALMENT", "AMT_PAYMENT"]
    inst = pd.read_csv(path, usecols=usecols)
    if sk_ids is not None:
        inst = inst[inst["SK_ID_CURR"].isin(sk_ids)].copy()

    if inst.empty:
        return None

    inst["LATE_PAYMENT"] = (inst["DAYS_ENTRY_PAYMENT"] > inst["DAYS_INSTALMENT"]).astype(int)
    inst["DPD"] = (inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]).clip(lower=0)

    inst_agg = inst.groupby("SK_ID_CURR").agg(
        INSTAL_COUNT=("LATE_PAYMENT", "count"),
        INSTAL_LATE_COUNT=("LATE_PAYMENT", "sum"),
        INSTAL_DPD_MAX=("DPD", "max"),
    ).reset_index()

    inst_agg["INSTAL_LATE_RATIO"] = inst_agg["INSTAL_LATE_COUNT"] / inst_agg["INSTAL_COUNT"].replace(0, np.nan)
    return inst_agg


def aggregate_pos_cash(data_dir: Path, sk_ids: Optional[Set[int]] = None) -> Optional[pd.DataFrame]:
    """Aggregates POS and cash loans monthly balance history (POS_CASH_balance.csv)."""
    path = data_dir / "POS_CASH_balance.csv"
    if not path.exists():
        return None

    usecols = ["SK_ID_CURR", "SK_DPD"]
    pos = pd.read_csv(path, usecols=usecols)
    if sk_ids is not None:
        pos = pos[pos["SK_ID_CURR"].isin(sk_ids)].copy()

    if pos.empty:
        return None

    pos_agg = pos.groupby("SK_ID_CURR").agg(
        POS_DPD_MAX=("SK_DPD", "max"),
    ).reset_index()
    return pos_agg


def aggregate_credit_card(data_dir: Path, sk_ids: Optional[Set[int]] = None) -> Optional[pd.DataFrame]:
    """Aggregates credit card monthly balance history (credit_card_balance.csv)."""
    path = data_dir / "credit_card_balance.csv"
    if not path.exists():
        return None

    usecols = ["SK_ID_CURR", "AMT_BALANCE"]
    cc = pd.read_csv(path, usecols=usecols)
    if sk_ids is not None:
        cc = cc[cc["SK_ID_CURR"].isin(sk_ids)]

    if cc.empty:
        return None

    cc_agg = cc.groupby("SK_ID_CURR").agg(
        CC_BALANCE_MAX=("AMT_BALANCE", "max"),
    ).reset_index()
    return cc_agg


def merge_historical_features(df: pd.DataFrame, data_dir: str = "data/home_credit") -> pd.DataFrame:
    """
    Enriches the application dataframe with aggregated historical features
    from bureau, previous applications, installments, POS cash, and credit card tables.
    """
    path = Path(data_dir)
    if not path.exists() or "SK_ID_CURR" not in df.columns:
        return df

    sk_ids = set(df["SK_ID_CURR"].dropna().astype(int).unique())

    print("  -> Aggregating bureau records...")
    bureau_agg = aggregate_bureau(path, sk_ids)
    if bureau_agg is not None:
        df = df.merge(bureau_agg, on="SK_ID_CURR", how="left")

    print("  -> Aggregating previous applications...")
    prev_agg = aggregate_previous_applications(path, sk_ids)
    if prev_agg is not None:
        df = df.merge(prev_agg, on="SK_ID_CURR", how="left")

    print("  -> Aggregating installment payment records...")
    inst_agg = aggregate_installments(path, sk_ids)
    if inst_agg is not None:
        df = df.merge(inst_agg, on="SK_ID_CURR", how="left")

    print("  -> Aggregating POS / cash balance records...")
    pos_agg = aggregate_pos_cash(path, sk_ids)
    if pos_agg is not None:
        df = df.merge(pos_agg, on="SK_ID_CURR", how="left")

    print("  -> Aggregating credit card balance records...")
    cc_agg = aggregate_credit_card(path, sk_ids)
    if cc_agg is not None:
        df = df.merge(cc_agg, on="SK_ID_CURR", how="left")

    return df
