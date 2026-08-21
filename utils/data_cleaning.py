"""
Customer Insights Platform – Universal Dataset Cleaning & Column Standardisation Pipeline.

Supports any CSV / Excel upload with flexible column name detection.
Maps common aliases → canonical schema used throughout the platform.
Never raises KeyError on missing columns.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


# ─── Canonical Schema Aliases ────────────────────────────────────────────────
# Keys are canonical names; values are lower-case normalised aliases to match.

ALIASES: dict[str, tuple[str, ...]] = {
    "TransactionID":  ("transactionid", "transaction_id", "orderid", "order_id",
                       "invoice", "invoiceid", "invoiceno", "receiptid", "txnid"),
    "CustomerID":     ("customerid", "customer_id", "customer", "clientid", "client_id",
                       "memberid", "member_id", "userid", "user_id", "id", "cust_id",
                       "custid", "clientno", "cid"),
    "CustomerName":   ("customername", "customer_name", "name", "clientname",
                       "client_name", "fullname", "full_name"),
    "CustomerAge":    ("customerage", "customer_age", "age"),
    "Gender":         ("gender", "sex"),
    "Region":         ("region", "state", "country", "city", "location",
                       "market", "territory", "area", "zone"),
    "PurchaseDate":   ("purchasedate", "purchase_date", "date", "orderdate",
                       "order_date", "transactiondate", "transaction_date",
                       "invoicedate", "invoice_date", "saledate", "sale_date",
                       "datetime", "timestamp"),
    "Category":       ("category", "productcategory", "product_category",
                       "department", "segment", "type", "itemcategory"),
    "ProductName":    ("productname", "product_name", "product", "item",
                       "itemname", "item_name", "description", "productdesc",
                       "sku_name", "skuname"),
    "Brand":          ("brand", "manufacturer", "make", "vendor"),
    "UnitPrice":      ("unitprice", "unit_price", "price", "sellingprice",
                       "selling_price", "rate", "cost", "baseprice"),
    "Quantity":       ("quantity", "qty", "units", "unitssold", "units_sold",
                       "count", "orderqty"),
    "TotalAmount":    ("totalamount", "total_amount", "sales", "revenue",
                       "amount", "total", "orderamount", "order_amount",
                       "totalsales", "totalrevenue", "saleprice", "invoiceamount",
                       "income", "totalprice"),
    "ProfitMargin":   ("profitmargin", "profit_margin", "profit", "grossprofit",
                       "gross_profit", "margin"),
    "PaymentMethod":  ("paymentmethod", "payment_method", "payment",
                       "paymenttype", "payment_type", "paymentmode"),
    "CustomerRating": ("customerrating", "customer_rating", "rating",
                       "reviewscore", "review_score", "score", "stars"),
    "ChurnStatus":    ("churnstatus", "churn_status", "churn", "ischurned",
                       "is_churned", "churned"),
}

_REQUIRED = ("CustomerID", "PurchaseDate", "TotalAmount")


def _norm(name: Any) -> str:
    """Normalise column name: lower-case, strip non-alphanumerics."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _to_numeric(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True)
    cleaned = cleaned.replace("", np.nan)
    return pd.to_numeric(cleaned, errors="coerce")


def _map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Map raw DataFrame columns to canonical schema.
    Returns (result_df, mapping_dict).
    """
    raw_cols  = list(df.columns)
    norm_map  = {_norm(c): c for c in raw_cols}   # normalised → original name
    result    = df.copy()
    mapped: dict[str, str] = {}

    for canonical, aliases in ALIASES.items():
        if canonical in result.columns:
            # Already present under canonical name
            mapped[canonical] = canonical
            continue
        for alias in aliases:
            orig = norm_map.get(_norm(alias))
            if orig is not None:
                result[canonical] = df[orig]
                mapped[canonical] = orig
                break

    return result, mapped


def _fill_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """Fill optional columns with sensible defaults when absent."""
    defaults: dict[str, Any] = {
        "TransactionID":  [f"UPL-{i+1:06d}" for i in range(len(df))],
        "CustomerName":   df["CustomerID"].astype(str),
        "CustomerAge":    35,
        "Gender":         "Not specified",
        "Region":         "Unspecified",
        "Category":       "Uncategorized",
        "ProductName":    "Unspecified Product",
        "Brand":          "Unspecified",
        "UnitPrice":      df["TotalAmount"],
        "Quantity":       1,
        "ProfitMargin":   df["TotalAmount"] * 0.25,
        "PaymentMethod":  "Unspecified",
        "CustomerRating": 4.0,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
    return df


@st.cache_data(show_spinner=False)
def standardise_dataset(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Map flexible column names → canonical schema.
    Raises ValueError if the three required columns cannot be found.
    """
    if df_raw.empty:
        raise ValueError("The uploaded file has no data rows.")

    df, mapped = _map_columns(df_raw)

    # Validate required columns
    missing = [c for c in _REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(
            f"Cannot find required columns: {', '.join(missing)}. "
            "The dataset must include customer ID, purchase date, and sales amount."
        )

    # Type coercion for critical columns
    df["CustomerID"]  = df["CustomerID"].astype(str).str.strip()
    df["CustomerID"]  = df["CustomerID"].replace({"": np.nan, "nan": np.nan, "None": np.nan})
    df = df.dropna(subset=["CustomerID"]).copy()

    df["PurchaseDate"] = pd.to_datetime(df["PurchaseDate"], errors="coerce")
    df["TotalAmount"]  = _to_numeric(df["TotalAmount"])
    df = df.dropna(subset=["PurchaseDate", "TotalAmount"]).copy()

    if df.empty:
        raise ValueError("No valid rows remain after parsing dates and amounts.")

    # Numeric columns
    for col in ("UnitPrice", "Quantity", "ProfitMargin", "CustomerAge", "CustomerRating"):
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    df["Quantity"]       = df["Quantity"].fillna(1).clip(lower=1)
    df["UnitPrice"]      = df["UnitPrice"].fillna(df["TotalAmount"] / df["Quantity"])
    df["ProfitMargin"]   = df["ProfitMargin"].fillna(df["TotalAmount"] * 0.25)
    df["CustomerAge"]    = df["CustomerAge"].fillna(35).clip(18, 100)
    df["CustomerRating"] = df["CustomerRating"].fillna(4.0).clip(1.0, 5.0)

    # String columns
    str_cols = ("TransactionID", "CustomerName", "Gender", "Region",
                 "Category", "ProductName", "Brand", "PaymentMethod")
    for col in str_cols:
        if col in df.columns:
            df[col] = (df[col].fillna("Unspecified").astype(str)
                               .str.strip().replace("", "Unspecified"))

    df = _fill_defaults(df)
    return df, mapped


@st.cache_data(show_spinner=False)
def clean_and_preprocess(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Full cleaning + RFM augmentation pipeline.
    Returns (cleaned_df, quality_report_dict).
    """
    initial_rows, initial_cols = df_raw.shape

    df, mapped = standardise_dataset(df_raw)

    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    missing_imputed = int(df.isna().sum().sum())

    # RFM enrichment
    max_date = df["PurchaseDate"].max()
    rfm = (
        df.groupby("CustomerID", as_index=False)
        .agg(
            RecencyDays      = ("PurchaseDate",    lambda d: (max_date - d.max()).days),
            PurchaseFrequency= ("TransactionID",   "count"),
            MonetaryValue    = ("TotalAmount",     "sum"),
        )
    )
    rfm["ChurnStatus"] = (rfm["RecencyDays"] > 120).astype(int)

    # Drop pre-existing RFM cols to avoid duplication
    drop_cols = [c for c in ("RecencyDays", "PurchaseFrequency", "MonetaryValue", "ChurnStatus")
                 if c in df.columns]
    df = df.drop(columns=drop_cols, errors="ignore")
    df = df.merge(rfm, on="CustomerID", how="left")
    df = df.sort_values("PurchaseDate", ascending=False).reset_index(drop=True)

    # Outlier detection (non-capping, informational)
    outlier_summary: dict[str, int] = {}
    for col in ("TotalAmount", "UnitPrice", "Quantity", "ProfitMargin"):
        vals = pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce").dropna()
        if len(vals) >= 4:
            q1, q3 = vals.quantile([0.25, 0.75])
            iqr     = q3 - q1
            if iqr > 0:
                outlier_summary[col] = int(((vals < q1 - 1.5*iqr) | (vals > q3 + 1.5*iqr)).sum())

    quality_score = round(max(0.0, 100 - duplicates / max(initial_rows, 1) * 100), 1)

    report: dict[str, Any] = {
        "initial_rows":        initial_rows,
        "initial_cols":        initial_cols,
        "final_rows":          len(df),
        "final_cols":          len(df.columns),
        "duplicates_removed":  duplicates,
        "total_missing_imputed": missing_imputed,
        "mapped_columns":      mapped,
        "outlier_summary":     outlier_summary,
        "data_quality_score":  quality_score,
    }
    return df, report
