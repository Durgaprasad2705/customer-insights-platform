"""
Customer Insights Platform – Top Navigation Bar v5.1
Breadcrumb header with teal accent, role chip, live status dot,
and admin notification badge for pending login requests.
"""
from __future__ import annotations
import datetime
import streamlit as st
from config import COMPANY_NAME, PAGE_ICONS, ROLES
from database.db import get_pending_count

_BREADCRUMB = {
    "Dashboard":              "Overview",
    "Upload Dataset":         "Data",
    "Customer Profiles":      "Customers",
    "Customer Segmentation":  "Customers",
    "Product Analytics":      "Products",
    "Sales Analytics":        "Sales",
    "Inventory Analytics":    "Inventory",
    "Machine Learning":       "AI & ML",
    "Reports":                "Reports",
    "Admin Panel":            "System",
    "Settings":               "System",
}

_ROLE_COLORS = {
    "Admin":    ("#00D4A8", "0,212,168"),
    "Manager":  ("#22C55E", "34,197,94"),
    "Analyst":  ("#9B6DFF", "155,109,255"),
    "Customer": ("#F59E0B", "245,158,11"),
}
_ROLE_ICONS = {"Admin": "🛡️", "Manager": "👔", "Analyst": "📊", "Customer": "🛒"}


def _build_notif_html(role: str) -> str:
    """Build the notification bell HTML separately to avoid f-string nesting issues."""
    if role != "Admin":
        return '<div class="ip-notif-btn">🔔</div>'
    try:
        n = get_pending_count()
        if n:
            badge = (
                '<span style="position:absolute;top:-4px;right:-4px;'
                'background:#FF4D6A;color:#fff;'
                'font-size:0.55rem;font-weight:700;'
                'width:16px;height:16px;border-radius:50%;'
                'display:flex;align-items:center;justify-content:center;'
                "font-family:'Space Grotesk',sans-serif;"
                'border:2px solid var(--nx-surface, #09091A);'
                'box-shadow:0 0 8px rgba(255,77,106,0.6);">'
                + str(n) +
                '</span>'
            )
            return (
                '<div class="ip-notif-btn" '
                'title="' + str(n) + ' login request(s) awaiting approval" '
                'style="position:relative;cursor:pointer;">'
                '🔔' + badge + '</div>'
            )
        return '<div class="ip-notif-btn" title="No pending requests">🔔</div>'
    except Exception:
        return '<div class="ip-notif-btn">🔔</div>'


def render_topbar(page_title: str, user: dict) -> None:
    role       = user.get("role", "Admin")
    full_name  = user.get("full_name", user.get("username", "user"))
    today_str  = datetime.date.today().strftime("%b %d, %Y")
    icon       = PAGE_ICONS.get(page_title, "✦")
    breadcrumb = _BREADCRUMB.get(page_title, "Platform")

    r_hex, r_rgb = _ROLE_COLORS.get(role, ("#00D4A8", "0,212,168"))
    r_icon = _ROLE_ICONS.get(role, "👤")
    first  = full_name.split()[0] if full_name else "User"

    notif_html = _build_notif_html(role)

    html = (
        '<div class="ip-topbar">'
        '<div class="ip-topbar-left">'
        '<span class="ip-breadcrumb-root">' + COMPANY_NAME + "</span>"
        '<span class="ip-breadcrumb-sep">›</span>'
        '<span class="ip-breadcrumb-root">' + breadcrumb + "</span>"
        '<span class="ip-breadcrumb-sep">›</span>'
        '<span class="ip-page-title">' + icon + "  " + page_title + "</span>"
        "</div>"
        '<div class="ip-topbar-right">'
        + notif_html +
        '<span class="ip-badge">'
        '<span style="width:6px;height:6px;border-radius:50%;'
        "background:var(--nx-teal, #00D4A8);"
        "box-shadow:0 0 6px var(--nx-teal-glow, rgba(0,212,168,0.8));"
        "display:inline-block;flex-shrink:0;"
        'animation:status-pulse 2.5s ease-in-out infinite;"></span>'
        " " + today_str +
        "</span>"
        '<span class="ip-badge" style="'
        "background:rgba(" + r_rgb + ",0.08);"
        "border-color:rgba(" + r_rgb + ",0.3);"
        "color:" + r_hex + ";font-weight:700;"
        "box-shadow:0 0 12px rgba(" + r_rgb + ',0.12);">'
        + r_icon + "  " + first + " · " + role +
        "</span>"
        "</div>"
        "</div>"
        '<div class="ip-page-content">'
    )

    st.markdown(html, unsafe_allow_html=True)
