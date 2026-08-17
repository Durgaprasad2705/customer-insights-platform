"""
Customer Insights Platform – Authentication Page v7.0
Three-tab login: User Sign In | Create Account | Admin Portal
User logins require admin approval before accessing the platform.
"""
from __future__ import annotations

import logging
import time

import streamlit as st

from config import APP_SUBTITLE, ROLES
from database.db import (
    authenticate_user,
    cancel_request,
    check_request_status,
    create_login_request,
    is_user_approved,
    register_user,
)

LOGGER = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _sign_in(user: dict) -> None:
    """Mark session as authenticated and wipe ALL pending-approval state."""
    st.session_state["authenticated"]     = True
    st.session_state["user"]              = user
    st.session_state["current_page"]      = ROLES[user["role"]]["pages"][0]
    # Wipe every pending-approval key so the waiting screen can NEVER show again
    st.session_state["pending_request"]    = None
    st.session_state["pending_request_id"] = None
    st.session_state["pending_user"]       = None
    st.rerun()



# ─── Waiting-for-Approval Screen ──────────────────────────────────────────────

def _render_waiting_screen(user: dict) -> None:
    """
    Shown to a non-admin user who has logged in but is awaiting admin approval.
    Polls the DB every 4 seconds. Auto-signs-in on approval.
    """
    req_id   = st.session_state.get("pending_request_id", -1)
    username = user.get("username", "")

    status = check_request_status(req_id) if req_id != -1 else "pending"

    if status == "approved":
        # Clear ALL pending state first, then sign in — no stale state left
        st.session_state["pending_request"]    = None
        st.session_state["pending_request_id"] = None
        st.session_state["pending_user"]       = None
        _sign_in(user)
        return


    if status == "denied":
        st.session_state["pending_request"]    = None
        st.session_state["pending_request_id"] = None
        st.session_state["pending_user"]       = None
        st.error("❌ Your login request was denied by the administrator. Please contact your admin.")
        if st.button("← Back to Sign In"):
            st.rerun()
        return

    # ── Waiting UI ────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .wait-overlay {
      display:flex; flex-direction:column; align-items:center;
      justify-content:center; min-height:70vh; text-align:center;
    }
    .wait-spinner {
      width:72px; height:72px; border-radius:50%;
      border:4px solid rgba(0,212,168,0.15);
      border-top:4px solid #00D4A8;
      animation:spin 1.1s linear infinite;
      margin:0 auto 28px;
    }
    @keyframes spin { to { transform:rotate(360deg); } }
    .wait-title {
      font-family:'Space Grotesk',sans-serif;
      font-size:1.5rem; font-weight:700; color:var(--nx-text-1, #EEEEFF);
      margin-bottom:10px; letter-spacing:-0.02em;
    }
    .wait-sub {
      font-size:0.88rem; color:var(--nx-text-2, #9898BB); line-height:1.65;
      max-width:380px; margin:0 auto 24px;
    }
    .wait-badge {
      display:inline-flex; align-items:center; gap:8px;
      padding:8px 18px; border-radius:9999px;
      background:rgba(0,212,168,0.08);
      border:1px solid rgba(0,212,168,0.25);
      color:#00D4A8; font-size:0.82rem; font-weight:600;
      font-family:'Space Grotesk',sans-serif;
      margin-bottom:30px;
    }
    .wait-info {
      background:rgba(255,255,255,0.03);
      border:1px solid rgba(255,255,255,0.07);
      border-radius:12px; padding:16px 24px;
      font-size:0.8rem; color:var(--nx-text-2, #9898BB);
      font-family:'Space Grotesk',sans-serif;
      max-width:340px; margin:0 auto;
      text-align:left; line-height:1.8;
    }
    </style>
    """, unsafe_allow_html=True)

    role      = user.get("role", "Analyst")
    full_name = user.get("full_name", username)
    initials  = "".join(w[0].upper() for w in full_name.split()[:2]) or "U"

    st.markdown(f"""
    <div class="wait-overlay">
      <div class="wait-spinner"></div>
      <div class="wait-title">Awaiting Admin Approval</div>
      <div class="wait-sub">
        Your login request has been sent to the platform administrator.
        You'll be signed in automatically once it's approved.
      </div>
      <div class="wait-badge">
        <span style="width:8px;height:8px;border-radius:50%;background:#00D4A8;
          box-shadow:0 0 8px rgba(0,212,168,0.8);display:inline-block;
          animation:spin 2s linear infinite;"></span>
        Checking every few seconds…
      </div>
      <div class="wait-info">
        <div style="color:var(--nx-text-1, #EEEEFF);font-weight:600;margin-bottom:6px;">Your Request</div>
        👤 <strong style="color:var(--nx-text-1, #EEEEFF);">{full_name}</strong><br>
        🏷️ Role: <strong style="color:#9B6DFF;">{role}</strong><br>
        🔐 Username: <code style="color:#00D4A8;">{username}</code>
      </div>
    </div>
    """, unsafe_allow_html=True)


    # ── Back to Login (clears session only — request stays pending for admin) ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("← Back to Login Page", use_container_width=True, key="back_to_login_btn"):
        # Do NOT cancel the DB request — leave it pending for the admin to decide.
        # Just return to the login page view.
        st.session_state["pending_request"]    = None
        st.session_state["pending_request_id"] = None
        st.session_state["pending_user"]       = None
        st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    col_cancel, col_refresh = st.columns([1, 1])
    with col_cancel:
        # This button explicitly cancels the request in the DB
        if st.button("✕  Cancel Request", use_container_width=True, key="cancel_req_btn"):
            if req_id != -1:
                cancel_request(req_id)
            st.session_state["pending_request"]    = None
            st.session_state["pending_request_id"] = None
            st.session_state["pending_user"]       = None
            st.rerun()
    with col_refresh:
        if st.button("↻  Refresh Status", use_container_width=True, key="refresh_req_btn"):
            st.rerun()

    # Auto-poll every 4 seconds
    time.sleep(4)
    st.rerun()



# ─── Main Login Renderer ──────────────────────────────────────────────────────

def render_login() -> None:
    """Render the auth page with three tabs."""

    # ── Check if this user is in pending state ────────────────────────────────
    if st.session_state.get("pending_request") == "waiting":
        pending_user = st.session_state.get("pending_user")
        if pending_user:
            _render_waiting_screen(pending_user)
            return

    # ── Aurora background ─────────────────────────────────────────────────────
    st.markdown('<div class="ip-auth-bg"></div>', unsafe_allow_html=True)

    hero_col, form_col = st.columns([1.15, 1], gap="large")

    # ══════════════════════════════════════════════════════════
    # LEFT — Hero Panel
    # ══════════════════════════════════════════════════════════
    with hero_col:
        st.markdown(f"""
        <div class="ip-login-hero">

          <!-- Logo mark -->
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:30px;">
            <div style="
              width:42px;height:42px;
              background:linear-gradient(135deg,#00A884,#00D4A8);
              border-radius:12px;
              display:flex;align-items:center;justify-content:center;
              font-size:20px;
              box-shadow:0 4px 24px rgba(0,212,168,0.35),
                         inset 0 1px 0 rgba(255,255,255,0.2);">
              ✦
            </div>
            <div>
              <div style="
                font-family:'Space Grotesk',sans-serif;
                font-size:1.1rem;font-weight:700;
                color:var(--nx-text-1, #EEEEFF);letter-spacing:-0.02em;">Customer Insights Platform</div>
              <div style="
                font-size:0.6rem;font-weight:600;color:var(--nx-text-4, #2D2D50);
                text-transform:uppercase;letter-spacing:0.1em;
                font-family:'Space Grotesk',sans-serif;">
                v7.0 Enterprise · AI Intelligence
              </div>
            </div>
          </div>

          <!-- Headline with gradient accent -->
          <div class="ip-login-hero-title">
            Intelligence that<br>
            <span style="
              background:linear-gradient(135deg,#00D4A8,#9B6DFF);
              -webkit-background-clip:text;
              -webkit-text-fill-color:transparent;
              background-clip:text;">
              drives growth.
            </span>
          </div>
          <div class="ip-login-hero-sub">{APP_SUBTITLE}</div>

          <!-- Feature list -->
          <div class="ip-login-feature">
            <div class="ip-login-feature-icon">🤖</div>
            <div class="ip-login-feature-text">
              <strong>Predictive AI Engine</strong>
              <p>Churn prediction, CLV regression &amp; revenue forecasting</p>
            </div>
          </div>
          <div class="ip-login-feature">
            <div class="ip-login-feature-icon">📊</div>
            <div class="ip-login-feature-text">
              <strong>Executive Dashboards</strong>
              <p>Real-time KPIs, interactive charts &amp; automated insights</p>
            </div>
          </div>
          <div class="ip-login-feature">
            <div class="ip-login-feature-icon">📤</div>
            <div class="ip-login-feature-text">
              <strong>Universal Data Ingestion</strong>
              <p>Upload any CSV or Excel — auto-detect, clean &amp; enrich</p>
            </div>
          </div>
          <div class="ip-login-feature">
            <div class="ip-login-feature-icon">🛡️</div>
            <div class="ip-login-feature-text">
              <strong>Admin-Controlled Access</strong>
              <p>Every login approved by admin — zero unauthorised access</p>
            </div>
          </div>

          <!-- Stat pills -->
          <div style="display:flex;gap:8px;margin-top:26px;flex-wrap:wrap;">
            <div style="
              padding:6px 13px;border-radius:9999px;
              background:rgba(0,212,168,0.08);
              border:1px solid rgba(0,212,168,0.2);
              color:#00D4A8;font-size:0.71rem;font-weight:600;
              font-family:'Space Grotesk',sans-serif;">
              ✦ 99.9% Uptime
            </div>
            <div style="
              padding:6px 13px;border-radius:9999px;
              background:rgba(155,109,255,0.08);
              border:1px solid rgba(155,109,255,0.2);
              color:#9B6DFF;font-size:0.71rem;font-weight:600;
              font-family:'Space Grotesk',sans-serif;">
              ✦ Admin Approved
            </div>
            <div style="
              padding:6px 13px;border-radius:9999px;
              background:rgba(255,173,0,0.08);
              border:1px solid rgba(255,173,0,0.2);
              color:#FFAD00;font-size:0.71rem;font-weight:600;
              font-family:'Space Grotesk',sans-serif;">
              ✦ 3 Role Tiers
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # RIGHT — Form Panel
    # ══════════════════════════════════════════════════════════
    with form_col:
        st.markdown("""
        <div class="ip-login-panel">
          <div class="ip-login-panel-title">Welcome back</div>
          <div class="ip-login-panel-sub">Sign in to your intelligence workspace</div>
        </div>
        """, unsafe_allow_html=True)

        login_tab, signup_tab, admin_tab = st.tabs([
            "🔑  Sign In",
            "✦  Create Account",
            "🛡️  Admin Portal",
        ])

        # ══════════════════════════════════════════════════════
        # Tab 1 — User Sign In (Analyst / Manager)
        # ══════════════════════════════════════════════════════
        with login_tab:
            st.markdown("""
            <div style="
              background:rgba(0,212,168,0.05);
              border:1px solid rgba(0,212,168,0.15);
              border-radius:10px; padding:10px 14px;
              margin-bottom:14px;
              font-family:'Space Grotesk',sans-serif;
              font-size:0.78rem; color:var(--nx-text-2, #9898BB); line-height:1.6;">
              🔒 <strong style="color:#00D4A8;">Admin approval required.</strong>
              After signing in, your request will be sent to the administrator.
            </div>
            """, unsafe_allow_html=True)

            show_pw = st.checkbox("Show password", key="show_login_pw")

            with st.form("login_form"):
                username = st.text_input(
                    "Username", placeholder="Enter your username", key="login_username"
                )
                password = st.text_input(
                    "Password",
                    placeholder="Enter your password",
                    type="default" if show_pw else "password",
                    key="login_password",
                )
                submitted = st.form_submit_button("Request Access  →", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("Please enter both username and password.")
                else:
                    user = authenticate_user(username.strip(), password)
                    if user:
                        if user["role"] == "Admin":
                            st.error("⚠️ Admin accounts must use the 🛡️ Admin Portal tab.")
                        else:
                            # Check if the user is already approved from a previous request
                            if is_user_approved(user["username"]):
                                _sign_in(user)
                            else:
                                # Create pending request
                                req_id = create_login_request(
                                    user["username"], user["full_name"], user["role"]
                                )
                                st.session_state["pending_request"]    = "waiting"
                                st.session_state["pending_request_id"] = req_id
                                st.session_state["pending_user"]       = user
                                st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")

        # ══════════════════════════════════════════════════════
        # Tab 2 — Create Account
        # ══════════════════════════════════════════════════════
        with signup_tab:
            st.markdown("""
            <div style="
              background:rgba(155,109,255,0.05);
              border:1px solid rgba(155,109,255,0.15);
              border-radius:10px; padding:10px 14px; margin-bottom:14px;
              font-family:'Space Grotesk',sans-serif;
              font-size:0.78rem; color:var(--nx-text-2, #9898BB); line-height:1.6;">
              ℹ️ After registering, use <strong style="color:#9B6DFF;">Sign In</strong>
              to request access. Admin approval is required to enter the platform.
            </div>
            """, unsafe_allow_html=True)

            show_sp = st.checkbox("Show password", key="show_signup_pw")
            with st.form("signup_form", clear_on_submit=True):
                s_username = st.text_input("Username (3–40 chars)", placeholder="Choose a username")
                s_fullname = st.text_input("Full Name", placeholder="Your full name")
                s_email    = st.text_input("Email Address", placeholder="your@email.com")
                s_role     = st.selectbox(
                    "Role", ["Analyst", "Manager"],
                    help="Admin accounts can only be created by existing admins.",
                )
                s_pw  = st.text_input(
                    "Password", placeholder="Create a strong password (min. 8 chars)",
                    type="default" if show_sp else "password",
                )
                s_pw2 = st.text_input(
                    "Confirm Password", placeholder="Repeat your password",
                    type="default" if show_sp else "password",
                )
                s_submit = st.form_submit_button("Create Account  →", use_container_width=True)

            if s_submit:
                if s_pw != s_pw2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(s_username, s_fullname, s_email, s_pw, s_role)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.info("✅ Account created! Go to Sign In tab to request access.")

        # ══════════════════════════════════════════════════════
        # Tab 3 — Admin Portal (distinct design)
        # ══════════════════════════════════════════════════════
        with admin_tab:
            # Amber/shield security styling
            st.markdown("""
            <style>
            /* Admin portal tab accent overrides */
            div[data-testid="stForm"][id*="admin"] button[kind="primaryFormSubmit"] {
              background: linear-gradient(135deg,#B45309,#D97706) !important;
            }
            </style>
            <div style="
              background:linear-gradient(135deg,rgba(180,83,9,0.12),rgba(217,119,6,0.06));
              border:1px solid rgba(217,119,6,0.35);
              border-left:3px solid #D97706;
              border-radius:12px; padding:16px 18px; margin-bottom:16px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <span style="font-size:1.4rem;">🛡️</span>
                <div>
                  <div style="
                    font-family:'Space Grotesk',sans-serif;
                    font-size:0.9rem;font-weight:700;color:#FCD34D;
                    letter-spacing:-0.01em;">Administrator Portal</div>
                  <div style="font-size:0.7rem;color:#92400E;
                    text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">
                    Restricted Access · Authorised Personnel Only
                  </div>
                </div>
              </div>
              <div style="
                font-size:0.78rem;color:#D97706;line-height:1.6;
                font-family:'Space Grotesk',sans-serif;">
                Admin sessions bypass the approval queue and have full platform control.
                Misuse of admin credentials will be logged and audited.
              </div>
            </div>
            """, unsafe_allow_html=True)

            show_adm_pw = st.checkbox("Show password", key="show_admin_pw")

            with st.form("admin_login_form"):
                adm_user = st.text_input(
                    "Admin Username",
                    placeholder="Enter admin username",
                    key="admin_username_input",
                )
                adm_pass = st.text_input(
                    "Admin Password",
                    placeholder="Enter admin password",
                    type="default" if show_adm_pw else "password",
                    key="admin_password_input",
                )
                adm_submit = st.form_submit_button(
                    "🛡️  Access Admin Portal", use_container_width=True
                )

            if adm_submit:
                if not adm_user.strip() or not adm_pass:
                    st.error("Please enter both username and password.")
                else:
                    adm = authenticate_user(adm_user.strip(), adm_pass)
                    if adm and adm["role"] == "Admin":
                        _sign_in(adm)
                    else:
                        st.error("❌ Invalid admin credentials or insufficient privileges.")

            st.markdown("""
            <div style="
              margin-top:16px;
              padding:10px 14px; border-radius:8px;
              background:rgba(255,255,255,0.02);
              border:1px solid rgba(255,255,255,0.05);
              font-family:'Space Grotesk',sans-serif;font-size:0.72rem;
              color:#3E3E5A;line-height:1.8;text-align:center;">
              🔒 All admin actions are recorded in the audit log
            </div>
            """, unsafe_allow_html=True)
