"""
core/audit.py
-------------
Helpers for writing to the append-only audit_logs table.
Every state change, decision, and human action calls one of these functions.
"""

import json
from core.database import execute


def log(
    conn,
    *,
    action: str,
    entity_type: str,
    entity_id: str | int,
    actor_type: str = "system",
    actor_id: int | None = None,
    invoice_id: int | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    detail: dict | None = None,
    reason: str | None = None,
):
    """
    Append a single row to audit_logs.
    Call this BEFORE the state transition it records (write-ahead logging pattern).
    """
    execute(conn,
        """INSERT INTO audit_logs
               (invoice_id, actor_id, actor_type, action,
                entity_type, entity_id,
                previous_status, new_status, detail_json, reason)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            invoice_id,
            actor_id,
            actor_type,
            action,
            entity_type,
            str(entity_id),
            previous_status,
            new_status,
            json.dumps(detail) if detail else None,
            reason,
        ),
    )


# ── Convenience wrappers ───────────────────────────────────────────────────

def log_submission(conn, invoice_id: int, vendor_id: int, submission_id: str):
    log(conn,
        action="invoice_submitted",
        entity_type="invoices",
        entity_id=invoice_id,
        actor_type="vendor",
        invoice_id=invoice_id,
        new_status="submitted",
        detail={"submission_id": submission_id, "vendor_id": vendor_id},
    )


def log_status_change(conn, invoice_id: int, previous: str, new: str,
                      action: str, reason: str | None = None, detail: dict | None = None):
    log(conn,
        action=action,
        entity_type="invoices",
        entity_id=invoice_id,
        actor_type="system",
        invoice_id=invoice_id,
        previous_status=previous,
        new_status=new,
        reason=reason,
        detail=detail,
    )


def log_check(conn, invoice_id: int, check_name: str, status: str, detail_text: str):
    action = "check_passed" if status == "passed" else "check_failed"
    log(conn,
        action=action,
        entity_type="validation_results",
        entity_id=f"{invoice_id}:{check_name}",
        actor_type="system",
        invoice_id=invoice_id,
        reason=detail_text,
    )


def log_override(conn, invoice_id: int, actor_id: int, action: str,
                 previous_status: str, new_status: str, comment: str):
    log(conn,
        action=action,
        entity_type="invoices",
        entity_id=invoice_id,
        actor_type="finance_ap",
        actor_id=actor_id,
        invoice_id=invoice_id,
        previous_status=previous_status,
        new_status=new_status,
        reason=comment,
    )


def log_retry(conn, invoice_id: int, stage: str, attempt: int, error: str):
    log(conn,
        action="retry_attempted",
        entity_type="invoices",
        entity_id=invoice_id,
        actor_type="system",
        invoice_id=invoice_id,
        reason=f"Stage: {stage}, Attempt: {attempt}, Error: {error}",
    )
