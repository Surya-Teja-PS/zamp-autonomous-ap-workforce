"""
db/seed_zamp.py
----------------
Seeds the enterprise database for Zamp Agent OS / InvoiceAI:
Populates exact vendors, purchase orders, goods receipts, and historical runs matching
both the reference mockup (INV-10421 BuildWell, INV-10422 ABC Traders) and
the Zamp AI Solutions Analyst Case Study Dossier.
"""

import sqlite3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "invoice_processing.db"
SCHEMA_FILE = ROOT / "db" / "schema.sql"

def seed():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    # Apply base schema if tables do not exist
    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

    # Add extra columns if needed
    for col, col_type in [
        ("total_amount", "REAL DEFAULT 0.0"),
        ("invoiced_amount", "REAL DEFAULT 0.0"),
        ("remaining_amount", "REAL DEFAULT 0.0"),
    ]:
        try:
            conn.execute(f"ALTER TABLE purchase_orders ADD COLUMN {col} {col_type}")
        except Exception:
            pass

    for col, col_type in [
        ("execution_time_ms", "REAL DEFAULT 1800.0"),
        ("raw_reasoning", "TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"ALTER TABLE invoices ADD COLUMN {col} {col_type}")
        except Exception:
            pass

    # Vendors
    conn.executemany(
        """INSERT OR REPLACE INTO vendors (vendor_id, name, gstin, email, phone, address, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (1, "Apex Cloud Services LLC", "US-94-3829101", "billing@apexcloud.com", "+1-415-555-0192", "500 Howard St, San Francisco, CA 94105", 1),
            (2, "Industrial Precision Tools", "US-12-8849102", "accounts@precisiontools.com", "+1-312-555-0144", "1200 Industrial Pkwy, Chicago, IL 60607", 1),
            (3, "CloudScale Networks", "US-88-2910492", "finance@cloudscale.io", "+1-206-555-0188", "101 Pike St, Seattle, WA 98101", 1),
            (4, "Starlight Logistics Inc", "US-33-9182740", "ap@starlightlogistics.com", "+1-214-555-0177", "8800 Logistics Way, Dallas, TX 75201", 1),
            (5, "BuildWell Constructions", "29AABCB1234F1Z5", "billing@buildwell.com", "+91-80-45678901", "12 Industrial Hub, Bengaluru, KA 560099", 1),
            (6, "ABC Traders Constructions", "29AABCA9876C1Z3", "orders@abctraders.com", "+91-80-87654321", "44 Commercial Street, Bengaluru, KA 560001", 1),
        ]
    )

    # Purchase Orders
    conn.executemany(
        """INSERT OR REPLACE INTO purchase_orders 
           (po_id, vendor_id, po_number, status, order_date, expected_delivery_date, notes, created_by, approved_by, approved_at, total_amount, invoiced_amount, remaining_amount)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            # Mockup PO: PO #45021 for BuildWell & ABC Traders
            (5, 5, "PO #45021", "approved", "2026-10-15", "2026-11-15", "Procurement Order for Cement Bags and Structural Steel", 2, 2, "2026-10-16T09:00:00", 62000.00, 62000.00, 0.00),
            # Case 1 & Case 4 PO: Apex Cloud Services
            (1, 1, "PO-9821", "approved", "2026-10-01", "2026-10-31", "Q4 Enterprise Cloud Infrastructure & Security Addon", 2, 2, "2026-10-02T09:00:00", 10000.00, 4871.25, 5128.75),
            # Case 2 PO: Starlight Logistics (Split PO, $14k already drawn down, only $6k remains)
            (2, 4, "PO-7710", "approved", "2026-09-15", "2026-11-15", "Quarterly Regional Freight Haulage Blanket Agreement", 2, 2, "2026-09-16T10:00:00", 20000.00, 14000.00, 6000.00),
            # Case 3 PO: Industrial Precision Tools (Hex Bolts @ $11.50 ea, no freight budgeted)
            (3, 2, "PO-4420", "approved", "2026-10-10", "2026-11-05", "Assembly Hardware & Precision Tooling replenishment", 2, 2, "2026-10-11T11:00:00", 3550.00, 0.00, 3550.00),
            # General PO: CloudScale Networks
            (4, 3, "PO-8812", "approved", "2026-10-12", "2026-11-12", "Network Backbone Fiber Leases Q4", 2, 2, "2026-10-13T14:00:00", 18500.00, 18500.00, 0.00),
        ]
    )

    # PO Line Items
    conn.executemany(
        """INSERT OR REPLACE INTO po_line_items (po_line_id, po_id, line_number, description, hsn_code, unit, quantity, unit_price, tax_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            # PO #45021 (BuildWell)
            (10, 5, 1, "Cement Bags (Grade 53)", "2523", "bags", 100.0, 320.00, 0.0),
            (11, 5, 2, "Steel Rods (12mm TMT)", "7214", "rods", 50.0, 600.00, 0.0),
            # PO-9821 (Apex)
            (1, 1, 1, "Enterprise Cloud Seats (50x $80)", "998313", "user", 50.0, 80.00, 8.25),
            (2, 1, 2, "Managed Security Addon", "998315", "month", 1.0, 500.00, 8.25),
            # PO-7710 (Starlight)
            (3, 2, 1, "Regional Freight Haulage (Tri-State)", "996511", "service", 1.0, 20000.00, 0.0),
            # PO-4420 (Industrial)
            (4, 3, 1, "10x Hex Bolts Grade 8 (Box of 10)", "7318", "box", 10.0, 115.00, 0.0),
            (5, 3, 2, "Industrial Drill Bits Set", "8207", "set", 20.0, 120.00, 0.0),
            # PO-8812 (CloudScale)
            (6, 4, 1, "Dedicated Dark Fiber 10Gbps Loop", "998411", "port", 2.0, 9250.00, 0.0),
        ]
    )

    # Goods Receipts (GRN)
    conn.executemany(
        """INSERT OR REPLACE INTO goods_receipts (grn_id, po_id, grn_number, received_date, received_by, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (5, 5, "GRN #78112", "2026-11-04", 3, "confirmed", "Warehouse Dock 4: 100 Cement Bags and 50 Steel Rods verified in full. Quality OK."),
            (1, 1, "GRN-9821-A", "2026-10-05", 3, "confirmed", "Cloud seats provisioned and verified active in Okta directory."),
            (2, 2, "GRN-7710-1", "2026-10-01", 3, "confirmed", "Shipments #1 through #4 delivered in September. $14,000 accepted."),
            (3, 3, "GRN-4420-A", "2026-10-20", 3, "confirmed", "Bolts and drill bits received in dock 3. Freight delivered without prior bill."),
        ]
    )

    # Historical Invoices for Runs Dashboard & Mockup Alignment
    conn.executemany(
        """INSERT OR REPLACE INTO invoices
           (invoice_id, vendor_id, po_id, submission_id, invoice_number, invoice_date, document_hash, original_pdf_path, subtotal, tax_amount, total_amount, currency, status, decision_reason, overall_confidence, submitted_at, decided_at, execution_time_ms, raw_reasoning)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            # Mockup Top-Right Screen: INV-10421 (BuildWell Constructions) -> 3-Way Match Successful
            (201, 5, 5, "SUB-2026-201", "INV-10421", "2026-11-05", "hash_bw_10421", "sample_invoices/INV-BW-001_HappyPath.pdf", 62000.00, 0.00, 62000.00, "INR", "approved", 
             "3-Way Match Successful: All documents are consistent. PO #45021 (₹62,000) = GRN #78112 (₹62,000) = Invoice (₹62,000). Zero variance detected.", 
             0.99, "2026-11-05 10:24:00", "2026-11-05 10:24:18", 1820.0,
             "Vendor verified. PO #45021 matched line-by-line: 100 Cement Bags @ ₹320.00 and 50 Steel Rods @ ₹600.00. GRN #78112 confirmed 100% receipt. Straight-Through Processing (STP) approved."),
            
            # Mockup Middle-Right Screen: INV-10422 (ABC Traders) -> Price Deviation Detected (Review)
            (202, 6, 5, "SUB-2026-202", "INV-10422", "2026-11-05", "hash_abc_10422", "sample_invoices/INV-BW-001_HappyPath.pdf", 25000.00, 0.00, 25000.00, "INR", "review", 
             "Price Deviation Detected: Invoice unit price (₹50.00) is 20% higher than PO benchmark price (₹40.00). Exceeds 2.0% tolerance threshold.", 
             0.96, "2026-11-05 10:20:00", "2026-11-05 10:20:15", 1540.0,
             "Vendor ABC Traders matched. Line item: 500 Tiles billed at ₹50.00/unit. PO contract unit rate was ₹40.00/unit (+₹10.00 / 20.0% variance). Routing to Finance Controller for manual exception review."),

            # Mockup Activity: INV-10423 (BuildWell) -> Approved
            (203, 5, 5, "SUB-2026-203", "INV-10423", "2026-11-05", "hash_bw_10423", "sample_invoices/INV-BW-001_HappyPath.pdf", 38400.00, 0.00, 38400.00, "INR", "approved", 
             "Auto-Approved: Supplementary material delivery matches procurement addendum.", 
             0.98, "2026-11-05 10:15:00", "2026-11-05 10:15:14", 1420.0,
             "Line quantities match GRN. Tolerance delta 0.0%. Auto-approved."),

            # Mockup Activity: INV-10420 (BuildWell) -> Approved
            (200, 5, 5, "SUB-2026-200", "INV-10420", "2026-11-05", "hash_bw_10420", "sample_invoices/INV-BW-001_HappyPath.pdf", 54000.00, 0.00, 54000.00, "INR", "approved", 
             "Auto-Approved: Standard construction phase 1 delivery confirmed.", 
             0.99, "2026-11-05 09:45:00", "2026-11-05 09:45:12", 1680.0,
             "3-way match verified with 0% discrepancy."),

            # Zamp Case Study 1: Apex Cloud Services
            (101, 1, 1, "SUB-2026-101", "INV-2026-0891", "2026-10-24", "hash101", "sample_invoices/INV-BW-001_HappyPath.pdf", 4500.00, 371.25, 4871.25, "USD", "approved", 
             "Auto-Approved: All 6 deterministic checks passed. Vendor verified, PO-9821 balance sufficient ($5,128.75 open), line unit prices match exactly, math check 100% verified.", 
             0.99, "2026-10-24 10:14:22", "2026-10-24 10:14:24", 1820.0,
             "Vendor ID VEND-001 active. PO #PO-9821 status OPEN. Line item 1 matches PO line 1 (50 seats @ $80.00). Line item 2 matches PO line 2 ($500.00). Subtotal $4,500.00 + 8.25% tax ($371.25) = $4,871.25. Zero variance."),
            
            # Zamp Case Study 2: Starlight Logistics (Split PO Exhaustion)
            (102, 4, 2, "SUB-2026-102", "INV-101", "2026-10-02", "hash102", "sample_invoices/INV-BW-001_HappyPath.pdf", 14000.00, 0.00, 14000.00, "USD", "approved", 
             "Auto-Approved: Partial billing on blanket agreement PO-7710. $14,000 committed against $20,000 ceiling. $6,000 remaining.", 
             0.98, "2026-10-02 09:30:10", "2026-10-02 09:30:12", 1950.0,
             "Vendor Starlight Logistics verified. Partial fulfillment against GRN-7710-1. Balance open: $6,000."),
            
            # Zamp Case Study: CloudScale
            (103, 3, 4, "SUB-2026-103", "CS-99410", "2026-10-15", "hash103", "sample_invoices/INV-BW-001_HappyPath.pdf", 18500.00, 0.00, 18500.00, "USD", "approved", 
             "Auto-Approved: Dedicated Dark Fiber Loop monthly lease matches contract PO-8812.", 
             0.99, "2026-10-15 14:20:00", "2026-10-15 14:20:02", 1640.0,
             "Contract terms verified. Straight-through automated payout scheduled."),
            
            # Zamp Case Study 3: Industrial Precision Tools
            (104, 2, 3, "SUB-2026-104", "IPT-8819", "2026-10-18", "hash104", "sample_invoices/INV-BW-001_HappyPath.pdf", 2400.00, 0.00, 2400.00, "USD", "approved", 
             "Auto-Approved: Drill bit sets delivered and inspected in good order under GRN-4420-A.", 
             0.97, "2026-10-18 16:45:10", "2026-10-18 16:45:11", 1750.0,
             "QC passed with zero defects. Straight-through approval committed."),
        ]
    )

    conn.commit()
    conn.close()
    print("[seed_zamp] Successfully seeded enterprise database with InvoiceAI & Zamp Case Study records!")

if __name__ == "__main__":
    seed()
