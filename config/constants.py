"""
Application Constants for Customer Insights Platform.
Includes color palettes, domain taxonomy, roles and permission maps, and page icons.
"""

from __future__ import annotations

# ─── Color Palette (Dark Glassmorphism SaaS) ─────────────────────────────────
PALETTE: dict[str, str | list[str]] = {
    # Backgrounds
    "bg_base":          "#ADA587",
    "bg_surface":       "#0F0F1A",
    "bg_card":          "rgba(255,255,255,0.04)",
    "bg_card_hover":    "rgba(255,255,255,0.07)",
    "bg_input":         "rgba(255,255,255,0.06)",

    # Brand Colors
    "primary":          "#6366F1",        # Indigo
    "primary_light":    "#818CF8",
    "primary_dark":     "#4F46E5",
    "secondary":        "#A855F7",        # Purple
    "accent":           "#06B6D4",        # Cyan
    "accent2":          "#10B981",        # Emerald

    # Status
    "success":          "#10B981",
    "warning":          "#F59E0B",
    "error":            "#EF4444",
    "info":             "#3B82F6",

    # Typography
    "text_primary":     "#F1F5F9",
    "text_secondary":   "#94A3B8",
    "text_muted":       "#475569",

    # Borders
    "border":           "rgba(255,255,255,0.08)",
    "border_accent":    "rgba(99,102,241,0.4)",

    # Chart Sequence
    "chart": [
        "#6366F1", "#A855F7", "#06B6D4", "#10B981",
        "#F59E0B", "#EF4444", "#EC4899", "#14B8A6"
    ],
}

# ─── Domain Taxonomies ────────────────────────────────────────────────────────
ELECTRONICS_CATEGORIES: list[str] = [
    "Laptops & Computers",
    "Smartphones & Accessories",
    "Televisions & Home Theater",
    "Headphones & Audio",
    "Smartwatches & Wearables",
    "Cameras & Photography",
    "Gaming Consoles & Gear",
    "Smart Home Devices",
]

ELECTRONICS_BRANDS: list[str] = [
    "Apple", "Samsung", "Sony", "Dell", "HP",
    "Lenovo", "LG", "Bose", "Asus", "Logitech", "Google",
]

ELECTRONICS_REGIONS: list[str] = [
    "North America", "Europe", "Asia Pacific",
    "Latin America", "Middle East & Africa",
]

# ─── Role Permissions & Navigation ───────────────────────────────────────────
ROLES: dict[str, dict] = {
    "Admin": {
        "description": "Full platform access including user management and system config.",
        "pages": [
            "Dashboard", "Upload Dataset", "Customer Profiles",
            "Customer Segmentation", "Product Analytics", "Sales Analytics",
            "Inventory Analytics", "Machine Learning", "Reports",
            "Admin Panel", "Settings",
        ],
        "color": "#6366F1",
        "icon": "🛡️",
        "theme": {
            "accent":           "#6366F1",
            "accent_light":     "#818CF8",
            "accent_dark":      "#4338CA",
            "sidebar_bg":       "rgba(99,102,241,0.08)",
            "sidebar_border":   "rgba(99,102,241,0.35)",
            "topbar_stripe":    "#6366F1",
            "nav_label":        "ADMIN TOOLS",
            "welcome_emoji":    "🛡️",
            "welcome_title":    "Admin Control Center",
            "welcome_desc":     "Full platform access — manage users, datasets, ML models, and system configuration.",
            "badge_bg":         "rgba(99,102,241,0.2)",
        },
    },
    "Analyst": {
        "description": "Access to datasets, analytics, ML predictions, and exportable reports.",
        "pages": [
            "Dashboard", "Upload Dataset", "Customer Profiles",
            "Customer Segmentation", "Product Analytics", "Sales Analytics",
            "Inventory Analytics", "Machine Learning", "Reports", "Settings",
        ],
        "color": "#06B6D4",
        "icon": "📊",
        "theme": {
            "accent":           "#06B6D4",
            "accent_light":     "#67E8F9",
            "accent_dark":      "#0891B2",
            "sidebar_bg":       "rgba(6,182,212,0.08)",
            "sidebar_border":   "rgba(6,182,212,0.35)",
            "topbar_stripe":    "#06B6D4",
            "nav_label":        "ANALYTICS",
            "welcome_emoji":    "📊",
            "welcome_title":    "Analytics Workspace",
            "welcome_desc":     "Your full analytics suite — explore data, run ML models, and generate exportable reports.",
            "badge_bg":         "rgba(6,182,212,0.2)",
        },
    },
    "Manager": {
        "description": "Executive dashboards, performance reports, and sales insights.",
        "pages": [
            "Dashboard", "Customer Profiles", "Product Analytics",
            "Sales Analytics", "Inventory Analytics", "Reports", "Settings",
        ],
        "color": "#10B981",
        "icon": "👔",
        "theme": {
            "accent":           "#10B981",
            "accent_light":     "#6EE7B7",
            "accent_dark":      "#059669",
            "sidebar_bg":       "rgba(16,185,129,0.08)",
            "sidebar_border":   "rgba(16,185,129,0.35)",
            "topbar_stripe":    "#10B981",
            "nav_label":        "EXECUTIVE",
            "welcome_emoji":    "👔",
            "welcome_title":    "Executive Dashboard",
            "welcome_desc":     "High-level business performance, revenue trends, and customer insights for decision-making.",
            "badge_bg":         "rgba(16,185,129,0.2)",
        },
    },
    "Customer": {
        "description": "Self-service customer portal with personalised dashboard.",
        "pages": [
            "Dashboard", "Settings",
        ],
        "color": "#F59E0B",
        "icon": "🛒",
        "theme": {
            "accent":           "#F59E0B",
            "accent_light":     "#FCD34D",
            "accent_dark":      "#D97706",
            "sidebar_bg":       "rgba(245,158,11,0.08)",
            "sidebar_border":   "rgba(245,158,11,0.35)",
            "topbar_stripe":    "#F59E0B",
            "nav_label":        "MY ACCOUNT",
            "welcome_emoji":    "🛒",
            "welcome_title":    "Customer Portal",
            "welcome_desc":     "View your personalised insights and account settings.",
            "badge_bg":         "rgba(245,158,11,0.2)",
        },
    },
}

# ─── Navigation Page Icons ───────────────────────────────────────────────────
PAGE_ICONS: dict[str, str] = {
    "Dashboard":            "⚡",
    "Upload Dataset":       "📤",
    "Customer Profiles":    "👤",
    "Customer Segmentation":"🎯",
    "Product Analytics":    "📦",
    "Sales Analytics":      "📈",
    "Inventory Analytics":  "🏬",
    "Machine Learning":     "🤖",
    "Reports":              "📄",
    "Admin Panel":          "⚙️",
    "Settings":             "🔧",
}
