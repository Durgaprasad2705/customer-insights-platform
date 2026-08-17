"""
Settings and Environment Configuration for Customer Insights Platform.
Handles filesystem paths, branding, Google OAuth, and database settings.
"""

from __future__ import annotations

import os
from pathlib import Path

# ─── Branding Metadata ────────────────────────────────────────────────────────
APP_NAME: str = os.getenv("APP_NAME", "CUSTOMER INSIGHTS PLATFORM")
APP_SUBTITLE: str = os.getenv("APP_SUBTITLE", "AI-Powered Customer Intelligence Platform")
COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Apex Electronics Retail Inc.")
VERSION: str = os.getenv("APP_VERSION", "v3.0 Enterprise")
TAGLINE: str = os.getenv("TAGLINE", "Turn raw data into confident decisions.")

# ─── File System Layout ───────────────────────────────────────────────────────
BASE_DIR: str = str(Path(__file__).resolve().parent.parent)
ASSETS_DIR: str = os.path.join(BASE_DIR, "assets")
CSS_DIR: str = os.path.join(ASSETS_DIR, "css")
DATABASE_DIR: str = os.path.join(BASE_DIR, "database")
UPLOADS_DIR: str = os.path.join(BASE_DIR, "uploads")
EXPORTS_DIR: str = os.path.join(BASE_DIR, "exports")
MODELS_DIR: str = os.path.join(BASE_DIR, "models")
SAMPLE_DATA_DIR: str = os.path.join(BASE_DIR, "sample_data")

# Ensure required directories exist
for _directory in [DATABASE_DIR, UPLOADS_DIR, EXPORTS_DIR, MODELS_DIR, CSS_DIR, SAMPLE_DATA_DIR]:
    os.makedirs(_directory, exist_ok=True)

# ─── Database Path ────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", os.path.join(DATABASE_DIR, "insightpulse.db"))

# ─── Google OAuth Configuration ───────────────────────────────────────────────
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
