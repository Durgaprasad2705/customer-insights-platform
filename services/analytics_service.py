"""
Customer Insights Platform – Analytics Service
All Plotly chart builders + AI automated insights engine.
Charts use dark glassmorphism theme consistent with the UI.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PALETTE

LOGGER = logging.getLogger(__name__)

# ─── Dark Plotly Base Layout ──────────────────────────────────────────────────
_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font         =dict(family="Plus Jakarta Sans, Manrope, sans-serif",
                       color=PALETTE["text_secondary"], size=12),
    margin       =dict(l=20, r=20, t=44, b=20),
    legend       =dict(bgcolor="rgba(0,0,0,0)", font=dict(color=PALETTE["text_primary"])),
    title        =dict(font=dict(color=PALETTE["text_primary"], size=15, family="Manrope, sans-serif")),
    xaxis        =dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True,
                       color=PALETTE["text_secondary"], zeroline=False),
    yaxis        =dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True,
                       color=PALETTE["text_secondary"], zeroline=False),
)

CHART_COLORS = PALETTE["chart"]


def _apply(fig: go.Figure, **overrides) -> go.Figure:
    layout = {**_BASE_LAYOUT, **overrides}

    # Theme-aware chart colors
    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        light_font_color = "#4A5068"
        light_title_color = "#1A1D2E"
        light_grid = "rgba(0,0,0,0.06)"
        layout["font"] = dict(
            family="Plus Jakarta Sans, Manrope, sans-serif",
            color=light_font_color, size=12,
        )
        layout["legend"] = dict(bgcolor="rgba(0,0,0,0)", font=dict(color=light_title_color))
        layout["title"] = dict(font=dict(color=light_title_color, size=15, family="Manrope, sans-serif"))
        layout["xaxis"] = dict(gridcolor=light_grid, showgrid=True, color=light_font_color, zeroline=False)
        layout["yaxis"] = dict(gridcolor=light_grid, showgrid=True, color=light_font_color, zeroline=False)

    fig.update_layout(**layout)
    return fig


def _safe_col(df: pd.DataFrame, *candidates: str) -> str | None:
    """Return first column name that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    # fuzzy search
    for kw in candidates:
        for col in df.columns:
            if kw.lower() in col.lower():
                return col
    return None


# ─── 1. Revenue Trend (Area) ─────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_revenue_trend(df: pd.DataFrame) -> go.Figure:
    date_col   = _safe_col(df, "PurchaseDate", "date", "orderdate")
    amount_col = _safe_col(df, "TotalAmount", "amount", "revenue", "sales")

    if not date_col or not amount_col:
        return _empty_fig("Monthly Revenue Trend – data unavailable")

    tmp = df[[date_col, amount_col]].copy()
    tmp[date_col]   = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[amount_col] = pd.to_numeric(tmp[amount_col], errors="coerce")
    tmp = tmp.dropna()

    if tmp.empty:
        return _empty_fig("Monthly Revenue Trend – no valid data")

    monthly = tmp.groupby(pd.Grouper(key=date_col, freq="ME"))[amount_col].sum().reset_index()
    monthly.columns = ["Month", "Revenue"]

    fig = px.area(monthly, x="Month", y="Revenue",
                  title="<b>Monthly Revenue Trend</b>",
                  color_discrete_sequence=[CHART_COLORS[0]])
    fig.update_traces(
        fillcolor=f"rgba(99,102,241,0.15)",
        line=dict(color=CHART_COLORS[0], width=3),
    )
    return _apply(fig)


# ─── 2. Category Revenue (Donut) ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_category_revenue(df: pd.DataFrame) -> go.Figure:
    cat_col    = _safe_col(df, "Category", "category", "segment")
    amount_col = _safe_col(df, "TotalAmount", "amount", "revenue", "sales")

    if not cat_col or not amount_col:
        return _empty_fig("Revenue by Category – data unavailable")

    cat_df = df.groupby(cat_col)[amount_col].sum().reset_index()
    fig = px.pie(cat_df, names=cat_col, values=amount_col,
                 title="<b>Revenue by Category</b>",
                 hole=0.55,
                 color_discrete_sequence=CHART_COLORS)
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont=dict(color=PALETTE["text_primary"]))
    return _apply(fig)


# ─── 3. Top Products (H-Bar) ─────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_top_products(df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    prod_col   = _safe_col(df, "ProductName", "product", "item")
    amount_col = _safe_col(df, "TotalAmount", "amount", "revenue", "sales")

    if not prod_col or not amount_col:
        return _empty_fig("Top Products – data unavailable")

    top = (df.groupby(prod_col)[amount_col].sum()
             .reset_index()
             .sort_values(amount_col, ascending=True)
             .tail(top_n))

    fig = px.bar(top, y=prod_col, x=amount_col, orientation="h",
                 title=f"<b>Top {top_n} Products by Revenue</b>",
                 color_discrete_sequence=[CHART_COLORS[1]])
    fig.update_traces(marker_color=CHART_COLORS[1])
    return _apply(fig)


# ─── 4. Brand Performance (Bar) ──────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_brand_performance(df: pd.DataFrame) -> go.Figure:
    brand_col  = _safe_col(df, "Brand", "brand", "manufacturer")
    amount_col = _safe_col(df, "TotalAmount", "amount", "revenue", "sales")

    if not brand_col or not amount_col:
        return _empty_fig("Brand Performance – data unavailable")

    brand_df = (df.groupby(brand_col)[amount_col].sum()
                  .reset_index()
                  .sort_values(amount_col, ascending=False))

    fig = px.bar(brand_df, x=brand_col, y=amount_col,
                 title="<b>Brand Performance</b>",
                 color=amount_col,
                 color_continuous_scale=["#312E81", "#6366F1", "#A5B4FC"])
    fig.update_coloraxes(showscale=False)
    return _apply(fig)


# ─── 5. Region Sales (Bar) ───────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_region_sales(df: pd.DataFrame) -> go.Figure:
    region_col = _safe_col(df, "Region", "region", "state", "country", "location")
    amount_col = _safe_col(df, "TotalAmount", "amount", "revenue", "sales")

    if not region_col or not amount_col:
        return _empty_fig("Regional Sales – data unavailable")

    reg = (df.groupby(region_col)[amount_col].sum()
             .reset_index()
             .sort_values(amount_col, ascending=False))

    fig = px.bar(reg, x=region_col, y=amount_col,
                 title="<b>Sales by Region</b>",
                 color_discrete_sequence=[CHART_COLORS[2]])
    return _apply(fig)


# ─── 6. Customer Funnel ───────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_sales_funnel(df: pd.DataFrame) -> go.Figure:
    cust_col = _safe_col(df, "CustomerID", "customer")
    orders   = max(len(df), 1)
    customers = max(df[cust_col].nunique(), 1) if cust_col else orders
    repeat    = int((df.groupby(cust_col).size() > 1).sum()) if cust_col else 0

    fig = go.Figure(go.Funnel(
        y=["Completed Orders", "Unique Customers", "Repeat Customers"],
        x=[orders, customers, repeat],
        marker=dict(color=[CHART_COLORS[0], CHART_COLORS[1], CHART_COLORS[2]]),
        textinfo="value+percent initial",
        textfont=dict(color=PALETTE["text_primary"]),
    ))
    fig.update_layout(title="<b>Customer Conversion Funnel</b>")
    return _apply(fig)


# ─── 7. Customer Segment Scatter ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_segment_scatter(rfm_df: pd.DataFrame) -> go.Figure:
    if rfm_df.empty or "SegmentName" not in rfm_df.columns:
        return _empty_fig("Customer Segments – run model first")

    fig = px.scatter(
        rfm_df, x="RecencyDays", y="MonetaryValue",
        color="SegmentName", size="PurchaseFrequency",
        hover_data=["CustomerID"] if "CustomerID" in rfm_df.columns else None,
        title="<b>Customer Segments (RFM)</b>",
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=0.5, color="rgba(255,255,255,0.2)")))
    return _apply(fig)


# ─── 8. Forecast Chart (Combined Area) ───────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_forecast(combined_df: pd.DataFrame) -> go.Figure:
    if combined_df.empty:
        return _empty_fig("Revenue Forecast – no data")

    hist = combined_df[combined_df["Type"] == "Historical"]
    fore = combined_df[combined_df["Type"] == "Forecast"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["Month"], y=hist["Revenue"], name="Historical",
        mode="lines+markers",
        line=dict(color=CHART_COLORS[0], width=3),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.12)",
    ))
    fig.add_trace(go.Scatter(
        x=fore["Month"], y=fore["Revenue"], name="Forecast",
        mode="lines+markers",
        line=dict(color=CHART_COLORS[3], width=3, dash="dash"),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.10)",
    ))
    fig.update_layout(title="<b>Revenue Forecast (6 Months)</b>")
    return _apply(fig)


# ─── 9. Payment Method Distribution (Donut) ──────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_payment_methods(df: pd.DataFrame) -> go.Figure:
    pay_col    = _safe_col(df, "PaymentMethod", "payment")
    amount_col = _safe_col(df, "TotalAmount", "amount", "revenue")

    if not pay_col or not amount_col:
        return _empty_fig("Payment Methods – data unavailable")

    pay_df = df.groupby(pay_col)[amount_col].sum().reset_index()
    fig = px.pie(pay_df, names=pay_col, values=amount_col,
                 title="<b>Revenue by Payment Method</b>",
                 hole=0.5, color_discrete_sequence=CHART_COLORS)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


# ─── 10. Age Distribution (Histogram) ────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_age_distribution(df: pd.DataFrame) -> go.Figure:
    age_col = _safe_col(df, "CustomerAge", "age")
    if not age_col:
        return _empty_fig("Age Distribution – data unavailable")
    fig = px.histogram(df, x=age_col, nbins=20,
                       title="<b>Customer Age Distribution</b>",
                       color_discrete_sequence=[CHART_COLORS[4]])
    fig.update_traces(marker_line_color="rgba(0,0,0,0.2)", marker_line_width=0.5)
    return _apply(fig)


# ─── 11. Gender Split (Donut) ────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def plot_gender_split(df: pd.DataFrame) -> go.Figure:
    gen_col = _safe_col(df, "Gender", "sex")
    if not gen_col:
        return _empty_fig("Gender Distribution – data unavailable")
    gen_df = df[gen_col].value_counts().reset_index()
    gen_df.columns = ["Gender", "Count"]
    fig = px.pie(gen_df, names="Gender", values="Count",
                 title="<b>Customer Gender Distribution</b>",
                 hole=0.5, color_discrete_sequence=CHART_COLORS)
    return _apply(fig)


# ─── Empty Figure Placeholder ─────────────────────────────────────────────────

def _empty_fig(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=f"<b>{msg}</b>", font=dict(color=PALETTE["text_secondary"])),
        **{k: v for k, v in _BASE_LAYOUT.items() if k != "title"},
        annotations=[dict(text="No data available", showarrow=False,
                          font=dict(color=PALETTE["text_muted"], size=14),
                          xref="paper", yref="paper", x=0.5, y=0.5)],
    )
    return fig


# ─── Monthly KPI Delta ────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def monthly_kpi_delta(df: pd.DataFrame, metric: str) -> tuple[str, bool]:
    """Calculate month-over-month change for a key metric."""
    try:
        date_col   = _safe_col(df, "PurchaseDate", "date")
        amount_col = _safe_col(df, "TotalAmount", "amount", "revenue")
        cust_col   = _safe_col(df, "CustomerID", "customer")
        if not date_col:
            return "0.0%", True
        dates  = pd.to_datetime(df[date_col], errors="coerce")
        period = dates.dt.to_period("M")
        cur_p  = period.max()
        if pd.isna(cur_p):
            return "0.0%", True
        cur_rows  = df[period == cur_p]
        prev_rows = df[period == cur_p - 1]

        if metric == "revenue" and amount_col:
            cur, prev = cur_rows[amount_col].sum(), prev_rows[amount_col].sum()
        elif metric == "orders":
            cur, prev = len(cur_rows), len(prev_rows)
        elif metric == "customers" and cust_col:
            cur, prev = cur_rows[cust_col].nunique(), prev_rows[cust_col].nunique()
        elif metric == "basket" and amount_col:
            cur, prev = cur_rows[amount_col].mean(), prev_rows[amount_col].mean()
        else:
            return "0.0%", True

        if not prev or pd.isna(prev) or prev == 0:
            return "0.0%", True
        change = (cur - prev) / abs(prev) * 100
        return f"{abs(change):.1f}%", change >= 0
    except Exception:
        return "0.0%", True


# ─── AI Automated Insights Engine ────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def generate_ai_insights(df: pd.DataFrame) -> list[dict]:
    """
    Analyse the active dataset and return a list of AI insight dicts.
    Each dict: title, confidence, priority, description,
               recommended_action, impact.
    """
    if df.empty:
        return []

    insights: list[dict] = []

    try:
        # Column discovery
        amount_col = _safe_col(df, "TotalAmount", "amount", "revenue", "sales")
        cat_col    = _safe_col(df, "Category", "category", "segment")
        brand_col  = _safe_col(df, "Brand", "brand", "manufacturer")
        prod_col   = _safe_col(df, "ProductName", "product", "item")
        cust_col   = _safe_col(df, "CustomerID", "customer")

        if not amount_col:
            return []

        total_rev = float(df[amount_col].sum())

        # ── Insight 1: Top Category ──────────────────────────────────────────
        if cat_col:
            cat_rev = df.groupby(cat_col)[amount_col].sum().sort_values(ascending=False)
            if not cat_rev.empty:
                top_cat  = cat_rev.index[0]
                top_c_rev = float(cat_rev.iloc[0])
                share    = top_c_rev / max(total_rev, 1) * 100
                insights.append({
                    "title":             f"Top Revenue Category: {top_cat}",
                    "confidence":        round(min(99, 70 + share), 1),
                    "priority":          "High",
                    "description":       f"{top_cat} contributes {share:.1f}% of revenue (${top_c_rev:,.0f}).",
                    "recommended_action": f"Prioritise {top_cat} in campaigns and inventory allocation.",
                    "impact":            f"${top_c_rev:,.0f} contribution from current dataset.",
                })

        # ── Insight 2: Churn Alert ────────────────────────────────────────────
        if "ChurnStatus" in df.columns and cust_col:
            churn_rate  = float(df.groupby(cust_col)["ChurnStatus"].first().mean() * 100)
            repeat_rate = float((df.groupby(cust_col).size() > 1).mean() * 100) if cust_col else 0.0
            insights.append({
                "title":             "Churn Risk Alert",
                "confidence":        90.0,
                "priority":          "High",
                "description":       f"{churn_rate:.1f}% of customers show churn risk based on purchase recency.",
                "recommended_action": "Launch personalised re-engagement campaigns for at-risk customers.",
                "impact":            f"Current repeat-purchase rate: {repeat_rate:.1f}%.",
            })

        # ── Insight 3: Top Brand ──────────────────────────────────────────────
        if brand_col:
            brand_rev = df.groupby(brand_col)[amount_col].sum().sort_values(ascending=False)
            if not brand_rev.empty:
                top_brand  = brand_rev.index[0]
                top_b_rev  = float(brand_rev.iloc[0])
                b_share    = top_b_rev / max(total_rev, 1) * 100
                insights.append({
                    "title":             f"{top_brand} Leads Brand Revenue",
                    "confidence":        round(min(99, 70 + b_share), 1),
                    "priority":          "Medium",
                    "description":       f"{top_brand} generated ${top_b_rev:,.0f} ({b_share:.1f}% of total revenue).",
                    "recommended_action": f"Feature {top_brand} in loyalty programs and bundle offers.",
                    "impact":            f"Brand leads revenue in the current dataset.",
                })

        # ── Insight 4: Low-Volume Product ─────────────────────────────────────
        if prod_col:
            prod_sales = df.groupby(prod_col)[amount_col].sum().sort_values()
            if not prod_sales.empty:
                low_prod = prod_sales.index[0]
                low_rev  = float(prod_sales.iloc[0])
                insights.append({
                    "title":             f"Low-Performing Product: {low_prod}",
                    "confidence":        85.0,
                    "priority":          "Medium",
                    "description":       f"{low_prod} has the lowest revenue (${low_rev:,.0f}) in the active dataset.",
                    "recommended_action": "Review demand, pricing and visibility before replenishment.",
                    "impact":            "Identifies a product that may need a demand or assortment decision.",
                })

        # ── Insight 5: Top Revenue Product ───────────────────────────────────
        if prod_col:
            prod_top     = df.groupby(prod_col)[amount_col].sum().sort_values(ascending=False)
            top_prod     = prod_top.index[0]
            top_prod_rev = float(prod_top.iloc[0])
            tp_share     = top_prod_rev / max(total_rev, 1) * 100
            insights.append({
                "title":             f"Top Revenue Product: {top_prod}",
                "confidence":        round(min(99, 70 + tp_share), 1),
                "priority":          "Low",
                "description":       f"{top_prod} is the #1 revenue product at ${top_prod_rev:,.0f} ({tp_share:.1f}% share).",
                "recommended_action": "Use as anchor product for cross-sell and bundle recommendations.",
                "impact":            f"Highest individual product contribution in this dataset.",
            })

    except Exception as exc:
        LOGGER.warning("generate_ai_insights: %s", exc)

    return insights
