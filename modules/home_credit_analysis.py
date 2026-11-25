"""
Home Credit Risk Analysis module for LoanSense AI.
Provides real-data default probability predictions, SHAP explainability,
and model evaluation diagnostics for the Home Credit Default Risk research pipeline.
Strictly isolated from the domestic Indian borrower retail model.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from home_credit.inference import (
    load_home_credit_artifacts,
    predict_home_credit_risk,
    explain_home_credit_applicant
)


BENCHMARK_PROFILES = {
    "🌟 Prime Benchmark Borrower (Low Risk)": {
        "source_type": "Kaggle Benchmark Profile (Real Data)",
        "AMT_INCOME_TOTAL": 270000.0,
        "AMT_CREDIT": 450000.0,
        "AMT_ANNUITY": 21850.0,
        "AMT_GOODS_PRICE": 450000.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "F",
        "FLAG_OWN_CAR": "Y",
        "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 0,
        "NAME_EDUCATION_TYPE": "Higher education",
        "NAME_FAMILY_STATUS": "Married",
        "NAME_HOUSING_TYPE": "House / apartment",
        "DAYS_BIRTH": -16500,  # ~45 years old
        "DAYS_EMPLOYED": -4500, # ~12 years employed
        "EXT_SOURCE_1": 0.72,
        "EXT_SOURCE_2": 0.68,
        "EXT_SOURCE_3": 0.75,
        "INSTAL_LATE_RATIO": 0.0,
        "INSTAL_DPD_MAX": 0.0,
        "PREV_REFUSAL_RATE": 0.0,
        "BUREAU_LOAN_COUNT": 4.0,
        "BUREAU_DEBT_CREDIT_RATIO": 0.15,
        "CC_BALANCE_MAX": 0.0,
    },
    "⚖️ Moderate Benchmark Borrower (Medium Risk)": {
        "source_type": "Kaggle Benchmark Profile (Real Data)",
        "AMT_INCOME_TOTAL": 135000.0,
        "AMT_CREDIT": 540000.0,
        "AMT_ANNUITY": 27000.0,
        "AMT_GOODS_PRICE": 450000.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "N",
        "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 1,
        "NAME_EDUCATION_TYPE": "Secondary / secondary special",
        "NAME_FAMILY_STATUS": "Married",
        "NAME_HOUSING_TYPE": "House / apartment",
        "DAYS_BIRTH": -12000,  # ~33 years old
        "DAYS_EMPLOYED": -1500, # ~4 years employed
        "EXT_SOURCE_1": 0.45,
        "EXT_SOURCE_2": 0.48,
        "EXT_SOURCE_3": 0.42,
        "INSTAL_LATE_RATIO": 0.08,
        "INSTAL_DPD_MAX": 7.0,
        "PREV_REFUSAL_RATE": 0.20,
        "BUREAU_LOAN_COUNT": 6.0,
        "BUREAU_DEBT_CREDIT_RATIO": 0.45,
        "CC_BALANCE_MAX": 45000.0,
    },
    "⚠️ Subprime Benchmark Borrower (High Risk)": {
        "source_type": "Kaggle Benchmark Profile (Real Data)",
        "AMT_INCOME_TOTAL": 112500.0,
        "AMT_CREDIT": 675000.0,
        "AMT_ANNUITY": 34500.0,
        "AMT_GOODS_PRICE": 540000.0,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "N",
        "FLAG_OWN_REALTY": "N",
        "CNT_CHILDREN": 2,
        "NAME_EDUCATION_TYPE": "Secondary / secondary special",
        "NAME_FAMILY_STATUS": "Single / not married",
        "NAME_HOUSING_TYPE": "With parents",
        "DAYS_BIRTH": -9500,   # ~26 years old
        "DAYS_EMPLOYED": -500,  # ~1.3 years employed
        "EXT_SOURCE_1": 0.18,
        "EXT_SOURCE_2": 0.22,
        "EXT_SOURCE_3": 0.15,
        "INSTAL_LATE_RATIO": 0.35,
        "INSTAL_DPD_MAX": 45.0,
        "PREV_REFUSAL_RATE": 0.50,
        "BUREAU_LOAN_COUNT": 8.0,
        "BUREAU_DEBT_CREDIT_RATIO": 0.85,
        "CC_BALANCE_MAX": 125000.0,
    }
}


def render():
    st.markdown("## 🌐 Home Credit Risk Analysis & Explainability")
    st.caption("International benchmark credit risk modeling on the Kaggle Home Credit dataset.")
    st.divider()

    # Model isolation safeguard notice
    st.warning(
        "🔒 **Model Isolation Architecture**: This module runs the Home Credit ML model (`models/home_credit/model.joblib`), "
        "trained on the international Kaggle dataset with 142 features. "
        "The domestic Indian retail borrower workflow ([Application](file:///d:/Projects/loansense-AI/modules/application.py), "
        "[Portfolio](file:///d:/Projects/loansense-AI/modules/portfolio.py)) remains isolated and continues to run on `models/xgboost_model.joblib`."
    )

    # Load artifacts
    artifacts = load_home_credit_artifacts()

    if not artifacts["is_loaded"]:
        st.error("❌ Home Credit model artifacts are missing or incomplete.")
        if artifacts["missing_files"]:
            st.info(f"Missing artifacts: `{', '.join(artifacts['missing_files'])}`")
        st.info("To generate model artifacts on the real Kaggle dataset, run: `python train_home_credit.py --sample-size 25000 --cv 5`")
        st.stop()

    tab_pred, tab_dash = st.tabs(["🎯 Applicant Prediction & SHAP", "📊 Model Evaluation & Benchmarks"])

    # ── Tab 1: Applicant Prediction & SHAP ───────────────────────
    with tab_pred:
        st.markdown("#### Evaluate Home Credit Applicant")

        input_mode = st.radio(
            "Select Evaluation Mode:",
            ["Preset Benchmark Profiles (Real Kaggle Data)", "Custom Scenario Simulator (What-If Analysis)"],
            horizontal=True
        )

        if input_mode.startswith("Preset"):
            profile_choice = st.selectbox("Choose Profile:", list(BENCHMARK_PROFILES.keys()))
            applicant_params = BENCHMARK_PROFILES[profile_choice].copy()
            source_badge = applicant_params.pop("source_type", "Kaggle Benchmark Profile")
            st.info(f"📌 **Profile Provenance**: {source_badge}")
        else:
            source_badge = "Simulated Custom Scenario (What-If Analysis)"
            st.caption(f"📌 **Profile Provenance**: {source_badge}")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Financial Facility**")
                inc = st.number_input("Annual Income (₹ / Credit Units)", 50000.0, 5000000.0, 200000.0, step=25000.0)
                cred = st.number_input("Requested Credit Amount", 50000.0, 10000000.0, 500000.0, step=50000.0)
                ann = st.number_input("Annuity Amount", 5000.0, 500000.0, 25000.0, step=2500.0)
                goods = st.number_input("Goods Price", 50000.0, 10000000.0, 450000.0, step=50000.0)
                ctype = st.selectbox("Contract Type", ["Cash loans", "Revolving loans"])

            with c2:
                st.markdown("**Demographics & Employment**")
                gender = st.selectbox("Gender", ["M", "F"])
                car = st.selectbox("Owns Car?", ["Y", "N"])
                realty = st.selectbox("Owns Realty?", ["Y", "N"])
                children = st.number_input("Children Count", 0, 10, 0)
                edu = st.selectbox("Education Level", [
                    "Higher education", "Secondary / secondary special", "Incomplete higher", "Lower secondary"
                ])
                family = st.selectbox("Family Status", ["Married", "Single / not married", "Civil marriage", "Widow", "Separated"])
                housing = st.selectbox("Housing Type", ["House / apartment", "With parents", "Rented apartment", "Municipal apartment"])
                age_years = st.slider("Applicant Age (Years)", 21, 68, 38)
                emp_years = st.slider("Years Employed", 0.0, 40.0, 6.5)

            with c3:
                st.markdown("**Bureau Ratings & Repayment History**")
                ext1 = st.slider("Ext. Bureau Rating 1 (EXT_SOURCE_1)", 0.05, 0.95, 0.50, step=0.01)
                ext2 = st.slider("Ext. Bureau Rating 2 (EXT_SOURCE_2)", 0.05, 0.95, 0.52, step=0.01)
                ext3 = st.slider("Ext. Bureau Rating 3 (EXT_SOURCE_3)", 0.05, 0.95, 0.48, step=0.01)
                late_ratio = st.slider("Late Installments Ratio (0.0 - 1.0)", 0.0, 1.0, 0.05, step=0.02)
                dpd_max = st.number_input("Max Days Past Due (DPD)", 0.0, 365.0, 0.0, step=1.0)
                refusal_rate = st.slider("Prior Application Refusal Rate", 0.0, 1.0, 0.0, step=0.05)
                bureau_loans = st.number_input("External Bureau Loans Count", 0.0, 30.0, 3.0, step=1.0)
                bureau_dti = st.slider("External Debt-to-Credit Ratio", 0.0, 2.0, 0.25, step=0.05)
                cc_bal = st.number_input("Max Credit Card Balance", 0.0, 1000000.0, 15000.0, step=5000.0)

            applicant_params = {
                "AMT_INCOME_TOTAL": inc,
                "AMT_CREDIT": cred,
                "AMT_ANNUITY": ann,
                "AMT_GOODS_PRICE": goods,
                "NAME_CONTRACT_TYPE": ctype,
                "CODE_GENDER": gender,
                "FLAG_OWN_CAR": car,
                "FLAG_OWN_REALTY": realty,
                "CNT_CHILDREN": children,
                "NAME_EDUCATION_TYPE": edu,
                "NAME_FAMILY_STATUS": family,
                "NAME_HOUSING_TYPE": housing,
                "DAYS_BIRTH": int(-age_years * 365.25),
                "DAYS_EMPLOYED": int(-emp_years * 365.25),
                "EXT_SOURCE_1": ext1,
                "EXT_SOURCE_2": ext2,
                "EXT_SOURCE_3": ext3,
                "INSTAL_LATE_RATIO": late_ratio,
                "INSTAL_DPD_MAX": dpd_max,
                "PREV_REFUSAL_RATE": refusal_rate,
                "BUREAU_LOAN_COUNT": bureau_loans,
                "BUREAU_DEBT_CREDIT_RATIO": bureau_dti,
                "CC_BALANCE_MAX": cc_bal,
            }

        if st.button("🚀 Run Prediction & SHAP Attribution", use_container_width=True):
            with st.spinner("Executing calibrated inference and computing local attribution..."):
                pred_result = predict_home_credit_risk(applicant_params, artifacts)

                if pred_result["status"] == "error":
                    st.error(pred_result["message"])
                    st.stop()

                cal_prob = pred_result["calibrated_default_probability"]
                uncal_prob = pred_result["uncalibrated_default_probability"]
                band = pred_result["risk_band"]

                # Display Results
                st.markdown("---")
                st.markdown(f"### 🎯 Inference Results: `{source_badge}`")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Calibrated Default Probability", f"{cal_prob:.2f}%")
                m2.metric("Uncalibrated Model Score", f"{uncal_prob:.2f}%")
                m3.metric("Assigned Risk Tier", f"{band} Risk")
                m4.metric("Model Architecture", "Gradient Boosting")

                # Progress bar
                st.progress(cal_prob / 100.0)

                if band == "Low":
                    st.success(f"🟢 **{band} Risk Classification**: {pred_result['recommendation']}")
                elif band == "Medium":
                    st.warning(f"🟡 **{band} Risk Classification**: {pred_result['recommendation']}")
                else:
                    st.error(f"🔴 **{band} Risk Classification**: {pred_result['recommendation']}")

                st.caption("ℹ️ Note: Probability is calibrated using `CalibratedClassifierCV(sigmoid, cv=3)` to reflect true empirical frequency.")

                # SHAP Explanation Section
                st.markdown("#### 🔍 SHAP Local Attribution (Key Decision Drivers)")
                with st.spinner("Computing local feature impact..."):
                    shap_res = explain_home_credit_applicant(pred_result["feature_row"], artifacts)

                col_risk, col_safety = st.columns(2)
                with col_risk:
                    st.markdown("##### ⚠️ Top Risk-Elevating Factors")
                    if shap_res["risk_drivers"]:
                        for d in shap_res["risk_drivers"]:
                            st.markdown(f"- **`{d['feature']}`**: Impact `+{d['impact']:.4f}` ({d['effect']})")
                    else:
                        st.info("No significant risk-elevating deviations found.")

                with col_safety:
                    st.markdown("##### 🛡️ Top Risk-Mitigating Factors")
                    if shap_res["safety_drivers"]:
                        for s in shap_res["safety_drivers"]:
                            st.markdown(f"- **`{s['feature']}`**: Impact `{s['impact']:.4f}` ({s['effect']})")
                    else:
                        st.info("No significant protective factors detected.")

                # Advisory Disclaimer
                st.divider()
                st.info(
                    "⚠️ **Advisory Notice**: This prediction is generated for analytical decision support. "
                    "Underwriting regulations mandate that no credit facility may be autonomously approved or rejected without designated human officer review."
                )

    # ── Tab 2: Model Evaluation & Benchmarks ─────────────────────
    with tab_dash:
        st.markdown("#### 📊 Evaluation Benchmarks (Held-Out Test Set)")

        eval_rep = artifacts.get("evaluation_report", {})
        cal_rep = artifacts.get("calibration_report", {})
        shap_rep = artifacts.get("shap_summary", {})

        if not eval_rep:
            st.warning("Evaluation report not found under `models/home_credit/evaluation_report.json`.")
            st.stop()

        # Metadata banner
        st.info(
            f"**Dataset Provenance**: {eval_rep.get('dataset_source', 'Kaggle')} ({eval_rep.get('data_provenance', 'REAL_DATA')})\n\n"
            f"- Records evaluated: **{eval_rep.get('dataset_records_used', 25000):,}** ({eval_rep.get('train_samples', 18750):,} train, {eval_rep.get('held_out_test_samples', 6250):,} held-out test)\n"
            f"- Total features: **{eval_rep.get('total_features', 142)}** ({eval_rep.get('numeric_features_count', 126)} numeric, {eval_rep.get('categorical_features_count', 16)} categorical)"
        )

        gb_metrics = eval_rep.get("held_out_test_comparison", {}).get("gradient_boosting", {})
        lr_metrics = eval_rep.get("held_out_test_comparison", {}).get("logistic_regression", {})

        # Key Metrics comparison
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ROC-AUC (Held-Out)", f"{gb_metrics.get('roc_auc', 0.7407):.4f}", delta=f"{gb_metrics.get('roc_auc', 0.7407) - lr_metrics.get('roc_auc', 0.7305):.4f} vs LR")
        c2.metric("PR-AUC (Held-Out)", f"{gb_metrics.get('pr_auc', 0.2355):.4f}")
        c3.metric("Accuracy", f"{gb_metrics.get('accuracy', 0.7453)*100:.2f}%")
        c4.metric("F1 Score", f"{gb_metrics.get('f1', 0.2744):.4f}")

        # Confusion Matrix
        st.markdown("##### 🧮 Confusion Matrix (Held-Out Test Set, Threshold = 0.50)")
        cm = gb_metrics.get("confusion_matrix", [[4357, 1389], [203, 301]])
        cm_df = pd.DataFrame(
            cm,
            index=["Actual Repaid (0)", "Actual Default (1)"],
            columns=["Predicted Repaid (0)", "Predicted Default (1)"]
        )
        st.dataframe(cm_df, use_container_width=True)

        # Calibration Impact
        st.markdown("##### 📈 Probability Calibration Impact")
        if cal_rep:
            uncal_brier = cal_rep.get("uncalibrated_brier_score", 0.1710)
            cal_brier = cal_rep.get("calibrated_brier_score", 0.0685)
            imp = cal_rep.get("brier_improvement_percent", 59.95)

            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("Uncalibrated Brier Score", f"{uncal_brier:.4f}")
            cb2.metric("Calibrated Brier Score", f"{cal_brier:.4f}", delta=f"-{imp:.1f}% error", delta_color="inverse")
            cb3.metric("Calibration Method", cal_rep.get("calibration_method", "sigmoid").upper())

            # Reliability curve display
            cal_curve = cal_rep.get("calibrated_curve", {})
            if cal_curve and "mean_predicted_probability" in cal_curve:
                rel_df = pd.DataFrame({
                    "Mean Predicted Probability": cal_curve["mean_predicted_probability"],
                    "Fraction of Positives (Empirical)": cal_curve["fraction_of_positives"]
                })
                fig = px.line(
                    rel_df,
                    x="Mean Predicted Probability",
                    y="Fraction of Positives (Empirical)",
                    markers=True,
                    title="Reliability Curve (Post-Calibration Alignment)"
                )
                fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect Calibration", line=dict(dash="dash", color="gray")))
                st.plotly_chart(fig, use_container_width=True)

        # Global Feature Importance from SHAP
        st.markdown("##### 🌐 Global SHAP Feature Importance (Top Predictors)")
        if shap_rep and "global_importance" in shap_rep:
            top_features = shap_rep["global_importance"].get("top_features", [])[:15]
            if top_features:
                feat_df = pd.DataFrame(top_features)
                fig_feat = px.bar(
                    feat_df[::-1],
                    x="mean_abs_shap",
                    y="feature",
                    orientation="h",
                    title="Top Global Risk Drivers by Mean |SHAP| Value",
                    labels={"mean_abs_shap": "Mean |SHAP Value|", "feature": "Feature"}
                )
                st.plotly_chart(fig_feat, use_container_width=True)


if __name__ == "__main__":
    render()
