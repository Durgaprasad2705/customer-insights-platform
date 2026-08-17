"""
Customer Insights Platform – Customer Portal Page (Customer role only)
Personal purchase history, spend summary, and product recommendations.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.kpi_cards import section_title
from services.ml_service import generate_recommendations
from utils.formatters import fmt_currency


def render_portal(df, current_user: dict) -> None:
    """Render the Customer Portal page."""
    username = current_user.get("username", "")
    cust_id  = current_user.get("username", "").upper()

    st.markdown(f"""
    <div class="ip-card">
      <div class="ip-card-title">🏠 My Purchase Dashboard</div>
      <div class="ip-card-sub">
        Welcome back, {current_user.get('full_name', 'Customer')}!
        View your personal purchase history and spending insights.
      </div>
    </div>
    """, unsafe_allow_html=True)

    amt_col  = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)
    cust_col = next((c for c in ["CustomerID"] if c in df.columns), None)
    date_col = next((c for c in ["PurchaseDate", "Date"] if c in df.columns), None)

    # For demo purposes show aggregate stats
    if amt_col:
        k1, k2, k3 = st.columns(3)
        k1.metric("Platform Total Revenue", fmt_currency(df[amt_col].sum()))
        k2.metric("Total Orders",           f"{len(df):,}")
        if cust_col:
            k3.metric("Total Customers",    f"{df[cust_col].nunique():,}")

    st.info("ℹ️ Your personal transaction history will appear here once orders are linked to your account.")

    st.markdown(section_title("Recent Platform Transactions", "🛒"), unsafe_allow_html=True)
    show_cols = [c for c in [cust_col, date_col, "Category", "ProductName", amt_col]
                 if c and c in df.columns]
    if show_cols:
        st.dataframe(df[show_cols].head(10), use_container_width=True)


def render_my_profile(current_user: dict) -> None:
    """Render the My Profile page."""
    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">🪪 My Profile</div>
      <div class="ip-card-sub">Your account information. Contact support to make changes.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ip-card">
      <div class="ip-stat-row">
        <span class="ip-stat-label">Full Name</span>
        <span class="ip-stat-value">{current_user.get('full_name', '–')}</span>
      </div>
      <div class="ip-stat-row">
        <span class="ip-stat-label">Username</span>
        <span class="ip-stat-value">{current_user.get('username', '–')}</span>
      </div>
      <div class="ip-stat-row">
        <span class="ip-stat-label">Email</span>
        <span class="ip-stat-value">{current_user.get('email', '–')}</span>
      </div>
      <div class="ip-stat-row">
        <span class="ip-stat-label">Role</span>
        <span class="ip-stat-value">{current_user.get('role', '–')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_recommendations(df) -> None:
    """Render the Product Recommendations page."""
    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">💡 Product Recommendations</div>
      <div class="ip-card-sub">
        AI-powered product recommendations based on purchase co-occurrence and revenue velocity.
      </div>
    </div>
    """, unsafe_allow_html=True)

    cat_col = next((c for c in ["Category"] if c in df.columns), None)
    categories = ["All Categories"] + sorted(df[cat_col].dropna().unique().tolist()) if cat_col else ["All Categories"]

    selected_cat = st.selectbox("Filter by Category", categories, key="rec_cat")

    recs = generate_recommendations(df, category=selected_cat)
    if recs:
        rec_df = pd.DataFrame(recs)
        st.dataframe(rec_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recommendations available for the selected category.")


def render_support(current_user: dict) -> None:
    """Render the Support page."""
    from database.db import log_activity

    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">💬 Support Center</div>
      <div class="ip-card-sub">
        Submit a support request and our team will respond within 24 hours.
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("support_form", clear_on_submit=True):
        subject  = st.text_input("Subject")
        category = st.selectbox("Category", ["General Question", "Technical Issue", "Account Access", "Data Question", "Other"])
        priority = st.selectbox("Priority",  ["Low", "Medium", "High"])
        message  = st.text_area("Message", height=140)
        submitted = st.form_submit_button("📨  Submit Request", use_container_width=True)

    if submitted:
        if subject.strip() and message.strip():
            log_activity(
                current_user.get("username", "unknown"),
                "SUPPORT_REQUEST",
                f"[{priority}] {subject.strip()}"
            )
            st.success("✅ Your support request has been recorded. We'll be in touch soon!")
        else:
            st.warning("Please fill in both Subject and Message fields.")
