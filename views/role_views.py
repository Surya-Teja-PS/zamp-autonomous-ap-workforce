"""
views/role_views.py
--------------------
Tailored portal views for Procurement and Warehouse roles:
  - Procurement: Purchase order management, line commitments, and linked invoices
  - Warehouse: Goods Receipt Notes (GRN), QC accepted/rejected quantities, and physical delivery status
Both roles have read-only access to invoice approvals.
"""

import streamlit as st
import pandas as pd

from core.auth import get_session_user, require_login
from core.database import get_connection, fetchall
from utils.ui_components import (
    inject_css, render_custom_sidebar, render_html, maybe_render_demo_banner,
    status_badge, format_inr, format_date, format_datetime,
    role_banner, section_header, empty_state
)


def render_procurement():
    require_login()
    inject_css()
    user = get_session_user()
    render_custom_sidebar(active_tab="Dashboard", exception_count=0, user=user)
    maybe_render_demo_banner()

    role_banner(
        "Procurement Portal · Authorised to inspect Purchase Order terms, commitments, and line item delivery status. "
        "Invoice approval and payment workflows are managed by Finance / AP.",
        style="read"
    )

    render_html('<div class="ia-section">📦 Purchase Orders Overview</div>')

    conn = get_connection()
    pos = fetchall(conn, """
        SELECT p.*, v.name as vendor_name,
               (SELECT COUNT(*) FROM po_line_items pl WHERE pl.po_id = p.po_id) as line_count,
               (SELECT SUM(pl.quantity * pl.unit_price) FROM po_line_items pl WHERE pl.po_id = p.po_id) as total_val
        FROM purchase_orders p
        JOIN vendors v ON p.vendor_id = v.vendor_id
        ORDER BY p.order_date DESC
    """)

    if pos:
        po_rows = []
        for p in pos:
            po_rows.append({
                "PO Number": p["po_number"],
                "Vendor": p["vendor_name"],
                "Order Date": format_date(p["order_date"]),
                "Status": p["status"].upper(),
                "Lines": p["line_count"],
                "Total Value": format_inr(p["total_val"]),
                "Notes": p["notes"] or "—",
            })
        st.dataframe(pd.DataFrame(po_rows), use_container_width=True, hide_index=True)

    # Invoices linked to POs
    render_html('<div class="ia-section">📑 Invoices Linked to Purchase Orders</div>')
    invoices = fetchall(conn, """
        SELECT i.*, p.po_number, v.name as vendor_name
        FROM invoices i
        JOIN purchase_orders p ON i.po_id = p.po_id
        JOIN vendors v ON i.vendor_id = v.vendor_id
        ORDER BY i.submitted_at DESC
    """)
    conn.close()

    if not invoices:
        empty_state("📄", "No Linked Invoices", "No invoices have been submitted against open POs.")
        return

    for inv in invoices:
        c1, c2 = st.columns([5, 1])
        with c1:
            render_html(f"""
            <div class="ia-inv-row">
                <span class="ia-inv-id"><code>{inv['submission_id']}</code></span>
                <span class="ia-inv-num"><strong>{inv['invoice_number'] or 'Pending'}</strong> · {inv['vendor_name']} · PO: {inv['po_number']}</span>
                <span class="ia-inv-amt">{format_inr(inv['total_amount'])}</span>
                {status_badge(inv['status'])}
            </div>""")
        with c2:
            if st.button("Inspect", key=f"proc_view_{inv['invoice_id']}", use_container_width=True):
                st.session_state["selected_invoice_id"] = inv["invoice_id"]
                st.session_state["nav_page"] = "invoice_detail"
                st.rerun()


def render_warehouse():
    require_login()
    inject_css()
    user = get_session_user()
    render_custom_sidebar(active_tab="Dashboard", exception_count=0, user=user)
    maybe_render_demo_banner()

    role_banner(
        "Warehouse Receiving Portal · Authorised to inspect physical deliveries, Goods Receipt Notes (GRN), "
        "and QC accept/reject records. Read-only for invoice approval workflows.",
        style="read"
    )

    render_html('<div class="ia-section">🚚 Goods Receipt Notes (GRN) & QC Inspections</div>')

    conn = get_connection()
    grns = fetchall(conn, """
        SELECT gr.*, p.po_number, v.name as vendor_name,
               SUM(gl.quantity_received) as total_received,
               SUM(gl.quantity_accepted) as total_accepted,
               SUM(gl.quantity_rejected) as total_rejected
        FROM goods_receipts gr
        JOIN purchase_orders p ON gr.po_id = p.po_id
        JOIN vendors v ON p.vendor_id = v.vendor_id
        JOIN grn_line_items gl ON gr.grn_id = gl.grn_id
        GROUP BY gr.grn_id
        ORDER BY gr.received_date DESC
    """)

    if grns:
        grn_rows = []
        for g in grns:
            grn_rows.append({
                "GRN Number": g["grn_number"],
                "PO Reference": g["po_number"],
                "Vendor": g["vendor_name"],
                "Received Date": format_date(g["received_date"]),
                "Status": g["status"].upper(),
                "Received": f"{g['total_received']:.0f}",
                "Accepted": f"{g['total_accepted']:.0f}",
                "Rejected": f"{g['total_rejected']:.0f}",
                "Notes / QC Exception": g["notes"] or "None",
            })
        st.dataframe(pd.DataFrame(grn_rows), use_container_width=True, hide_index=True)

    # Detailed GRN Line Items with rejection reasons
    render_html('<div class="ia-section">🔍 Line-Item Quality Control Breakdown</div>')
    items = fetchall(conn, """
        SELECT gl.*, gr.grn_number, pl.description, pl.unit
        FROM grn_line_items gl
        JOIN goods_receipts gr ON gl.grn_id = gr.grn_id
        JOIN po_line_items pl ON gl.po_line_id = pl.po_line_id
        ORDER BY gr.received_date DESC
    """)
    conn.close()

    if items:
        item_rows = []
        for it in items:
            item_rows.append({
                "GRN": it["grn_number"],
                "Item Description": it["description"],
                "Received": f"{it['quantity_received']:.0f} {it['unit']}",
                "Accepted": f"{it['quantity_accepted']:.0f} {it['unit']}",
                "Rejected": f"{it['quantity_rejected']:.0f} {it['unit']}",
                "Rejection Reason": it["rejection_reason"] or "All items accepted in good order",
            })
        st.dataframe(pd.DataFrame(item_rows), use_container_width=True, hide_index=True)

