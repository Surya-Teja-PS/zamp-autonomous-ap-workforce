"""
core/auth.py
------------
Password verification and Streamlit session state helpers.
"""

import bcrypt
import streamlit as st
from core.database import get_connection, get_user_by_email, fetchone


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def login(email: str, password: str) -> dict | None:
    """
    Attempt login. Returns user dict on success, None on failure.
    Updates last_login_at on success.
    """
    conn = get_connection()
    try:
        user = get_user_by_email(conn, email)
        if not user:
            return None
        if not user["is_active"]:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        # Update last login
        conn.execute(
            "UPDATE users SET last_login_at = datetime('now') WHERE user_id = ?",
            (user["user_id"],),
        )
        conn.commit()
        return dict(user)
    finally:
        conn.close()


def get_session_user() -> dict | None:
    return st.session_state.get("user")


def set_session_user(user: dict | None):
    st.session_state["user"] = user


authenticate = login


def require_login():
    """Call at the top of any page that requires authentication."""
    if not get_session_user():
        st.warning("Please log in to continue.")
        st.stop()


def require_role(*roles: str):
    """Require the logged-in user to have one of the specified roles."""
    user = get_session_user()
    if not user or user["role"] not in roles:
        st.error("You do not have permission to view this page.")
        st.stop()


def logout():
    for key in ["user", "page", "finance_tab", "nav_page", "selected_invoice_id"]:
        st.session_state.pop(key, None)


clear_session = logout
