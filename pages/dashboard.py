"""
Customer Insights Platform – Executive Dashboard Page
Role-tailored rendering:
  Admin   → Full dashboard + system health quick-links
  Analyst → Full dashboard + data-quality indicator
  Manager → Executive view: KPIs + revenue/region/product charts only
  Customer→ Personalised welcome (no business KPIs leaked)
"""

from __future__ import annotations

import streamlit as st

from components.kpi_cards import kpi_card, insight_card, section_title
from config import ROLES
from services.analytics_service import (
    generate_ai_insights, monthly_kpi_delta,
    plot_revenue_trend, plot_category_revenue,
    plot_brand_performance, plot_sales_funnel,
    plot_region_sales, plot_top_products,
)
from utils.formatters import fmt_currency, fmt_number, fmt_percent


def _welcome_hero(role: str) -> None:
    """Render a role-specific welcome hero card — Cosmic Aurora v5."""
    theme = ROLES.get(role, ROLES["Admin"]).get("theme", {})
    emoji = theme.get("welcome_emoji", "✦")
    title = theme.get("welcome_title", "Dashboard")
    desc  = theme.get("welcome_desc",  "")

    # Cosmic Aurora role accents
    role_accents = {
        "Admin":    ("#00D4A8", "rgba(0,212,168,0.07)"),
        "Manager":  ("#22C55E", "rgba(34,197,94,0.07)"),
        "Analyst":  ("#9B6DFF", "rgba(155,109,255,0.07)"),
        "Customer": ("#FFAD00", "rgba(255,173,0,0.07)"),
    }
    accent, accent_bg = role_accents.get(role, ("#00D4A8", "rgba(0,212,168,0.07)"))

    st.markdown(f"""
    <div class="ip-welcome-hero" style="
        background:{accent_bg};
        border-color:rgba(255,255,255,0.06);
        border-left:2px solid {accent};">
      <div style="position:relative;z-index:1;">
        <div class="ip-welcome-title">{emoji}  {title}</div>
        <div class="ip-welcome-sub">{desc}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _compute_kpis(df) -> dict:
    amt_col  = next((c for c in ["TotalAmount", "Revenue", "Amount", "Sales"] if c in df.columns), None)
    cust_col = next((c for c in ["CustomerID"] if c in df.columns), None)
    profit_col = next((c for c in ["ProfitMargin", "Profit"] if c in df.columns), None)

    total_rev    = float(df[amt_col].sum())   if amt_col   else 0.0
    total_orders = len(df)
    unique_custs = df[cust_col].nunique()     if cust_col  else 0
    avg_order    = float(df[amt_col].mean())  if amt_col   else 0.0
    total_profit = float(df[profit_col].sum()) if profit_col else 0.0

    rev_delta,  rev_pos  = monthly_kpi_delta(df, "revenue")
    ord_delta,  ord_pos  = monthly_kpi_delta(df, "orders")
    cust_delta, cust_pos = monthly_kpi_delta(df, "customers")
    bask_delta, bask_pos = monthly_kpi_delta(df, "basket")

    return {
        "total_rev": total_rev,
        "total_orders": total_orders,
        "unique_custs": unique_custs,
        "avg_order": avg_order,
        "total_profit": total_profit,
        "rev_delta": rev_delta, "rev_pos": rev_pos,
        "ord_delta": ord_delta, "ord_pos": ord_pos,
        "cust_delta": cust_delta, "cust_pos": cust_pos,
        "bask_delta": bask_delta, "bask_pos": bask_pos,
    }


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

def _render_admin(df) -> None:
    """Full platform dashboard + system-health metrics for Admin."""
    _welcome_hero("Admin")

    kpis = _compute_kpis(df)

    # KPI row
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.markdown(kpi_card("Total Revenue",    fmt_currency(kpis["total_rev"]),    kpis["rev_delta"],  kpis["rev_pos"],  "revenue"),  unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Total Orders",     fmt_number(kpis["total_orders"]),   kpis["ord_delta"],  kpis["ord_pos"],  "orders"),   unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Active Customers", fmt_number(kpis["unique_custs"]),   kpis["cust_delta"], kpis["cust_pos"], "customers"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Avg Order Value",  fmt_currency(kpis["avg_order"]),    kpis["bask_delta"], kpis["bask_pos"], "basket"),   unsafe_allow_html=True)

    # Data-quality / admin system banner
    report = st.session_state.get("cleaning_report", {})
    if report:
        q = report.get("data_quality_score", 100)
        q_color = "#10B981" if q >= 90 else ("#F59E0B" if q >= 70 else "#EF4444")
        st.markdown(f"""
        <div style="display:flex;gap:12px;margin:8px 0 14px 0;flex-wrap:wrap;">
          <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
               border-radius:10px;padding:8px 16px;font-size:0.82rem;color:var(--nx-text-2, #94A3B8);">
            🗄️ <strong style="color:var(--nx-text-1, #F1F5F9);">{report.get('final_rows',len(df)):,}</strong> clean rows loaded
          </div>
          <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
               border-radius:10px;padding:8px 16px;font-size:0.82rem;color:var(--nx-text-2, #94A3B8);">
            🔬 Data Quality: <strong style="color:{q_color};">{q}%</strong>
          </div>
          <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
               border-radius:10px;padding:8px 16px;font-size:0.82rem;color:var(--nx-text-2, #94A3B8);">
            🧹 <strong style="color:var(--nx-text-1, #F1F5F9);">{report.get('duplicates_removed',0):,}</strong> duplicates removed
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Charts: full set
    col_a, col_b = st.columns([1.65, 1], gap="small")
    with col_a:
        st.plotly_chart(plot_revenue_trend(df),    use_container_width=True)
    with col_b:
        st.plotly_chart(plot_category_revenue(df), use_container_width=True)

    col_c, col_d = st.columns(2, gap="small")
    with col_c:
        st.plotly_chart(plot_brand_performance(df), use_container_width=True)
    with col_d:
        st.plotly_chart(plot_sales_funnel(df),      use_container_width=True)

    # AI Insights
    st.markdown(section_title("AI Automated Insights & Recommendations", "🤖"), unsafe_allow_html=True)
    insights = generate_ai_insights(df)
    if insights:
        for item in insights:
            st.markdown(insight_card(
                title=item["title"], description=item["description"],
                action=item["recommended_action"], impact=item["impact"],
                priority=item["priority"], confidence=item["confidence"],
            ), unsafe_allow_html=True)
    else:
        st.info("No AI insights available for the current dataset selection.")

    col_e, col_f = st.columns(2, gap="small")
    with col_e:
        st.plotly_chart(plot_region_sales(df),       use_container_width=True)
    with col_f:
        st.plotly_chart(plot_top_products(df, top_n=6), use_container_width=True)

    # Admin quick-links
    st.markdown(section_title("Admin Quick Actions", "⚙️"), unsafe_allow_html=True)
    qa1, qa2, qa3 = st.columns(3, gap="small")
    with qa1:
        st.markdown("""
        <div class="ip-card" style="text-align:center;cursor:pointer;">
          <div style="font-size:2rem;">👥</div>
          <div style="font-weight:700;color:var(--nx-text-1, #F1F5F9);margin-top:6px;">User Management</div>
          <div style="font-size:0.8rem;color:var(--nx-text-2, #94A3B8);">Go to Admin Panel → Users</div>
        </div>""", unsafe_allow_html=True)
    with qa2:
        st.markdown("""
        <div class="ip-card" style="text-align:center;cursor:pointer;">
          <div style="font-size:2rem;">📤</div>
          <div style="font-weight:700;color:var(--nx-text-1, #F1F5F9);margin-top:6px;">Upload New Dataset</div>
          <div style="font-size:0.8rem;color:var(--nx-text-2, #94A3B8);">Go to Upload Dataset</div>
        </div>""", unsafe_allow_html=True)
    with qa3:
        st.markdown("""
        <div class="ip-card" style="text-align:center;cursor:pointer;">
          <div style="font-size:2rem;">🤖</div>
          <div style="font-weight:700;color:var(--nx-text-1, #F1F5F9);margin-top:6px;">Run ML Models</div>
          <div style="font-size:0.8rem;color:var(--nx-text-2, #94A3B8);">Go to Machine Learning</div>
        </div>""", unsafe_allow_html=True)


# ─── Analyst Dashboard ────────────────────────────────────────────────────────

def _render_analyst(df) -> None:
    """Full analytics dashboard + data-quality badge for Analyst."""
    _welcome_hero("Analyst")

    kpis = _compute_kpis(df)

    # Data quality indicator
    report = st.session_state.get("cleaning_report", {})
    if report:
        q = report.get("data_quality_score", 100)
        q_color = "#10B981" if q >= 90 else ("#F59E0B" if q >= 70 else "#EF4444")
        st.markdown(f"""
        <div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.3);
             border-radius:10px;padding:10px 16px;margin-bottom:14px;
             display:flex;gap:20px;flex-wrap:wrap;align-items:center;">
          <span style="color:#67E8F9;font-weight:700;font-size:0.84rem;">📊 DATASET STATUS</span>
          <span style="color:var(--nx-text-2, #94A3B8);font-size:0.82rem;">
            <strong style="color:var(--nx-text-1, #F1F5F9);">{report.get('final_rows', len(df)):,}</strong> rows ·
            <strong style="color:var(--nx-text-1, #F1F5F9);">{report.get('final_cols', len(df.columns))}</strong> columns ·
            Quality: <strong style="color:{q_color};">{q}%</strong> ·
            Duplicates removed: <strong style="color:var(--nx-text-1, #F1F5F9);">{report.get('duplicates_removed',0):,}</strong>
          </span>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.markdown(kpi_card("Total Revenue",    fmt_currency(kpis["total_rev"]),    kpis["rev_delta"],  kpis["rev_pos"],  "revenue"),   unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Total Orders",     fmt_number(kpis["total_orders"]),   kpis["ord_delta"],  kpis["ord_pos"],  "orders"),    unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Active Customers", fmt_number(kpis["unique_custs"]),   kpis["cust_delta"], kpis["cust_pos"], "customers"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Avg Order Value",  fmt_currency(kpis["avg_order"]),    kpis["bask_delta"], kpis["bask_pos"], "basket"),    unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1.65, 1], gap="small")
    with col_a:
        st.plotly_chart(plot_revenue_trend(df),    use_container_width=True)
    with col_b:
        st.plotly_chart(plot_category_revenue(df), use_container_width=True)

    col_c, col_d = st.columns(2, gap="small")
    with col_c:
        st.plotly_chart(plot_brand_performance(df), use_container_width=True)
    with col_d:
        st.plotly_chart(plot_sales_funnel(df),      use_container_width=True)

    st.markdown(section_title("AI Automated Insights & Recommendations", "🤖"), unsafe_allow_html=True)
    insights = generate_ai_insights(df)
    if insights:
        for item in insights:
            st.markdown(insight_card(
                title=item["title"], description=item["description"],
                action=item["recommended_action"], impact=item["impact"],
                priority=item["priority"], confidence=item["confidence"],
            ), unsafe_allow_html=True)
    else:
        st.info("No AI insights available for the current dataset selection.")

    col_e, col_f = st.columns(2, gap="small")
    with col_e:
        st.plotly_chart(plot_region_sales(df),          use_container_width=True)
    with col_f:
        st.plotly_chart(plot_top_products(df, top_n=6), use_container_width=True)


# ─── Manager Dashboard ────────────────────────────────────────────────────────

def _render_manager(df) -> None:
    """Executive view: KPIs, revenue, region, top products — no ML/upload clutter."""
    _welcome_hero("Manager")

    kpis = _compute_kpis(df)

    # Executive KPI row — 5 cards for Manager (includes profit)
    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    with c1:
        st.markdown(kpi_card("Revenue",         fmt_currency(kpis["total_rev"]),    kpis["rev_delta"],  kpis["rev_pos"],  "revenue"),   unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Orders",          fmt_number(kpis["total_orders"]),   kpis["ord_delta"],  kpis["ord_pos"],  "orders"),    unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Customers",       fmt_number(kpis["unique_custs"]),   kpis["cust_delta"], kpis["cust_pos"], "customers"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Avg Order",       fmt_currency(kpis["avg_order"]),    kpis["bask_delta"], kpis["bask_pos"], "basket"),    unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("Total Profit",    fmt_currency(kpis["total_profit"]), "–", True, "profit"),              unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Manager sees: revenue trend (wide) + region sales
    col_a, col_b = st.columns([1.6, 1], gap="small")
    with col_a:
        st.plotly_chart(plot_revenue_trend(df),    use_container_width=True)
    with col_b:
        st.plotly_chart(plot_region_sales(df),     use_container_width=True)

    # Top products + category breakdown
    col_c, col_d = st.columns(2, gap="small")
    with col_c:
        st.plotly_chart(plot_top_products(df, top_n=8), use_container_width=True)
    with col_d:
        st.plotly_chart(plot_category_revenue(df),      use_container_width=True)

    # Focused AI Insights (top 3 only for manager — keep it brief)
    st.markdown(section_title("Executive AI Insights", "🤖"), unsafe_allow_html=True)
    insights = generate_ai_insights(df)
    if insights:
        for item in insights[:3]:
            st.markdown(insight_card(
                title=item["title"], description=item["description"],
                action=item["recommended_action"], impact=item["impact"],
                priority=item["priority"], confidence=item["confidence"],
            ), unsafe_allow_html=True)
    else:
        st.info("No AI insights available.")



# ─── Main dispatcher ──────────────────────────────────────────────────────────

def render(df) -> None:
    """Render the Dashboard page — adapts content to the logged-in user's role."""

    if df.empty:
        st.warning("No data available. Adjust filters or upload a dataset.")
        return

    role = st.session_state.get("user", {}).get("role", "Admin")

    if role == "Admin":
        _render_admin(df)
    elif role == "Analyst":
        _render_analyst(df)
    else:
        _render_manager(df)
