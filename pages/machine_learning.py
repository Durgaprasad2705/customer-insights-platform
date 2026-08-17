"""
Customer Insights Platform – Machine Learning Hub Page
Churn Prediction, CLV Forecast, Sales Revenue Forecasting – all in tabs.
"""

from __future__ import annotations

import streamlit as st

from components.kpi_cards import section_title
from services.analytics_service import plot_forecast
from services.ml_service import train_churn, train_clv, forecast_revenue
from utils.formatters import fmt_currency


def render(df) -> None:
    """Render the Machine Learning Hub page."""

    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">🤖 Machine Learning Predictive Engine</div>
      <div class="ip-card-sub">
        Automated model training on the active dataset.
        Models retrain automatically whenever a new dataset is uploaded.
      </div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available for ML modelling.")
        return

    tab1, tab2, tab3 = st.tabs(["📉 Churn Prediction", "💎 CLV Forecast", "📈 Revenue Forecast"])

    # ── Tab 1: Churn Prediction ───────────────────────────────────────────────
    with tab1:
        st.markdown(section_title("Random Forest Churn Classifier", "📉"), unsafe_allow_html=True)
        st.markdown("""
        <div style="color:var(--nx-text-2, #94A3B8);font-size:0.84rem;margin-bottom:16px;">
        Identifies customers at risk of churning based on Recency, Frequency, Monetary value,
        Customer Age, and Rating features. Uses RandomForestClassifier with 75 estimators.
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀  Train Churn Model", key="churn_btn", use_container_width=False):
            with st.spinner("Training churn prediction model…"):
                try:
                    result = train_churn(df)
                    st.session_state["ml_churn_result"] = result
                except ValueError as exc:
                    st.info(f"ℹ️ {exc}")
                except Exception as exc:
                    st.error(f"Churn model error: {exc}")

        if "ml_churn_result" in st.session_state and st.session_state["ml_churn_result"]:
            result = st.session_state["ml_churn_result"]
            # Metric cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Accuracy",  f"{result['accuracy']}%")
            c2.metric("Precision", f"{result['precision']}%")
            c3.metric("Recall",    f"{result['recall']}%")
            c4.metric("F1 Score",  f"{result['f1']}%")

            # Feature importance
            st.markdown(section_title("Feature Importance", "📊"), unsafe_allow_html=True)
            st.dataframe(result["importances"], use_container_width=True)

            # At-risk customers
            preds = result["predictions"]
            at_risk = preds[preds["PredictedChurn"] == 1].sort_values(
                "ChurnRiskProbability", ascending=False
            )
            st.markdown(section_title(f"At-Risk Customers ({len(at_risk)} identified)", "⚠️"),
                        unsafe_allow_html=True)
            show_cols = [c for c in ["CustomerID", "RecencyDays", "PurchaseFrequency",
                                      "MonetaryValue", "ChurnRiskProbability"]
                         if c in at_risk.columns]
            st.dataframe(at_risk[show_cols].head(20), use_container_width=True)

    # ── Tab 2: CLV Forecast ───────────────────────────────────────────────────
    with tab2:
        st.markdown(section_title("Customer Lifetime Value Regressor", "💎"), unsafe_allow_html=True)
        st.markdown("""
        <div style="color:var(--nx-text-2, #94A3B8);font-size:0.84rem;margin-bottom:16px;">
        Predicts the expected 12-month revenue from each customer using a RandomForest regressor
        trained on RFM (Recency, Frequency, Monetary) features.
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀  Train CLV Model", key="clv_btn", use_container_width=False):
            with st.spinner("Computing CLV predictions…"):
                try:
                    result = train_clv(df)
                    st.session_state["ml_clv_result"] = result
                except ValueError as exc:
                    st.info(f"ℹ️ {exc}")
                except Exception as exc:
                    st.error(f"CLV model error: {exc}")

        if "ml_clv_result" in st.session_state and st.session_state["ml_clv_result"]:
            result = st.session_state["ml_clv_result"]
            # Score banner
            st.markdown(f"""
            <div class="ip-card" style="border-left:3px solid #6366F1;">
              <div style="display:flex;align-items:center;gap:24px;">
                <div>
                  <div style="font-size:1.8rem;font-weight:800;color:var(--nx-text-1, #F1F5F9);">
                    {result['r2_score']:.3f}
                  </div>
                  <div style="color:var(--nx-text-2, #94A3B8);font-size:0.8rem;">Model R² Score</div>
                </div>
                <div style="border-left:1px solid rgba(255,255,255,0.1);padding-left:20px;">
                  <div style="font-size:1.8rem;font-weight:800;color:#10B981;">
                    {fmt_currency(result['avg_clv'])}
                  </div>
                  <div style="color:var(--nx-text-2, #94A3B8);font-size:0.8rem;">Average 12M CLV per customer</div>
                </div>
                <div style="border-left:1px solid rgba(255,255,255,0.1);padding-left:20px;">
                  <div style="font-size:1.8rem;font-weight:800;color:#A855F7;">
                    {result['rmse']:,.0f}
                  </div>
                  <div style="color:var(--nx-text-2, #94A3B8);font-size:0.8rem;">RMSE</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(section_title("Top 10 Highest-Value Customers", "🏆"), unsafe_allow_html=True)
            top_cust = result["top_clv_customers"]
            show_cols = [c for c in ["CustomerID", "RecencyDays", "PurchaseFrequency",
                                      "MonetaryValue", "Predicted_12M_CLV"]
                         if c in top_cust.columns]
            st.dataframe(top_cust[show_cols], use_container_width=True)

    # ── Tab 3: Revenue Forecast ───────────────────────────────────────────────
    with tab3:
        st.markdown(section_title("6-Month Revenue Forecast (Ridge Regression)", "📈"),
                    unsafe_allow_html=True)
        st.markdown("""
        <div style="color:var(--nx-text-2, #94A3B8);font-size:0.84rem;margin-bottom:16px;">
        Uses Ridge regression on monthly time-series data to project future revenue
        with seasonal noise adjustment. Ideal for 3–12 month planning horizons.
        </div>
        """, unsafe_allow_html=True)

        months = st.slider("Forecast horizon (months)", 3, 12, 6, key="fc_months")

        try:
            result = forecast_revenue(df, months_ahead=months)

            st.markdown(f"""
            <div class="ip-card" style="border-left:3px solid #10B981;">
              <div style="font-size:1.6rem;font-weight:800;color:#10B981;">{result['r2']:.3f}</div>
              <div style="color:var(--nx-text-2, #94A3B8);font-size:0.8rem;">Historical model R² — confidence in trend line</div>
            </div>
            """, unsafe_allow_html=True)

            st.plotly_chart(plot_forecast(result["combined_df"]), use_container_width=True)

            st.markdown(section_title("Forecast Data Table", "📋"), unsafe_allow_html=True)
            fc_df = result["forecast_df"].copy()
            fc_df["Month"] = fc_df["Month"].dt.strftime("%b %Y")
            st.dataframe(fc_df, use_container_width=True)

        except ValueError as exc:
            st.info(f"ℹ️ {exc}")
        except Exception as exc:
            st.error(f"Forecast error: {exc}")
