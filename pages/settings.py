"""
Customer Insights Platform – Settings Page
User profile preferences, theme toggle, account information.
"""

from __future__ import annotations

import streamlit as st
from database.db import log_activity


def render(current_user: dict) -> None:
    """Render the Settings & Profile page."""

    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">🔧 User Profile & Platform Settings</div>
      <div class="ip-card-sub">
        Update your display preferences and view account information.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("#### 👤 Account Information")
        with st.form("settings_form"):
            full_name = st.text_input("Full Name",     value=current_user.get("full_name", ""))
            email     = st.text_input("Email Address", value=current_user.get("email", ""), disabled=True)
            role      = st.text_input("Role",          value=current_user.get("role", ""),  disabled=True)

            current_theme = st.session_state.get("theme", "dark")
            theme_options = ["Dark Mode", "Light Mode"]
            theme_index   = 0 if current_theme == "dark" else 1
            theme_opt = st.selectbox("Display Theme", theme_options, index=theme_index)

            notifs    = st.toggle("Enable Email Notifications", value=False)
            submitted = st.form_submit_button("💾  Save Preferences", use_container_width=True)

        if submitted:
            # Apply theme change
            new_theme = "dark" if theme_opt == "Dark Mode" else "light"
            if new_theme != current_theme:
                st.session_state["theme"] = new_theme
            log_activity(current_user.get("username", ""), "SETTINGS_UPDATE", "User updated preferences")
            st.success("✅ Preferences saved successfully!")
            if new_theme != current_theme:
                st.rerun()

    with col2:
        st.markdown("#### 🔐 Account Security")
        st.markdown("""
        <div class="ip-card">
          <div class="ip-stat-row">
            <span class="ip-stat-label">Password</span>
            <span class="ip-stat-value">••••••••</span>
          </div>
          <div class="ip-stat-row">
            <span class="ip-stat-label">2FA</span>
            <span class="ip-stat-value" style="color:#F59E0B;">Not configured</span>
          </div>
          <div class="ip-stat-row">
            <span class="ip-stat-label">Session</span>
            <span class="ip-stat-value" style="color:#10B981;">Active</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📊 Platform Info")
        st.markdown("""
        <div class="ip-card">
          <div class="ip-stat-row">
            <span class="ip-stat-label">Platform</span>
            <span class="ip-stat-value">Customer Insights Platform</span>
          </div>
          <div class="ip-stat-row">
            <span class="ip-stat-label">Version</span>
            <span class="ip-stat-value">v3.0 Enterprise</span>
          </div>
          <div class="ip-stat-row">
            <span class="ip-stat-label">License</span>
            <span class="ip-stat-value" style="color:#6366F1;">Enterprise</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
