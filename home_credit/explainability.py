"""
SHAP Explainability module for Home Credit Default Risk models.
Provides global feature importance rankings and local individual prediction explanations.
Extracts post-transformation feature names from ColumnTransformer for human-interpretable outputs.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import shap
from home_credit.evaluation import SYNTHETIC_DATA_DISCLAIMER


class HomeCreditExplainer:
    """
    SHAP-based explainer for Home Credit pipelines.
    Supports both tree-based and linear models.
    """

    def __init__(self, pipeline, background_data: pd.DataFrame, max_background_samples: int = 100):
        self.pipeline = pipeline
        self.preprocessor = pipeline.named_steps["preprocessor"]
        self.classifier = pipeline.named_steps["classifier"]

        # Sample background data for explainer calibration
        if len(background_data) > max_background_samples:
            sampled_bg = background_data.sample(n=max_background_samples, random_state=42)
        else:
            sampled_bg = background_data

        # Transform background data
        self.X_bg_trans = self.preprocessor.transform(sampled_bg)

        # Retrieve feature names out of ColumnTransformer
        try:
            self.feature_names = [
                col.replace("num__", "").replace("cat__", "")
                for col in self.preprocessor.get_feature_names_out()
            ]
        except Exception:
            self.feature_names = [f"feature_{i}" for i in range(self.X_bg_trans.shape[1])]

        # Initialize appropriate explainer
        classifier_type = type(self.classifier).__name__.lower()
        if "logistic" in classifier_type:
            self.explainer = shap.LinearExplainer(self.classifier, self.X_bg_trans)
            self.is_linear = True
        else:
            # Model-agnostic prediction probability explainer for tree models
            predict_fn = lambda x: self.classifier.predict_proba(x)[:, 1]
            self.explainer = shap.Explainer(predict_fn, self.X_bg_trans)
            self.is_linear = False

    def compute_global_importance(self, X_eval: pd.DataFrame, max_eval_samples: int = 200) -> Dict[str, Any]:
        """
        Computes global feature importance by averaging absolute SHAP values across evaluation samples.
        """
        if len(X_eval) > max_eval_samples:
            eval_subset = X_eval.sample(n=max_eval_samples, random_state=42)
        else:
            eval_subset = X_eval

        X_eval_trans = self.preprocessor.transform(eval_subset)

        if self.is_linear:
            shap_values = self.explainer.shap_values(X_eval_trans)
            if isinstance(shap_values, list):
                shap_matrix = np.array(shap_values[1] if len(shap_values) > 1 else shap_values[0])
            else:
                shap_matrix = np.array(shap_values)
        else:
            shap_obj = self.explainer(X_eval_trans)
            shap_matrix = shap_obj.values

        # Mean absolute SHAP value per feature
        mean_abs_shap = np.mean(np.abs(shap_matrix), axis=0)

        # Pair feature names with importance and sort
        importance_pairs = [
            {"feature": name, "mean_abs_shap": round(float(val), 5)}
            for name, val in zip(self.feature_names, mean_abs_shap)
        ]
        importance_pairs.sort(key=lambda x: x["mean_abs_shap"], reverse=True)

        return {
            "top_features": importance_pairs[:25],
            "total_features": len(self.feature_names),
            "evaluation_samples": len(eval_subset),
            "disclaimer": SYNTHETIC_DATA_DISCLAIMER
        }

    def explain_individual_prediction(self, single_applicant: pd.DataFrame) -> Dict[str, Any]:
        """
        Explains why a specific loan applicant received their default risk prediction.
        Breaks down top risk-elevating and risk-mitigating factors.
        """
        X_trans = self.preprocessor.transform(single_applicant)
        predicted_prob = float(self.pipeline.predict_proba(single_applicant)[0][1])

        if self.is_linear:
            shap_vals = self.explainer.shap_values(X_trans)
            if isinstance(shap_vals, list):
                row_vals = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
            else:
                row_vals = shap_vals[0]
        else:
            shap_obj = self.explainer(X_trans)
            row_vals = shap_obj.values[0]

        factors = []
        for name, val in zip(self.feature_names, row_vals):
            factors.append({
                "feature": name,
                "shap_value": round(float(val), 5),
                "effect": "Increases Risk" if val > 0 else "Decreases Risk"
            })

        # Top positive contributors (increase risk)
        top_risk_drivers = sorted([f for f in factors if f["shap_value"] > 0], key=lambda x: x["shap_value"], reverse=True)[:5]
        # Top negative contributors (lower risk)
        top_safety_drivers = sorted([f for f in factors if f["shap_value"] < 0], key=lambda x: x["shap_value"])[:5]

        return {
            "predicted_default_probability": round(predicted_prob * 100, 2),
            "risk_drivers": top_risk_drivers,
            "safety_drivers": top_safety_drivers,
            "disclaimer": SYNTHETIC_DATA_DISCLAIMER
        }
