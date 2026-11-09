"""
core/pipeline.py
----------------
Orchestrates all pipeline stages for one invoice.
Called synchronously from the Streamlit UI.
Yields (stage_name, status, message) tuples so the UI can update stage-by-stage.
"""

import logging
from core.database import get_connection, set_invoice_status, get_invoice
from core.extraction import run_extraction
from core.matching import run_line_matching
from core.validation import run_all_checks
from core.decision import run_decision
from core.audit import log_status_change

logger = logging.getLogger(__name__)

STAGES = [
    "intake",
    "extraction",
    "data_validation",
    "line_matching",
    "validation",
    "decision",
]


def run_pipeline(invoice_id: int):
    """
    Generator that runs the full pipeline for an invoice.
    Yields (stage, state, message) where state ∈ {running, done, error, skipped}.
    The caller (Streamlit page) iterates and updates the UI after each yield.
    """
    conn = get_connection()
    try:
        invoice = get_invoice(conn, invoice_id)
        if not invoice:
            yield ("pipeline", "error", f"Invoice {invoice_id} not found.")
            return

        pdf_path = invoice["original_pdf_path"]

        # ── Phase 2: Extraction ───────────────────────────────────────────
        yield ("extraction", "running", "Parsing PDF and calling Gemini…")
        extracted = run_extraction(conn, invoice_id, pdf_path)

        # Re-read status (may have been routed to review during extraction)
        invoice = get_invoice(conn, invoice_id)
        if invoice["status"] == "review":
            yield ("extraction", "done", "Routed to review — extraction issue.")
            yield ("data_validation", "skipped", "Skipped — routed to review during extraction.")
            yield ("line_matching",   "skipped", "Skipped.")
            yield ("validation",      "skipped", "Skipped.")
            yield ("decision",        "done", invoice["decision_reason"] or "Review.")
            return

        yield ("extraction", "done",
               f"Extracted {len(extracted.get('line_items', []))} line item(s). "
               f"Confidence: {invoice['overall_confidence']:.0%}")

        # ── Phase 3: Data Pre-Validation ──────────────────────────────────
        yield ("data_validation", "running", "Checking confidence and mandatory fields…")
        from utils.config import load_system_config
        cfg = load_system_config(conn)
        confidence = invoice["overall_confidence"] or 0.0
        threshold  = cfg["min_extraction_confidence"]

        if confidence < threshold:
            reason = (f"Extraction confidence {confidence:.2f} below threshold {threshold:.2f}. "
                      "Human verification required before automated checks can run.")
            set_invoice_status(conn, invoice_id, "review",
                               decision_reason=reason,
                               decided_at="datetime('now')")
            conn.commit()
            log_status_change(conn, invoice_id, "extracted", "review",
                              "decision_review", reason=reason)
            conn.commit()
            yield ("data_validation", "done", f"Confidence {confidence:.0%} < {threshold:.0%} threshold → Review.")
            yield ("line_matching", "skipped", "Skipped.")
            yield ("validation",    "skipped", "Skipped.")
            yield ("decision",      "done", reason)
            return

        # Check mandatory fields
        missing = []
        if not invoice["invoice_number"]: missing.append("invoice_number")
        if not invoice["invoice_date"]:   missing.append("invoice_date")
        if not invoice["total_amount"]:   missing.append("total_amount")
        if not extracted.get("line_items"): missing.append("line_items")

        if missing:
            reason = f"Missing mandatory fields: {', '.join(missing)}. Human extraction required."
            set_invoice_status(conn, invoice_id, "review",
                               decision_reason=reason,
                               decided_at="datetime('now')")
            conn.commit()
            log_status_change(conn, invoice_id, "extracted", "review",
                              "decision_review", reason=reason)
            conn.commit()
            yield ("data_validation", "done", f"Missing fields: {missing} → Review.")
            yield ("line_matching", "skipped", "Skipped.")
            yield ("validation",    "skipped", "Skipped.")
            yield ("decision",      "done", reason)
            return

        yield ("data_validation", "done", "Confidence and mandatory fields OK.")

        # ── Phase 4: Line Matching ─────────────────────────────────────────
        yield ("line_matching", "running", "Matching invoice lines to PO lines…")
        match_results = run_line_matching(conn, invoice_id, invoice["po_id"])
        unmatched = [m for m in match_results if m["status"] != "matched"]
        yield ("line_matching", "done",
               f"{len(match_results) - len(unmatched)}/{len(match_results)} lines matched.")

        # ── Phase 5: Multi-Gate Validation ────────────────────────────────
        yield ("validation", "running", "Running 6 validation checks inside transaction…")
        set_invoice_status(conn, invoice_id, "validating")
        conn.commit()
        log_status_change(conn, invoice_id, "extracted", "validating", "validation_started")
        conn.commit()

        check_results = run_all_checks(conn, invoice_id)
        passed = sum(1 for v in check_results.values() if v.get("status") == "passed")
        total  = len(check_results)
        yield ("validation", "done", f"{passed}/{total} checks passed.")

        # ── Phase 6: Decision Synthesis ───────────────────────────────────
        yield ("decision", "running", "Applying decision matrix…")
        decision = run_decision(conn, invoice_id, check_results)
        yield ("decision", "done", decision["decision_reason"] or decision["status"])

    except Exception as e:
        logger.exception("Pipeline error for invoice_id=%d: %s", invoice_id, e)
        yield ("pipeline", "error", f"Unexpected error: {e}")
    finally:
        conn.close()
