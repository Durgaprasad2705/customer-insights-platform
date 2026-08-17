"""
Customer Insights Platform – Admin Panel Page
User management, login approvals, audit logs, database stats, upload history.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.kpi_cards import section_title
from database.db import (
    approve_request,
    deny_request,
    get_all_login_requests,
    get_all_users,
    get_database_stats,
    get_pending_count,
    get_pending_requests,
    get_recent_activity_logs,
    get_uploaded_datasets,
)


def render() -> None:
    """Render the Admin Panel page."""

    current_admin = st.session_state.get("user", {}).get("username", "admin")

    st.markdown("""
    <div class="ip-card">
      <div class="ip-card-title">⚙️ System Administration Panel</div>
      <div class="ip-card-sub">
        Manage users, approve login requests, review audit logs, and track uploads.
        Admin access only.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Database Stats ────────────────────────────────────────────────────────
    stats        = get_database_stats()
    pending_n    = get_pending_count()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Registered Users",  stats["users"])
    k2.metric("Audit Log Entries", stats["logs"])
    k3.metric("Uploaded Datasets", stats["uploads"])
    k4.metric("Database Size",     f"{stats['db_size_kb']} KB")
    k5.metric("⏳ Pending Logins", pending_n, delta="Needs Review" if pending_n else None,
              delta_color="inverse")

    # ── Notification banner if there are pending requests ─────────────────────
    if pending_n:
        st.markdown(f"""
        <div style="
          background:linear-gradient(135deg,rgba(255,173,0,0.1),rgba(255,107,138,0.05));
          border:1px solid rgba(255,173,0,0.35);
          border-left:3px solid #FFAD00;
          border-radius:12px; padding:14px 20px; margin:8px 0 16px;
          display:flex; align-items:center; gap:14px;">
          <span style="font-size:1.6rem;">🔔</span>
          <div>
            <div style="
              font-family:'Space Grotesk',sans-serif;
              font-size:0.92rem;font-weight:700;color:#FCD34D;">
              {pending_n} Login Request{"s" if pending_n > 1 else ""} Awaiting Approval
            </div>
            <div style="font-size:0.78rem;color:#D97706;margin-top:2px;">
              Review them in the <strong>🔔 Login Approvals</strong> tab below.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Build tab label with badge
    approval_label = f"🔔 Login Approvals  {'🔴' if pending_n else ''}"
    tab_approvals, tab_users, tab_logs, tab_uploads, tab_system = st.tabs([
        approval_label, "👥 Users", "📋 Audit Logs", "📤 Upload History", "🔧 System"
    ])

    # ══════════════════════════════════════════════════════════
    # Tab 1 — Login Approvals
    # ══════════════════════════════════════════════════════════
    with tab_approvals:
        st.markdown(section_title("Pending Login Requests", "🔔"), unsafe_allow_html=True)

        pending = get_pending_requests()

        if not pending:
            st.markdown("""
            <div style="
              text-align:center;padding:48px 0;
              font-family:'Space Grotesk',sans-serif;
              color:#4E4E7A;font-size:0.88rem;">
              <div style="font-size:2.5rem;margin-bottom:12px;">✅</div>
              No pending login requests. All clear!
            </div>
            """, unsafe_allow_html=True)
        else:
            for req in pending:
                req_id    = req["id"]
                uname     = req["username"]
                fname     = req["full_name"]
                role      = req["role"]
                req_time  = req["requested_at"]

                role_colors = {
                    "Analyst": ("#9B6DFF", "rgba(155,109,255,0.1)"),
                    "Manager": ("#22C55E", "rgba(34,197,94,0.1)"),
                }
                r_color, r_bg = role_colors.get(role, ("#9898BB", "rgba(152,152,187,0.1)"))
                initials = "".join(w[0].upper() for w in fname.split()[:2]) or "U"

                st.markdown(f"""
                <div style="
                  background:rgba(255,255,255,0.03);
                  border:1px solid rgba(255,173,0,0.2);
                  border-left:3px solid #FFAD00;
                  border-radius:14px; padding:18px 20px; margin-bottom:12px;">
                  <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
                    <div style="
                      width:44px;height:44px;border-radius:50%;flex-shrink:0;
                      background:linear-gradient(135deg,{r_color},{r_bg.replace('0.1','0.7')});
                      display:flex;align-items:center;justify-content:center;
                      font-family:'Space Grotesk',sans-serif;
                      font-size:14px;font-weight:700;color:#02020A;">
                      {initials}
                    </div>
                    <div style="flex:1;min-width:0;">
                      <div style="
                        font-family:'Space Grotesk',sans-serif;
                        font-size:0.96rem;font-weight:700;color:var(--nx-text-1, #EEEEFF);">
                        {fname}
                      </div>
                      <div style="font-size:0.78rem;color:var(--nx-text-2, #9898BB);margin-top:2px;">
                        @{uname} ·
                        <span style="
                          background:{r_bg};color:{r_color};
                          padding:2px 8px;border-radius:9999px;
                          font-size:0.7rem;font-weight:600;
                          border:1px solid {r_color}44;">
                          {role}
                        </span>
                      </div>
                    </div>
                    <div style="
                      font-size:0.7rem;color:#4E4E7A;
                      font-family:'Space Grotesk',sans-serif;
                      text-align:right;flex-shrink:0;">
                      🕐 {req_time}
                    </div>
                  </div>
                """, unsafe_allow_html=True)

                col_approve, col_deny = st.columns([1, 1])
                with col_approve:
                    if st.button(
                        f"✅  Approve", key=f"approve_{req_id}",
                        use_container_width=True,
                    ):
                        if approve_request(req_id, current_admin):
                            st.success(f"✅ Approved login for **{fname}**")
                            st.rerun()
                with col_deny:
                    if st.button(
                        f"❌  Deny", key=f"deny_{req_id}",
                        use_container_width=True,
                    ):
                        if deny_request(req_id, current_admin):
                            st.warning(f"❌ Denied login for **{fname}**")
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        # History
        st.markdown(section_title("Approval History (Last 30)", "📋"), unsafe_allow_html=True)
        history = get_all_login_requests(limit=30)
        if history:
            hist_df = pd.DataFrame(history)
            hist_df = hist_df[hist_df["status"] != "pending"]
            if not hist_df.empty:
                st.dataframe(hist_df, use_container_width=True)
            else:
                st.info("No decisions made yet.")
        else:
            st.info("No login request history yet.")

        # Auto-refresh when there are pending requests
        if pending_n:
            st.markdown("""
            <div style="text-align:center;font-size:0.72rem;color:#4E4E7A;
              margin-top:12px;font-family:'Space Grotesk',sans-serif;">
              🔄 This page auto-refreshes while requests are pending…
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # Tab 2 — Users
    # ══════════════════════════════════════════════════════════
    with tab_users:
        st.markdown(section_title("Registered Platform Users", "👥"), unsafe_allow_html=True)
        users = get_all_users()
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True)
        else:
            st.info("No users found.")

    # ══════════════════════════════════════════════════════════
    # Tab 3 — Audit Logs
    # ══════════════════════════════════════════════════════════
    with tab_logs:
        col_lim, _ = st.columns([1, 3])
        with col_lim:
            limit = st.selectbox("Show last N entries", [25, 50, 100, 200], index=1, key="log_limit")
        st.markdown(section_title(f"Recent Activity Logs (last {limit})", "📋"), unsafe_allow_html=True)
        logs = get_recent_activity_logs(limit=limit)
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.info("No activity logs found.")

    # ══════════════════════════════════════════════════════════
    # Tab 4 — Upload History
    # ══════════════════════════════════════════════════════════
    with tab_uploads:
        st.markdown(section_title("Dataset Upload History", "📤"), unsafe_allow_html=True)
        uploads = get_uploaded_datasets(limit=30)
        if uploads:
            st.dataframe(pd.DataFrame(uploads), use_container_width=True)
        else:
            st.info("No uploads recorded yet.")

    # ══════════════════════════════════════════════════════════
    # Tab 5 — System Info
    # ══════════════════════════════════════════════════════════
    with tab_system:
        st.markdown(section_title("System Information", "🔧"), unsafe_allow_html=True)
        import sys, platform
        sys_info = {
            "Python Version":    sys.version.split()[0],
            "Platform":          platform.system() + " " + platform.release(),
            "Streamlit Version": st.__version__,
        }
        try:
            import pandas as pd_
            sys_info["Pandas Version"] = pd_.__version__
            import sklearn
            sys_info["Scikit-learn Version"] = sklearn.__version__
        except Exception:
            pass

        for k, v in sys_info.items():
            st.markdown(f"""
            <div class="ip-stat-row">
              <span class="ip-stat-label">{k}</span>
              <span class="ip-stat-value">{v}</span>
            </div>
            """, unsafe_allow_html=True)
