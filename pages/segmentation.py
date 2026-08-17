"""
Customer Insights Platform – Customer Segmentation Page
RFM K-Means clustering with adjustable K, silhouette score, and scatter plot.
"""

from __future__ import annotations

import streamlit as st

from components.kpi_cards import section_title
from services.analytics_service import plot_segment_scatter
from services.ml_service import train_segmentation


def render(df) -> None:
    """Render the Customer Segmentation page."""

    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">🎯 AI Customer Segmentation (RFM + K-Means)</div>
      <div class="ip-card-sub">
        Automatically segments customers using Recency, Frequency, and Monetary value.
        Clusters are labelled with business-friendly names.
      </div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available for segmentation.")
        return

    # ── Controls ──────────────────────────────────────────────────────────────
    col_k, col_btn = st.columns([2, 1])
    with col_k:
        k = st.slider("Number of Segments (K)", min_value=2, max_value=7, value=4,
                      help="Select how many customer segments to create.")
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run = st.button("🚀  Run Segmentation", use_container_width=True)

    auto_run = st.session_state.get("seg_auto_run", True)

    if run or auto_run:
        st.session_state["seg_auto_run"] = False
        with st.spinner("Training K-Means clustering model…"):
            try:
                result = train_segmentation(df, n_clusters=k)
                rfm_df  = result["rfm_df"]
                sil     = result["silhouette"]
                summary = result["summary"]

                # ── Score Banner ──────────────────────────────────────────
                score_color = "#10B981" if sil > 0.4 else ("#F59E0B" if sil > 0.25 else "#EF4444")
                st.markdown(f"""
                <div class="ip-card" style="border-left:3px solid {score_color};">
                  <div style="display:flex;align-items:center;gap:16px;">
                    <div>
                      <div style="font-size:2rem;font-weight:800;color:{score_color};">{sil:.3f}</div>
                      <div style="color:#94A3B8;font-size:0.8rem;">Silhouette Score
                        (higher = better separation)</div>
                    </div>
                    <div style="color:#94A3B8;font-size:0.85rem;border-left:1px solid rgba(255,255,255,0.1);padding-left:16px;">
                      <strong style="color:#F1F5F9;">{k} segments</strong> created from
                      <strong style="color:#F1F5F9;">{rfm_df['CustomerID'].nunique() if 'CustomerID' in rfm_df.columns else len(rfm_df)}</strong> customers
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Scatter Plot ─────────────────────────────────────────
                st.plotly_chart(plot_segment_scatter(rfm_df), use_container_width=True)

                # ── Summary Table ────────────────────────────────────────
                st.markdown(section_title("Segment Profiles", "📊"), unsafe_allow_html=True)
                st.dataframe(summary, use_container_width=True)

                # ── Segment Details ──────────────────────────────────────
                st.markdown(section_title("Customer Distribution by Segment", "👥"), unsafe_allow_html=True)
                if "SegmentName" in rfm_df.columns:
                    cols_show = [c for c in ["CustomerID", "SegmentName", "RecencyDays",
                                              "PurchaseFrequency", "MonetaryValue"]
                                 if c in rfm_df.columns]
                    st.dataframe(rfm_df[cols_show].sort_values("MonetaryValue", ascending=False),
                                 use_container_width=True)

            except ValueError as exc:
                st.info(f"ℹ️ {exc}")
            except Exception as exc:
                st.error(f"Segmentation error: {exc}")
