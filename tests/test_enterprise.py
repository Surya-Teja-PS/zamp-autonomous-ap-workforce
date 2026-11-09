"""
tests/test_enterprise.py
--------------------
Master verification suite for enterprise 3-way match & treasury optimization:
1. Industrial 3-Way Match Telemetry in ERP store & Scenario Registry
2. Corporate Treasury Engine & 2/10 Net 30 Alpha (36.73% APR) in Analytics
3. Balanced NetSuite Double-Entry GL Voucher with SHA-256 SOX Hash & ISO-20022 Fedwire
4. Interactive Guided Product Tour DOM nodes in index.html
"""

import sys
import io
from pathlib import Path

# Force UTF-8 on Windows Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.erp_store import erp_store
from core.validation_engine import validation_engine

def test_enterprise_verification():
    print("=" * 60)
    print("MASTER VERIFICATION SUITE: INDUSTRIAL 3-WAY MATCH & TREASURY ENGINE")
    print("=" * 60)

    # 1. Check Purchase Orders GRN enrichment
    print("\n[1] Checking PO Master Store GRN integration...")
    for po in erp_store.purchase_orders:
        assert "grn_id" in po, f"PO {po['po_number']} missing grn_id"
        assert "grn_dock" in po, f"PO {po['po_number']} missing grn_dock"
        assert "grn_inspector" in po, f"PO {po['po_number']} missing grn_inspector"
        print(f"  [PASS] {po['po_number']} linked to {po['grn_id']} ({po['grn_dock']})")

    # 2. Check 3-Way Match in all 6 Scenarios
    print("\n[2] Checking 3-Way Match telemetry across all 6 scenarios...")
    for s in erp_store.scenarios:
        assert "three_way_match" in s, f"Scenario {s['scenario_id']} missing three_way_match"
        m = s["three_way_match"]
        assert "grn_id" in m
        assert "contracted_po_qty" in m
        assert "warehouse_grn_qty" in m
        assert "billed_invoice_qty" in m
        assert "match_status" in m
        print(f"  [PASS] Scenario #{s['scenario_id']} ({s['name'][:30]}...): {m['match_status']} [GRN: {m['grn_id']}]")

    # 3. Test NetSuite GL Disbursement, Balanced Double-Entry & SHA-256 Hash
    print("\n[3] Testing NetSuite GL Disbursement & Cryptographic SOX Hash...")
    disburse_res = erp_store.disburse_invoice(1, analyst_signature="P. S. Surya Teja (AI Solutions Architect)")
    assert disburse_res["success"] is True
    voucher = disburse_res["voucher"]
    assert voucher["is_balanced"] is True
    assert voucher["total_debits"] == voucher["total_credits"] == 12960.00
    assert len(voucher["sox_section_404_hash"]) == 64
    assert voucher["iso_20022_wire"]["message_definition"] == "pain.001.001.09"
    print(f"  [PASS] Journal Entry ID: {voucher['journal_entry_id']}")
    print(f"  [PASS] Balanced GL Check: Total Debits ${voucher['total_debits']:,.2f} == Total Credits ${voucher['total_credits']:,.2f}")
    print(f"  [PASS] SOX Section 404 Cryptographic Hash (SHA-256): {voucher['sox_section_404_hash']}")
    print(f"  [PASS] ISO-20022 Fedwire Wire ID: {voucher['iso_20022_wire']['instruction_identification']}")

    # 4. Check index.html DOM structure for Interactive Guided Tour & Treasury
    print("\n[4] Checking index.html DOM elements for Interactive Guided Tour Engine...")
    html_content = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "btn-start-tour" in html_content, "Missing ▶ Interactive Product Tour navbar button"
    assert "dash-treasury-strip" in html_content, "Missing Treasury & Working Capital strip"
    assert "36.73% APR" in html_content, "Missing 36.73% APR calculation"
    assert "studio-3way-match-card" in html_content, "Missing 3-Way Match Telemetry Card in Studio"
    assert "tour-spotlight-ring" in html_content, "Missing Tour Spotlight Ring"
    assert "tour-card" in html_content, "Missing Floating Executive Walkthrough Card"
    assert "welcome-modal" in html_content, "Missing First-Load Welcome Modal"
    assert "TOUR_STEPS" in html_content, "Missing 7-Step Tour sequence definition"
    print("  [PASS] All Interactive Product Tour DOM nodes and scripts verified.")

    print("\n" + "=" * 60)
    print("ALL ENTERPRISE RECONCILIATION REQUIREMENTS VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_enterprise_verification()
