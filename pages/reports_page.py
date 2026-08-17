"""Reports & Export Center — generate PDF, Excel, CSV reports with AI insights."""

from __future__ import annotations

import datetime

import pandas as pd
import streamlit as st

from components.kpi_cards import section_title
from services.analytics_service import generate_ai_insights
from services.report_service import generate_csv_export, generate_excel_report, generate_pdf_report


def render(df, current_user: dict) -> None:

    st.markdown('<div class="ip-card"><div class="ip-card-title">📄 Reports & Data Export Center</div>'
                '<div class="ip-card-sub">Generate enterprise-grade reports with KPIs, AI insights, '
                'and transaction data. All reports reflect your current filter selection.</div></div>',
                unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available. Adjust filters or upload a dataset.")
        return

    insights = generate_ai_insights(df)

    today    = datetime.date.today()
    username = current_user.get("username", "user")

    # Column detection
    amt_col    = next((c for c in ["TotalAmount", "Revenue", "Amount"] if c in df.columns), None)
    cust_col   = next((c for c in ["CustomerID"] if c in df.columns), None)
    date_col   = next((c for c in ["PurchaseDate", "Date", "OrderDate"] if c in df.columns), None)
    cat_col    = "Category" if "Category" in df.columns else None
    region_col = next((c for c in ["Region", "Location", "State"] if c in df.columns), None)
    rating_col = next((c for c in ["CustomerRating", "Rating"] if c in df.columns), None)

    # Report format cards
    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        st.markdown('<div class="ip-card"><div style="font-size:2.5rem;margin-bottom:8px;">📕</div>'
                    '<div class="ip-card-title">PDF Executive Report</div>'
                    '<div class="ip-card-sub">Professional multi-section PDF with KPI summary, '
                    'AI insights, and transaction preview. Ideal for stakeholder presentations.</div></div>',
                    unsafe_allow_html=True)
        if st.button("⚡  Generate PDF", use_container_width=True, key="gen_pdf"):
            with st.spinner("Building PDF report…"):
                try:
                    pdf_bytes = generate_pdf_report(df, insights)
                    st.download_button(
                        "📥 Download PDF", data=pdf_bytes,
                        file_name=f"Customer_Insights_Report_{today}.pdf",
                        mime="application/pdf", use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"PDF generation failed: {exc}")

    with col2:
        st.markdown('<div class="ip-card"><div style="font-size:2.5rem;margin-bottom:8px;">📗</div>'
                    '<div class="ip-card-title">Excel Workbook</div>'
                    '<div class="ip-card-sub">Multi-sheet workbook: Transaction Data, Category Summary, '
                    'Customer Summary, and AI Insights tabs. Best for deep-dive analysis.</div></div>',
                    unsafe_allow_html=True)
        if st.button("⚡  Generate Excel", use_container_width=True, key="gen_excel"):
            with st.spinner("Building Excel workbook…"):
                try:
                    excel_bytes = generate_excel_report(df, insights)
                    st.download_button(
                        "📥 Download Excel", data=excel_bytes,
                        file_name=f"Customer_Insights_Analytics_{today}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"Excel generation failed: {exc}")

    with col3:
        st.markdown('<div class="ip-card"><div style="font-size:2.5rem;margin-bottom:8px;">📊</div>'
                    '<div class="ip-card-title">CSV Data Export</div>'
                    '<div class="ip-card-sub">Raw cleaned dataset in CSV format. '
                    'Reflects current filters. Use for custom analysis in any BI tool.</div></div>',
                    unsafe_allow_html=True)
        if st.button("⚡  Prepare CSV Export", use_container_width=True, key="gen_csv"):
            try:
                csv_bytes = generate_csv_export(df)
                st.download_button(
                    "📥 Download CSV", data=csv_bytes,
                    file_name=f"Customer_Insights_Data_{today}.csv",
                    mime="text/csv", use_container_width=True,
                )
            except Exception as exc:
                st.error(f"CSV export failed: {exc}")

    # Dataset Summary Metrics
    st.markdown(section_title("Active Dataset Summary", "📊"), unsafe_allow_html=True)

    metrics = []
    metrics.append(("Total Rows", f"{len(df):,}", "Number of transactions in the current dataset"))
    metrics.append(("Columns", f"{len(df.columns):,}", "Total data fields available"))
    if cust_col:
        metrics.append(("Unique Customers", f"{df[cust_col].nunique():,}", "Distinct customer IDs"))
    if amt_col:
        total_rev = df[amt_col].sum()
        avg_order = df[amt_col].mean()
        metrics.append(("Total Revenue", f"${total_rev:,.0f}", "Sum of all transaction amounts"))
        metrics.append(("Avg Order Value", f"${avg_order:,.2f}", "Average revenue per transaction"))
    if rating_col:
        avg_rating = df[rating_col].mean()
        metrics.append(("Avg Rating", f"{avg_rating:.2f} ★", "Mean customer satisfaction score"))
    if cat_col:
        metrics.append(("Categories", f"{df[cat_col].nunique():,}", "Distinct product categories"))

    cols = st.columns(min(len(metrics), 4))
    for i, (label, value, help_text) in enumerate(metrics):
        with cols[i % 4]:
            st.metric(label, value, help=help_text)

    # Date range info
    if date_col:
        try:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if not dates.empty:
                date_from = dates.min().strftime("%d %b %Y")
                date_to   = dates.max().strftime("%d %b %Y")
                date_span = (dates.max() - dates.min()).days
                st.markdown(
                    f'<div style="background:rgba(0,212,168,0.05);border:1px solid rgba(0,212,168,0.2);'
                    f'border-radius:10px;padding:12px 18px;margin-top:12px;font-size:0.85rem;color:var(--nx-text-2, #9898BB);">'
                    f'📅 Data covers <strong style="color:var(--nx-text-1, #EEEEFF);">{date_from}</strong> → '
                    f'<strong style="color:var(--nx-text-1, #EEEEFF);">{date_to}</strong> '
                    f'<span style="color:#4E4E7A;margin-left:8px;">({date_span} days)</span></div>',
                    unsafe_allow_html=True
                )
        except Exception:
            pass

    # Top Category breakdown (mini table)
    if cat_col and amt_col:
        st.markdown(section_title("Revenue by Category", "📦"), unsafe_allow_html=True)
        cat_df = (
            df.groupby(cat_col)[amt_col].agg(["sum", "count", "mean"])
            .rename(columns={"sum": "Total Revenue", "count": "Transactions", "mean": "Avg Order"})
            .sort_values("Total Revenue", ascending=False)
            .reset_index()
        )
        cat_df["Total Revenue"] = cat_df["Total Revenue"].map("${:,.0f}".format)
        cat_df["Avg Order"]     = cat_df["Avg Order"].map("${:,.2f}".format)
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

    # Top Customers (if available)
    if cust_col and amt_col:
        st.markdown(section_title("Top 10 Customers by Revenue", "👑"), unsafe_allow_html=True)

        agg_dict = {amt_col: ["sum", "count"]}
        top_custs = (
            df.groupby(cust_col)
            .agg(**{
                "Total Revenue": pd.NamedAgg(column=amt_col, aggfunc="sum"),
                "Orders":        pd.NamedAgg(column=amt_col, aggfunc="count"),
                "Avg Order":     pd.NamedAgg(column=amt_col, aggfunc="mean"),
            })
            .sort_values("Total Revenue", ascending=False)
            .head(10)
            .reset_index()
        )
        top_custs["Total Revenue"] = top_custs["Total Revenue"].map("${:,.0f}".format)
        top_custs["Avg Order"]     = top_custs["Avg Order"].map("${:,.2f}".format)
        st.dataframe(top_custs, use_container_width=True, hide_index=True)

    # AI Insights Preview
    if insights:
        st.markdown(section_title("AI Insights Included in Reports", "🤖"), unsafe_allow_html=True)

        priority_cfg = {
            "high":   ("#FF6B8A", "rgba(255,77,106,0.1)",  "rgba(255,77,106,0.3)",  "🔴 HIGH"),
            "medium": ("#FFAD00", "rgba(255,173,0,0.1)",   "rgba(255,173,0,0.3)",   "🟡 MEDIUM"),
            "low":    ("#22C55E", "rgba(34,197,94,0.1)",   "rgba(34,197,94,0.25)",  "🟢 LOW"),
        }

        for item in insights[:5]:
            priority = item.get("priority", "low").lower()
            color, bg, border, badge = priority_cfg.get(priority, priority_cfg["low"])
            confidence = item.get("confidence", 0)
            title      = item.get("title", "")
            description = item.get("description", item.get("why", ""))

            card = (
                f'<div style="padding:14px 18px;background:{bg};border:1px solid {border};'
                f'border-left:3px solid {color};border-radius:10px;margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                f'<span style="font-size:0.6rem;font-weight:700;color:{color};text-transform:uppercase;'
                f'letter-spacing:0.08em;">{badge}</span>'
                f'<span style="font-size:0.65rem;font-weight:600;color:#00D4A8;background:rgba(0,212,168,0.08);'
                f'border:1px solid rgba(0,212,168,0.25);padding:2px 8px;border-radius:99px;">✦ {confidence:.0f}% Confidence</span>'
                f'</div>'
                f'<div style="font-size:0.88rem;font-weight:700;color:var(--nx-text-1, #EEEEFF);margin-bottom:4px;">{title}</div>'
                f'<div style="font-size:0.78rem;color:var(--nx-text-2, #9898BB);line-height:1.5;">{description}</div>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)

    # Data preview
    st.markdown(section_title("Data Preview (First 20 Rows)", "🔍"), unsafe_allow_html=True)
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)
