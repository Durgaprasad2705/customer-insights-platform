"""
Customer Insights Platform – Dataset Upload Page
Universal CSV/Excel ingestion with auto column mapping and data quality report.
"""

from __future__ import annotations

import datetime
import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

from components.kpi_cards import section_title
from database.db import log_dataset_upload
from utils.data_cleaning import clean_and_preprocess


def render(df, current_user: dict) -> None:
    """Render the Dataset Upload page."""

    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">📤 Universal Dataset Upload</div>
      <div class="ip-card-sub">
        Upload any CSV or Excel file. The platform automatically detects columns,
        cleans data, handles missing values, removes duplicates, and maps non-standard
        column names to the canonical schema.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File Uploader ────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Drag & drop or click to upload CSV / Excel",
        type=["csv", "xlsx", "xls"],
        key="upload_widget",
    )

    if uploaded is not None:
        try:
            file_bytes = uploaded.getvalue()
            signature  = hashlib.sha256(file_bytes).hexdigest()

            # Only re-process if this is a new file
            if st.session_state.get("upload_signature") != signature:
                with st.spinner("🔄 Analysing and cleaning your dataset…"):
                    if uploaded.name.lower().endswith(".csv"):
                        raw_df = pd.read_csv(BytesIO(file_bytes))
                    else:
                        raw_df = pd.read_excel(BytesIO(file_bytes))

                    cleaned_df, report = clean_and_preprocess(raw_df)

                    st.session_state["raw_df"]            = raw_df
                    st.session_state["cleaned_df"]        = cleaned_df
                    st.session_state["cleaning_report"]   = report
                    st.session_state["upload_signature"]  = signature

                    log_dataset_upload(
                        filename      = uploaded.name,
                        row_count     = report["final_rows"],
                        column_count  = report["final_cols"],
                        file_size_kb  = round(uploaded.size / 1024, 2),
                        uploaded_by   = current_user.get("username", "unknown"),
                    )

            cleaned_df = st.session_state["cleaned_df"]
            report     = st.session_state["cleaning_report"]

            # ── Success Banner ────────────────────────────────────────────
            st.success(f"✅ **{uploaded.name}** processed successfully. All dashboards and models now use this dataset.")

            # ── Quality Metrics ───────────────────────────────────────────
            st.markdown(section_title("Data Quality Report", "🔬"), unsafe_allow_html=True)

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Original Rows",     f"{report['initial_rows']:,}")
            m2.metric("Cleaned Rows",      f"{report['final_rows']:,}")
            m3.metric("Duplicates Removed",f"{report['duplicates_removed']:,}")
            m4.metric("Values Imputed",    f"{report['total_missing_imputed']:,}")
            m5.metric("Quality Score",     f"{report['data_quality_score']}%")

            # ── Column Mapping ────────────────────────────────────────────
            if report.get("mapped_columns"):
                mapping_text = " · ".join(
                    f"`{src}` → `{tgt}`"
                    for tgt, src in report["mapped_columns"].items()
                    if src != tgt
                )
                if mapping_text:
                    st.info(f"**Column mapping applied:** {mapping_text}")

            # ── Outlier Summary ───────────────────────────────────────────
            if report.get("outlier_summary"):
                with st.expander("🔍 Outlier Detection Summary", expanded=False):
                    for col, count in report["outlier_summary"].items():
                        st.write(f"• **{col}**: {count:,} potential outliers detected (informational, not capped)")

            # ── Dataset Preview ───────────────────────────────────────────
            st.markdown(section_title("Cleaned Dataset Preview", "📋"), unsafe_allow_html=True)
            st.dataframe(cleaned_df.head(20), use_container_width=True)

            # ── Downloads ─────────────────────────────────────────────────
            st.markdown(section_title("Export Cleaned Data", "⬇️"), unsafe_allow_html=True)
            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button(
                    "📥 Download Cleaned CSV",
                    data=cleaned_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"Customer Insights Platform_cleaned_{datetime.date.today()}.csv",
                    mime="text/csv",
                )
            with dl2:
                from io import BytesIO as _B
                buf = _B()
                cleaned_df.to_excel(buf, index=False, engine="openpyxl")
                buf.seek(0)
                st.download_button(
                    "📥 Download Cleaned Excel",
                    data=buf.getvalue(),
                    file_name=f"Customer Insights Platform_cleaned_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        except Exception as exc:
            st.error(f"**Upload failed:** {exc}")
            st.caption("Ensure the file contains at least: customer ID, purchase date, and sales amount columns.")

    else:
        # No file uploaded – show current dataset summary
        st.markdown(section_title("Current Active Dataset", "📊"), unsafe_allow_html=True)
        rep = st.session_state.get("cleaning_report", {})
        if rep:
            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", f"{rep.get('final_rows', len(df)):,}")
            c2.metric("Columns", f"{rep.get('final_cols', len(df.columns)):,}")
            c3.metric("Quality Score", f"{rep.get('data_quality_score', 100)}%")

        st.markdown(section_title("Sample Data (first 10 rows)", "👁️"), unsafe_allow_html=True)
        st.dataframe(df.head(10), use_container_width=True)

        # Accepted formats help card
        st.markdown("""
        <div class="ip-card" style="margin-top:20px;">
          <div class="ip-card-title">ℹ️ Supported Column Names</div>
          <div class="ip-card-sub">The platform automatically recognises these common variations:</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px;font-size:0.82rem;color:#94A3B8;">
            <div><strong style="color:#F1F5F9;">Customer ID</strong><br>CustomerID · customer_id · ClientID · CustID · ID · MemberID</div>
            <div><strong style="color:#F1F5F9;">Revenue / Amount</strong><br>TotalAmount · Revenue · Sales · Amount · Income · TotalPrice · OrderAmount</div>
            <div><strong style="color:#F1F5F9;">Purchase Date</strong><br>PurchaseDate · Date · OrderDate · InvoiceDate · SaleDate</div>
            <div><strong style="color:#F1F5F9;">Product / Category</strong><br>ProductName · Product · Item · Category · Segment · Department</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
