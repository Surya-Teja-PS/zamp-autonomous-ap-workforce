"""
app.py
------
Streamlit application entry point for InvoiceAI.
Uses modern st.navigation and st.Page to guarantee:
  1. Zero sidebar navigation shown before login.
  2. Strict role-based isolation — users only access their authorized views.
  3. Integrated design system and demo mode.
"""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from core.auth import get_session_user
from utils.ui_components import render_login_page, inject_css

st.set_page_config(
    page_title="InvoiceAI — AP Processing System",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _page_vendor():
    from views.vendor_portal import render
    render()


def _page_finance():
    from views.finance_dashboard import render
    render()


def _page_procurement():
    from views.role_views import render_procurement
    render_procurement()


def _page_warehouse():
    from views.role_views import render_warehouse
    render_warehouse()


def _page_detail():
    from views.invoice_detail import render
    render()


def main():
    user = get_session_user()

    # ── Unauthenticated State: Show Login Page Only ───────────────────────
    if not user:
        p_login = st.Page(render_login_page, title="Sign In — InvoiceAI")
        nav = st.navigation([p_login], position="hidden")
        nav.run()
        return

    # ── Authenticated State: Strict Role-Based Routing ────────────────────
    role = user.get("role", "")
    nav_page = st.session_state.get("nav_page", "")

    # Main role landing page
    if role == "vendor":
        p_main = st.Page(
            _page_vendor,
            title="Vendor Portal",
            icon="🏭",
            default=(nav_page != "invoice_detail")
        )
    elif role == "finance_ap":
        p_main = st.Page(
            _page_finance,
            title="Finance Dashboard",
            icon="💼",
            default=(nav_page != "invoice_detail")
        )
    elif role == "procurement":
        p_main = st.Page(
            _page_procurement,
            title="Procurement Portal",
            icon="📦",
            default=(nav_page != "invoice_detail")
        )
    elif role == "warehouse":
        p_main = st.Page(
            _page_warehouse,
            title="Warehouse Receiving",
            icon="🚚",
            default=(nav_page != "invoice_detail")
        )
    else:
        st.error(f"Unrecognized user role: {role}")
        return

    p_detail = st.Page(
        _page_detail,
        title="Invoice Details",
        icon="📄",
        default=(nav_page == "invoice_detail")
    )

    pages = [p_main, p_detail]
    nav = st.navigation(pages, position="hidden")

    if "nav_page" in st.session_state:
        target = st.session_state.pop("nav_page")
        if target == "invoice_detail":
            st.switch_page(p_detail)
        elif target in ("finance_dashboard", "vendor_portal", "role_portal", "main"):
            st.switch_page(p_main)

    nav.run()


if __name__ == "__main__":
    main()
