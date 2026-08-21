"""
Chart Exporter — Reliable chart-to-PNG conversion with retry, fallback,
and thread-safe kaleido access.
"""

import logging
import threading
import time
import traceback
from io import BytesIO

from reports.report_cache import get_cached_item, set_cached_item, get_df_hash

LOGGER = logging.getLogger(__name__)

# Global lock to serialise kaleido access (kaleido is NOT thread-safe)
_KALEIDO_LOCK = threading.Lock()

# Retry configuration
_MAX_RETRIES = 3
_RETRY_DELAY = 0.5  # seconds between retries


def _create_fallback_png(chart_name: str, width_px: int = 700, height_px: int = 380) -> bytes | None:
    """Create a styled placeholder PNG when chart rendering fails.

    Instead of returning ``None`` and showing 'Chart unavailable', this
    generates a clean placeholder image that matches the report's visual
    style.
    """
    try:
        import plotly.graph_objects as go

        display_name = chart_name.replace("_", " ").title()

        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#F8FAFC",
            plot_bgcolor="#F8FAFC",
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[
                dict(
                    text=(
                        f"<b>{display_name}</b><br>"
                        f"<span style='font-size:11px;color:#94A3B8;'>"
                        f"Data visualization will appear here when data is available"
                        f"</span>"
                    ),
                    showarrow=False,
                    font=dict(color="#64748B", size=14, family="Helvetica"),
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    align="center",
                ),
            ],
            shapes=[
                # Border rectangle
                dict(
                    type="rect",
                    xref="paper", yref="paper",
                    x0=0.02, y0=0.02, x1=0.98, y1=0.98,
                    line=dict(color="#E2E8F0", width=1.5, dash="dot"),
                    fillcolor="rgba(241,245,249,0.5)",
                ),
            ],
        )

        with _KALEIDO_LOCK:
            png_bytes = fig.to_image(format="png", width=width_px, height=height_px, scale=1.0)
        return png_bytes

    except Exception as exc:
        LOGGER.warning("Fallback placeholder generation also failed for %s: %s", chart_name, exc)
        return None


def fig_to_png(fig, width_px: int = 700, height_px: int = 380, chart_name: str = "chart") -> bytes | None:
    """Convert a Plotly figure to PNG bytes using kaleido.

    Features:
    - Retries up to ``_MAX_RETRIES`` times on failure.
    - Uses a global lock to prevent concurrent kaleido access.
    - Falls back to a styled placeholder on persistent failure.
    - Logs detailed error information.
    """
    if fig is None:
        LOGGER.warning("fig_to_png received None figure for chart '%s'", chart_name)
        return _create_fallback_png(chart_name, width_px, height_px)

    last_exc = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            import plotly.io as pio

            with _KALEIDO_LOCK:
                png_bytes = pio.to_image(
                    fig, format="png",
                    width=width_px, height=height_px,
                    scale=1.2,
                )

            if png_bytes and len(png_bytes) > 100:  # sanity check
                if attempt > 1:
                    LOGGER.info("Chart '%s' exported on attempt %d", chart_name, attempt)
                return png_bytes
            else:
                LOGGER.warning(
                    "Chart '%s' attempt %d produced empty/tiny output (%d bytes)",
                    chart_name, attempt, len(png_bytes) if png_bytes else 0,
                )

        except Exception as exc:
            last_exc = exc
            LOGGER.warning(
                "Chart '%s' export attempt %d/%d failed: %s",
                chart_name, attempt, _MAX_RETRIES, exc,
            )
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY * attempt)  # progressive backoff

    # All retries exhausted
    LOGGER.error(
        "Chart '%s' FAILED after %d attempts. Last error: %s\n%s",
        chart_name, _MAX_RETRIES, last_exc,
        traceback.format_exc() if last_exc else "No exception captured",
    )
    return _create_fallback_png(chart_name, width_px, height_px)


def get_chart_png(df, chart_name: str, chart_func, width: int, height: int, **kwargs) -> bytes | None:
    """
    Get a PNG for a chart, using the cache if available.
    ``chart_func`` is the function that returns the ``go.Figure``.
    """
    df_hash = get_df_hash(df)
    cache_key = f"chart_png_{chart_name}_{df_hash}_{width}x{height}"

    cached_png = get_cached_item(cache_key)
    if cached_png is not None:
        return cached_png

    try:
        fig = chart_func(df, **kwargs) if kwargs else chart_func(df)
        png_bytes = fig_to_png(fig, width, height, chart_name=chart_name)
        if png_bytes:
            set_cached_item(cache_key, png_bytes)
        return png_bytes
    except Exception as exc:
        LOGGER.error("Failed to generate '%s' chart: %s\n%s", chart_name, exc, traceback.format_exc())
        return _create_fallback_png(chart_name, width, height)


def _generate_single_chart(func, df, kwargs, w, h, chart_name: str = "chart"):
    """Generate a single chart PNG with proper kwargs dispatch and error handling."""
    try:
        if kwargs and "rfm_df" in kwargs:
            fig = func(kwargs["rfm_df"])
        elif kwargs and "combined_df" in kwargs:
            fig = func(kwargs["combined_df"])
        else:
            fig = func(df, **kwargs) if kwargs else func(df)
        return fig_to_png(fig, w, h, chart_name=chart_name)
    except Exception as exc:
        LOGGER.error(
            "Chart '%s' generation function failed: %s\n%s",
            chart_name, exc, traceback.format_exc(),
        )
        return _create_fallback_png(chart_name, w, h)


def generate_all_charts(df, figs_config: dict) -> dict:
    """Generate multiple charts sequentially with cache and thread-safe kaleido.

    Uses serial execution (not ThreadPoolExecutor) because kaleido's
    Chromium subprocess is not thread-safe and concurrent calls cause
    segfaults and corrupted output on Windows.

    Each chart is checked against the cache first, so repeat exports
    are instant.

    ``figs_config`` format::

        {
            'chart_key': (chart_func, width, height),
            'chart_key': (chart_func, width, height, kwargs_dict),
        }
    """
    df_hash = get_df_hash(df)
    results = {}
    total = len(figs_config)

    for idx, (key, config) in enumerate(figs_config.items(), 1):
        func = config[0]
        w = config[1]
        h = config[2]
        kwargs = config[3] if len(config) > 3 else {}

        cache_key = f"chart_png_{key}_{df_hash}_{w}x{h}"
        cached_png = get_cached_item(cache_key)

        if cached_png is not None:
            results[key] = cached_png
            LOGGER.debug("Chart '%s' served from cache (%d/%d)", key, idx, total)
        else:
            LOGGER.info("Rendering chart '%s' (%d/%d)...", key, idx, total)
            png_bytes = _generate_single_chart(func, df, kwargs, w, h, chart_name=key)
            results[key] = png_bytes
            if png_bytes:
                set_cached_item(cache_key, png_bytes)

    # Summary log
    rendered = sum(1 for v in results.values() if v is not None)
    LOGGER.info(
        "Chart export complete: %d/%d charts rendered successfully",
        rendered, total,
    )

    return results
