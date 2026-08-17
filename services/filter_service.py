"""
Customer Insights Platform – Global Filter Service
Extracts sidebar dataset filters and applies them to any DataFrame.
Fully column-agnostic – detects available columns dynamically.

Performance: filter metadata (unique values, date ranges) is cached per
DataFrame so repeated reruns don't recompute expensive .unique() / .min()
/ .max() / pd.to_datetime() calls. The heavy df.copy() + filter operations
are skipped entirely when no filter is active.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def _safe_col(df: pd.DataFrame, *names: str) -> str | None:
    for n in names:
        if n in df.columns:
            return n
    return None


@st.cache_data(show_spinner=False)
def _filter_meta(df: pd.DataFrame) -> dict:
    """
    Compute all filter metadata for a given DataFrame exactly once.
    Cached per-DataFrame so repeated reruns never recompute this.
    """
    meta: dict = {}

    date_col   = _safe_col(df, "PurchaseDate", "OrderDate", "Date")
    amount_col = _safe_col(df, "TotalAmount", "Revenue", "Amount")
    region_col = _safe_col(df, "Region", "Location", "State", "Country")
    cat_col    = _safe_col(df, "Category", "Segment")
    brand_col  = _safe_col(df, "Brand", "Manufacturer")
    prod_col   = _safe_col(df, "ProductName", "Product", "Item")
    gender_col = _safe_col(df, "Gender", "Sex")
    pay_col    = _safe_col(df, "PaymentMethod", "Payment")
    age_col    = _safe_col(df, "CustomerAge", "Age")

    meta["date_col"]   = date_col
    meta["amount_col"] = amount_col
    meta["region_col"] = region_col
    meta["cat_col"]    = cat_col
    meta["brand_col"]  = brand_col
    meta["prod_col"]   = prod_col
    meta["gender_col"] = gender_col
    meta["pay_col"]    = pay_col
    meta["age_col"]    = age_col

    if date_col:
        parsed = pd.to_datetime(df[date_col], errors="coerce")
        meta["date_min"] = parsed.min().date()
        meta["date_max"] = parsed.max().date()
    else:
        meta["date_min"] = meta["date_max"] = None

    for key, col in [
        ("regions",    region_col),
        ("categories", cat_col),
        ("brands",     brand_col),
        ("products",   prod_col),
        ("genders",    gender_col),
        ("payments",   pay_col),
    ]:
        meta[key] = sorted(df[col].dropna().unique().tolist()) if col else []

    if age_col and not df[age_col].isna().all():
        meta["age_min"] = int(df[age_col].min())
        meta["age_max"] = int(df[age_col].max())
    else:
        meta["age_min"] = meta["age_max"] = None

    if amount_col and not df[amount_col].isna().all():
        meta["amt_min"] = float(df[amount_col].min())
        meta["amt_max"] = float(df[amount_col].max())
    else:
        meta["amt_min"] = meta["amt_max"] = None

    return meta


def render_global_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render sidebar filter widgets and return a filtered copy of df.
    Silently skips any filter whose column doesn't exist.
    """
    if df.empty:
        return df

    m = _filter_meta(df)

    with st.expander("🔍 Dataset Filters", expanded=False):

        # Date range filter
        if m["date_col"] and m["date_min"] and m["date_max"]:
            sel_dates = st.date_input(
                "Date range",
                value=(m["date_min"], m["date_max"]),
                min_value=m["date_min"],
                max_value=m["date_max"],
                key="gf_date",
            )
        else:
            sel_dates = None

        # Categorical multi-selects
        sel_regions    = st.multiselect("Region",         m["regions"],    key="gf_region")
        sel_categories = st.multiselect("Category",       m["categories"], key="gf_cat")
        sel_brands     = st.multiselect("Brand",          m["brands"],     key="gf_brand")
        sel_products   = st.multiselect("Product",        m["products"],   key="gf_prod")
        sel_genders    = st.multiselect("Gender",         m["genders"],    key="gf_gender")
        sel_payments   = st.multiselect("Payment Method", m["payments"],   key="gf_pay")

        # Numeric sliders
        if m["age_min"] is not None and m["age_min"] < m["age_max"]:
            sel_age = st.slider(
                "Age range", m["age_min"], m["age_max"],
                (m["age_min"], m["age_max"]), key="gf_age",
            )
        else:
            sel_age = None

        if m["amt_min"] is not None and m["amt_min"] < m["amt_max"]:
            sel_amount = st.slider(
                "Order amount", m["amt_min"], m["amt_max"],
                (m["amt_min"], m["amt_max"]), key="gf_amount", format="$%.0f",
            )
        else:
            sel_amount = None

    # ─── Short-circuit: if nothing is filtered, return the original df ─────────
    active_date = (
        sel_dates is not None
        and isinstance(sel_dates, (list, tuple))
        and len(sel_dates) == 2
        and (sel_dates[0] != m["date_min"] or sel_dates[1] != m["date_max"])
    )
    active_cats = any([sel_regions, sel_categories, sel_brands,
                       sel_products, sel_genders, sel_payments])
    active_age  = sel_age   is not None and (sel_age[0]    != m["age_min"] or sel_age[1]    != m["age_max"])
    active_amt  = sel_amount is not None and (sel_amount[0] != m["amt_min"] or sel_amount[1] != m["amt_max"])

    if not (active_date or active_cats or active_age or active_amt):
        return df  # nothing changed — skip all pandas work

    # ─── Apply only active filters ─────────────────────────────────────────────
    filtered = df.copy()

    if active_date and m["date_col"]:
        if isinstance(sel_dates, (list, tuple)) and len(sel_dates) == 2:
            d0, d1 = sel_dates[0], sel_dates[1]
        else:
            d0 = d1 = sel_dates
        parsed = pd.to_datetime(filtered[m["date_col"]], errors="coerce").dt.date
        filtered = filtered[parsed.between(d0, d1)]

    for col, sel in [
        (m["region_col"],  sel_regions),
        (m["cat_col"],     sel_categories),
        (m["brand_col"],   sel_brands),
        (m["prod_col"],    sel_products),
        (m["gender_col"],  sel_genders),
        (m["pay_col"],     sel_payments),
    ]:
        if col and sel:
            filtered = filtered[filtered[col].isin(sel)]

    if active_age and m["age_col"]:
        filtered = filtered[
            pd.to_numeric(filtered[m["age_col"]], errors="coerce").between(sel_age[0], sel_age[1])
        ]

    if active_amt and m["amount_col"]:
        filtered = filtered[
            pd.to_numeric(filtered[m["amount_col"]], errors="coerce").between(sel_amount[0], sel_amount[1])
        ]

    return filtered
