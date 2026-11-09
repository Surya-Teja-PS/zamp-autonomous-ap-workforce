"""
core/erp_store.py
-----------------
Master Relational ERP State Store & Commercial Scenario Registry.
Author: P. S. Surya Teja (AI Solutions Architect)
Faithfully encodes the exact relational dataset, tolerance policy parameters, 
and 6 test scenarios defined in zamp_ps1_master_research_blueprint.pdf.
"""

from typing import Dict, List, Any
import copy
import time
import hashlib
from datetime import datetime

COMPANY_POLICY = {
    "tolerance_max_percent": 3.0,
    "tolerance_max_usd": 250.00,
    "manager_escalation_max_percent": 10.0,
    "duplicate_window_days": 14,
    "require_verified_bank_last4": True,
}

APPROVED_VENDORS = [
    {
        "vendor_id": "VND-01",
        "name": "Apex Cloud Systems Inc.",
        "tax_id": "94-3829104",
        "bank_last4": "4821",
        "bank_name": "Silicon Valley Commercial Bank",
        "status": "APPROVED",
        "default_currency": "USD",
        "payment_terms": "Net 30",
        "remittance_address": "500 Howard St, San Francisco, CA 94105",
    },
    {
        "vendor_id": "VND-02",
        "name": "Kinetic Studio Partners",
        "tax_id": "82-1940281",
        "bank_last4": "9910",
        "bank_name": "JPMorgan Chase N.A.",
        "status": "APPROVED",
        "default_currency": "USD",
        "payment_terms": "Net 30",
        "remittance_address": "742 Evergreen Terrace, New York, NY 10001",
    },
    {
        "vendor_id": "VND-03",
        "name": "Vanguard Industrial Supply",
        "tax_id": "36-7748291",
        "bank_last4": "3304",
        "bank_name": "Northern Trust Bank",
        "status": "APPROVED",
        "default_currency": "USD",
        "payment_terms": "2/10 Net 30",
        "remittance_address": "1200 Industrial Pkwy, Chicago, IL 60607",
    },
    {
        "vendor_id": "VND-04",
        "name": "Nova Office Interiors",
        "tax_id": "51-9021844",
        "bank_last4": "6102",
        "bank_name": "PNC Bank Commercial",
        "status": "APPROVED",
        "default_currency": "USD",
        "payment_terms": "Net 30",
        "remittance_address": "8800 Logistics Way, Dallas, TX 75201",
    },
]

PURCHASE_ORDERS = [
    {
        "po_number": "PO-2026-101",
        "vendor_id": "VND-01",
        "vendor_name": "Apex Cloud Systems Inc.",
        "issue_date": "2026-10-01",
        "status": "OPEN",
        "currency": "USD",
        "total_budget": 12000.00,
        "amount_previously_billed": 0.00,
        "remaining_capacity": 12000.00,
        "payment_terms": "Net 30",
        "description": "Annual Infrastructure Refresh: Gen-5 Server Blades",
        "prior_invoices": [],
        "grn_id": "GRN-2026-881",
        "grn_receipt_date": "2026-10-26",
        "grn_dock": "Bay 4 North Facility",
        "grn_inspector": "Marcus Vance (Principal HW Eng)",
        "line_items": [
            {
                "line_number": 1,
                "sku": "ACS-BLADE-X1",
                "description": "Enterprise Server Blade Gen-5",
                "qty_ordered": 10.0,
                "unit": "EA",
                "unit_price": 1200.00,
                "line_total": 12000.00,
            }
        ],
    },
    {
        "po_number": "PO-2026-204",
        "vendor_id": "VND-02",
        "vendor_name": "Kinetic Studio Partners",
        "issue_date": "2026-08-15",
        "status": "PARTIALLY_BILLED",
        "currency": "USD",
        "total_budget": 50000.00,
        "amount_previously_billed": 30000.00,
        "remaining_capacity": 20000.00,
        "payment_terms": "Net 30",
        "description": "Brand Campaign Retainer: Phase 1, 2 & Phase 3 Final Assets",
        "prior_invoices": ["INV-KS-101 ($15,000.00)", "INV-KS-102 ($15,000.00)"],
        "grn_id": "MS-ACK-204",
        "grn_receipt_date": "2026-11-01",
        "grn_dock": "Digital Deliverables Portal",
        "grn_inspector": "Elena Rostova (VP Brand Mktg)",
        "line_items": [
            {
                "line_number": 1,
                "sku": "KSP-RET-Q3Q4",
                "description": "Brand Campaign Retainer - Phase 1, 2 & Phase 3 Final Campaign Assets",
                "qty_ordered": 1.0,
                "unit": "SERVICE",
                "unit_price": 50000.00,
                "line_total": 50000.00,
            }
        ],
    },
    {
        "po_number": "PO-2026-309",
        "vendor_id": "VND-03",
        "vendor_name": "Vanguard Industrial Supply",
        "issue_date": "2026-09-01",
        "status": "OPEN",
        "currency": "USD",
        "total_budget": 15000.00,
        "amount_previously_billed": 0.00,
        "remaining_capacity": 15000.00,
        "payment_terms": "2/10 Net 30",
        "description": "Warehouse Replacement Parts: Hydraulic Valves & Couplings",
        "prior_invoices": [],
        "grn_id": "GRN-2026-442",
        "grn_receipt_date": "2026-11-03",
        "grn_dock": "Chicago Plant Dock 2",
        "grn_inspector": "David K. (Plant Inventory Lead)",
        "line_items": [
            {
                "line_number": 1,
                "sku": "VIS-VALVE-HD",
                "description": "Heavy-Duty Hydraulic Valve Model-X",
                "qty_ordered": 150.0,
                "unit": "EA",
                "unit_price": 100.00,
                "line_total": 15000.00,
            }
        ],
    },
    {
        "po_number": "PO-2026-412",
        "vendor_id": "VND-04",
        "vendor_name": "Nova Office Interiors",
        "issue_date": "2026-10-10",
        "status": "OPEN",
        "currency": "USD",
        "total_budget": 8000.00,
        "amount_previously_billed": 0.00,
        "remaining_capacity": 8000.00,
        "payment_terms": "Net 30",
        "description": "Headquarters Expansion: Modular Workstation Desks",
        "prior_invoices": [],
        "grn_id": "GRN-2026-904",
        "grn_receipt_date": "2026-10-22",
        "grn_dock": "Dallas HQ Floor 3 Dock",
        "grn_inspector": "Sarah Jenkins (Facilities Lead)",
        "line_items": [
            {
                "line_number": 1,
                "sku": "NOI-DESK-MOD",
                "description": "Modular Office Workstation Desks",
                "qty_ordered": 16.0,
                "unit": "UNIT",
                "unit_price": 500.00,
                "line_total": 8000.00,
            }
        ],
    },
]

HISTORICAL_PAID_INVOICES = [
    {
        "invoice_number": "INV-2026-8821",
        "vendor_id": "VND-01",
        "vendor_name": "Apex Cloud Systems Inc.",
        "po_number": "PO-2026-101",
        "invoice_date": "2026-10-24",
        "paid_date": "2026-10-25",
        "net_amount": 12000.00,
        "tax_amount": 960.00,
        "gross_amount": 12960.00,
        "currency": "USD",
        "status": "PAID",
        "bank_last4": "4821",
        "payment_reference": "WIRE-2026-88219",
    },
    {
        "invoice_number": "INV-KS-101",
        "vendor_id": "VND-02",
        "vendor_name": "Kinetic Studio Partners",
        "po_number": "PO-2026-204",
        "invoice_date": "2026-08-30",
        "paid_date": "2026-09-01",
        "net_amount": 15000.00,
        "tax_amount": 0.00,
        "gross_amount": 15000.00,
        "currency": "USD",
        "status": "PAID",
        "bank_last4": "9910",
        "payment_reference": "ACH-2026-09101",
    },
    {
        "invoice_number": "INV-KS-102",
        "vendor_id": "VND-02",
        "vendor_name": "Kinetic Studio Partners",
        "po_number": "PO-2026-204",
        "invoice_date": "2026-09-30",
        "paid_date": "2026-10-01",
        "net_amount": 15000.00,
        "tax_amount": 0.00,
        "gross_amount": 15000.00,
        "currency": "USD",
        "status": "PAID",
        "bank_last4": "9910",
        "payment_reference": "ACH-2026-10102",
    },
]

SCENARIO_PAYLOADS = [
    {
        "scenario_id": 1,
        "scenario_code": "HAPPY_PATH",
        "name": "Scenario 1 — Happy Path: Clean 2-Way Match with Embedded Tax",
        "description": "Invoice INV-2026-9001 from Apex Cloud Systems Inc. referencing PO-2026-101 ($12,000 net budget). Lists $12,960.00 gross inclusive of 8% embedded sales tax ($960.00).",
        "vendor_id": "VND-01",
        "vendor_name": "Apex Cloud Systems Inc.",
        "tax_id": "94-3829104",
        "remit_bank_last4": "4821",
        "invoice_number": "INV-2026-9001",
        "invoice_date": "2026-10-28",
        "due_date": "2026-11-27",
        "po_number": "PO-2026-101",
        "currency": "USD",
        "tax_mode": "embedded",
        "tax_rate_percent": 8.0,
        "stated_subtotal": 12000.00,
        "stated_tax": 960.00,
        "stated_freight": 0.00,
        "stated_discount": 0.00,
        "stated_grand_total": 12960.00,
        "line_items": [
            {
                "line_number": 1,
                "sku": "ACS-BLADE-X1",
                "description": "Enterprise Server Blade Gen-5",
                "quantity": 10.0,
                "unit": "EA",
                "unit_price": 1200.00,
                "amount": 12000.00,
            }
        ],
        "three_way_match": {
            "grn_id": "GRN-2026-881",
            "receipt_date": "2026-10-26",
            "dock_location": "Bay 4 North Facility",
            "inspector": "Marcus Vance (Principal HW Eng)",
            "contracted_po_qty": 10.0,
            "contracted_po_rate": 1200.00,
            "warehouse_grn_qty": 10.0,
            "billed_invoice_qty": 10.0,
            "billed_invoice_rate": 1200.00,
            "match_status": "3-WAY MATCH VERIFIED [✓]",
            "status_color": "emerald",
            "notes": "Contracted PO (10 EA @ $1,200), Warehouse GRN-2026-881 (10 EA inspected & accepted), and Invoice INV-2026-9001 (10 EA @ $1,200) achieve 100% quantity and rate parity."
        },
        "expected_gate_verdicts": {
            "node_1_math": "PASS",
            "node_2_fraud": "PASS",
            "node_3_po": "PASS",
            "node_4_drawdown": "PASS",
            "node_5_tolerance": "PASS",
            "node_6_decision": "AUTO-APPROVED",
        },
        "target_status_badge": "AUTO-APPROVED",
        "target_badge_color": "emerald",
        "expected_reasoning": "Clean 2-Way Match: Extracted Net Subtotal ($12,000.00 backed out from $12,960.00 gross with 8% embedded tax) reconciles with PO-2026-101 with exactly $0.00 (0.00%) variance. Verified bank account ending in *4821 matches approved Vendor Master record.",
    },
    {
        "scenario_id": 2,
        "scenario_code": "EDGE_SPLIT_PO",
        "name": "Scenario 2 — Edge Case A: Split-PO Milestone Drawdown + Tolerance Pass",
        "description": "Invoice INV-KS-103 from Kinetic Studio Partners referencing PO-2026-204 ($50k total, $30k prior billed, $20k capacity). Bills $20,000 final milestone plus $185 rush courier fee.",
        "vendor_id": "VND-02",
        "vendor_name": "Kinetic Studio Partners",
        "tax_id": "82-1940281",
        "remit_bank_last4": "9910",
        "invoice_number": "INV-KS-103",
        "invoice_date": "2026-11-02",
        "due_date": "2026-12-02",
        "po_number": "PO-2026-204",
        "currency": "USD",
        "tax_mode": "separated",
        "tax_rate_percent": 0.0,
        "stated_subtotal": 20000.00,
        "stated_tax": 0.00,
        "stated_freight": 185.00,
        "stated_discount": 0.00,
        "stated_grand_total": 20185.00,
        "line_items": [
            {
                "line_number": 1,
                "sku": "KSP-RET-PH3",
                "description": "Phase 3 Final Campaign Assets",
                "quantity": 1.0,
                "unit": "SERVICE",
                "unit_price": 20000.00,
                "amount": 20000.00,
            },
            {
                "line_number": 2,
                "sku": "FREIGHT-RUSH",
                "description": "Rush Courier Delivery Surcharge",
                "quantity": 1.0,
                "unit": "FEE",
                "unit_price": 185.00,
                "amount": 185.00,
            },
        ],
        "three_way_match": {
            "grn_id": "MS-ACK-204",
            "receipt_date": "2026-11-01",
            "dock_location": "Digital Deliverables Portal",
            "inspector": "Elena Rostova (VP Brand Mktg)",
            "contracted_po_qty": 1.0,
            "contracted_po_rate": 20000.00,
            "warehouse_grn_qty": 1.0,
            "billed_invoice_qty": 1.0,
            "billed_invoice_rate": 20000.00,
            "match_status": "3-WAY MATCH VERIFIED (TOLERANCE PASS)",
            "status_color": "sky",
            "notes": "Milestone delivery verified by VP Brand Marketing. Invoiced base ($20,000.00) matches milestone PO. Courier freight (+$185.00) compliant with corporate tolerance policy."
        },
        "expected_gate_verdicts": {
            "node_1_math": "PASS",
            "node_2_fraud": "PASS",
            "node_3_po": "PASS",
            "node_4_drawdown": "PASS",
            "node_5_tolerance": "PASS_WITH_TOLERANCE",
            "node_6_decision": "APPROVED (TOLERANCE PASS)",
        },
        "target_status_badge": "APPROVED (TOLERANCE PASS)",
        "target_badge_color": "sky",
        "expected_reasoning": "Split-PO Milestone Drawdown Approved: Cumulative drawdown on PO-2026-204 ($30,000 previously disbursed across INV-KS-101 and INV-KS-102) leaves $20,000.00 remaining capacity. Billed total of $20,185.00 introduces a +$185.00 (+0.925%) net courier variance, which is fully compliant with company tolerance policy (<= 3.0% and <= $250.00).",
    },
    {
        "scenario_id": 3,
        "scenario_code": "EDGE_IMPLIED_PO_PRICE_OVERCHARGE",
        "name": "Scenario 3 — Edge Case B: Missing/Implied PO + 22% Unit Price Overbilling",
        "description": "Scanned invoice INV-VIS-774 from Vanguard Industrial Supply arrives with PO Number completely blank. Bills 80x Hydraulic Valves @ $122/unit vs contracted $100/unit.",
        "vendor_id": "VND-03",
        "vendor_name": "Vanguard Industrial Supply",
        "tax_id": "36-7748291",
        "remit_bank_last4": "3304",
        "invoice_number": "INV-VIS-774",
        "invoice_date": "2026-11-04",
        "due_date": "2026-11-14",
        "po_number": "",  # Implied PO discovery test!
        "currency": "USD",
        "tax_mode": "separated",
        "tax_rate_percent": 0.0,
        "stated_subtotal": 9760.00,
        "stated_tax": 0.00,
        "stated_freight": 0.00,
        "stated_discount": 0.00,
        "stated_grand_total": 9760.00,
        "line_items": [
            {
                "line_number": 1,
                "sku": "VIS-VALVE-HD",
                "description": "Heavy-Duty Hydraulic Valve Model-X",
                "quantity": 80.0,
                "unit": "EA",
                "unit_price": 122.00,
                "amount": 9760.00,
            }
        ],
        "three_way_match": {
            "grn_id": "GRN-2026-442",
            "receipt_date": "2026-11-03",
            "dock_location": "Chicago Plant Dock 2",
            "inspector": "David K. (Plant Inventory Lead)",
            "contracted_po_qty": 80.0,
            "contracted_po_rate": 100.00,
            "warehouse_grn_qty": 80.0,
            "billed_invoice_qty": 80.0,
            "billed_invoice_rate": 122.00,
            "match_status": "QTY MATCH [✓] / UNIT PRICE DRIFT EXCEEDED",
            "status_color": "amber",
            "notes": "Dock receipt confirms 80 hydraulic valves delivered. However, invoiced rate of $122.00/unit breaches PO contracted price of $100.00/unit (+22.0% / +$1,760 overcharge)."
        },
        "expected_gate_verdicts": {
            "node_1_math": "PASS",
            "node_2_fraud": "PASS",
            "node_3_po": "PASS_IMPLIED",
            "node_4_drawdown": "FAIL_PRICE_CREEP",
            "node_5_tolerance": "FAIL_EXCEEDED",
            "node_6_decision": "ROUTED FOR APPROVAL",
        },
        "target_status_badge": "ROUTED FOR APPROVAL",
        "target_badge_color": "amber",
        "expected_reasoning": "Missing PO Number inferred: Node 3 discovered open PO-2026-309 via semantic item description matching (96.4% confidence). However, Node 4 flagged that the invoiced rate of $122.00/unit exceeds the contracted PO rate ($100.00/unit) by +$22.00/unit (+22.0% / +$1,760.00 overcharge). Routed to Procurement with pre-drafted vendor dispute memo.",
    },
    {
        "scenario_id": 4,
        "scenario_code": "EDGE_FUZZY_DUPLICATE",
        "name": "Scenario 4 — Edge Case C: Fuzzy Duplicate Detection with Altered Suffix",
        "description": "Invoice INV-2026-8821-R from Apex Cloud Systems Inc. dated 3 days after settled invoice INV-2026-8821 for the exact same $12,960.00 amount.",
        "vendor_id": "VND-01",
        "vendor_name": "Apex Cloud Systems Inc.",
        "tax_id": "94-3829104",
        "remit_bank_last4": "4821",
        "invoice_number": "INV-2026-8821-R",  # Altered suffix to trick simple hash
        "invoice_date": "2026-10-27",
        "due_date": "2026-11-26",
        "po_number": "PO-2026-101",
        "currency": "USD",
        "tax_mode": "embedded",
        "tax_rate_percent": 8.0,
        "stated_subtotal": 12000.00,
        "stated_tax": 960.00,
        "stated_freight": 0.00,
        "stated_discount": 0.00,
        "stated_grand_total": 12960.00,
        "line_items": [
            {
                "line_number": 1,
                "sku": "ACS-BLADE-X1",
                "description": "Enterprise Server Blade Gen-5",
                "quantity": 10.0,
                "unit": "EA",
                "unit_price": 1200.00,
                "amount": 12000.00,
            }
        ],
        "three_way_match": {
            "grn_id": "GRN-2026-881 (HISTORICALLY CLOSED)",
            "receipt_date": "2026-10-24",
            "dock_location": "Bay 4 North Facility",
            "inspector": "Marcus Vance",
            "contracted_po_qty": 10.0,
            "contracted_po_rate": 1200.00,
            "warehouse_grn_qty": 0.0,
            "billed_invoice_qty": 10.0,
            "billed_invoice_rate": 1200.00,
            "match_status": "RE-RECEIPT CONFLICT / DUPLICATE INVOICE",
            "status_color": "rose",
            "notes": "Zero pending physical receipts. Warehouse GRN-2026-881 was already liquidated and disbursed under original invoice INV-2026-8821 on 2026-10-25."
        },
        "expected_gate_verdicts": {
            "node_1_math": "PASS",
            "node_2_fraud": "FAIL_FUZZY_DUPLICATE",
            "node_3_po": "HALT",
            "node_4_drawdown": "HALT",
            "node_5_tolerance": "HALT",
            "node_6_decision": "BLOCKED / REJECTED",
        },
        "target_status_badge": "BLOCKED / REJECTED",
        "target_badge_color": "rose",
        "expected_reasoning": "Fuzzy Duplicate Blocked: Invoice INV-2026-8821-R exhibits 94.1% string similarity with settled invoice INV-2026-8821, shares identical Vendor (VND-01), identical $12,960.00 total, and falls within the 14-day rolling window (3 days apart). Automatic rejection enforced to prevent duplicate disbursement.",
    },
    {
        "scenario_id": 5,
        "scenario_code": "EDGE_MATH_AND_MISSING_DATE",
        "name": "Scenario 5 — Edge Case D: Internal Math Discrepancy & Missing Statutory Date",
        "description": "Invoice INV-ERR-402 from Nova Office Interiors lists 5 desks @ $500 = $2,500 subtotal, $200 tax, but stated Grand Total is $3,700 ($1,000 addition error) and Date is missing.",
        "vendor_id": "VND-04",
        "vendor_name": "Nova Office Interiors",
        "tax_id": "51-9021844",
        "remit_bank_last4": "6102",
        "invoice_number": "INV-ERR-402",
        "invoice_date": "",  # MISSING DATE!
        "due_date": "",
        "po_number": "PO-2026-412",
        "currency": "USD",
        "tax_mode": "separated",
        "tax_rate_percent": 8.0,
        "stated_subtotal": 2500.00,
        "stated_tax": 200.00,
        "stated_freight": 0.00,
        "stated_discount": 0.00,
        "stated_grand_total": 3700.00,  # $1,000 addition error!
        "line_items": [
            {
                "line_number": 1,
                "sku": "NOI-DESK-MOD",
                "description": "Modular Office Workstation Desks",
                "quantity": 5.0,
                "unit": "UNIT",
                "unit_price": 500.00,
                "amount": 2500.00,
            }
        ],
        "three_way_match": {
            "grn_id": "GRN-2026-904",
            "receipt_date": "2026-10-22",
            "dock_location": "Dallas HQ Floor 3 Dock",
            "inspector": "Sarah Jenkins (Facilities Lead)",
            "contracted_po_qty": 5.0,
            "contracted_po_rate": 500.00,
            "warehouse_grn_qty": 5.0,
            "billed_invoice_qty": 5.0,
            "billed_invoice_rate": 500.00,
            "match_status": "GOODS RECEIVED / INVOICE INTEGRITY BREACH",
            "status_color": "rose",
            "notes": "Dock receipt confirms 5 desks physically accepted. However, commercial invoice has $1,000 internal addition discrepancy ($2,500 + $200 != $3,700) and missing date."
        },
        "expected_gate_verdicts": {
            "node_1_math": "FAIL_MATH_AND_DATE",
            "node_2_fraud": "HALT",
            "node_3_po": "HALT",
            "node_4_drawdown": "HALT",
            "node_5_tolerance": "HALT",
            "node_6_decision": "BLOCKED / REJECTED",
        },
        "target_status_badge": "BLOCKED / REJECTED",
        "target_badge_color": "rose",
        "expected_reasoning": "Document Forensics Failure: Halted at Node 1 before querying the ERP. Two critical statutory errors detected: (1) Internal Addition Discrepancy: Subtotal ($2,500.00) + Tax ($200.00) = $2,700.00 != Stated Grand Total ($3,700.00), an arithmetic discrepancy of $1,000.00; (2) Statutory Invoice Date is completely missing.",
    },
    {
        "scenario_id": 6,
        "scenario_code": "EDGE_BANK_REMITTANCE_FRAUD",
        "name": "Scenario 6 — Edge Case E: Remittance Bank Account Mismatch (BEC Fraud Alert)",
        "description": "Invoice INV-KS-104 from Kinetic Studio Partners has valid math and matches an open PO, but footer wire remittance account ends in *7749 instead of verified *9910.",
        "vendor_id": "VND-02",
        "vendor_name": "Kinetic Studio Partners",
        "tax_id": "82-1940281",
        "remit_bank_last4": "7749",  # FRAUD! Unverified account!
        "invoice_number": "INV-KS-104",
        "invoice_date": "2026-11-05",
        "due_date": "2026-12-05",
        "po_number": "PO-2026-204",
        "currency": "USD",
        "tax_mode": "separated",
        "tax_rate_percent": 0.0,
        "stated_subtotal": 10000.00,
        "stated_tax": 0.00,
        "stated_freight": 0.00,
        "stated_discount": 0.00,
        "stated_grand_total": 10000.00,
        "line_items": [
            {
                "line_number": 1,
                "sku": "KSP-RET-PH3",
                "description": "Supplementary Production Consulting Retainer",
                "quantity": 1.0,
                "unit": "SERVICE",
                "unit_price": 10000.00,
                "amount": 10000.00,
            }
        ],
        "three_way_match": {
            "grn_id": "MS-ACK-302",
            "receipt_date": "2026-11-04",
            "dock_location": "Digital Deliverables Portal",
            "inspector": "Elena Rostova (VP Brand Mktg)",
            "contracted_po_qty": 1.0,
            "contracted_po_rate": 10000.00,
            "warehouse_grn_qty": 1.0,
            "billed_invoice_qty": 1.0,
            "billed_invoice_rate": 10000.00,
            "match_status": "SERVICE DELIVERED / TREASURY SUSPENDED (BEC)",
            "status_color": "rose",
            "notes": "Retainer deliverables confirmed by marketing. However, wire payment instructions route funds to unverified account *7749 (vendor master specifies *9910). Treasury hold active."
        },
        "expected_gate_verdicts": {
            "node_1_math": "PASS",
            "node_2_fraud": "FAIL_BANK_MISMATCH",
            "node_3_po": "HALT",
            "node_4_drawdown": "HALT",
            "node_5_tolerance": "HALT",
            "node_6_decision": "BLOCKED / REJECTED",
        },
        "target_status_badge": "BLOCKED / REJECTED",
        "target_badge_color": "rose",
        "expected_reasoning": "Security Firewall Lock: High-severity Business Email Compromise (BEC) alert triggered at Node 2. Invoice wire instructions route funds to unverified bank account ending in *7749, whereas verified Vendor Master record specifies *9910. All payment pathways immediately locked to prevent treasury diversion.",
    },
]


class ERPStateStore:
    """Thread-safe in-memory and stateful ERP database store."""
    def __init__(self):
        self.reset_to_seed()

    def reset_to_seed(self):
        self.policy = copy.deepcopy(COMPANY_POLICY)
        self.vendors = copy.deepcopy(APPROVED_VENDORS)
        self.purchase_orders = copy.deepcopy(PURCHASE_ORDERS)
        self.historical_invoices = copy.deepcopy(HISTORICAL_PAID_INVOICES)
        self.scenarios = copy.deepcopy(SCENARIO_PAYLOADS)
        self.audit_runs = []

    def get_full_state(self) -> Dict[str, Any]:
        return {
            "policy": self.policy,
            "vendors": self.vendors,
            "purchase_orders": self.purchase_orders,
            "historical_invoices": self.historical_invoices,
            "scenarios": self.scenarios,
            "audit_runs": self.audit_runs,
        }

    def get_vendor_by_id(self, vendor_id: str) -> Dict[str, Any] | None:
        for v in self.vendors:
            if v["vendor_id"] == vendor_id:
                return v
        return None

    def get_po_by_number(self, po_number: str) -> Dict[str, Any] | None:
        for po in self.purchase_orders:
            if po["po_number"].strip().upper() == po_number.strip().upper():
                return po
        return None

    def update_policy(self, max_pct: float, max_usd: float) -> Dict[str, Any]:
        self.policy["tolerance_max_percent"] = max_pct
        self.policy["tolerance_max_usd"] = max_usd
        return self.policy

    def disburse_invoice(self, scenario_id: int, payment_ref: str = None, analyst_signature: str = "Surya Teja") -> Dict[str, Any]:
        """Settles invoice, posts NetSuite GL voucher, and deducts remaining capacity from PO."""
        target_scenario = None
        for s in self.scenarios:
            if s.get("scenario_id") == scenario_id:
                target_scenario = s
                break
        if not target_scenario:
            return {"success": False, "error": f"Scenario {scenario_id} not found"}

        target_scenario["execution_status"] = "DISBURSED / SETTLED"
        target_scenario["settled"] = True
        target_scenario["disbursed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Deduct from PO
        po_num = target_scenario.get("po_number")
        net_amt = float(target_scenario.get("stated_subtotal", 0.0))
        po = self.get_po_by_number(po_num) if po_num else None
        if po:
            po["amount_previously_billed"] += net_amt
            po["remaining_capacity"] = max(0.0, round(po["total_budget"] - po["amount_previously_billed"], 2))
            po["status"] = "CLOSED" if po["remaining_capacity"] == 0 else "PARTIALLY_BILLED"

        # Record in historical settled invoices
        ref = payment_ref or f"ACH-AUTONOMOUS-{target_scenario.get('invoice_number', 'VCH')}"
        self.historical_invoices.append({
            "invoice_number": target_scenario.get("invoice_number"),
            "vendor_id": target_scenario.get("vendor_id"),
            "vendor_name": target_scenario.get("vendor_name"),
            "po_number": po_num,
            "invoice_date": target_scenario.get("invoice_date"),
            "paid_date": time.strftime("%Y-%m-%d"),
            "net_amount": net_amt,
            "tax_amount": target_scenario.get("stated_tax", 0.0),
            "gross_amount": target_scenario.get("stated_grand_total", 0.0),
            "currency": "USD",
            "status": "PAID",
            "bank_last4": target_scenario.get("remit_bank_last4"),
            "payment_reference": ref
        })

        # Cryptographic SOX Section 404 Audit Hash (SHA-256)
        iso_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        inv_num = target_scenario.get("invoice_number", "INV-UNKNOWN")
        vendor_legal = target_scenario.get("vendor_name", "UNKNOWN")
        gross_amt = float(target_scenario.get("stated_grand_total", 0.0))
        net_amt = float(target_scenario.get("stated_subtotal", 0.0))
        tax_amt = float(target_scenario.get("stated_tax", 0.0))
        freight_amt = float(target_scenario.get("stated_freight", 0.0))

        raw_audit_str = f"{inv_num}|{po_num}|{vendor_legal}|{gross_amt:.2f}|{iso_timestamp}|{analyst_signature}|SOX_404_SEC_AUDIT"
        sha256_hash = hashlib.sha256(raw_audit_str.encode("utf-8")).hexdigest()

        # Balanced Double-Entry General Ledger (GL) Lines
        gl_lines = []
        if "Apex" in vendor_legal:
            gl_lines.append({
                "account_number": "1520-00",
                "account_name": "IT Hardware CapEx (Enterprise Server Blades)",
                "type": "DEBIT",
                "amount": net_amt,
                "po_ref": po_num or "N/A"
            })
            if tax_amt > 0:
                gl_lines.append({
                    "account_number": "2140-00",
                    "account_name": "Input Sales Tax Receivable",
                    "type": "DEBIT",
                    "amount": tax_amt,
                    "po_ref": po_num or "N/A"
                })
        elif "Kinetic" in vendor_legal:
            gl_lines.append({
                "account_number": "51000-00",
                "account_name": "Brand Marketing Agency Retainer OpEx",
                "type": "DEBIT",
                "amount": net_amt,
                "po_ref": po_num or "N/A"
            })
            if freight_amt > 0:
                gl_lines.append({
                    "account_number": "52100-00",
                    "account_name": "Freight & Rush Courier Expenses",
                    "type": "DEBIT",
                    "amount": freight_amt,
                    "po_ref": po_num or "N/A"
                })
        elif "Vanguard" in vendor_legal:
            gl_lines.append({
                "account_number": "1310-00",
                "account_name": "Warehouse Inventory Assets (Valves)",
                "type": "DEBIT",
                "amount": net_amt,
                "po_ref": po_num or "N/A"
            })
        else:
            gl_lines.append({
                "account_number": "1600-00",
                "account_name": "Furniture & Fixtures Assets",
                "type": "DEBIT",
                "amount": net_amt,
                "po_ref": po_num or "N/A"
            })
            if tax_amt > 0:
                gl_lines.append({
                    "account_number": "2140-00",
                    "account_name": "Input Sales Tax Receivable",
                    "type": "DEBIT",
                    "amount": tax_amt,
                    "po_ref": po_num or "N/A"
                })

        # Credit balancing line: AP Liability / Fedwire Clearing
        gl_lines.append({
            "account_number": "2010-00",
            "account_name": "Accounts Payable Liability (Fedwire Clearing)",
            "type": "CREDIT",
            "amount": gross_amt,
            "disbursement_method": "AUTOMATED_FEDWIRE_SWIFT"
        })

        total_debits = sum(line["amount"] for line in gl_lines if line["type"] == "DEBIT")
        total_credits = sum(line["amount"] for line in gl_lines if line["type"] == "CREDIT")
        is_balanced = round(total_debits, 2) == round(total_credits, 2)

        # ISO-20022 Fedwire Payment Instruction
        iso_20022_wire = {
            "message_definition": "pain.001.001.09",
            "payment_information_id": f"PMT-INF-{int(time.time()) % 100000}",
            "instruction_identification": f"FEDWIRE-{inv_num}-ZAMP",
            "end_to_end_id": f"E2E-{sha256_hash[:16].upper()}",
            "instructed_amount": {
                "currency": "USD",
                "value": gross_amt
            },
            "charge_bearer": "DEBT",
            "debtor": {
                "name": "Zamp Autonomous Holdings LLC",
                "account": "US44WELS00000987654321",
                "agent_bic": "WELSUS6SXXX"
            },
            "creditor": {
                "name": vendor_legal,
                "tax_id": target_scenario.get("tax_id"),
                "account_last4": target_scenario.get("remit_bank_last4"),
                "agent_bic": "SVBKUS6SXXX" if "Apex" in vendor_legal else "CHASUS33XXX"
            },
            "remittance_information": f"INV REF {inv_num} / PO {po_num or 'N/A'}"
        }

        voucher = {
            "journal_entry_id": f"JE-2026-00{scenario_id}",
            "posting_status": "POSTED_TO_NETSUITE_GL",
            "settlement_timestamp": iso_timestamp,
            "sox_section_404_hash": sha256_hash,
            "authorizer": analyst_signature,
            "is_balanced": is_balanced,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "gl_lines": gl_lines,
            "iso_20022_wire": iso_20022_wire,
            "po_remaining_capacity": po["remaining_capacity"] if po else 0.0
        }

        # Record SOX audit entry
        self.audit_runs.append({
            "timestamp": iso_timestamp,
            "scenario_id": scenario_id,
            "invoice_number": inv_num,
            "action": "NETSUITE_GL_POSTING_AND_DISBURSEMENT",
            "auditor": analyst_signature,
            "sox_section_404_hash": sha256_hash,
            "gl_debit": gl_lines[0]["account_name"],
            "gl_credit": "2010-00 Accounts Payable Liability",
            "disbursed_amount": gross_amt,
            "po_remaining_capacity": po["remaining_capacity"] if po else 0.0
        })

        return {"success": True, "scenario": target_scenario, "po": po, "voucher": voucher}

    def override_invoice(self, scenario_id: int, override_reason: str, analyst_signature: str = "Surya Teja") -> Dict[str, Any]:
        """Applies CFO/Analyst manual override with immutable audit entry."""
        target_scenario = None
        for s in self.scenarios:
            if s.get("scenario_id") == scenario_id:
                target_scenario = s
                break
        if not target_scenario:
            return {"success": False, "error": f"Scenario {scenario_id} not found"}

        target_scenario["execution_status"] = "APPROVED (MANUAL OVERRIDE)"
        target_scenario["manual_override"] = True
        target_scenario["override_reason"] = override_reason
        target_scenario["overridden_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Deduct from PO if approved
        po_num = target_scenario.get("po_number")
        net_amt = float(target_scenario.get("stated_subtotal", 0.0))
        po = self.get_po_by_number(po_num) if po_num else None
        if po:
            po["amount_previously_billed"] += net_amt
            po["remaining_capacity"] = max(0.0, round(po["total_budget"] - po["amount_previously_billed"], 2))
            po["status"] = "CLOSED" if po["remaining_capacity"] == 0 else "PARTIALLY_BILLED"

        self.audit_runs.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "scenario_id": scenario_id,
            "invoice_number": target_scenario.get("invoice_number"),
            "action": "EXECUTIVE_ANALYST_OVERRIDE",
            "auditor": analyst_signature,
            "override_reason": override_reason,
            "compliance_status": "APPROVED_UNDER_CONTROLLED_EXCEPTION"
        })

        return {"success": True, "scenario": target_scenario, "po": po}

    def dispute_invoice(self, scenario_id: int, dispute_memo: str, analyst_signature: str = "Surya Teja") -> Dict[str, Any]:
        """Locks invoice for payment hold and dispatches formal vendor dispute memo."""
        target_scenario = None
        for s in self.scenarios:
            if s.get("scenario_id") == scenario_id:
                target_scenario = s
                break
        if not target_scenario:
            return {"success": False, "error": f"Scenario {scenario_id} not found"}

        target_scenario["execution_status"] = "DISPUTE SENT — VENDOR HOLD"
        target_scenario["disputed"] = True
        target_scenario["disputed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        self.audit_runs.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "scenario_id": scenario_id,
            "invoice_number": target_scenario.get("invoice_number"),
            "action": "DISPATCH_VENDOR_DISPUTE_AND_LOCK",
            "auditor": analyst_signature,
            "dispute_summary": dispute_memo[:150]
        })

        return {"success": True, "scenario": target_scenario}

    def add_custom_scenario(self, scenario_data: Dict[str, Any]) -> int:
        """Appends a new synthesized or uploaded commercial invoice scenario."""
        new_id = len(self.scenarios) + 1
        scenario_data["scenario_id"] = new_id
        if "execution_status" not in scenario_data:
            scenario_data["execution_status"] = "AUDITED"
        self.scenarios.append(scenario_data)
        return new_id

# Singleton ERP instance
erp_store = ERPStateStore()
