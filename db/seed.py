"""
db/seed.py
----------
Creates the SQLite database, applies the schema, and inserts demo seed data.
Run once:  python db/seed.py
Run fresh: python db/seed.py --reset   (drops and recreates everything)
"""

import sqlite3
import os
import sys
import bcrypt
import argparse
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT / "db" / "schema.sql"
DB_PATH = ROOT / "invoice_processing.db"
UPLOAD_DIR = ROOT / "uploads"


def get_password_hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def seed(reset: bool = False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[seed] Deleted existing database: {DB_PATH}")

    UPLOAD_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    # ── Apply schema ───────────────────────────────────────────────────────
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print("[seed] Schema applied.")

    # ── Password hash (Demo@1234 for all demo users — CHANGE IN PRODUCTION) ─
    pw = get_password_hash("Demo@1234")

    # ── system_config ──────────────────────────────────────────────────────
    conn.executemany(
        "INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES (?,?,?)",
        [
            ("price_tolerance_pct",       "2.00",        "Max % deviation of invoice unit price from PO unit price"),
            ("min_extraction_confidence", "0.80",        "Min Gemini confidence to allow automated processing"),
            ("valid_gst_rates",           "0,5,12,18,28","Comma-separated valid GST rates (%)"),
            ("max_retry_attempts",        "3",           "Max retries on technical failure before routing to Review"),
            ("retry_delay_seconds",       "5",           "Base delay (seconds) between retries — doubles each attempt"),
            ("currency",                  "INR",         "Default currency for all transactions"),
        ],
    )

    # ── vendors ────────────────────────────────────────────────────────────
    conn.executemany(
        "INSERT OR IGNORE INTO vendors (vendor_id, name, gstin, email, phone, address, is_active) VALUES (?,?,?,?,?,?,?)",
        [
            (1, "Buildwell Supplies Pvt Ltd", "29AABCB1234F1Z5",
             "vendor@buildwell.com", "+91-80-12345678",
             "12, Industrial Area, Bengaluru, KA 560099", 1),
            (2, "TechParts India Pvt Ltd", "27AABCT5678G1Z3",
             "vendor@techparts.com", "+91-22-98765432",
             "45, MIDC, Pune, MH 411019", 1),
        ],
    )

    # ── users ──────────────────────────────────────────────────────────────
    conn.executemany(
        "INSERT OR IGNORE INTO users (user_id, vendor_id, email, password_hash, role) VALUES (?,?,?,?,?)",
        [
            (1, None, "ap@company.com",           pw, "finance_ap"),
            (2, None, "procurement@company.com",  pw, "procurement"),
            (3, None, "warehouse@company.com",    pw, "warehouse"),
            (4, 1,    "vendor@buildwell.com",     pw, "vendor"),
            (5, 2,    "vendor@techparts.com",     pw, "vendor"),
        ],
    )

    # ── purchase_orders ────────────────────────────────────────────────────
    conn.executemany(
        """INSERT OR IGNORE INTO purchase_orders
           (po_id, vendor_id, po_number, status, order_date, expected_delivery_date,
            notes, created_by, approved_by, approved_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [
            (1, 1, "PO-2024-001", "approved", "2024-10-01", "2024-10-20",
             "Construction materials for Site A — Phase 1",
             2, 2, "2024-10-02T09:00:00"),
            (2, 2, "PO-2024-002", "approved", "2024-10-05", "2024-10-25",
             "Electronic components for assembly line — Batch Q4",
             2, 2, "2024-10-06T10:00:00"),
        ],
    )

    # ── po_line_items ──────────────────────────────────────────────────────
    conn.executemany(
        """INSERT OR IGNORE INTO po_line_items
           (po_line_id, po_id, line_number, description, hsn_code, unit,
            quantity, unit_price, tax_rate)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            # PO-2024-001: Buildwell
            (1, 1, 1, "MS Steel Rods 12mm dia (TMT Fe500)",  "7213", "kg",   100.0, 500.00, 18.0),
            (2, 1, 2, "Portland Cement OPC 53 Grade (50kg)", "2523", "bag",  200.0, 350.00, 28.0),
            # PO-2024-002: TechParts
            (3, 2, 1, "Ceramic Capacitors 100nF 50V SMD",   "8532", "pcs", 1000.0,  25.00, 18.0),
        ],
    )

    # ── goods_receipts ─────────────────────────────────────────────────────
    conn.executemany(
        """INSERT OR IGNORE INTO goods_receipts
           (grn_id, po_id, grn_number, received_date, received_by, status, notes)
           VALUES (?,?,?,?,?,?,?)""",
        [
            (1, 1, "GRN-2024-001", "2024-10-18", 3, "confirmed",
             "Steel rods in good condition. Cement: 10 bags damaged in transit."),
            (2, 2, "GRN-2024-002", "2024-10-22", 3, "confirmed",
             "Capacitors received. 50 units failed incoming QC — bent leads."),
        ],
    )

    # ── grn_line_items ─────────────────────────────────────────────────────
    conn.executemany(
        """INSERT OR IGNORE INTO grn_line_items
           (grn_line_id, grn_id, po_line_id,
            quantity_received, quantity_accepted, quantity_rejected, rejection_reason)
           VALUES (?,?,?,?,?,?,?)""",
        [
            # GRN-001: 80/100 steel rods accepted; 190/200 cement accepted
            (1, 1, 1,  80.0,  80.0,  0.0, None),
            (2, 1, 2, 200.0, 190.0, 10.0, "Bags damaged in transit — cement hardened"),
            # GRN-002: 950/1000 capacitors accepted
            (3, 2, 3, 1000.0, 950.0, 50.0, "Incoming QC failure: bent leads on 50 units"),
        ],
    )

    conn.commit()
    conn.close()

    print("[seed] [OK] Seed data inserted.")
    print(f"[seed] [OK] Database ready: {DB_PATH}")
    print()
    print("Demo credentials (password: Demo@1234 for all):")
    print("  ap@company.com           -> Finance / AP")
    print("  procurement@company.com  -> Procurement")
    print("  warehouse@company.com    -> Warehouse")
    print("  vendor@buildwell.com     -> Buildwell Supplies (Vendor)")
    print("  vendor@techparts.com     -> TechParts India (Vendor)")
    print()
    print("Demo scenarios (run in order during demo):")
    print("  1. Happy path   -> INV-BW-001, 50 kg Steel Rods @ Rs 500 -> Approved")
    print("  2. T1 Duplicate -> Resubmit INV-BW-001 -> Blocked")
    print("  3. T2 Qty       -> INV-BW-002, 40 kg Steel Rods @ Rs 500 -> Review (30 remaining)")
    print("  4. T3 Price     -> INV-TP-001, 100 Capacitors @ Rs 26.50 -> Review (>2% tolerance)")
    print("  5. T4 Missing   -> Degraded/scanned PDF -> Review (low confidence)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate the database")
    args = parser.parse_args()
    seed(reset=args.reset)
