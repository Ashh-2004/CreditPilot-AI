"""
Portfolio metrics and analytics dashboard for LoanSense AI.
Renders executive KPIs, dynamic portfolio filters, disbursement visualizations,
and filtered loan application history with CSV export.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db import fetch_all


def render():
    st.markdown("## 📊 Loan Portfolio & Dynamic Analytics")
    st.caption("Executive portfolio KPIs, dynamic multi-dimensional filters, and risk exposure distribution")
    st.divider()

    # ── Fetch Live Portfolio Data ────────────────────────────────
    try:
        raw_apps = fetch_all("""
            SELECT
                a.application_id,
                b.full_name,
                b.credit_score,
                b.annual_income,
                b.property_area,
                b.employment_type,
                a.loan_amount,
                a.loan_purpose,
                a.interest_rate,
                a.tenure_months,
                a.status,
                a.approval_probability,
                a.ml_default_probability,
                a.ml_risk_band,
                DATE(a.applied_at) as applied_date
            FROM loan_applications a
            JOIN borrowers b ON a.borrower_id = b.borrower_id
            ORDER BY a.application_id DESC
        """)
        df_all = pd.DataFrame(raw_apps) if raw_apps else pd.DataFrame()
    except Exception:
        df_all = pd.DataFrame()

    # Fallback sample dataset if database has 0 records
    if df_all.empty:
        st.info("ℹ️ Database contains no application records or is disconnected — displaying sample portfolio benchmark data.")
        df_all = pd.DataFrame({
            "application_id": [101, 102, 103, 104, 105, 106, 107, 108],
            "full_name": ["Amit Verma", "Sneha Rao", "Rohan Mehta", "Deepa Nair", "Kunal Shah", "Ananya Sen", "Vikas Dubey", "Pooja Hegde"],
            "credit_score": [780, 640, 590, 720, 680, 760, 550, 710],
            "annual_income": [1200000, 750000, 480000, 950000, 850000, 1400000, 400000, 900000],
            "property_area": ["Urban", "Semi-Urban", "Rural", "Urban", "Semi-Urban", "Urban", "Rural", "Semi-Urban"],
            "employment_type": ["Salaried", "Self-Employed", "Business", "Salaried", "Business", "Salaried", "Self-Employed", "Salaried"],
            "loan_amount": [2500000, 600000, 350000, 1800000, 1200000, 3200000, 250000, 1500000],
            "loan_purpose": ["Home Loan", "Personal Loan", "Vehicle Loan", "Home Loan", "Business Loan", "Home Loan", "Personal Loan", "Education Loan"],
            "interest_rate": [8.5, 13.5, 10.5, 8.75, 12.0, 8.4, 15.0, 9.5],
            "tenure_months": [240, 36, 60, 180, 60, 300, 24, 84],
            "status": ["approved", "review", "rejected", "approved", "approved", "approved", "rejected", "approved"],
            "approval_probability": [85.0, 55.0, 35.0, 78.0, 68.0, 88.0, 30.0, 75.0],
            "ml_default_probability": [8.5, 28.0, 62.0, 12.0, 22.0, 6.0, 74.0, 14.0],
            "ml_risk_band": ["Low", "Medium", "High", "Low", "Medium", "Low", "High", "Low"],
            "applied_date": ["2026-03-01", "2026-03-03", "2026-03-05", "2026-03-08", "2026-03-10", "2026-03-12", "2026-03-14", "2026-03-16"]
        })

    # ── Dynamic Filter Controls ──────────────────────────────────
    with st.expander("🔍 Dynamic Portfolio Filters", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        all_purposes = sorted(df_all["loan_purpose"].dropna().unique().tolist())
        all_statuses = sorted(df_all["status"].dropna().unique().tolist())
        all_bands = sorted([b for b in df_all["ml_risk_band"].dropna().unique().tolist() if b])
        all_areas = sorted(df_all["property_area"].dropna().unique().tolist())

        with col_f1:
            sel_purposes = st.multiselect("Loan Purpose", all_purposes, default=all_purposes)
        with col_f2:
            sel_statuses = st.multiselect("Status", all_statuses, default=all_statuses)
        with col_f3:
            sel_bands = st.multiselect("Risk Band", all_bands, default=all_bands) if all_bands else []
        with col_f4:
            search_query = st.text_input("Search Borrower Name / ID", "")

    # Apply filters
    filtered_df = df_all.copy()
    if sel_purposes:
        filtered_df = filtered_df[filtered_df["loan_purpose"].isin(sel_purposes)]
    if sel_statuses:
        filtered_df = filtered_df[filtered_df["status"].isin(sel_statuses)]
    if sel_bands:
        filtered_df = filtered_df[filtered_df["ml_risk_band"].isin(sel_bands)]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["full_name"].astype(str).str.lower().str.contains(q) |
            filtered_df["application_id"].astype(str).str.contains(q)
        ]

    # ── Executive Dynamic KPIs ───────────────────────────────────
    total_apps = len(filtered_df)
    approved_df = filtered_df[filtered_df["status"] == "approved"]
    approved_count = len(approved_df)
    approval_rate = (approved_count / total_apps * 100) if total_apps > 0 else 0.0

    total_disbursed = approved_df["loan_amount"].sum()
    avg_ticket = approved_df["loan_amount"].mean() if approved_count > 0 else 0.0
    weighted_rate = (
        (approved_df["loan_amount"] * approved_df["interest_rate"]).sum() / max(1.0, total_disbursed)
        if total_disbursed > 0 else 0.0
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Filtered Applications", f"{total_apps:,}")
    k2.metric("Approved Loans", f"{approved_count:,}", delta=f"{approval_rate:.1f}% Approval Rate")
    k3.metric("Total Disbursed", f"₹{total_disbursed/1e5:,.1f} Lakhs" if total_disbursed < 1e7 else f"₹{total_disbursed/1e7:,.2f} Cr")
    k4.metric("Average Ticket Size", f"₹{avg_ticket/1e5:,.1f} Lakhs" if avg_ticket < 1e7 else f"₹{avg_ticket/1e7:,.2f} Cr")
    k5.metric("Avg. Interest Rate", f"{weighted_rate:.2f}% p.a.")

    st.divider()

    # ── Visual Analytics ─────────────────────────────────────────
    tab_charts, tab_data = st.tabs(["📈 Portfolio Visualizations", "📋 Filtered Application Records"])

    with tab_charts:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### 💼 Capital Disbursed by Purpose")
            if not approved_df.empty:
                disp_summary = approved_df.groupby("loan_purpose")["loan_amount"].sum().reset_index()
                fig_disp = px.bar(
                    disp_summary,
                    x="loan_purpose",
                    y="loan_amount",
                    color="loan_purpose",
                    color_discrete_sequence=["#c9a227", "#378add", "#1d9e75", "#4ab86a", "#8a6add"],
                    labels={"loan_amount": "Total Disbursed (₹)", "loan_purpose": "Facility"}
                )
                fig_disp.update_layout(
                    plot_bgcolor="#111820", paper_bgcolor="#111820",
                    font_color="#8aa8c0", showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_disp, use_container_width=True)
            else:
                st.info("No approved loans match current filters.")

        with c2:
            st.markdown("##### 🍩 Application Status Distribution")
            if not filtered_df.empty:
                status_summary = filtered_df["status"].value_counts().reset_index()
                status_summary.columns = ["Status", "Count"]
                color_map = {"approved": "#4ab86a", "rejected": "#e05050", "review": "#c9a227", "pending": "#378add"}
                fig_pie = px.pie(
                    status_summary,
                    names="Status",
                    values="Count",
                    hole=0.6,
                    color="Status",
                    color_discrete_map=color_map
                )
                fig_pie.update_layout(
                    plot_bgcolor="#111820", paper_bgcolor="#111820",
                    font_color="#8aa8c0", showlegend=True,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No records match current filters.")

        # Secondary row of charts: Property Area & Risk Band Composition
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("##### 🏘️ Property Area Demographics")
            if not filtered_df.empty and "property_area" in filtered_df.columns:
                area_summary = filtered_df["property_area"].value_counts().reset_index()
                area_summary.columns = ["Area", "Count"]
                fig_area = px.bar(
                    area_summary,
                    x="Area",
                    y="Count",
                    color="Area",
                    color_discrete_sequence=["#378add", "#c9a227", "#1d9e75"]
                )
                fig_area.update_layout(
                    plot_bgcolor="#111820", paper_bgcolor="#111820",
                    font_color="#8aa8c0", showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_area, use_container_width=True)

        with c4:
            st.markdown("##### 🎯 ML Risk Tier Composition")
            if not filtered_df.empty and "ml_risk_band" in filtered_df.columns:
                band_summary = filtered_df["ml_risk_band"].value_counts().reset_index()
                band_summary.columns = ["Risk Band", "Count"]
                fig_band = px.pie(
                    band_summary,
                    names="Risk Band",
                    values="Count",
                    color="Risk Band",
                    color_discrete_map={"Low": "#4ab86a", "Medium": "#c9a227", "High": "#e05050"}
                )
                fig_band.update_layout(
                    plot_bgcolor="#111820", paper_bgcolor="#111820",
                    font_color="#8aa8c0", showlegend=True,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_band, use_container_width=True)

    with tab_data:
        st.markdown(f"##### Showing {len(filtered_df):,} matching applications")
        display_cols = [
            "application_id", "full_name", "loan_amount", "loan_purpose",
            "interest_rate", "tenure_months", "credit_score", "status", "ml_risk_band"
        ]
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        st.dataframe(filtered_df[available_cols], use_container_width=True, hide_index=True)

        # CSV Download
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export Filtered Portfolio Data (CSV)",
            data=csv_data,
            file_name="loansense_portfolio_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )


if __name__ == "__main__":
    render()
