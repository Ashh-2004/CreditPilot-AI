"""
Standalone runner for the Home Credit Default Risk machine learning pipeline.
Executes dataset ingestion, domain feature engineering, Stratified 5-Fold Cross Validation,
held-out test evaluation, probability calibration, and SHAP explainability.
Artifacts are saved under models/home_credit/.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from home_credit.pipeline import train_and_evaluate_home_credit


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate Home Credit ML pipeline.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=25000,
        help="Number of records to sample for training (default: 25000; set 0 or -1 for full dataset)",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=5,
        help="Number of cross-validation folds (default: 5)",
    )
    args = parser.parse_args()
    sample_size = None if args.sample_size in (0, -1) else args.sample_size

    report = train_and_evaluate_home_credit(sample_size=sample_size, cv_folds=args.cv)
    print("\nExecution complete. Output artifacts saved under models/home_credit/:")
    print("  - model.joblib (Calibrated Pipeline)")
    print("  - uncalibrated_model.joblib")
    print("  - evaluation_report.json (CV & Held-out comparison)")
    print("  - calibration_report.json (Calibration curves & Brier score)")
    print("  - shap_summary.json (SHAP Global importance & Local explanation)")
    print(f"\n{report['disclaimer']}")


if __name__ == "__main__":
    main()
