"""
Dataset ingestion and validation module for Home Credit Default Risk.
Handles loading real Kaggle CSVs (application_train and auxiliary tables),
validating file manifests, and providing stratified sampling where configured.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd
from home_credit.schema import (
    ID_COLUMN,
    TARGET_COLUMN,
    REQUIRED_TABLES,
    HISTORICAL_TABLES,
    OPTIONAL_TABLES,
)


def validate_home_credit_dataset_directory(data_dir: str = "data/home_credit") -> Dict[str, Any]:
    """
    Validates the Home Credit data directory:
    - Verifies existence of application_train.csv
    - Verifies TARGET column presence and class distribution
    - Checks for historical tables (bureau, previous applications, installments, POS, credit card)
    - Identifies any missing or unexpected files
    """
    p = Path(data_dir)
    if not p.exists():
        return {
            "valid": False,
            "data_dir": str(p),
            "error": f"Directory '{data_dir}' does not exist.",
            "present_files": [],
            "missing_required": REQUIRED_TABLES,
            "missing_historical": HISTORICAL_TABLES,
        }

    present_files = [f.name for f in p.glob("*.csv")]
    missing_required = [f for f in REQUIRED_TABLES if f not in present_files]
    missing_historical = [f for f in HISTORICAL_TABLES if f not in present_files]
    missing_optional = [f for f in OPTIONAL_TABLES if f not in present_files]

    # Inspect application_train.csv if present
    app_train_path = p / "application_train.csv"
    train_metadata: Dict[str, Any] = {}

    if app_train_path.exists():
        try:
            head_df = pd.read_csv(app_train_path, nrows=5)
            has_target = TARGET_COLUMN in head_df.columns
            has_id = ID_COLUMN in head_df.columns
            col_count = head_df.shape[1]

            # Fast row count reading only the ID column
            id_col = pd.read_csv(app_train_path, usecols=[ID_COLUMN])
            total_records = len(id_col)

            target_col = pd.read_csv(app_train_path, usecols=[TARGET_COLUMN])
            target_distribution = target_col[TARGET_COLUMN].value_counts(normalize=True).to_dict()

            train_metadata = {
                "has_target": has_target,
                "has_id": has_id,
                "total_records": total_records,
                "total_columns": col_count,
                "target_distribution": {
                    int(k): round(float(v), 4) for k, v in target_distribution.items()
                },
            }
        except Exception as e:
            train_metadata = {"error": str(e)}

    is_valid = len(missing_required) == 0 and train_metadata.get("has_target", False)

    return {
        "valid": is_valid,
        "data_dir": str(p.resolve()),
        "data_provenance": "REAL_KAGGLE_HOME_CREDIT_DATASET" if is_valid else "INCOMPLETE_OR_SYNTHETIC",
        "dataset_source": "anggundwilestari/home-credit" if is_valid else "None",
        "present_files": sorted(present_files),
        "missing_required": missing_required,
        "missing_historical": missing_historical,
        "missing_optional": missing_optional,
        "application_train": train_metadata,
    }


def load_or_create_home_credit_dataset(
    data_dir: str = "data/home_credit",
    sample_size: Optional[int] = 50000,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Loads Home Credit dataset from local directory if present.
    If the real application_train.csv exists, it is loaded. If sample_size is set,
    a stratified sample on TARGET is extracted to maintain exact class proportions.
    If absent, falls back to generating a synthetic sample conforming to the schema.
    """
    path = Path(data_dir) / "application_train.csv"

    if path.exists():
        print(f"Loading real Kaggle dataset from {path}...")
        df = pd.read_csv(path)

        # Confirm target column
        if TARGET_COLUMN not in df.columns:
            raise ValueError(f"Required target column '{TARGET_COLUMN}' not found in {path}")

        # If sample size specified and smaller than full dataset, perform stratified sampling
        if sample_size is not None and sample_size < len(df):
            print(f"Applying stratified sampling: {sample_size:,} records from {len(df):,} total (seed={random_seed})...")
            from sklearn.model_selection import train_test_split
            df, _ = train_test_split(
                df,
                train_size=sample_size,
                stratify=df[TARGET_COLUMN],
                random_state=random_seed
            )
            df = df.reset_index(drop=True)

        df.attrs["data_provenance"] = "REAL_KAGGLE_HOME_CREDIT_DATASET"
        df.attrs["dataset_source"] = "anggundwilestari/home-credit"
        df.attrs["total_available_records"] = 307511
        df.attrs["loaded_records"] = len(df)
        print(f"Successfully loaded {len(df):,} records (default rate: {df[TARGET_COLUMN].mean()*100:.2f}%).")
        return df

    # Fallback to generating synthetic dataset if real CSV is missing
    print("Real dataset not found. Generating synthetic dataset conforming to Home Credit schema...")
    np.random.seed(random_seed)
    n = sample_size if sample_size is not None else 2500

    sk_ids = np.arange(100001, 100001 + n)
    targets = np.random.choice([0, 1], size=n, p=[0.92, 0.08])
    incomes = np.random.lognormal(mean=11.8, sigma=0.5, size=n).round(-2)
    credits = (incomes * np.random.uniform(1.8, 4.5, size=n)).round(-2)
    annuities = (credits / np.random.uniform(10.0, 25.0, size=n)).round(-1)
    goods_prices = credits * np.random.uniform(0.85, 1.0, size=n)

    ages_years = np.random.uniform(21, 65, size=n)
    days_birth = (-ages_years * 365.25).astype(int)
    employed_years = np.random.uniform(0.5, 30, size=n)
    days_employed = (-employed_years * 365.25).astype(int)
    days_registration = np.random.uniform(-10000, -100, size=n).astype(int)
    days_id_publish = np.random.uniform(-5000, -100, size=n).astype(int)

    children = np.random.choice([0, 1, 2, 3], size=n, p=[0.70, 0.20, 0.08, 0.02])
    fam_members = children + np.random.choice([1, 2], size=n, p=[0.3, 0.7])

    ext_1 = np.clip(np.random.normal(0.50 - targets * 0.15, 0.18, size=n), 0.01, 0.99)
    ext_2 = np.clip(np.random.normal(0.52 - targets * 0.16, 0.17, size=n), 0.01, 0.99)
    ext_3 = np.clip(np.random.normal(0.48 - targets * 0.15, 0.19, size=n), 0.01, 0.99)

    region_ratings = np.random.choice([1, 2, 3], size=n, p=[0.2, 0.6, 0.2])
    region_ratings_city = region_ratings

    contract_types = np.random.choice(["Cash loans", "Revolving loans"], size=n, p=[0.9, 0.1])
    genders = np.random.choice(["M", "F"], size=n, p=[0.45, 0.55])
    own_car = np.random.choice(["Y", "N"], size=n, p=[0.35, 0.65])
    own_realty = np.random.choice(["Y", "N"], size=n, p=[0.7, 0.3])
    income_types = np.random.choice(
        ["Working", "Commercial associate", "State servant", "Pensioner"],
        size=n, p=[0.52, 0.23, 0.15, 0.10]
    )
    education_types = np.random.choice(
        ["Secondary / secondary special", "Higher education", "Incomplete higher", "Lower secondary"],
        size=n, p=[0.71, 0.24, 0.04, 0.01]
    )
    family_statuses = np.random.choice(
        ["Married", "Single / not married", "Civil marriage", "Separated", "Widow"],
        size=n, p=[0.64, 0.15, 0.10, 0.06, 0.05]
    )
    housing_types = np.random.choice(
        ["House / apartment", "With parents", "Municipal apartment", "Rented apartment"],
        size=n, p=[0.88, 0.06, 0.04, 0.02]
    )

    data = {
        ID_COLUMN: sk_ids,
        TARGET_COLUMN: targets,
        "AMT_INCOME_TOTAL": incomes,
        "AMT_CREDIT": credits,
        "AMT_ANNUITY": annuities,
        "AMT_GOODS_PRICE": goods_prices,
        "DAYS_BIRTH": days_birth,
        "DAYS_EMPLOYED": days_employed,
        "DAYS_REGISTRATION": days_registration,
        "DAYS_ID_PUBLISH": days_id_publish,
        "CNT_CHILDREN": children,
        "CNT_FAM_MEMBERS": fam_members,
        "EXT_SOURCE_1": ext_1,
        "EXT_SOURCE_2": ext_2,
        "EXT_SOURCE_3": ext_3,
        "REGION_RATING_CLIENT": region_ratings,
        "REGION_RATING_CLIENT_W_CITY": region_ratings_city,
        "NAME_CONTRACT_TYPE": contract_types,
        "CODE_GENDER": genders,
        "FLAG_OWN_CAR": own_car,
        "FLAG_OWN_REALTY": own_realty,
        "NAME_INCOME_TYPE": income_types,
        "NAME_EDUCATION_TYPE": education_types,
        "NAME_FAMILY_STATUS": family_statuses,
        "NAME_HOUSING_TYPE": housing_types,
    }

    df = pd.DataFrame(data)
    df.attrs["data_provenance"] = "SYNTHETIC_RESEARCH_SAMPLE"
    df.attrs["dataset_source"] = "synthetic_generator"
    return df
