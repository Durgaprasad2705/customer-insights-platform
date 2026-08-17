"""
Customer Insights Platform – ML Feature Engineering & Preprocessing Helpers.

Provides RFM features, churn dataset preparation, and time-series resampling.
All functions are dataset-agnostic: they discover columns by name patterns.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, *keywords: str) -> str | None:
    """Return the first column whose lower-case name contains any keyword."""
    for kw in keywords:
        for col in df.columns:
            if kw in col.lower():
                return col
    return None


# ─── RFM Features ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def prepare_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract per-customer RFM (Recency, Frequency, Monetary) features.

    Works whether the dataframe already contains pre-computed RFM columns
    (from the cleaning pipeline) or raw transaction records.
    """
    if df.empty:
        raise ValueError("Dataset is empty; cannot compute RFM.")
    if "CustomerID" not in df.columns:
        raise ValueError("Dataset must contain a CustomerID column.")

    # Fast path: canonical RFM columns already present
    if {"RecencyDays", "PurchaseFrequency", "MonetaryValue"}.issubset(df.columns):
        agg: dict[str, str] = {
            "RecencyDays":       "first",
            "PurchaseFrequency": "first",
            "MonetaryValue":     "first",
        }
        if "CustomerAge" in df.columns:
            agg["CustomerAge"] = "first"
        rfm = df.groupby("CustomerID").agg(agg).reset_index()
        if "CustomerAge" not in rfm.columns:
            rfm["CustomerAge"] = 35
        return rfm

    # Slow path: compute from raw transactions
    date_col   = _find_col(df, "date", "time")
    amount_col = _find_col(df, "amount", "revenue", "sales", "price", "total")

    if not date_col or not amount_col:
        raise ValueError("Dataset must contain date and amount columns for RFM analysis.")

    tmp = df.copy()
    tmp[date_col]   = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[amount_col] = pd.to_numeric(tmp[amount_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col, amount_col])

    if tmp.empty:
        raise ValueError("No valid dated transactions available for RFM analysis.")

    max_date = tmp[date_col].max()
    rfm = tmp.groupby("CustomerID").agg(
        RecencyDays      = (date_col,   lambda d: (max_date - d.max()).days),
        PurchaseFrequency= ("CustomerID", "count"),
        MonetaryValue    = (amount_col,  "sum"),
    ).reset_index()
    rfm["CustomerAge"] = 35
    return rfm


# ─── Churn Preprocessing ──────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def preprocess_churn(df: pd.DataFrame):
    """
    Prepare features and labels for the churn classification model.

    Returns:
        X_train, X_test, y_train, y_test, feature_names, scaler, rfm_full
    """
    rfm = prepare_rfm(df)

    if len(rfm) < 8:
        raise ValueError("At least 8 unique customers are required for churn modelling.")

    # Merge customer rating if available
    if "CustomerRating" in df.columns:
        ratings = df.groupby("CustomerID")["CustomerRating"].mean().reset_index()
        rfm     = rfm.merge(ratings, on="CustomerID", how="left")
    else:
        rfm["CustomerRating"] = 4.0

    # Churn label
    if "ChurnStatus" in df.columns:
        churn_labels = df.groupby("CustomerID")["ChurnStatus"].first().reset_index()
        rfm          = rfm.merge(churn_labels, on="CustomerID", how="left")
    else:
        rfm["ChurnStatus"] = (rfm["RecencyDays"] > 90).astype(int)

    feature_cols = [c for c in
                    ["RecencyDays", "PurchaseFrequency", "MonetaryValue",
                     "CustomerAge", "CustomerRating"]
                    if c in rfm.columns]

    X = rfm[feature_cols].fillna(0)
    y = rfm["ChurnStatus"].fillna(0).astype(int)

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    class_counts = y.value_counts()
    stratify     = y if len(class_counts) > 1 and class_counts.min() >= 2 else None

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_scaled, y, test_size=0.25, random_state=42, stratify=stratify
    )
    return X_tr, X_te, y_tr, y_te, feature_cols, scaler, rfm


# ─── Monthly Time-Series ──────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def prepare_monthly_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample transaction data into a monthly revenue time series.
    Returns a DataFrame with columns [Month, Revenue].
    """
    date_col   = _find_col(df, "date", "time")
    amount_col = _find_col(df, "amount", "revenue", "sales", "price", "total")

    if not date_col or not amount_col:
        raise ValueError("Dataset must contain date and amount columns for forecasting.")

    tmp = df[[date_col, amount_col]].dropna()
    tmp[date_col]   = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[amount_col] = pd.to_numeric(tmp[amount_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col, amount_col])

    if tmp.empty:
        raise ValueError("No valid dated records available for time-series analysis.")

    tmp = tmp.set_index(date_col)
    monthly = tmp[amount_col].resample("MS").sum().reset_index()
    monthly.columns = ["Month", "Revenue"]
    return monthly.sort_values("Month").reset_index(drop=True)
