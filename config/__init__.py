"""
Configuration Package for Customer Insights Platform.
Re-exports settings and constants for backward compatibility and clean access.
"""

from __future__ import annotations

from config.settings import (
    APP_NAME,
    APP_SUBTITLE,
    COMPANY_NAME,
    VERSION,
    TAGLINE,
    BASE_DIR,
    ASSETS_DIR,
    CSS_DIR,
    DATABASE_DIR,
    UPLOADS_DIR,
    EXPORTS_DIR,
    MODELS_DIR,
    SAMPLE_DATA_DIR,
    DB_PATH,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)

from config.constants import (
    PALETTE,
    ELECTRONICS_CATEGORIES,
    ELECTRONICS_BRANDS,
    ELECTRONICS_REGIONS,
    ROLES,
    PAGE_ICONS,
)

__all__ = [
    "APP_NAME",
    "APP_SUBTITLE",
    "COMPANY_NAME",
    "VERSION",
    "TAGLINE",
    "BASE_DIR",
    "ASSETS_DIR",
    "CSS_DIR",
    "DATABASE_DIR",
    "UPLOADS_DIR",
    "EXPORTS_DIR",
    "MODELS_DIR",
    "SAMPLE_DATA_DIR",
    "DB_PATH",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    "PALETTE",
    "ELECTRONICS_CATEGORIES",
    "ELECTRONICS_BRANDS",
    "ELECTRONICS_REGIONS",
    "ROLES",
    "PAGE_ICONS",
]
