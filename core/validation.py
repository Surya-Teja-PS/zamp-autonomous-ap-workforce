"""
core/validation.py
------------------
Phase 5: Six deterministic validation checks — atomic transactional evaluation.
Each check writes one row to validation_results.
Returns a dict: check_name → {status, detail, expected, actual}
"""

import logging
from core.database import (
    fetchone, fetchall, execute,
    get_vendor, get_po, get_invoice, get_invoice_lines,
    get_grn_quantity_summary, transaction,
)
from core.audit import log_check
from utils.config import load_system_config

logger = logging.getLogger(__name__)

CHECKS = [
    "duplicate_check",
    "vendor_check",
    "po_check",
    "quantity_check",
    "price_check",
    "tax_check",
]

# Statuses that stop further processing (hard blocks)
HARD_STOP_STATUSES = {"failed"}  # from checks 1-3 only
HARD_STOP_CHECKS   = {"duplicate_check", "vendor_check"}


def _write_result(conn, invoice_id, check_name, status, detail,
                  expected=None, actual=None):
    execute(conn,
        """INSERT OR REPLACE INTO validation_results
               (invoice_id, check_name, status, detail, expected_value,
                actual_value, checked_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
        (invoice_id, check_name, status, detail,
         str(expected) if expected is not None else None,
         str(actual)   if actual   is not None else None),
    )
    log_check(conn, invoice_id, check_name, status, detail)


def _skip_remaining(conn, invoice_id, skipped_checks, reason):
    for check_name in skipped_checks:
        _write_result(conn, invoice_id, check_name, "skipped",
                      f"Skipped — earlier check blocked processing: {reason}")


# ── Check 1: Duplicate ────────────────────────────────────────────────────

def check_duplicate(conn, invoice_id, vendor_id, invoice_number, document_hash) -> dict:
    result = {"status": "passed", "detail": "No duplicate found.", "expected": None, "actual": None}

    if invoice_number:
        existing = fetchone(conn,
            "SELECT invoice_id, submission_id, status FROM invoices "
            "WHERE vendor_id = ? AND invoice_number = ? AND invoice_id != ?",
            (vendor_id, invoice_number, invoice_id))
        if existing:
            result = {
                "status": "failed",
                "detail": (f"Invoice number '{invoice_number}' already submitted by this vendor "
                           f"(Submission {existing['submission_id']}, status: {existing['status']}). "
                           "Duplicate submissions are permanently blocked."),
                "expected": "Unique invoice number",
                "actual": f"Duplicate: {existing['submission_id']}",
            }
            return result

    # Secondary: document hash
    hash_match = fetchone(conn,
        "SELECT invoice_id, submission_id FROM invoices "
        "WHERE document_hash = ? AND invoice_id != ? AND status NOT IN ('rejected','duplicate')",
        (document_hash, invoice_id))
    if hash_match:
        result = {
            "status": "warning",
            "detail": (f"PDF file is identical to a previous submission "
                       f"({hash_match['submission_id']}). "
                       "Flagged for review — vendor may have resubmitted with a corrected number."),
            "expected": "Unique document",
            "actual": f"Hash match: {hash_match['submission_id']}",
        }
    return result


# ── Check 2: Vendor ───────────────────────────────────────────────────────

def check_vendor(conn, vendor_id, po_id) -> dict:
    vendor = get_vendor(conn, vendor_id)
    if not vendor:
        return {"status": "failed",
                "detail": f"Vendor ID {vendor_id} not found.",
                "expected": "Active vendor", "actual": "Not found"}

    if not vendor["is_active"]:
        return {"status": "failed",
                "detail": f"Vendor '{vendor['name']}' is inactive. Contact Procurement.",
                "expected": "Active vendor", "actual": "Inactive"}

    po = get_po(conn, po_id)
    if po and po["vendor_id"] != vendor_id:
        return {"status": "failed",
                "detail": (f"PO {po['po_number']} belongs to a different vendor. "
                           "This submission is flagged as a potential data integrity issue."),
                "expected": f"Vendor {vendor_id} owns PO",
                "actual": f"PO owned by vendor {po['vendor_id']}"}

    return {"status": "passed",
            "detail": f"Vendor '{vendor['name']}' is active and owns the referenced PO.",
            "expected": None, "actual": None}


# ── Check 3: PO ───────────────────────────────────────────────────────────

def check_po(conn, po_id) -> tuple[dict, bool]:
    """Returns (result_dict, is_hard_stop)"""
    po = get_po(conn, po_id)
    if not po:
        return ({"status": "failed", "detail": f"PO {po_id} not found.",
                 "expected": "Approved PO", "actual": "Not found"}, True)

    pn = po["po_number"]
    if po["status"] == "approved":
        return ({"status": "passed",
                 "detail": f"PO {pn} is approved and open for invoicing.",
                 "expected": "approved", "actual": "approved"}, False)
    elif po["status"] == "cancelled":
        return ({"status": "failed",
                 "detail": f"PO {pn} has been cancelled. No further invoicing is permitted.",
                 "expected": "approved", "actual": "cancelled"}, True)
    elif po["status"] == "closed":
        return ({"status": "failed",
                 "detail": f"PO {pn} is closed. All items have been fully invoiced.",
                 "expected": "approved", "actual": "closed"}, True)
    else:  # draft
        return ({"status": "failed",
                 "detail": f"PO {pn} is in draft and has not been approved yet.",
                 "expected": "approved", "actual": "draft"}, False)


# ── Check 4: Quantity ─────────────────────────────────────────────────────

def check_quantity(conn, invoice_id) -> dict:
    lines = get_invoice_lines(conn, invoice_id)
    issues, warnings = [], []

    for line in lines:
        if not line["po_line_id"]:
            warnings.append(f"Line {line['line_number']} ('{line['description']}'): "
                            "not matched to a PO line — cannot verify quantity.")
            continue

        qty = line["quantity"]
        if qty is None:
            warnings.append(f"Line {line['line_number']}: quantity not extracted.")
            continue

        summary = get_grn_quantity_summary(conn, line["po_line_id"], invoice_id)
        if not summary or summary["total_grn_accepted"] == 0:
            warnings.append(f"Line {line['line_number']} ('{line['description']}'): "
                            "no confirmed GRN found. Goods may not have been received yet.")
            continue

        avail = summary["available_qty"]
        if qty > avail + 0.001:  # 0.001 float tolerance
            issues.append(
                f"Line {line['line_number']} ('{line['description']}'): "
                f"invoiced {qty} {summary.get('po_description','units')} but only {avail:.2f} available "
                f"({summary['total_grn_accepted']:.2f} GRN-accepted "
                f"− {summary['committed_qty']:.2f} committed "
                f"− {summary['reserved_qty']:.2f} in-process reserved)."
            )

    if issues:
        return {"status": "failed",
                "detail": "Quantity over-claim: " + " | ".join(issues),
                "expected": "Invoiced qty ≤ available qty", "actual": "; ".join(issues)}
    if warnings:
        return {"status": "warning",
                "detail": "Quantity warnings: " + " | ".join(warnings),
                "expected": "Confirmed GRN for all lines", "actual": "; ".join(warnings)}
    return {"status": "passed",
            "detail": "All invoiced quantities are within GRN-accepted limits.",
            "expected": None, "actual": None}


# ── Check 5: Price ────────────────────────────────────────────────────────

def check_price(conn, invoice_id, tolerance_pct: float) -> dict:
    lines = get_invoice_lines(conn, invoice_id)
    issues = []
    tol = tolerance_pct / 100.0

    for line in lines:
        if not line["po_line_id"] or line["unit_price"] is None:
            continue
        po_line = fetchone(conn, "SELECT * FROM po_line_items WHERE po_line_id = ?",
                           (line["po_line_id"],))
        if not po_line:
            continue
        po_price = po_line["unit_price"]
        inv_price = line["unit_price"]
        lower = po_price * (1 - tol)
        upper = po_price * (1 + tol)
        deviation = abs(inv_price - po_price) / po_price * 100

        if not (lower - 0.001 <= inv_price <= upper + 0.001):
            direction = "above" if inv_price > po_price else "below"
            issues.append(
                f"Line {line['line_number']} ('{line['description']}'): "
                f"invoice price ₹{inv_price:.2f} is {direction} PO price ₹{po_price:.2f} "
                f"by {deviation:.2f}% (tolerance: {tolerance_pct:.1f}%). "
                f"Allowed range: ₹{lower:.2f}–₹{upper:.2f}."
            )

    if issues:
        return {"status": "failed",
                "detail": "Price deviation: " + " | ".join(issues),
                "expected": f"Within {tolerance_pct:.1f}% of PO price",
                "actual": "; ".join(issues)}
    return {"status": "passed",
            "detail": f"All unit prices within {tolerance_pct:.1f}% tolerance of PO prices.",
            "expected": None, "actual": None}


# ── Check 6: Tax & Totals ─────────────────────────────────────────────────

def check_tax(conn, invoice_id, valid_gst_rates: list[float]) -> dict:
    invoice = get_invoice(conn, invoice_id)
    lines   = get_invoice_lines(conn, invoice_id)
    issues  = []

    for line in lines:
        if line["tax_rate"] is None or line["unit_price"] is None or line["quantity"] is None:
            continue
        # Rate validity
        if line["tax_rate"] not in valid_gst_rates:
            issues.append(f"Line {line['line_number']}: tax rate {line['tax_rate']}% "
                          f"is not a valid GST rate (valid: {valid_gst_rates}).")
        # Rate vs PO agreed rate
        if line["po_line_id"]:
            po_line = fetchone(conn, "SELECT tax_rate FROM po_line_items WHERE po_line_id = ?",
                               (line["po_line_id"],))
            if po_line and abs(line["tax_rate"] - po_line["tax_rate"]) > 0.01:
                issues.append(f"Line {line['line_number']}: invoice rate {line['tax_rate']}% "
                              f"≠ PO agreed rate {po_line['tax_rate']}%.")
        # Line arithmetic
        if line["tax_amount"] is not None:
            expected_tax = round(line["quantity"] * line["unit_price"] * line["tax_rate"] / 100, 2)
            if abs(line["tax_amount"] - expected_tax) > 0.50:
                issues.append(f"Line {line['line_number']}: stated tax ₹{line['tax_amount']:.2f} "
                              f"≠ computed ₹{expected_tax:.2f}.")
        if line["line_total"] is not None and line["tax_amount"] is not None:
            expected_total = round(line["quantity"] * line["unit_price"] + line["tax_amount"], 2)
            if abs(line["line_total"] - expected_total) > 0.50:
                issues.append(f"Line {line['line_number']}: stated line total ₹{line['line_total']:.2f} "
                              f"≠ computed ₹{expected_total:.2f}.")

    # Invoice-level totals (₹1 rounding tolerance)
    computed_subtotal = sum(
        (r["quantity"] or 0) * (r["unit_price"] or 0) for r in lines
    )
    computed_tax = sum(r["tax_amount"] or 0 for r in lines)
    computed_total = computed_subtotal + computed_tax

    if invoice["subtotal"] is not None and abs(invoice["subtotal"] - computed_subtotal) > 1.00:
        issues.append(f"Invoice subtotal ₹{invoice['subtotal']:.2f} ≠ computed ₹{computed_subtotal:.2f}.")
    if invoice["tax_amount"] is not None and abs(invoice["tax_amount"] - computed_tax) > 1.00:
        issues.append(f"Invoice tax ₹{invoice['tax_amount']:.2f} ≠ computed ₹{computed_tax:.2f}.")
    if invoice["total_amount"] is not None and abs(invoice["total_amount"] - computed_total) > 1.00:
        issues.append(f"Invoice total ₹{invoice['total_amount']:.2f} ≠ computed ₹{computed_total:.2f}.")

    if issues:
        return {"status": "failed",
                "detail": "Tax/total discrepancy: " + " | ".join(issues),
                "expected": "Correct GST rates and arithmetic",
                "actual": "; ".join(issues)}
    return {"status": "passed",
            "detail": (f"All tax calculations verified. "
                       f"Subtotal ₹{computed_subtotal:.2f}, "
                       f"Tax ₹{computed_tax:.2f}, "
                       f"Total ₹{computed_total:.2f}."),
            "expected": None, "actual": None}


# ── Orchestrator ──────────────────────────────────────────────────────────

def run_all_checks(conn, invoice_id: int) -> dict[str, dict]:
    """
    Run all six checks inside a single BEGIN IMMEDIATE transaction.
    Returns results dict keyed by check_name.
    """
    invoice = get_invoice(conn, invoice_id)
    cfg     = load_system_config(conn)

    results = {}

    with transaction(conn, immediate=True) as tx:
        # ── Check 1: Duplicate ─────────────────────────────────────────────
        r1 = check_duplicate(tx, invoice_id, invoice["vendor_id"],
                             invoice["invoice_number"], invoice["document_hash"])
        _write_result(tx, invoice_id, "duplicate_check", **r1)
        results["duplicate_check"] = r1

        if r1["status"] == "failed":
            # Hard block — skip remaining
            _skip_remaining(tx, invoice_id,
                            ["vendor_check","po_check","quantity_check","price_check","tax_check"],
                            "Confirmed duplicate invoice.")
            for c in ["vendor_check","po_check","quantity_check","price_check","tax_check"]:
                results[c] = {"status": "skipped",
                               "detail": "Skipped — confirmed duplicate."}
            return results

        # ── Check 2: Vendor ────────────────────────────────────────────────
        r2 = check_vendor(tx, invoice["vendor_id"], invoice["po_id"])
        _write_result(tx, invoice_id, "vendor_check", **r2)
        results["vendor_check"] = r2

        if r2["status"] == "failed":
            _skip_remaining(tx, invoice_id,
                            ["po_check","quantity_check","price_check","tax_check"],
                            "Vendor validation failed.")
            for c in ["po_check","quantity_check","price_check","tax_check"]:
                results[c] = {"status": "skipped",
                               "detail": "Skipped — vendor check failed."}
            return results

        # ── Check 3: PO ────────────────────────────────────────────────────
        r3, po_hard_stop = check_po(tx, invoice["po_id"])
        _write_result(tx, invoice_id, "po_check", **r3)
        results["po_check"] = r3

        if r3["status"] == "failed" and po_hard_stop:
            _skip_remaining(tx, invoice_id,
                            ["quantity_check","price_check","tax_check"],
                            "PO is cancelled or closed.")
            for c in ["quantity_check","price_check","tax_check"]:
                results[c] = {"status": "skipped",
                               "detail": "Skipped — PO is cancelled or closed."}
            return results

        # ── Check 4: Quantity (runs inside same transaction for locking) ───
        r4 = check_quantity(tx, invoice_id)
        _write_result(tx, invoice_id, "quantity_check", **r4)
        results["quantity_check"] = r4

        # ── Check 5: Price ────────────────────────────────────────────────
        r5 = check_price(tx, invoice_id, cfg["price_tolerance_pct"])
        _write_result(tx, invoice_id, "price_check", **r5)
        results["price_check"] = r5

        # ── Check 6: Tax ──────────────────────────────────────────────────
        r6 = check_tax(tx, invoice_id, cfg["valid_gst_rates"])
        _write_result(tx, invoice_id, "tax_check", **r6)
        results["tax_check"] = r6

    return results
