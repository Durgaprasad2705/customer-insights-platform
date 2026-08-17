"""
Customer Insights Platform Database Layer
SQLite auto-init, CRUD helpers, audit logging, user management,
and login-approval workflow.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import re
import sqlite3
from typing import Any, Optional

from config import DB_PATH, ROLES

LOGGER = logging.getLogger(__name__)
_SALT = "Customer Insights Platform_secure_salt_2026"


import streamlit as st

_INIT_DONE = False

# ─── Connection ───────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    """Return a high-performance thread-safe SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


# ─── Password Hashing ─────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), _SALT.encode(), 100_000
    ).hex()


# ─── Schema Initialisation ───────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables, indexes, seed default accounts, and self-heal admin password once."""
    global _INIT_DONE
    if _INIT_DONE:
        return

    conn = _connect()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            full_name     TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login    TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS uploaded_datasets (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filename     TEXT    NOT NULL,
            row_count    INTEGER,
            column_count INTEGER,
            file_size_kb REAL,
            uploaded_by  TEXT    NOT NULL,
            uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status       TEXT    DEFAULT 'Cleaned'
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL,
            action    TEXT    NOT NULL,
            details   TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS system_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS pending_logins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status      TEXT    NOT NULL DEFAULT 'pending',
            reviewed_by TEXT,
            reviewed_at TIMESTAMP
        );

        -- Performance Indexes
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_pending_logins_status ON pending_logins(status);
        CREATE INDEX IF NOT EXISTS idx_uploaded_datasets_uploaded_at ON uploaded_datasets(uploaded_at DESC);
    """)

    # ── Seed default accounts (only on first run) ─────────────────────────────
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        seeds = [
            ("admin",   "System Administrator",      "admin@customerinsights.io",   _hash("Admin@2026"),   "Admin"),
            ("analyst", "Senior Data Analyst",       "analyst@customerinsights.io", _hash("analyst123"),   "Analyst"),
            ("manager", "Retail Operations Manager", "manager@customerinsights.io", _hash("manager123"),   "Manager"),
        ]
        c.executemany(
            "INSERT INTO users (username, full_name, email, password_hash, role) VALUES (?,?,?,?,?)",
            seeds,
        )
        c.execute(
            "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
            ("SYSTEM", "DATABASE_INIT", "Database initialised with 3 default seed accounts"),
        )
    else:
        # ── Self-heal: always force the admin password to the correct hash ─────
        c.execute(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (_hash("Admin@2026"),),
        )

    conn.commit()
    conn.close()
    _INIT_DONE = True


# ─── Authentication ───────────────────────────────────────────────────────────

def authenticate_user(username: str, password_raw: str) -> Optional[dict[str, Any]]:
    """Validate credentials and return the user dict, or None on failure."""
    if not username or not password_raw:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username.lower().strip(), _hash(password_raw)),
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.datetime.now(), row["id"]),
        )
        conn.execute(
            "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
            (row["username"], "LOGIN", "Successful login"),
        )
        get_recent_activity_logs.clear()
        get_database_stats.clear()
        return dict(row)


def register_user(
    username: str, full_name: str, email: str, password_raw: str, role: str = "Analyst"
) -> tuple[bool, str]:
    """Register a new platform user."""
    username  = username.strip().lower()
    full_name = full_name.strip()
    email     = email.strip().lower()

    if not re.fullmatch(r"[a-z0-9_.\-]{3,40}", username):
        return False, "Username must be 3–40 chars: letters, numbers, dots, underscores, hyphens."
    if len(full_name) < 2:
        return False, "Please provide your full name."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False, "Enter a valid email address."
    if len(password_raw) < 8:
        return False, "Password must be at least 8 characters."
    if role not in ROLES or role == "Admin":
        return False, "That role is not available for self-registration."

    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, full_name, email, password_hash, role) VALUES (?,?,?,?,?)",
                (username, full_name, email, _hash(password_raw), role),
            )
            conn.execute(
                "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
                (username, "REGISTER", f"New account registered as {role}"),
            )
        get_all_users.clear()
        get_database_stats.clear()
        get_recent_activity_logs.clear()
        return True, "Account created successfully! You can now sign in."
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."
    except sqlite3.Error:
        LOGGER.exception("register_user failed")
        return False, "Registration failed. Please try again."


# ─── Logging Helpers ─────────────────────────────────────────────────────────

def log_activity(username: str, action: str, details: str = "") -> None:
    """Append an audit log entry."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
                (username, action, details),
            )
        get_recent_activity_logs.clear()
        get_database_stats.clear()
    except Exception:
        LOGGER.exception("log_activity failed")


def log_dataset_upload(
    filename: str, row_count: int, column_count: int,
    file_size_kb: float, uploaded_by: str,
) -> None:
    """Record metadata for an uploaded dataset."""
    try:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO uploaded_datasets
                   (filename, row_count, column_count, file_size_kb, uploaded_by)
                   VALUES (?,?,?,?,?)""",
                (filename, row_count, column_count, file_size_kb, uploaded_by),
            )
        get_uploaded_datasets.clear()
        get_database_stats.clear()
    except Exception:
        LOGGER.exception("log_dataset_upload failed")


# ─── Query Helpers ────────────────────────────────────────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def get_all_users() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, username, full_name, email, role, created_at, last_login "
            "FROM users ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=5, show_spinner=False)
def get_recent_activity_logs(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=10, show_spinner=False)
def get_database_stats() -> dict[str, Any]:
    with _connect() as conn:
        users   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        logs    = conn.execute("SELECT COUNT(*) FROM activity_logs").fetchone()[0]
        uploads = conn.execute("SELECT COUNT(*) FROM uploaded_datasets").fetchone()[0]
    size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "users":      users,
        "logs":       logs,
        "uploads":    uploads,
        "db_size_kb": round(size_bytes / 1024, 2),
    }


@st.cache_data(ttl=10, show_spinner=False)
def get_uploaded_datasets(limit: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM uploaded_datasets ORDER BY uploaded_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ─── Login Approval Workflow ──────────────────────────────────────────────────

def create_login_request(username: str, full_name: str, role: str) -> int:
    """
    Create a pending login request for a non-admin user.
    Returns the new request ID.
    Cancels any existing pending request for the same username first.
    """
    try:
        with _connect() as conn:
            # Cancel any stale pending request for this user
            conn.execute(
                "UPDATE pending_logins SET status='cancelled' "
                "WHERE username=? AND status='pending'",
                (username,),
            )
            cur = conn.execute(
                "INSERT INTO pending_logins (username, full_name, role) VALUES (?,?,?)",
                (username, full_name, role),
            )
            request_id = cur.lastrowid
            conn.execute(
                "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
                (username, "LOGIN_REQUEST", f"Pending approval as {role}"),
            )
        get_pending_count.clear()
        get_pending_requests.clear()
        get_all_login_requests.clear()
        get_recent_activity_logs.clear()
        return request_id
    except Exception:
        LOGGER.exception("create_login_request failed")
        return -1


@st.cache_data(ttl=3, show_spinner=False)
def get_pending_requests() -> list[dict]:
    """Return all currently pending login requests, newest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM pending_logins WHERE status='pending' ORDER BY requested_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=5, show_spinner=False)
def get_all_login_requests(limit: int = 50) -> list[dict]:
    """Return all login requests (any status) for the admin history view."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM pending_logins ORDER BY requested_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def is_user_approved(username: str) -> bool:
    """Check if the user has ever had a login request approved by an admin."""
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT id FROM pending_logins WHERE username=? AND status='approved' LIMIT 1",
                (username,)
            ).fetchone()
        return row is not None
    except Exception:
        return False


def check_request_status(request_id: int) -> str:
    """Return 'pending', 'approved', 'denied', 'cancelled', or 'unknown'."""
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT status FROM pending_logins WHERE id=?", (request_id,)
            ).fetchone()
        return row["status"] if row else "unknown"
    except Exception:
        return "unknown"


def approve_request(request_id: int, admin_username: str) -> bool:
    """Mark a login request as approved."""
    try:
        with _connect() as conn:
            conn.execute(
                "UPDATE pending_logins SET status='approved', reviewed_by=?, reviewed_at=? WHERE id=?",
                (admin_username, datetime.datetime.now(), request_id),
            )
            row = conn.execute(
                "SELECT username FROM pending_logins WHERE id=?", (request_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
                    (admin_username, "APPROVE_LOGIN", f"Approved login for {row['username']}"),
                )
        get_pending_count.clear()
        get_pending_requests.clear()
        get_all_login_requests.clear()
        get_recent_activity_logs.clear()
        return True
    except Exception:
        LOGGER.exception("approve_request failed")
        return False


def deny_request(request_id: int, admin_username: str) -> bool:
    """Mark a login request as denied."""
    try:
        with _connect() as conn:
            conn.execute(
                "UPDATE pending_logins SET status='denied', reviewed_by=?, reviewed_at=? WHERE id=?",
                (admin_username, datetime.datetime.now(), request_id),
            )
            row = conn.execute(
                "SELECT username FROM pending_logins WHERE id=?", (request_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "INSERT INTO activity_logs (username, action, details) VALUES (?,?,?)",
                    (admin_username, "DENY_LOGIN", f"Denied login for {row['username']}"),
                )
        get_pending_count.clear()
        get_pending_requests.clear()
        get_all_login_requests.clear()
        get_recent_activity_logs.clear()
        return True
    except Exception:
        LOGGER.exception("deny_request failed")
        return False


def cancel_request(request_id: int) -> None:
    """Allow a user to cancel their own pending request."""
    try:
        with _connect() as conn:
            conn.execute(
                "UPDATE pending_logins SET status='cancelled' WHERE id=?",
                (request_id,),
            )
        get_pending_count.clear()
        get_pending_requests.clear()
        get_all_login_requests.clear()
    except Exception:
        LOGGER.exception("cancel_request failed")


@st.cache_data(ttl=2, show_spinner=False)
def get_pending_count() -> int:
    """Fast count of pending requests — used for the notification badge."""
    try:
        with _connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM pending_logins WHERE status='pending'"
            ).fetchone()[0]
    except Exception:
        return 0


# Auto-initialise once
init_db()
