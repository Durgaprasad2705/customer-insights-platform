"""
Customer Insights Platform – Product Analytics Page
Category/brand/product revenue breakdown with interactive charts.
"""

from __future__ import annotations

import streamlit as st

from components.kpi_cards import section_title
from services.analytics_service import plot_top_products, plot_brand_performance, plot_category_revenue
from utils.formatters import fmt_currency


def render(df) -> None:
    """Render the Product Analytics page."""

    if df.empty:
        st.warning("No product data available.")
        return

    cat_col  = next((c for c in ["Category"] if c in df.columns), None)
    prod_col = next((c for c in ["ProductName", "Product", "Item"] if c in df.columns), None)
    brand_col= next((c for c in ["Brand", "Manufacturer"] if c in df.columns), None)
    amt_col  = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)
    qty_col  = next((c for c in ["Quantity", "Units"] if c in df.columns), None)
    profit_col= next((c for c in ["ProfitMargin", "Profit"] if c in df.columns), None)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    if prod_col:  k1.metric("Unique Products",  f"{df[prod_col].nunique():,}")
    if cat_col:   k2.metric("Categories",        f"{df[cat_col].nunique():,}")
    if brand_col: k3.metric("Brands",            f"{df[brand_col].nunique():,}")
    if amt_col:   k4.metric("Total Revenue",     fmt_currency(df[amt_col].sum()))

    # ── Top Products + Brand Charts ───────────────────────────────────────────
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.plotly_chart(plot_top_products(df, top_n=8), use_container_width=True)
    with col2:
        st.plotly_chart(plot_brand_performance(df), use_container_width=True)

    # ── Category Donut ────────────────────────────────────────────────────────
    st.plotly_chart(plot_category_revenue(df), use_container_width=True)

    # ── Category Margin Breakdown Table ──────────────────────────────────────
    if cat_col and amt_col:
        st.markdown(section_title("Category Revenue & Margin Breakdown", "📊"), unsafe_allow_html=True)
        agg_cols: dict = {"Revenue": (amt_col, "sum")}
        if qty_col:    agg_cols["Units Sold"]   = (qty_col,    "sum")
        if profit_col: agg_cols["Total Profit"] = (profit_col, "sum")

        cat_df = df.groupby(cat_col).agg(**{k: (v[0], v[1]) for k, v in agg_cols.items()}).reset_index()
        if profit_col and "Total Profit" in cat_df.columns:
            cat_df["Margin %"] = (cat_df["Total Profit"] / cat_df["Revenue"].replace(0, 1) * 100).round(1)
        cat_df = cat_df.sort_values("Revenue", ascending=False)
        st.dataframe(cat_df, use_container_width=True)

    # ── Product Detail Table ──────────────────────────────────────────────────
    if prod_col and amt_col:
        st.markdown(section_title("Product Revenue Breakdown", "📦"), unsafe_allow_html=True)
        grp_cols = [c for c in [cat_col, prod_col, brand_col] if c]
        prod_agg: dict = {"Revenue": (amt_col, "sum")}
        if qty_col: prod_agg["Units"] = (qty_col, "sum")

        prod_df = df.groupby(grp_cols).agg(**{k: (v[0], v[1]) for k, v in prod_agg.items()}).reset_index()
        prod_df = prod_df.sort_values("Revenue", ascending=False)
        st.dataframe(prod_df, use_container_width=True)
