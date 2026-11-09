"""
core/decision.py
----------------
Phase 6: Autonomous Decision Synthesis
Reads all six validation_results rows and applies the deterministic decision matrix.
Generative LLM has NO execution authority in this deterministic module.

Also handles human review overrides (FR-31).
"""

import logging
from core.database import (
    fetchall, set_invoice_status, get_invoice, get_invoice_lines,
    transaction
)
from core.audit import log_status_change, log_override

logger = logging.getLogger(__name__)

# Statuses that cannot be overridden by a reviewer
NON_OVERRIDEABLE_STATUSES = {"rejected", "duplicate", "approved"}

# Which PO statuses are hard rejections (not overrideable)
HARD_REJECTION_CATEGORIES = {"duplicate", "cancelled_po"}


def run_decision(conn, invoice_id: int, results: dict[str, dict]) -> dict:
    """
    Apply the decision matrix to validation results.
    Updates invoice.status and writes audit log.
    Returns dict with new_status and decision_reason.
    """

    def r(check):
        return results.get(check, {}).get("status", "error")

    def detail(check):
        return results.get(check, {}).get("detail", "")

    new_status = None
    decision_reason = None
    rejection_category = None

    # ── Hard blocks ────────────────────────────────────────────────────────
    if r("duplicate_check") == "failed":
        new_status = "duplicate"
        rejection_category = "duplicate"
        decision_reason = (
            "🚫 BLOCKED — Confirmed duplicate invoice.\n\n"
            + detail("duplicate_check")
        )

    elif r("vendor_check") == "failed":
        new_status = "rejected"
        rejection_category = "policy_violation"
        decision_reason = (
            "❌ REJECTED — Vendor validation failed.\n\n"
            + detail("vendor_check")
        )

    elif r("po_check") == "failed":
        po_detail = detail("po_check")
        if "cancelled" in po_detail.lower() or "closed" in po_detail.lower():
            new_status = "rejected"
            rejection_category = "cancelled_po"
            decision_reason = "❌ REJECTED — " + po_detail
        else:
            # Draft PO — route to review (procurement may approve it)
            new_status = "review"
            decision_reason = "⚠️ REVIEW REQUIRED — PO not yet approved.\n\n" + po_detail

    # ── Review conditions ──────────────────────────────────────────────────
    if new_status is None:
        review_reasons = []

        if r("duplicate_check") == "warning":
            review_reasons.append("• Hash duplicate signal: " + detail("duplicate_check"))
        if r("quantity_check") in ("failed", "warning"):
            review_reasons.append("• Quantity issue: " + detail("quantity_check"))
        if r("price_check") == "failed":
            review_reasons.append("• Price deviation: " + detail("price_check"))
        if r("tax_check") == "failed":
            review_reasons.append("• Tax/total discrepancy: " + detail("tax_check"))
        if any(r(c) == "error" for c in results):
            review_reasons.append("• One or more checks encountered a system error.")

        if review_reasons:
            new_status = "review"
            decision_reason = "⚠️ REVIEW REQUIRED — Issues found:\n\n" + "\n".join(review_reasons)

    # ── Auto-approve ───────────────────────────────────────────────────────
    if new_status is None:
        all_pass = all(
            r(c) in ("passed",)
            for c in ["duplicate_check", "vendor_check", "po_check",
                      "quantity_check", "price_check", "tax_check"]
        )
        if all_pass:
            new_status = "approved"
            decision_reason = (
                "✅ AUTO-APPROVED\n\n"
                "All six validation checks passed:\n"
                "• No duplicate found\n"
                "• Vendor active and matches PO\n"
                "• PO approved and open\n"
                "• Quantity within GRN-accepted limits\n"
                "• Unit prices within tolerance\n"
                "• Tax and totals verified"
            )
        else:
            # Fallback — should not reach here
            new_status = "review"
            decision_reason = (
                "⚠️ REVIEW REQUIRED — Unexpected check status combination. "
                "Manual inspection required."
            )

    # ── Persist ───────────────────────────────────────────────────────────
    kwargs = {
        "decision_reason": decision_reason,
        "decided_at": "datetime('now')",
    }
    if rejection_category:
        kwargs["rejection_category"] = rejection_category

    set_invoice_status(conn, invoice_id, new_status, **kwargs)
    conn.commit()

    action = {
        "approved":  "decision_approved",
        "review":    "decision_review",
        "rejected":  "decision_rejected",
        "duplicate": "decision_rejected",
    }.get(new_status, "decision_review")

    log_status_change(conn, invoice_id, "validating", new_status,
                      action, reason=decision_reason)
    conn.commit()

    logger.info("Decision: invoice_id=%d → %s", invoice_id, new_status)
    return {"status": new_status, "decision_reason": decision_reason}


# ── Human Review Override (FR-31) ──────────────────────────────────────────

def override_review(conn, invoice_id: int, reviewer_user_id: int,
                    action: str, comment: str) -> dict:
    """
    Reviewer overrides a Review-status invoice.
    action: 'approve' | 'reject'
    comment: mandatory non-empty string.
    Returns dict with new_status.
    Raises ValueError on invalid input.
    """
    if not comment or not comment.strip():
        raise ValueError("Reviewer comment is mandatory.")
    if action not in ("approve", "reject"):
        raise ValueError("action must be 'approve' or 'reject'.")

    with transaction(conn, immediate=True) as tx:
        # Re-read inside transaction to prevent race condition
        invoice = get_invoice(tx, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found.")
        if invoice["status"] != "review":
            raise ValueError(
                f"Only Review-status invoices can be overridden. "
                f"This invoice is '{invoice['status']}'."
            )

        previous_status = invoice["status"]
        new_status = "approved" if action == "approve" else "rejected"
        audit_action = (
            "review_override_approved" if action == "approve"
            else "review_override_rejected"
        )

        # Update invoice — quantity commitment is implicit:
        # setting status='approved' makes the quantity check query count these
        # lines as 'committed' for all future invoices on the same PO line.
        tx.execute(
            """UPDATE invoices SET
                   status           = ?,
                   reviewer_comment = ?,
                   decided_at       = datetime('now'),
                   decided_by       = ?,
                   updated_at       = datetime('now')
               WHERE invoice_id = ?""",
            (new_status, comment.strip(), reviewer_user_id, invoice_id),
        )

        log_override(tx, invoice_id, reviewer_user_id, audit_action,
                     previous_status, new_status, comment.strip())

    logger.info("Override: invoice_id=%d → %s by user_id=%d",
                invoice_id, new_status, reviewer_user_id)
    return {"status": new_status}
