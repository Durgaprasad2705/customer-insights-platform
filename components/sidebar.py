"""
Customer Insights Platform – Sidebar Navigation v5.0 — Cosmic Aurora
Grouped navigation, teal glow active state, aurora role badges.
"""
from __future__ import annotations
import streamlit as st
from config import APP_NAME, ROLES, PAGE_ICONS
from database.db import log_activity
from services.filter_service import render_global_filters

_NAV_GROUPS = {
    "OVERVIEW":   ["Dashboard", "Upload Dataset"],
    "ANALYTICS":  [
        "Customer Profiles", "Customer Segmentation",
        "Product Analytics", "Sales Analytics",
        "Inventory Analytics", "Machine Learning", "Reports",
    ],
    "SYSTEM":     ["Admin Panel", "Settings"],
}

# Role: (color, glow_color, bg)
_ROLE_STYLES = {
    "Admin":    ("#00D4A8", "rgba(0,212,168,0.2)",  "rgba(0,212,168,0.1)"),
    "Manager":  ("#22C55E", "rgba(34,197,94,0.2)",  "rgba(34,197,94,0.1)"),
    "Analyst":  ("#9B6DFF", "rgba(155,109,255,0.2)","rgba(155,109,255,0.1)"),
    "Customer": ("#F59E0B", "rgba(245,158,11,0.2)", "rgba(245,158,11,0.1)"),
}
_ROLE_ICONS = {"Admin": "🛡️", "Manager": "👔", "Analyst": "📊", "Customer": "🛒"}


def _get_group(page: str) -> str:
    for grp, pages in _NAV_GROUPS.items():
        if page in pages:
            return grp
    return "OVERVIEW"


def render_sidebar(user: dict, df) -> tuple[str, any]:
    role      = user.get("role", "Admin")
    full_name = user.get("full_name", "User")
    email     = user.get("email", "")
    username  = user.get("username", "user")
    role_cfg  = ROLES.get(role, ROLES["Admin"])
    allowed   = role_cfg["pages"]

    r_color, r_glow, r_bg = _ROLE_STYLES.get(role, _ROLE_STYLES["Admin"])
    r_icon = _ROLE_ICONS.get(role, "👤")

    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────
        st.markdown(f"""
        <div class="ip-logo">
          <div class="ip-logo-icon">✦</div>
          <div class="ip-logo-text">
            <div class="ip-logo-title">Customer Insights Platform</div>
            <div class="ip-logo-sub">AI Intelligence</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── User Card ─────────────────────────────────────────────
        initials = "".join(w[0].upper() for w in full_name.split()[:2]) or "U"
        short_email = (email[:22] + "…") if len(email) > 24 else email

        st.markdown(f"""
        <div class="ip-user-card">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="position:relative;flex-shrink:0;">
              <div style="
                width:35px;height:35px;border-radius:50%;
                background:linear-gradient(135deg,{r_color},{r_glow.replace('0.2','0.9')});
                display:flex;align-items:center;justify-content:center;
                font-family:'Space Grotesk',sans-serif;
                font-size:12px;font-weight:700;color:#02020A;
                box-shadow:0 0 14px {r_glow};">
                {initials}
              </div>
              <div class="ip-status-dot" style="
                position:absolute;bottom:0;right:0;
                border:2px solid #09091A;"></div>
            </div>
            <div style="min-width:0;flex:1;">
              <div class="ip-user-name" style="
                overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {full_name}
              </div>
              <div class="ip-user-email" style="
                overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {short_email}
              </div>
            </div>
          </div>
          <div style="margin-top:8px;">
            <span style="
              display:inline-flex;align-items:center;gap:5px;
              padding:3px 9px;border-radius:9999px;
              background:{r_bg};
              border:1px solid {r_color}44;
              color:{r_color};font-size:0.65rem;font-weight:700;
              text-transform:uppercase;letter-spacing:0.06em;
              font-family:'Space Grotesk',sans-serif;">
              {r_icon} {role}
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Theme Toggle ─────────────────────────────────────────
        current_theme = st.session_state.get("theme", "dark")
        is_dark = current_theme == "dark"
        toggle_label = "☀️  Switch to Light Mode" if is_dark else "🌙  Switch to Dark Mode"
        next_theme = "light" if is_dark else "dark"

        if st.button(
            toggle_label,
            key="theme_toggle_btn",
            use_container_width=True,
        ):
            st.session_state["theme"] = next_theme
            st.rerun()

        # ── Build grouped, sorted nav list ────────────────────────
        group_order   = list(_NAV_GROUPS.keys())
        sorted_pages  = sorted(
            allowed,
            key=lambda p: (
                group_order.index(_get_group(p)),
                _NAV_GROUPS.get(_get_group(p), []).index(p)
                if p in _NAV_GROUPS.get(_get_group(p), []) else 99
            )
        )
        nav_labels    = [f"{PAGE_ICONS.get(p,'📄')}  {p}" for p in sorted_pages]
        label_to_page = dict(zip(nav_labels, sorted_pages))

        current = st.session_state.get("current_page", sorted_pages[0])
        if current not in sorted_pages:
            current = sorted_pages[0]

        # ── Grouped Button Navigation ─────────────────────────────
        group_headers = {
            "OVERVIEW":  ("📊", "Overview"),
            "ANALYTICS": ("📁", "Data Workspace"),
            "SYSTEM":    ("⚙️", "Operations"),
        }

        selected_page = current
        for grp in group_order:
            pages_in_grp = [p for p in sorted_pages if _get_group(p) == grp]
            if not pages_in_grp:
                continue

            icon, title = group_headers.get(grp, ("📁", grp.title()))
            
            st.markdown(f'<div class="nav-group-header">{icon} {title}</div>', unsafe_allow_html=True)
            
            for p in pages_in_grp:
                is_active = (p == current)
                btn_type  = "primary" if is_active else "secondary"
                label     = f"{PAGE_ICONS.get(p,'📄')}  {p}"
                
                if st.button(label, key=f"nav_btn_{p}", type=btn_type, use_container_width=True):
                    st.session_state["current_page"] = p
                    st.rerun()

        # ── Divider ───────────────────────────────────────────────
        st.markdown(
            '<div style="height:1px;background:var(--nx-border, rgba(255,255,255,0.05));margin:10px 8px;"></div>',
            unsafe_allow_html=True,
        )

        # ── Filters ───────────────────────────────────────────────
        filtered_df = render_global_filters(df)

        # ── Sign Out ──────────────────────────────────────────────
        st.markdown(
            '<div style="height:1px;background:rgba(255,255,255,0.05);margin:10px 8px;"></div>',
            unsafe_allow_html=True,
        )
        if st.button("⬡  Sign Out", use_container_width=True, key="signout_btn"):
            log_activity(username, "LOGOUT", "User signed out")
            st.session_state["authenticated"] = False
            st.session_state["user"]          = None
            st.rerun()

        # ── Footer ────────────────────────────────────────────────
        st.markdown(
            '<div style="text-align:center;color:var(--nx-text-4, #2D2D50);'
            'font-size:0.58rem;padding:10px 0 4px;letter-spacing:0.06em;'
            'font-family:DM Sans,sans-serif;">'
            'Customer Insights Platform v5.0 · Enterprise</div>',
            unsafe_allow_html=True,
        )

    return selected_page, filtered_df
