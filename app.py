"""
Customer Insights Platform – AI Customer Intelligence Platform
Main entry point: page config → CSS → session init → auth gate → routing.

Run:  streamlit run app.py
"""

from __future__ import annotations

# Standard Library
import logging
import os

# Third-Party Libraries
import pandas as pd
import streamlit as st
import streamlit.components.v1 as _components

# ─── Page Config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Customer Insights Platform – AI Customer Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Local Modules
from config import APP_NAME, CSS_DIR, ROLES                   # noqa: E402

logging.basicConfig(level=logging.WARNING)
LOGGER = logging.getLogger(__name__)


# ─── CSS Loader ───────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _read_css() -> str:
    """Read CSS from disk with caching for low latency."""
    css_file = os.path.join(CSS_DIR, "theme.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as fh:
            return fh.read()
    LOGGER.warning("theme.css not found at %s", css_file)
    return ""

def _load_css() -> None:
    css = _read_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

_load_css()


# ─── Theme Injection ──────────────────────────────────────────────────────────

def _inject_theme() -> None:
    """Use a zero-height iframe component to run JS that sets data-theme on the
    parent document. st.markdown <script> tags are stripped by Streamlit, so
    components.html is the only reliable way to execute JavaScript."""
    theme = st.session_state.get("theme", "dark")
    _components.html(
        f"""
        <script>
        (function() {{
            try {{
                var doc = window.parent.document;
                doc.documentElement.setAttribute('data-theme', '{theme}');
                var app = doc.querySelector('.stApp');
                if (app) app.setAttribute('data-theme', '{theme}');
                // Also set on every major Streamlit container
                var containers = doc.querySelectorAll(
                    '[data-testid="stAppViewContainer"], [data-testid="stMain"], section[data-testid="stSidebar"]'
                );
                containers.forEach(function(el) {{
                    el.setAttribute('data-theme', '{theme}');
                }});
            }} catch(e) {{ console.warn('Theme injection failed:', e); }}
        }})();
        </script>
        """,
        height=0,
        scrolling=False,
    )

_inject_theme()


# ─── Session State Init ───────────────────────────────────────────────────────

def _init_session() -> None:
    defaults = {
        "authenticated":     False,
        "user":              None,
        "current_page":      "Dashboard",
        "theme":             "dark",
        "raw_df":            None,
        "cleaned_df":        None,
        "cleaning_report":   None,
        "upload_signature":  None,
        "seg_auto_run":      True,
        "pending_request":   None,
        "pending_request_id": None,
        "pending_user":      None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session()


# ─── Authentication Gate ──────────────────────────────────────────────────────

if not st.session_state.get("authenticated"):
    from pages.auth import render_login
    render_login()
    st.stop()



# ─── Authenticated Shell ──────────────────────────────────────────────────────

current_user  = st.session_state["user"] or {"username": "guest", "full_name": "Guest", "email": "", "role": "Admin"}
user_role     = current_user.get("role", "Admin")
allowed_pages = ROLES.get(user_role, ROLES["Admin"])["pages"]

# Active cleaned dataframe — None if no dataset uploaded yet
import pandas as pd
active_df = st.session_state["cleaned_df"]
_no_data  = active_df is None

# Pass an empty DataFrame to the sidebar when no data is loaded
# so filters don't crash; pages receive empty df and show upload prompt.
_sidebar_df = active_df if not _no_data else pd.DataFrame()

# ─── Sidebar (navigation + filters) ──────────────────────────────────────────
from components.sidebar import render_sidebar
selected_page, filtered_df = render_sidebar(current_user, _sidebar_df)

# ─── Top Navigation Bar ───────────────────────────────────────────────────────
from components.topbar import render_topbar
render_topbar(selected_page, current_user)

# ─── No Data Guard (skip for Upload Dataset and non-data pages) ───────────────
_data_free_pages = {"Upload Dataset", "Admin Panel", "Settings"}

if _no_data and selected_page not in _data_free_pages:
    st.markdown("""
    <div style="
        background:var(--nx-teal-sub, rgba(0,212,168,0.05));
        border:1px solid var(--nx-border-teal, rgba(0,212,168,0.18));
        border-left:2px solid var(--nx-teal, #00D4A8);
        border-radius:14px;
        padding:36px 40px;
        margin:48px auto;
        max-width:620px;
        text-align:center;">
      <div style="
        width:52px;height:52px;margin:0 auto 16px;
        background:var(--nx-teal-sub, rgba(0,212,168,0.1));
        border-radius:12px;
        display:flex;align-items:center;justify-content:center;
        font-size:22px;
        box-shadow:0 0 20px var(--nx-teal-glow, rgba(0,212,168,0.15));">📂</div>
      <div style="
        font-family:'Space Grotesk',sans-serif;
        font-size:1.1rem;font-weight:700;
        color:var(--nx-text-1, #EEEEFF);margin-bottom:8px;
        letter-spacing:-0.02em;">
        No Dataset Loaded
      </div>
      <div style="
        color:var(--nx-text-2, #9898BB);font-size:0.83rem;
        line-height:1.65;margin-bottom:22px;">
        Upload a CSV or Excel file to unlock all analytics,<br>
        dashboards, and AI/ML features. Processed locally.
      </div>
      <div style="
        display:inline-flex;align-items:center;gap:7px;
        padding:7px 16px;border-radius:9999px;
        background:var(--nx-teal-sub, rgba(0,212,168,0.1));
        border:1px solid var(--nx-border-teal, rgba(0,212,168,0.28));
        color:var(--nx-teal, #00D4A8);font-size:0.79rem;font-weight:600;
        font-family:'Space Grotesk',sans-serif;">
        ✦ Navigate to <strong>Upload Dataset</strong> in the sidebar
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Guard: if filtered df is empty warn but don't crash the page
if not _no_data and filtered_df.empty:
    st.warning("⚠️ No records match the selected filters. Adjust or clear them to continue.")
    st.stop()

# ─── Page Router ─────────────────────────────────────────────────────────────

df = filtered_df  # all pages receive the filtered dataframe


if selected_page == "Dashboard":
    from pages.dashboard import render
    render(df)

elif selected_page == "Upload Dataset":
    from pages.upload import render
    render(df, current_user)

elif selected_page == "Customer Profiles":
    from pages.customer_profiles import render
    render(df)

elif selected_page == "Customer Segmentation":
    from pages.segmentation import render
    render(df)

elif selected_page == "Product Analytics":
    from pages.product_analytics import render
    render(df)

elif selected_page == "Sales Analytics":
    from pages.sales_analytics import render
    render(df)

elif selected_page == "Inventory Analytics":
    from pages.inventory import render
    render(df)

elif selected_page == "Machine Learning":
    from pages.machine_learning import render
    render(df)

elif selected_page == "Reports":
    from pages.reports_page import render
    render(df, current_user)

elif selected_page == "Admin Panel":
    if user_role == "Admin":
        from pages.admin import render
        render()
    else:
        st.error("🚫 Access denied. Admin role required.")

elif selected_page == "Settings":
    from pages.settings import render
    render(current_user)

else:
    st.error(f"Page '{selected_page}' is not registered. Please contact support.")
