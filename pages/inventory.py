"""
Customer Insights Platform – Inventory Analytics Page
Stock risk scoring, reorder alerts, product velocity tracking.
"""

from __future__ import annotations

import streamlit as st

from components.kpi_cards import section_title
from utils.formatters import fmt_number


def render(df) -> None:
    """Render the Inventory Analytics page."""

    if df.empty:
        st.warning("No inventory data available.")
        return

    cat_col  = next((c for c in ["Category"] if c in df.columns), None)
    prod_col = next((c for c in ["ProductName", "Product", "Item"] if c in df.columns), None)
    qty_col  = next((c for c in ["Quantity", "Units"] if c in df.columns), None)
    amt_col  = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)

    if not prod_col or not qty_col:
        st.info("Inventory analytics requires ProductName and Quantity columns.")
        return

    # ── Build Inventory Summary ───────────────────────────────────────────────
    grp_cols = [c for c in [cat_col, prod_col] if c]
    agg_cols: dict = {"UnitsSold": (qty_col, "sum")}
    if amt_col: agg_cols["Revenue"] = (amt_col, "sum")

    inv = df.groupby(grp_cols).agg(**{k: (v[0], v[1]) for k, v in agg_cols.items()}).reset_index()

    # Estimate remaining stock (simulated: 45% of sold qty remaining)
    inv["EstimatedStock"] = inv["UnitsSold"].apply(lambda q: max(4, int(q * 0.45)))
    inv["StockStatus"]    = inv["EstimatedStock"].apply(
        lambda s: "🚨 Reorder Alert" if s < 15 else ("⚠️ Low Stock" if s < 30 else "✅ Healthy")
    )
    inv["VelocityScore"]  = (inv["UnitsSold"] / inv["UnitsSold"].max() * 100).round(1)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_prods   = len(inv)
    reorder_count = int((inv["EstimatedStock"] < 15).sum())
    low_count     = int(((inv["EstimatedStock"] >= 15) & (inv["EstimatedStock"] < 30)).sum())
    healthy_count = int((inv["EstimatedStock"] >= 30).sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Products",    fmt_number(total_prods))
    k2.metric("🚨 Reorder Alert",  fmt_number(reorder_count))
    k3.metric("⚠️ Low Stock",      fmt_number(low_count))
    k4.metric("✅ Healthy Stock",  fmt_number(healthy_count))

    # ── Reorder Alerts ────────────────────────────────────────────────────────
    reorder_df = inv[inv["EstimatedStock"] < 15]
    if not reorder_df.empty:
        st.markdown(section_title("🚨 Reorder Alerts – Immediate Action Required", ""), unsafe_allow_html=True)
        st.markdown(f"""
        <div class="ip-card" style="border-left:3px solid #EF4444;">
          <div style="color:#EF4444;font-weight:700;margin-bottom:8px;">
            ⚠️ {len(reorder_df)} product(s) require immediate restocking
          </div>
          <div style="color:var(--nx-text-2, #94A3B8);font-size:0.84rem;">
            Products with estimated remaining stock below 15 units are highlighted below.
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(reorder_df.sort_values("EstimatedStock"), use_container_width=True)

    # ── Full Inventory Table ──────────────────────────────────────────────────
    st.markdown(section_title("Full Inventory Risk Dashboard", "📊"), unsafe_allow_html=True)
    st.dataframe(
        inv.sort_values("EstimatedStock"),
        use_container_width=True,
    )

    # ── Top Velocity Products ─────────────────────────────────────────────────
    st.markdown(section_title("Top 10 High-Velocity Products", "🚀"), unsafe_allow_html=True)
    st.dataframe(inv.sort_values("UnitsSold", ascending=False).head(10), use_container_width=True)
