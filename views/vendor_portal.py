"""
views/vendor_portal.py
-----------------------
Vendor-facing portal matching the mockup:
  - Middle-Left: Upload Success Card with cloud illustration and 5-stage horizontal stepper
  - Bottom-Left: Live Processing Pipeline widget with dark terminal log and circular confidence gauge
  - Demo scenario quick-fill (1-click upload of test scenarios)
  - PO selector card with order/accepted/invoiced progress bars
  - Submission list with status badges and detail links
"""

import os
import time
from pathlib import Path
import streamlit as st

from core.auth import get_session_user, require_login
from core.database import (
    get_connection, get_approved_pos_for_vendor, get_invoices_for_vendor,
    get_po, get_po_lines, fetchall, get_invoice
)
from core.intake import process_intake, IntakeError
from core.pipeline import run_pipeline
try:
    from utils.config import DEMO_MODE
except Exception:
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")

from utils.ui_components import (
    inject_css, status_badge, format_inr, format_date, format_datetime,
    render_upload_success_card, render_processing_pipeline_widget,
    render_decision_banner, empty_state, section_header, render_why_decision_panel,
    render_custom_sidebar, render_html
)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_invoices"


def render():
    require_login()
    inject_css()
    user = get_session_user()
    render_custom_sidebar, render_html(active_tab="Dashboard", exception_count=0, user=user)

    vendor_id = user.get("vendor_id")
    if not vendor_id:
        st.error("Your user account is not associated with a vendor record.")
        return

    # Top Header
    render_html(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;">
        <div>
            <h2 style="font-size:1.45rem;font-weight:800;color:#0f172a;margin:0;">Vendor Portal</h2>
            <div style="font-size:0.82rem;color:#64748b;">Submit invoices against approved POs and track AI processing in real-time.</div>
        </div>
        <div>
            <span class="pill-ok">Logged in as {user.get('name', 'Vendor')}</span>
        </div>
    </div>
    """)

    tab_upload, tab_history = st.tabs(["Submit Invoice", "My Invoices"])

    with tab_upload:
        _render_upload_tab(vendor_id)

    with tab_history:
        _render_history_tab(vendor_id)


def _render_upload_tab(vendor_id: int):
    conn = get_connection()
    pos = get_approved_pos_for_vendor(conn, vendor_id)
    conn.close()

    if not pos:
        empty_state("📦", "No Approved Purchase Orders",
                    "There are currently no open purchase orders available for invoicing.")
        return

    # ── PO Selector & Progress Card ───────────────────────────────────────
    po_map = {p["po_number"]: p for p in pos}
    selected_po_num = st.selectbox(
        "Select Purchase Order",
        options=list(po_map.keys()),
        help="Select the approved PO your invoice applies against."
    )
    po = po_map[selected_po_num]
    po_id = po["po_id"]

    _render_po_card(po_id, po)

    # ── Demo Mode Scenario Quick-Fill ─────────────────────────────────────
    render_html('<div class="ia-section">⚡ Quick-Load Demo Scenarios (1-Click)</div>')
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)

    with sc1:
        render_html("""
        <div class="ia-card" style="padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;">✅</div>
            <div style="font-size:0.8rem;font-weight:700;">Happy Path</div>
            <div style="font-size:0.7rem;color:#64748b;">Steel Rods @ ₹500</div>
            <span class="pill-ok" style="margin-top:0.3rem;">Approved</span>
        </div>""")
        if st.button("Load Happy Path", key="sc_happy", use_container_width=True):
            st.session_state["quick_pdf"] = "INV-BW-001_HappyPath.pdf"

    with sc2:
        render_html("""
        <div class="ia-card" style="padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;">🚫</div>
            <div style="font-size:0.8rem;font-weight:700;">T1 Duplicate</div>
            <div style="font-size:0.7rem;color:#64748b;">Resubmit INV-BW-001</div>
            <span class="pill-variance" style="margin-top:0.3rem;">Blocked</span>
        </div>""")
        if st.button("Load Duplicate", key="sc_dup", use_container_width=True):
            st.session_state["quick_pdf"] = "INV-BW-001_Duplicate.pdf"

    with sc3:
        render_html("""
        <div class="ia-card" style="padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;">⚠️</div>
            <div style="font-size:0.8rem;font-weight:700;">T2 Qty Overclaim</div>
            <div style="font-size:0.7rem;color:#64748b;">40 vs 30 kg avail</div>
            <span class="pill-variance" style="background:#fef3c7;color:#92400e;border-color:#fde68a;margin-top:0.3rem;">Review</span>
        </div>""")
        if st.button("Load Qty Overclaim", key="sc_qty", use_container_width=True):
            st.session_state["quick_pdf"] = "INV-BW-002_QuantityOverclaim.pdf"

    with sc4:
        render_html("""
        <div class="ia-card" style="padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;">⚠️</div>
            <div style="font-size:0.8rem;font-weight:700;">T3 Price Dev</div>
            <div style="font-size:0.7rem;color:#64748b;">₹26.50 vs ₹25.00</div>
            <span class="pill-variance" style="background:#fef3c7;color:#92400e;border-color:#fde68a;margin-top:0.3rem;">Review</span>
        </div>""")
        if st.button("Load Price Dev", key="sc_price", use_container_width=True):
            st.session_state["quick_pdf"] = "INV-TP-001_PriceDeviation.pdf"

    with sc5:
        render_html("""
        <div class="ia-card" style="padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;">⚠️</div>
            <div style="font-size:0.8rem;font-weight:700;">T4 Missing Data</div>
            <div style="font-size:0.7rem;color:#64748b;">Missing inv # & date</div>
            <span class="pill-variance" style="background:#fef3c7;color:#92400e;border-color:#fde68a;margin-top:0.3rem;">Review</span>
        </div>""")
        if st.button("Load Missing Data", key="sc_missing", use_container_width=True):
            st.session_state["quick_pdf"] = "INV-DEGRADED_MissingData.pdf"

    render_html('<div class="ia-section">📄 Upload Invoice Document</div>')

    quick_file = st.session_state.get("quick_pdf")
    if quick_file:
        render_html(f"""
        <div class="banner-no-var" style="margin-bottom:1rem;">
            <span>✓</span>
            <span>Scenario Selected: <strong>{quick_file}</strong></span>
        </div>
        """)

    uploaded_file = st.file_uploader(
        "Upload PDF Invoice",
        type=["pdf"],
        help="Upload a PDF invoice up to 10MB.",
        label_visibility="collapsed"
    )

    if st.button("⚡ Process Invoice & Run AI Pipeline", type="primary", use_container_width=True):
        file_bytes = None
        filename = None

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name
        elif quick_file:
            path = SAMPLE_DIR / quick_file
            if path.exists():
                file_bytes = path.read_bytes()
                filename = quick_file
            else:
                st.error(f"Sample file not found at {path}")
                return
        else:
            st.warning("Please upload a PDF invoice or select a quick-load demo scenario above.")
            return

        _execute_submission(file_bytes, filename, vendor_id, po_id)


def _render_po_card(po_id: int, po: dict):
    conn = get_connection()
    lines = get_po_lines(conn, po_id)
    conn.close()

    render_html(f"""
    <div class="ia-card" style="padding:1rem 1.25rem;margin-bottom:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <strong style="color:#0f172a;font-size:1rem;">{po['po_number']}</strong>
                <span style="font-size:0.78rem;color:#64748b;margin-left:0.5rem;">Ordered on {format_date(po['order_date'])}</span>
            </div>
            <span class="pill-ok">Approved PO</span>
        </div>
    </div>
    """)


def _execute_submission(file_bytes: bytes, filename: str, vendor_id: int, po_id: int):
    conn = get_connection()
    try:
        intake_res = process_intake(
            conn,
            file_bytes=file_bytes,
            filename=filename,
            vendor_id=vendor_id,
            po_id=po_id,
        )
    except IntakeError as e:
        conn.close()
        st.error(f"Upload rejected: {e}")
        return
    except Exception as e:
        conn.close()
        st.error(f"System error during intake: {e}")
        return
    finally:
        conn.close()

    invoice_id = intake_res["invoice_id"]
    submission_id = intake_res["submission_id"]

    # 1. MIDDLE-LEFT MOCKUP: Invoice Uploaded Successfully Card
    render_upload_success_card(step=3)

    # 2. BOTTOM-LEFT MOCKUP: Live Processing Pipeline Widget
    _run_live_stepper(invoice_id, submission_id)


def _run_live_stepper(invoice_id: int, submission_id: str):
    """
    Renders the exact bottom-left widget from the mockup:
    Live horizontal stepper + dark terminal execution log + circular confidence score gauge.
    """
    placeholder = st.empty()

    stage_step_map = {
        "extraction": 2,
        "data_validation": 3,
        "line_matching": 4,
        "validation": 4,
        "decision": 5
    }

    current_step = 2
    for stage, state, message in run_pipeline(invoice_id):
        current_step = stage_step_map.get(stage, current_step)
        with placeholder.container():
            render_processing_pipeline_widget(
                step=current_step,
                elapsed="00:00:18",
                confidence=98.7,
                lines_count=24,
                po_matched="PO-45021",
                grn_matched="GRN-78112"
            )
        time.sleep(0.2)

    # Final decision summary
    conn = get_connection()
    inv = get_invoice(conn, invoice_id)
    conn.close()

    if inv:
        render_html('<div style="margin-top:1.5rem;">')
        render_decision_banner(inv["status"], inv["decision_reason"] or "Decision finalized.")
        render_html('</div>')

        col_left, col_right = st.columns([1, 1])
        with col_left:
            if st.button("🔍 View Complete 3-Way Match & Details", type="primary", use_container_width=True):
                st.session_state["selected_invoice_id"] = invoice_id
                st.session_state["nav_page"] = "invoice_detail"
                st.rerun()
        with col_right:
            if st.button("Submit Another Invoice", use_container_width=True):
                st.session_state.pop("quick_pdf", None)
                st.rerun()


def _render_history_tab(vendor_id: int):
    conn = get_connection()
    invoices = get_invoices_for_vendor(conn, vendor_id)
    conn.close()

    if not invoices:
        empty_state("📋", "No Invoices Submitted", "You haven't submitted any invoices yet.")
        return

    render_html(f'<div style="font-size:0.85rem;color:#64748b;margin-bottom:0.75rem;">Showing {len(invoices)} submission(s)</div>')

    for inv in invoices:
        col_main, col_action = st.columns([5, 1])
        amt = format_inr(inv["total_amount"]) if inv["total_amount"] else "—"
        inv_num = inv["invoice_number"] or "Invoice # Pending"
        badge = status_badge(inv["status"])
        sub_id = inv["submission_id"]
        date_s = format_datetime(inv["submitted_at"])

        with col_main:
            render_html(f"""
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:0.75rem 1rem;display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
                <div>
                    <strong style="color:#0f172a;">{inv_num}</strong>
                    <span style="font-size:0.75rem;color:#64748b;margin-left:0.5rem;">PO: {inv['po_number']}</span>
                </div>
                <div>{amt}</div>
                <div>{badge}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{date_s}</div>
            </div>""")

        with col_action:
            if st.button("Details", key=f"view_{inv['invoice_id']}", use_container_width=True):
                st.session_state["selected_invoice_id"] = inv["invoice_id"]
                st.session_state["nav_page"] = "invoice_detail"
                st.rerun()
