"""
Customer Insights Platform – Sales Analytics Page
Revenue trends, regional performance, payment methods, monthly breakdown.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.kpi_cards import section_title
from services.analytics_service import (
    plot_revenue_trend, plot_region_sales,
    plot_payment_methods, plot_age_distribution,
)
from utils.formatters import fmt_currency, fmt_number


def render(df) -> None:
    """Render the Sales Analytics page."""

    if df.empty:
        st.warning("No sales data available.")
        return

    amt_col  = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)
    date_col = next((c for c in ["PurchaseDate", "Date", "OrderDate"] if c in df.columns), None)
    cust_col = next((c for c in ["CustomerID"] if c in df.columns), None)
    pay_col  = next((c for c in ["PaymentMethod", "Payment"] if c in df.columns), None)
    region_col= next((c for c in ["Region", "Location", "State"] if c in df.columns), None)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    if amt_col:
        k1.metric("Total Revenue",   fmt_currency(df[amt_col].sum()))
        k2.metric("Avg Order Value", fmt_currency(df[amt_col].mean()))
        k3.metric("Max Order",       fmt_currency(df[amt_col].max()))
    if cust_col:
        k4.metric("Unique Customers", fmt_number(df[cust_col].nunique()))

    # ── Revenue Trend + Region ────────────────────────────────────────────────
    # Store figures in session state for report reuse
    if "report_charts" not in st.session_state:
        st.session_state["report_charts"] = {}
    charts = st.session_state["report_charts"]

    fig_trend = plot_revenue_trend(df)
    fig_reg   = plot_region_sales(df)
    fig_pay   = plot_payment_methods(df)
    fig_age   = plot_age_distribution(df)

    charts["trend"] = fig_trend
    charts["reg"]   = fig_reg
    charts["pay"]   = fig_pay
    charts["age"]   = fig_age

    col1, col2 = st.columns([1.6, 1], gap="small")
    with col1:
        st.plotly_chart(fig_trend, use_container_width=True)
    with col2:
        st.plotly_chart(fig_reg,   use_container_width=True)

    # ── Payment Method + Age Distribution ────────────────────────────────────
    col3, col4 = st.columns(2, gap="small")
    with col3:
        st.plotly_chart(fig_pay, use_container_width=True)
    with col4:
        st.plotly_chart(fig_age, use_container_width=True)

    # ── Monthly Revenue Table ─────────────────────────────────────────────────
    if date_col and amt_col:
        st.markdown(section_title("Monthly Revenue Breakdown", "📅"), unsafe_allow_html=True)
        tmp = df[[date_col, amt_col]].copy()
        tmp[date_col]   = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp[amt_col]    = pd.to_numeric(tmp[amt_col], errors="coerce")
        monthly = tmp.groupby(pd.Grouper(key=date_col, freq="ME"))[amt_col].agg(
            Revenue="sum", Orders="count"
        ).reset_index()
        monthly.columns = ["Month", "Revenue", "Orders"]
        monthly["Avg Order"] = (monthly["Revenue"] / monthly["Orders"].replace(0, 1)).round(2)
        monthly = monthly.sort_values("Month", ascending=False)
        st.dataframe(monthly, use_container_width=True)

    # ── Payment Method Breakdown ──────────────────────────────────────────────
    if pay_col and amt_col:
        st.markdown(section_title("Payment Method Revenue", "💳"), unsafe_allow_html=True)
        pay_df = df.groupby(pay_col)[amt_col].agg(Revenue="sum", Orders="count").reset_index()
        pay_df["Avg Order"] = (pay_df["Revenue"] / pay_df["Orders"].replace(0, 1)).round(2)
        st.dataframe(pay_df.sort_values("Revenue", ascending=False), use_container_width=True)
