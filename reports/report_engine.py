"""
Report Engine — Orchestrates chart collection, ML model execution,
and PDF/Excel/CSV report generation.
"""

import logging
import pandas as pd
import streamlit as st

from reports.chart_exporter import generate_all_charts
from reports.report_builder import PDFReportBuilder, ExcelReportBuilder
from services.analytics_service import (
    plot_revenue_trend, plot_category_revenue, plot_brand_performance,
    plot_region_sales, plot_top_products, plot_payment_methods,
    plot_age_distribution, plot_sales_funnel, plot_segment_scatter,
    plot_forecast, plot_gender_split,
)
from services.ml_service import train_segmentation, forecast_revenue

LOGGER = logging.getLogger(__name__)


def _collect_all_chart_configs(df: pd.DataFrame) -> tuple[dict, dict]:
    """Collect all chart configurations and ML data for the report.

    Returns a tuple of ``(figs_config, ml_data)`` where:
    - ``figs_config`` is the chart render config for ``generate_all_charts()``
    - ``ml_data`` is a dict with ML summary tables for the PDF builder

    This ensures every chart visible in the application is included
    in the exported report.
    """
    # ── Core dashboard + analytics charts ─────────────────────────────────
    figs_config = {
        "trend":  (plot_revenue_trend,     900, 400),
        "cat":    (plot_category_revenue,   440, 340),
        "brand":  (plot_brand_performance,  440, 340),
        "reg":    (plot_region_sales,       440, 340),
        "prod":   (plot_top_products,       440, 340, {"top_n": 8}),
        "pay":    (plot_payment_methods,    440, 340),
        "age":    (plot_age_distribution,   440, 340),
        "funnel": (plot_sales_funnel,       700, 360),
    }

    # ── Gender distribution (if data has a Gender column) ─────────────────
    gender_col = next(
        (c for c in ["Gender", "Sex"] if c in df.columns), None
    )
    if gender_col:
        figs_config["gender"] = (plot_gender_split, 440, 340)

    # ── ML model charts — robust collection with detailed logging ─────────
    ml_data = {
        "segment_summary": None,
        "forecast_data": None,
    }

    # Segmentation scatter chart
    try:
        LOGGER.info("Running customer segmentation for report...")
        seg_res = train_segmentation(df)
        figs_config["segment"] = (
            plot_segment_scatter, 440, 340,
            {"rfm_df": seg_res["rfm_df"]},
        )
        ml_data["segment_summary"] = seg_res.get("summary")
        LOGGER.info(
            "Segmentation complete: %d segments, silhouette=%.3f",
            len(seg_res.get("summary", [])),
            seg_res.get("silhouette", 0),
        )
    except ValueError as e:
        LOGGER.info("Segmentation skipped (insufficient data): %s", e)
    except Exception as e:
        LOGGER.warning("Segmentation failed — chart will use fallback: %s", e)

    # Revenue forecast chart
    try:
        LOGGER.info("Running revenue forecast for report...")
        fore_res = forecast_revenue(df)
        figs_config["forecast"] = (
            plot_forecast, 440, 340,
            {"combined_df": fore_res["combined_df"]},
        )
        ml_data["forecast_data"] = fore_res.get("forecast_df")
        LOGGER.info(
            "Forecast complete: R²=%.3f, %d months projected",
            fore_res.get("r2", 0),
            len(fore_res.get("forecast_df", [])),
        )
    except ValueError as e:
        LOGGER.info("Forecast skipped (insufficient data): %s", e)
    except Exception as e:
        LOGGER.warning("Forecast failed — chart will use fallback: %s", e)

    return figs_config, ml_data


def generate_pdf(
    df: pd.DataFrame,
    insights: list[dict],
    progress_bar=None,
    status_text=None,
) -> bytes | None:
    """Generate a high-performance PDF report with all charts and KPIs."""
    try:
        # ── Phase 1: Collect chart configs & ML data ──────────────────────
        if status_text:
            status_text.text("Collecting Analytics & ML Models...")
        if progress_bar:
            progress_bar.progress(10)

        figs_config, ml_data = _collect_all_chart_configs(df)

        if progress_bar:
            progress_bar.progress(30)

        # ── Phase 2: Export all charts to PNG ─────────────────────────────
        if status_text:
            status_text.text(
                f"Exporting {len(figs_config)} Charts to PNG..."
            )
        if progress_bar:
            progress_bar.progress(40)

        charts_pngs = generate_all_charts(df, figs_config)

        if progress_bar:
            progress_bar.progress(70)

        # Log chart export results
        rendered = sum(1 for v in charts_pngs.values() if v is not None)
        total = len(charts_pngs)
        LOGGER.info("Chart export: %d/%d charts rendered", rendered, total)

        # ── Phase 3: Build PDF document ──────────────────────────────────
        if status_text:
            status_text.text("Building PDF Document...")
        if progress_bar:
            progress_bar.progress(80)

        builder = PDFReportBuilder(df, insights, charts_pngs, ml_data)
        pdf_bytes = builder.build()

        # ── Phase 4: Finalise ────────────────────────────────────────────
        if status_text:
            status_text.text("Finalizing Report...")
        if progress_bar:
            progress_bar.progress(100)

        LOGGER.info(
            "PDF report generated: %d bytes, %d charts, %d insights",
            len(pdf_bytes), rendered, len(insights),
        )
        return pdf_bytes

    except Exception as exc:
        LOGGER.error("PDF generation error: %s", exc, exc_info=True)
        raise exc


def generate_excel(
    df: pd.DataFrame,
    insights: list[dict],
    progress_bar=None,
    status_text=None,
) -> bytes | None:
    """Generate a high-performance Excel report."""
    try:
        if status_text:
            status_text.text("Building Excel workbooks...")
        if progress_bar:
            progress_bar.progress(30)

        builder = ExcelReportBuilder(df, insights)

        if status_text:
            status_text.text("Formatting data...")
        if progress_bar:
            progress_bar.progress(70)

        excel_bytes = builder.build()

        if status_text:
            status_text.text("Finalizing Report...")
        if progress_bar:
            progress_bar.progress(100)

        return excel_bytes
    except Exception as exc:
        LOGGER.error("Excel generation error: %s", exc, exc_info=True)
        raise exc


def generate_csv(df: pd.DataFrame) -> bytes:
    """Return the dataframe as UTF-8 CSV bytes."""
    # Fast path for CSV
    return df.to_csv(index=False).encode("utf-8")
