"""
core/database.py
----------------
SQLite connection management, transaction helpers, and common query wrappers.
Every public function takes an explicit connection — no module-level globals.
"""

import sqlite3
import contextlib
from pathlib import Path
from utils.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with row_factory and foreign keys enabled.
    Caller is responsible for closing.
    """
    path = Path(DATABASE_PATH)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextlib.contextmanager
def transaction(conn: sqlite3.Connection, immediate: bool = True):
    """
    Context manager for explicit transactions.
    Uses BEGIN IMMEDIATE to lock for writes (prevents race conditions on
    quantity calculations — equivalent to SELECT FOR UPDATE in PostgreSQL).

    Usage:
        with transaction(conn) as tx:
            tx.execute(...)
        # auto-committed on exit; rolled back on exception
    """
    mode = "BEGIN IMMEDIATE" if immediate else "BEGIN"
    conn.execute(mode)
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


# ── Generic helpers ────────────────────────────────────────────────────────

def fetchone(conn, sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def fetchall(conn, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def execute(conn, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    return conn.execute(sql, params)


# ── Domain-specific queries ────────────────────────────────────────────────

def get_vendor(conn, vendor_id: int) -> sqlite3.Row | None:
    return fetchone(conn, "SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,))


def get_user_by_email(conn, email: str) -> sqlite3.Row | None:
    return fetchone(conn, "SELECT * FROM users WHERE email = ?", (email,))


def get_po(conn, po_id: int) -> sqlite3.Row | None:
    return fetchone(conn, "SELECT * FROM purchase_orders WHERE po_id = ?", (po_id,))


def get_po_lines(conn, po_id: int) -> list[sqlite3.Row]:
    return fetchall(conn,
        "SELECT * FROM po_line_items WHERE po_id = ? ORDER BY line_number",
        (po_id,))


def get_approved_pos_for_vendor(conn, vendor_id: int) -> list[sqlite3.Row]:
    return fetchall(conn,
        "SELECT * FROM purchase_orders WHERE vendor_id = ? AND status = 'approved' ORDER BY po_number",
        (vendor_id,))


def get_invoice(conn, invoice_id: int) -> sqlite3.Row | None:
    return fetchone(conn, "SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))


def get_invoice_by_submission(conn, submission_id: str) -> sqlite3.Row | None:
    return fetchone(conn, "SELECT * FROM invoices WHERE submission_id = ?", (submission_id,))


def get_invoice_lines(conn, invoice_id: int) -> list[sqlite3.Row]:
    return fetchall(conn,
        "SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY line_number",
        (invoice_id,))


def get_validation_results(conn, invoice_id: int) -> list[sqlite3.Row]:
    return fetchall(conn,
        "SELECT * FROM validation_results WHERE invoice_id = ? ORDER BY checked_at",
        (invoice_id,))


def get_audit_trail(conn, invoice_id: int) -> list[sqlite3.Row]:
    return fetchall(conn,
        "SELECT al.*, u.email as actor_email FROM audit_logs al "
        "LEFT JOIN users u ON al.actor_id = u.user_id "
        "WHERE al.invoice_id = ? ORDER BY al.created_at",
        (invoice_id,))


def get_invoices_for_vendor(conn, vendor_id: int) -> list[sqlite3.Row]:
    return fetchall(conn,
        """SELECT i.*, p.po_number, v.name as vendor_name
           FROM invoices i
           JOIN purchase_orders p ON i.po_id = p.po_id
           JOIN vendors v ON i.vendor_id = v.vendor_id
           WHERE i.vendor_id = ?
           ORDER BY i.submitted_at DESC""",
        (vendor_id,))


def get_all_invoices(conn) -> list[sqlite3.Row]:
    return fetchall(conn,
        """SELECT i.*, p.po_number, v.name as vendor_name
           FROM invoices i
           JOIN purchase_orders p ON i.po_id = p.po_id
           JOIN vendors v ON i.vendor_id = v.vendor_id
           ORDER BY i.submitted_at DESC""")


def next_submission_id(conn) -> str:
    """Generate a unique sequential submission ID: SUB-YYYYMMDD-NNNNN."""
    from datetime import date
    today = date.today().strftime("%Y%m%d")
    row = fetchone(conn,
        "SELECT COUNT(*) as cnt FROM invoices WHERE submission_id LIKE ?",
        (f"SUB-{today}-%",))
    seq = (row["cnt"] if row else 0) + 1
    return f"SUB-{today}-{seq:05d}"


def set_invoice_status(conn, invoice_id: int, status: str, **kwargs):
    """Update invoice status and any additional fields atomically."""
    fields = ["status = ?", "updated_at = datetime('now')"]
    values = [status]
    for col, val in kwargs.items():
        fields.append(f"{col} = ?")
        values.append(val)
    values.append(invoice_id)
    conn.execute(
        f"UPDATE invoices SET {', '.join(fields)} WHERE invoice_id = ?",
        values,
    )


def get_grn_quantity_summary(conn, po_line_id: int, current_invoice_id: int) -> dict:
    """
    Returns the quantity breakdown needed for the quantity check.
    Runs inside the caller's transaction for consistency.
    """
    row = fetchone(conn, """
        SELECT
            pl.quantity                                          AS po_ordered_qty,
            pl.unit_price                                        AS po_unit_price,
            pl.tax_rate                                          AS po_tax_rate,
            pl.description                                       AS po_description,
            (
                SELECT COALESCE(SUM(gl.quantity_accepted), 0)
                FROM grn_line_items gl
                JOIN goods_receipts gr ON gl.grn_id = gr.grn_id AND gr.status = 'confirmed'
                WHERE gl.po_line_id = pl.po_line_id
            )                                                    AS total_grn_accepted,
            (
                SELECT COALESCE(SUM(il.quantity), 0)
                FROM invoice_line_items il
                JOIN invoices i ON il.invoice_id = i.invoice_id
                WHERE il.po_line_id = pl.po_line_id AND i.status = 'approved'
            )                                                    AS committed_qty,
            (
                SELECT COALESCE(SUM(il.quantity), 0)
                FROM invoice_line_items il
                JOIN invoices i ON il.invoice_id = i.invoice_id
                WHERE il.po_line_id = pl.po_line_id
                  AND i.status NOT IN ('approved', 'rejected', 'duplicate')
                  AND i.invoice_id != ?
            )                                                    AS reserved_qty
        FROM po_line_items pl
        WHERE pl.po_line_id = ?
    """, (current_invoice_id, po_line_id))

    if not row:
        return {}
    r = dict(row)
    r["available_qty"] = r["total_grn_accepted"] - r["committed_qty"] - r["reserved_qty"]
    return r
