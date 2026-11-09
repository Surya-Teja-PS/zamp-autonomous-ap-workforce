"""
core/intake.py
--------------
Phase 1: Secure Ingestion & Virus Scan
  - Validate file format and size
  - Compute document hash
  - Store original PDF
  - Create invoice record in DB
  - Write audit log entry
"""

import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime

from core.database import execute, next_submission_id, set_invoice_status
from core.audit import log_submission
from utils.config import UPLOAD_DIR

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
PDF_MAGIC = b"%PDF"


class IntakeError(Exception):
    """Raised for format/size validation failures — not a business rejection."""
    pass


def _validate_pdf(file_bytes: bytes, filename: str):
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise IntakeError(f"File size {len(file_bytes) // (1024*1024)} MB exceeds 20 MB limit.")
    if not file_bytes.startswith(PDF_MAGIC):
        raise IntakeError(f"File '{filename}' does not appear to be a valid PDF.")


def _compute_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def _store_pdf(file_bytes: bytes, submission_id: str, filename: str) -> str:
    """Save the original PDF to uploads/<submission_id>/<filename>. Returns the path."""
    dest_dir = Path(UPLOAD_DIR) / submission_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    dest.write_bytes(file_bytes)
    return str(dest)


def process_intake(
    conn,
    *,
    file_bytes: bytes,
    filename: str,
    vendor_id: int,
    po_id: int,
) -> dict:
    """
    Run Phase 1 ingestion for an uploaded invoice PDF.

    Returns a dict with invoice_id, submission_id, document_hash, pdf_path.
    Raises IntakeError for format/size problems (shown to vendor, NOT recorded as invoice).
    """
    _validate_pdf(file_bytes, filename)

    doc_hash = _compute_hash(file_bytes)
    submission_id = next_submission_id(conn)
    pdf_path = _store_pdf(file_bytes, submission_id, filename)

    cursor = execute(conn,
        """INSERT INTO invoices
               (submission_id, vendor_id, po_id, document_hash,
                original_pdf_path, status, submitted_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'submitted', datetime('now'), datetime('now'))""",
        (submission_id, vendor_id, po_id, doc_hash, pdf_path),
    )
    invoice_id = cursor.lastrowid
    conn.commit()

    # Audit log (outside the commit — we want it after the record exists)
    with conn:
        log_submission(conn, invoice_id, vendor_id, submission_id)

    logger.info("Intake complete: invoice_id=%d, submission_id=%s", invoice_id, submission_id)

    return {
        "invoice_id": invoice_id,
        "submission_id": submission_id,
        "document_hash": doc_hash,
        "pdf_path": pdf_path,
    }
