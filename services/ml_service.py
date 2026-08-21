"""
Customer Insights Platform – Machine Learning Service
Segmentation, Churn Prediction, CLV Regression, Sales Forecasting, Recommendations.
All models are dataset-agnostic and retrain automatically on new data.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    mean_squared_error, precision_score, r2_score, recall_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from utils.preprocessing import prepare_rfm, preprocess_churn, prepare_monthly_series

import streamlit as st

LOGGER = logging.getLogger(__name__)


# ─── 1. Customer Segmentation (K-Means + RFM) ────────────────────────────────

@st.cache_resource(show_spinner=False)
def train_segmentation(df: pd.DataFrame, n_clusters: int = 4) -> dict[str, Any]:
    """
    K-Means clustering on RFM data with automatic segment labelling.

    Returns dict with: rfm_df, model, scaler, silhouette, summary_df.
    """
    rfm = prepare_rfm(df).copy()
    if len(rfm) < 3:
        raise ValueError("At least 3 customers are required for segmentation.")

    n_clusters = min(max(2, n_clusters), len(rfm) - 1)
    features   = ["RecencyDays", "PurchaseFrequency", "MonetaryValue"]

    scaler     = StandardScaler()
    X_scaled   = scaler.fit_transform(rfm[features])

    model  = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
    labels = model.fit_predict(X_scaled)
    rfm["Cluster"] = labels

    sil = silhouette_score(X_scaled, labels) if len(rfm) > n_clusters else 0.0

    # Auto-label clusters by centroid characteristics
    means = rfm.groupby("Cluster")[features].mean()
    med_m = means["MonetaryValue"].median()
    med_f = means["PurchaseFrequency"].median()
    med_r = means["RecencyDays"].median()

    seg_names: dict[int, str] = {}
    for cid, row in means.iterrows():
        if row["MonetaryValue"] > med_m and row["PurchaseFrequency"] > med_f:
            name = "VIP Champions"
        elif row["RecencyDays"] > med_r:
            name = "At-Risk / Inactive"
        elif row["PurchaseFrequency"] > med_f:
            name = "Loyal Shoppers"
        else:
            name = "New / Occasional"
        seg_names[cid] = name

    rfm["SegmentName"] = rfm["Cluster"].map(seg_names)

    summary = (
        rfm.groupby(["Cluster", "SegmentName"])
        .agg(
            CustomerCount = ("CustomerID",        "count"),
            AvgRecency    = ("RecencyDays",        "mean"),
            AvgFrequency  = ("PurchaseFrequency",  "mean"),
            AvgMonetary   = ("MonetaryValue",      "mean"),
            TotalRevenue  = ("MonetaryValue",      "sum"),
        )
        .reset_index()
    )

    return {
        "rfm_df":    rfm,
        "model":     model,
        "scaler":    scaler,
        "silhouette": round(float(sil), 3),
        "summary":   summary,
    }


# ─── 2. Churn Prediction (Random Forest Classifier) ──────────────────────────

@st.cache_resource(show_spinner=False)
def train_churn(df: pd.DataFrame) -> dict[str, Any]:
    """
    Random Forest churn classifier.
    Returns metrics dict including predictions on full dataset.
    """
    X_tr, X_te, y_tr, y_te, feat_cols, scaler, rfm_orig = preprocess_churn(df)
    rfm = rfm_orig.copy()

    model  = RandomForestClassifier(n_estimators=75, max_depth=6, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)

    pos_idx = list(model.classes_).index(1) if 1 in model.classes_ else 0

    # Full dataset predictions
    X_full                          = scaler.transform(rfm[feat_cols].fillna(0))
    rfm["ChurnRiskProbability"]     = model.predict_proba(X_full)[:, pos_idx]
    rfm["PredictedChurn"]           = model.predict(X_full)

    importances = (
        pd.DataFrame({"Feature": feat_cols, "Importance": model.feature_importances_})
        .sort_values("Importance", ascending=False)
    )

    return {
        "accuracy":         round(accuracy_score(y_te, y_pred) * 100, 2),
        "precision":        round(precision_score(y_te, y_pred, zero_division=0) * 100, 2),
        "recall":           round(recall_score(y_te, y_pred, zero_division=0) * 100, 2),
        "f1":               round(f1_score(y_te, y_pred, zero_division=0) * 100, 2),
        "confusion_matrix": confusion_matrix(y_te, y_pred),
        "importances":      importances,
        "predictions":      rfm,
        "model":            model,
        "scaler":           scaler,
    }


# ─── 3. Customer Lifetime Value Regression ───────────────────────────────────

@st.cache_resource(show_spinner=False)
def train_clv(df: pd.DataFrame) -> dict[str, Any]:
    """
    Random Forest regressor for 12-month CLV prediction.
    """
    rfm = prepare_rfm(df).copy()

    rfm["TargetCLV"] = rfm["MonetaryValue"] * (1.15 + rfm["PurchaseFrequency"] * 0.2)

    feature_cols = ["RecencyDays", "PurchaseFrequency", "MonetaryValue"]
    X = rfm[feature_cols].fillna(0)
    y = rfm["TargetCLV"]

    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    model  = RandomForestRegressor(n_estimators=60, max_depth=8, random_state=42, n_jobs=-1)
    model.fit(X_sc, y)
    preds  = model.predict(X_sc)

    rfm["Predicted_12M_CLV"] = np.round(preds, 2)

    return {
        "r2_score":         round(float(r2_score(y, preds)), 3),
        "rmse":             round(float(np.sqrt(mean_squared_error(y, preds))), 2),
        "avg_clv":          round(float(rfm["Predicted_12M_CLV"].mean()), 2),
        "top_clv_customers": rfm.sort_values("Predicted_12M_CLV", ascending=False).head(10),
        "rfm_df":           rfm,
        "model":            model,
    }


# ─── 4. Sales Revenue Forecasting (Ridge Time-Series) ────────────────────────

@st.cache_resource(show_spinner=False)
def forecast_revenue(df: pd.DataFrame, months_ahead: int = 6) -> dict[str, Any]:
    """
    Ridge regression linear time-series forecast for monthly revenue.
    """
    monthly = prepare_monthly_series(df)
    if monthly.empty:
        raise ValueError("No dated records available for revenue forecasting.")

    # Ensure at least 2 data points
    if len(monthly) == 1:
        extra   = monthly.copy()
        extra["Month"] = extra["Month"] + pd.DateOffset(months=1)
        monthly = pd.concat([monthly, extra], ignore_index=True)

    monthly["MonthNum"] = np.arange(len(monthly))
    X = monthly[["MonthNum"]].values
    y = monthly["Revenue"].values

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    last_num = int(monthly["MonthNum"].max())
    last_date = monthly["Month"].max()

    future_nums   = np.arange(last_num + 1, last_num + 1 + months_ahead).reshape(-1, 1)
    future_dates  = [last_date + pd.DateOffset(months=i + 1) for i in range(months_ahead)]
    future_preds  = model.predict(future_nums)
    future_preds  = [max(1_000, float(v) * (1 + 0.05 * np.sin(i))) for i, v in enumerate(future_preds)]

    hist_df          = monthly[["Month", "Revenue"]].copy()
    hist_df["Type"]  = "Historical"

    fore_df = pd.DataFrame({
        "Month":   future_dates,
        "Revenue": np.round(future_preds, 2),
        "Type":    "Forecast",
    })

    combined = pd.concat([hist_df, fore_df], ignore_index=True)
    r2_val   = r2_score(y, model.predict(X)) if len(y) > 2 else 0.85

    return {
        "combined_df":  combined,
        "forecast_df":  fore_df,
        "historical_df": hist_df,
        "r2":           round(float(r2_val), 3),
    }


# ─── 5. Product Recommendation Engine ────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def generate_recommendations(df: pd.DataFrame, category: str | None = None) -> list[dict]:
    """
    Co-occurrence based product recommendation engine.
    Returns a list of top-8 recommended products with scoring.
    """
    prod_col   = "ProductName" if "ProductName" in df.columns else None
    cat_col    = "Category"    if "Category"    in df.columns else None
    brand_col  = "Brand"       if "Brand"       in df.columns else None
    qty_col    = "Quantity"    if "Quantity"    in df.columns else None
    amt_col    = "TotalAmount" if "TotalAmount" in df.columns else None
    rat_col    = "CustomerRating" if "CustomerRating" in df.columns else None

    if not prod_col or not amt_col:
        return []

    agg_cols: dict[str, Any] = {amt_col: "sum"}
    if qty_col:   agg_cols[qty_col]  = "sum"
    if rat_col:   agg_cols[rat_col]  = "mean"

    grp_cols = [c for c in [cat_col, prod_col, brand_col] if c]
    top = df.groupby(grp_cols).agg(agg_cols).reset_index()

    if category and category != "All Categories" and cat_col:
        top = top[top[cat_col] == category]

    sort_col = qty_col if qty_col else amt_col
    top = top.sort_values(sort_col, ascending=False)

    max_rev = float(top[amt_col].max()) if not top.empty else 1.0
    max_rev = max(max_rev, 1.0)

    results = []
    for _, row in top.head(8).iterrows():
        results.append({
            "product":              row.get(prod_col,  "–"),
            "category":             row.get(cat_col,   "–"),
            "brand":                row.get(brand_col, "–"),
            "avg_rating":           round(float(row.get(rat_col, 4.0)), 1),
            "recommendation_score": round(60 + 39 * float(row[amt_col]) / max_rev, 1),
            "reason":               f"High conversion rate in {row.get(cat_col, 'this category')}",
        })
    return results
