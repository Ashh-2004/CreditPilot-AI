"""
EMI, Amortization, and Prepayment Simulator module for LoanSense AI.
Provides reducing balance instalment calculations, accelerated prepayment analysis,
side-by-side payoff curves, and full schedule export.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from calculations import calc_emi, calc_amortization_schedule


def render():
    st.markdown("## 🧮 EMI & Prepayment Amortization Simulator")
    st.caption("Calculate monthly instalments, evaluate accelerated prepayment strategies, and model interest savings")
    st.divider()

    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.markdown("#### Facility Parameters")
        principal = st.number_input("Principal Loan Amount (₹)", min_value=10000.0, max_value=50000000.0, value=1500000.0, step=50000.0)
        annual_rate = st.number_input("Annual Interest Rate (% p.a.)", min_value=1.0, max_value=30.0, value=8.75, step=0.1)
        tenure_months = st.number_input("Loan Tenure (Months)", min_value=6, max_value=360, value=180, step=6)
        processing_fee_pct = st.number_input("Processing Fee (% of Principal)", min_value=0.0, max_value=5.0, value=0.75, step=0.1)

        st.markdown("#### ⚡ Accelerated Prepayment Strategy (Optional)")
        extra_monthly = st.number_input("Monthly Extra Prepayment (₹)", min_value=0.0, max_value=500000.0, value=2500.0, step=500.0)
        use_lump_sum = st.checkbox("Include One-Time Lump-Sum Prepayment?", value=False)
        lump_sum = 0.0
        lump_month = 0
        if use_lump_sum:
            lump_sum = st.number_input("Lump-Sum Prepayment Amount (₹)", min_value=10000.0, max_value=5000000.0, value=100000.0, step=10000.0)
            lump_month = st.slider("Execute Prepayment at Month #", 1, int(tenure_months), 12)

    with col2:
        # Standard Baseline EMI calculation
        base_emi = calc_emi(principal, annual_rate, int(tenure_months))
        processing_fee = round(principal * processing_fee_pct / 100.0)

        # Accelerated Prepayment Schedule Calculation
        schedule_data = calc_amortization_schedule(
            principal=principal,
            annual_rate=annual_rate,
            tenure_months=int(tenure_months),
            monthly_prepayment=extra_monthly,
            lump_sum_prepayment=lump_sum,
            lump_sum_month=lump_month
        )

        st.markdown("#### Executive Payment Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Scheduled Monthly EMI", f"₹{base_emi:,.0f}")
        m2.metric("Total Interest (Stressed)", f"₹{schedule_data['total_interest']:,.0f}")
        m3.metric(
            "Interest Saved",
            f"₹{schedule_data['interest_saved']:,.0f}",
            delta=f"-{schedule_data['tenure_months_saved']} Months Saved!" if schedule_data['tenure_months_saved'] > 0 else "Baseline Pace",
            delta_color="normal"
        )

        p1, p2 = st.columns(2)
        p1.metric("Actual Payoff Tenure", f"{schedule_data['actual_tenure_months']} Months", delta=f"{schedule_data['tenure_months_saved']} Months Faster" if schedule_data['tenure_months_saved'] > 0 else "Full Term")
        p2.metric("Total Outflow", f"₹{schedule_data['total_payment'] + processing_fee:,.0f}")

        # Cost Breakdown Donut
        fig_donut = go.Figure(data=[go.Pie(
            labels=["Principal", "Interest Paid", "Processing Fee"],
            values=[principal, schedule_data["total_interest"], processing_fee],
            hole=0.6,
            marker_colors=["#4ab86a", "#c9a227", "#378add"]
        )])
        fig_donut.update_layout(
            plot_bgcolor="#111820", paper_bgcolor="#111820",
            font_color="#8aa8c0", showlegend=True,
            legend=dict(font=dict(color="#8aa8c0")),
            margin=dict(l=10, r=10, t=10, b=10),
            height=200
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # ── Interactive Balance Payoff Trajectory ─────────────────────
    st.markdown("#### 📉 Loan Balance Amortization Trajectory")

    # Generate baseline schedule for comparison chart
    base_schedule_data = calc_amortization_schedule(
        principal=principal,
        annual_rate=annual_rate,
        tenure_months=int(tenure_months),
        monthly_prepayment=0.0,
        lump_sum_prepayment=0.0
    )

    df_base = pd.DataFrame(base_schedule_data["schedule"])
    df_accel = pd.DataFrame(schedule_data["schedule"])

    if not df_base.empty and not df_accel.empty:
        fig_traj = go.Figure()
        fig_traj.add_trace(go.Scatter(
            x=df_base["month"],
            y=df_base["closing_balance"],
            mode="lines",
            name="Scheduled Standard Amortization",
            line=dict(color="#c9a227", width=2, dash="dash")
        ))
        fig_traj.add_trace(go.Scatter(
            x=df_accel["month"],
            y=df_accel["closing_balance"],
            mode="lines",
            name="Accelerated Prepayment Amortization",
            line=dict(color="#4ab86a", width=3)
        ))
        fig_traj.update_layout(
            plot_bgcolor="#111820", paper_bgcolor="#111820",
            font_color="#8aa8c0",
            xaxis_title="Tenure Month",
            yaxis_title="Outstanding Balance (₹)",
            margin=dict(l=10, r=10, t=20, b=10),
            height=300
        )
        st.plotly_chart(fig_traj, use_container_width=True)

    # ── Full Amortization Table ──────────────────────────────────
    st.markdown("#### Month-by-Month Amortization Schedule")
    show_all = st.checkbox("Show full schedule", value=False)

    if not df_accel.empty:
        display_df = df_accel.copy()
        display_df.rename(columns={
            "month": "Month",
            "opening_balance": "Opening (₹)",
            "interest_component": "Interest (₹)",
            "principal_component": "Principal (₹)",
            "total_payment": "Total Paid (₹)",
            "closing_balance": "Closing (₹)"
        }, inplace=True)

        view_df = display_df if show_all else display_df.head(12)
        st.dataframe(view_df, use_container_width=True, hide_index=True)

        if not show_all and len(df_accel) > 12:
            st.caption(f"Displaying first 12 of {len(df_accel)} months. Check 'Show full schedule' to inspect entire tenure.")

        # CSV Download
        csv_bytes = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export Complete Amortization Schedule (CSV)",
            data=csv_bytes,
            file_name="amortization_schedule_prepayment.csv",
            mime="text/csv",
            use_container_width=True
        )


if __name__ == "__main__":
    render()
