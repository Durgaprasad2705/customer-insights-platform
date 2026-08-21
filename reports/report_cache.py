import hashlib
import time
import logging
import pandas as pd
import streamlit as st

LOGGER = logging.getLogger(__name__)

# Default cache TTL in seconds (5 minutes)
_CACHE_TTL = 300


def get_df_hash(df: pd.DataFrame) -> str:
    """Generate a collision-resistant hash for a DataFrame.

    Uses shape, column names, multiple column aggregates, and
    head/tail row sampling to minimise false cache hits.
    """
    if df is None or df.empty:
        return "empty"

    parts: list[str] = []

    # 1. Shape
    parts.append(f"{df.shape[0]}x{df.shape[1]}")

    # 2. Column names (sorted for determinism)
    parts.append(",".join(sorted(df.columns.tolist())))

    # 3. Aggregates from ALL numeric columns (sum + mean)
    try:
        num_cols = df.select_dtypes(include="number").columns
        for col in num_cols[:6]:  # cap at 6 to keep fast
            col_sum = df[col].sum()
            col_mean = df[col].mean()
            parts.append(f"{col}:{col_sum:.4f}:{col_mean:.4f}")
    except Exception:
        pass

    # 4. First & last row sample (string repr)
    try:
        first_row = df.iloc[0].astype(str).values.tolist()
        last_row = df.iloc[-1].astype(str).values.tolist()
        parts.append("|".join(first_row[:8]))
        parts.append("|".join(last_row[:8]))
    except Exception:
        pass

    hash_input = "||".join(parts)
    return hashlib.md5(hash_input.encode("utf-8", errors="replace")).hexdigest()


def _get_cache_store() -> dict:
    """Return the session-state cache store, creating it if needed."""
    if "report_cache" not in st.session_state:
        st.session_state.report_cache = {}
    return st.session_state.report_cache


def _get_cache_stats() -> dict:
    """Return the session-state cache statistics dict."""
    if "report_cache_stats" not in st.session_state:
        st.session_state.report_cache_stats = {"hits": 0, "misses": 0}
    return st.session_state.report_cache_stats


def get_cached_item(cache_key: str):
    """Retrieve an item from the session state cache.

    Returns ``None`` if the item is absent or has expired.
    """
    store = _get_cache_store()
    stats = _get_cache_stats()

    entry = store.get(cache_key)
    if entry is not None:
        stored_time, value = entry
        if (time.time() - stored_time) < _CACHE_TTL:
            stats["hits"] += 1
            return value
        else:
            # Expired — remove stale entry
            del store[cache_key]

    stats["misses"] += 1
    return None


def set_cached_item(cache_key: str, value) -> None:
    """Store an item in the session state cache with a timestamp."""
    store = _get_cache_store()
    store[cache_key] = (time.time(), value)


def get_cached_dataframe_agg(df: pd.DataFrame, agg_name: str, agg_func) -> pd.DataFrame:
    """
    Cache aggregations on a dataframe to avoid recomputing GroupBys
    during report generation.
    """
    df_hash = get_df_hash(df)
    cache_key = f"df_agg_{agg_name}_{df_hash}"

    cached_df = get_cached_item(cache_key)
    if cached_df is not None:
        return cached_df

    result = agg_func(df)
    set_cached_item(cache_key, result)
    return result


def get_cache_statistics() -> dict:
    """Return current cache hit/miss statistics."""
    stats = _get_cache_stats()
    total = stats["hits"] + stats["misses"]
    return {
        "hits": stats["hits"],
        "misses": stats["misses"],
        "total": total,
        "hit_rate": f"{(stats['hits'] / max(total, 1) * 100):.1f}%",
    }


def clear_report_cache() -> None:
    """Clear all cached report items."""
    if "report_cache" in st.session_state:
        st.session_state.report_cache = {}
    if "report_cache_stats" in st.session_state:
        st.session_state.report_cache_stats = {"hits": 0, "misses": 0}
    LOGGER.info("Report cache cleared")
