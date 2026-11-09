-- ============================================================
-- Invoice Processing System — SQLite Schema
-- Version 1.0 | 2026-11-05
-- Run:  python db/seed.py   (creates DB, runs this schema, inserts seed data)
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ------------------------------------------------------------
-- system_config: configurable validation parameters
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_config (
    config_key   TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,
    description  TEXT,
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_by   INTEGER REFERENCES users(user_id)
);

-- ------------------------------------------------------------
-- vendors
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    gstin      TEXT NOT NULL UNIQUE,
    email      TEXT NOT NULL,
    phone      TEXT,
    address    TEXT,
    is_active  INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- users
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id     INTEGER REFERENCES vendors(vendor_id),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN (
                      'vendor', 'procurement', 'warehouse', 'finance_ap'
                  )),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);

-- ------------------------------------------------------------
-- purchase_orders
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id              INTEGER NOT NULL REFERENCES vendors(vendor_id),
    po_number              TEXT NOT NULL UNIQUE,
    status                 TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
                               'draft', 'approved', 'closed', 'cancelled'
                           )),
    order_date             TEXT NOT NULL,
    expected_delivery_date TEXT,
    notes                  TEXT,
    created_by             INTEGER NOT NULL REFERENCES users(user_id),
    approved_by            INTEGER REFERENCES users(user_id),
    approved_at            TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at             TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- po_line_items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS po_line_items (
    po_line_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    po_id       INTEGER NOT NULL REFERENCES purchase_orders(po_id),
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    hsn_code    TEXT,
    unit        TEXT NOT NULL DEFAULT 'unit',
    quantity    REAL NOT NULL CHECK (quantity > 0),
    unit_price  REAL NOT NULL CHECK (unit_price > 0),
    tax_rate    REAL NOT NULL DEFAULT 18.0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (po_id, line_number)
);

-- ------------------------------------------------------------
-- goods_receipts
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goods_receipts (
    grn_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    po_id         INTEGER NOT NULL REFERENCES purchase_orders(po_id),
    grn_number    TEXT NOT NULL UNIQUE,
    received_date TEXT NOT NULL,
    received_by   INTEGER NOT NULL REFERENCES users(user_id),
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
                      'draft', 'confirmed', 'cancelled'
                  )),
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- grn_line_items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS grn_line_items (
    grn_line_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    grn_id            INTEGER NOT NULL REFERENCES goods_receipts(grn_id),
    po_line_id        INTEGER NOT NULL REFERENCES po_line_items(po_line_id),
    quantity_received REAL NOT NULL CHECK (quantity_received >= 0),
    quantity_accepted REAL NOT NULL CHECK (quantity_accepted >= 0),
    quantity_rejected REAL NOT NULL DEFAULT 0 CHECK (quantity_rejected >= 0),
    rejection_reason  TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (grn_id, po_line_id),
    CHECK (ABS(quantity_received - (quantity_accepted + quantity_rejected)) < 0.001)
);

-- ------------------------------------------------------------
-- invoices  (central table)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id       TEXT NOT NULL UNIQUE,
    vendor_id           INTEGER NOT NULL REFERENCES vendors(vendor_id),
    po_id               INTEGER NOT NULL REFERENCES purchase_orders(po_id),
    invoice_number      TEXT,
    invoice_date        TEXT,
    document_hash       TEXT NOT NULL,
    original_pdf_path   TEXT NOT NULL,
    extracted_data_json TEXT,
    overall_confidence  REAL CHECK (overall_confidence BETWEEN 0.0 AND 1.0),
    subtotal            REAL,
    tax_amount          REAL,
    total_amount        REAL,
    currency            TEXT NOT NULL DEFAULT 'INR',
    status              TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN (
                            'submitted', 'extracting', 'extracted',
                            'validating', 'review', 'approved',
                            'rejected', 'duplicate'
                        )),
    rejection_category  TEXT CHECK (rejection_category IN (
                            'duplicate', 'cancelled_po', 'policy_violation'
                        )),
    decision_reason     TEXT,
    reviewer_comment    TEXT,
    submitted_at        TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at          TEXT,
    decided_by          INTEGER REFERENCES users(user_id),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Partial unique index: at most one invoice can be approved per vendor and invoice_number.
-- Allows rejected/duplicate attempts to be recorded in the DB for audit/compliance.
CREATE UNIQUE INDEX IF NOT EXISTS idx_vendor_invoice_approved
    ON invoices(vendor_id, invoice_number)
    WHERE invoice_number IS NOT NULL AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_invoice_hash   ON invoices(document_hash);
CREATE INDEX IF NOT EXISTS idx_invoice_status ON invoices(status, submitted_at);
CREATE INDEX IF NOT EXISTS idx_invoice_vendor ON invoices(vendor_id, submitted_at);

-- ------------------------------------------------------------
-- invoice_line_items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoice_line_items (
    invoice_line_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id       INTEGER NOT NULL REFERENCES invoices(invoice_id),
    po_line_id       INTEGER REFERENCES po_line_items(po_line_id),
    line_number      INTEGER NOT NULL,
    description      TEXT,
    quantity         REAL,
    unit_price       REAL,
    tax_rate         REAL,
    tax_amount       REAL,
    line_total       REAL,
    confidence_score REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (invoice_id, line_number)
);

-- ------------------------------------------------------------
-- validation_results  (one row per check per invoice)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_results (
    validation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id     INTEGER NOT NULL REFERENCES invoices(invoice_id),
    check_name     TEXT NOT NULL CHECK (check_name IN (
                       'duplicate_check', 'vendor_check', 'po_check',
                       'quantity_check', 'price_check', 'tax_check'
                   )),
    status         TEXT NOT NULL CHECK (status IN (
                       'passed', 'failed', 'warning', 'skipped', 'error'
                   )),
    detail         TEXT NOT NULL,
    expected_value TEXT,
    actual_value   TEXT,
    checked_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (invoice_id, check_name)
);

-- ------------------------------------------------------------
-- audit_logs  (append-only; no UPDATE or DELETE ever issued)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id      INTEGER REFERENCES invoices(invoice_id),
    actor_id        INTEGER REFERENCES users(user_id),
    actor_type      TEXT NOT NULL CHECK (actor_type IN (
                        'system', 'vendor', 'procurement',
                        'warehouse', 'finance_ap'
                    )),
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    previous_status TEXT,
    new_status      TEXT,
    detail_json     TEXT,
    reason          TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_invoice ON audit_logs(invoice_id, created_at);
