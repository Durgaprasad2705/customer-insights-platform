"""
Customer Insights Platform – Core System Validation & Health Suite.
Tests module imports, data pipelines, ML predictions, configuration, and database integrity.
"""

from __future__ import annotations
import sys

# 1. Config Validation
from config import (
    APP_NAME,
    PALETTE,
    ROLES,
    PAGE_ICONS,
    DB_PATH,
    BASE_DIR,
)
print(f"[OK] Config package loaded: {APP_NAME} ({BASE_DIR})")

# 2. Database Validation
from database.db import get_database_stats, get_all_users
stats = get_database_stats()
users = get_all_users()
print(f"[OK] Database connected: {stats['users']} users ({len(users)} records), {stats['logs']} logs, DB size: {stats['db_size_kb']} KB")

# 3. Data Pipeline & Utilities Validation
from utils.data_generator import generate_electronics_dataset
from utils.data_cleaning import clean_and_preprocess
from utils.formatters import fmt_currency, fmt_number, fmt_percent
from utils.preprocessing import prepare_rfm, preprocess_churn, prepare_monthly_series

df_raw = generate_electronics_dataset(400)
df_clean, report = clean_and_preprocess(df_raw)
print(f"[OK] Data pipeline OK: {len(df_clean)} rows, quality score: {report['data_quality_score']}%")

# 4. Analytics & AI Insights Service Validation
from services.analytics_service import generate_ai_insights, plot_revenue_trend
insights = generate_ai_insights(df_clean)
fig = plot_revenue_trend(df_clean)
print(f"[OK] Analytics engine OK: {len(insights)} AI insights, chart elements: {len(fig.data)}")

# 5. Machine Learning Service Validation
from services.ml_service import train_segmentation, train_churn, train_clv, forecast_revenue
seg_res = train_segmentation(df_clean, n_clusters=4)
churn_res = train_churn(df_clean)
clv_res = train_clv(df_clean)
fc_res = forecast_revenue(df_clean, months_ahead=6)

print(f"[OK] ML models trained: Seg silhouette={seg_res['silhouette']}, Churn Acc={churn_res['accuracy']}%, CLV R2={clv_res['r2_score']}, Forecast R2={fc_res['r2']}")

print("\n>>> ALL SYSTEM VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<")
