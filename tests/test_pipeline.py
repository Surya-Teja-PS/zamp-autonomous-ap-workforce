"""
tests/test_pipeline.py
----------------------
End-to-end automated test suite verifying all 5 demo scenarios plus human override:
  1. Happy Path -> Approved
  2. Duplicate Submission -> Blocked / Duplicate
  3. Quantity Overclaim -> Review
  4. Price Deviation -> Review
  5. Missing Data -> Review
  6. Human Review Override -> Direct approve with mandatory comment
  7. Hard-block protection -> Duplicate cannot be overridden
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.seed import seed
from core.database import get_connection, get_invoice, get_validation_results, get_audit_trail
from core.intake import process_intake
from core.pipeline import run_pipeline
from core.decision import override_review

SAMPLE_DIR = ROOT / "sample_invoices"


def run_test_suite():
    print("=" * 60)
    print("STARTING INVOICEAI END-TO-END VERIFICATION SUITE")
    print("=" * 60)

    # 1. Reset database with seed data
    print("\n[Step 0] Resetting and seeding database...")
    seed(reset=True)

    # ── Test 1: Happy Path ──────────────────────────────────────────────────
    print("\n[Scenario 1] Testing Happy Path (INV-BW-001)...")
    pdf_path = SAMPLE_DIR / "INV-BW-001_HappyPath.pdf"
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    conn = get_connection()
    intake = process_intake(
        conn,
        file_bytes=file_bytes,
        filename=pdf_path.name,
        vendor_id=1,  # Buildwell
        po_id=1       # PO-2024-001
    )
    inv1_id = intake["invoice_id"]
    conn.close()

    # Run pipeline generator to completion
    for stage, state, msg in run_pipeline(inv1_id):
        pass

    conn = get_connection()
    inv1 = get_invoice(conn, inv1_id)
    checks1 = {c["check_name"]: c["status"] for c in get_validation_results(conn, inv1_id)}
    conn.close()

    print(f"  Result status: {inv1['status']}")
    print(f"  Validation checks: {checks1}")
    assert inv1["status"] == "approved", f"Expected approved, got {inv1['status']}"
    assert all(st == "passed" for st in checks1.values()), "All checks should pass"
    print("  -> [PASS] Scenario 1: Happy Path AUTO-APPROVED")

    # ── Test 2: Duplicate Invoice ───────────────────────────────────────────
    print("\n[Scenario 2] Testing T1 Duplicate Block (INV-BW-001 resubmission)...")
    pdf_path2 = SAMPLE_DIR / "INV-BW-001_Duplicate.pdf"
    with open(pdf_path2, "rb") as f:
        file_bytes2 = f.read()

    conn = get_connection()
    intake2 = process_intake(
        conn,
        file_bytes=file_bytes2,
        filename=pdf_path2.name,
        vendor_id=1,
        po_id=1
    )
    inv2_id = intake2["invoice_id"]
    conn.close()

    for stage, state, msg in run_pipeline(inv2_id):
        pass

    conn = get_connection()
    inv2 = get_invoice(conn, inv2_id)
    checks2 = {c["check_name"]: c["status"] for c in get_validation_results(conn, inv2_id)}
    conn.close()

    print(f"  Result status: {inv2['status']}")
    print(f"  Duplicate check status: {checks2.get('duplicate_check')}")
    assert inv2["status"] in ("duplicate", "rejected"), f"Expected duplicate, got {inv2['status']}"
    assert checks2.get("duplicate_check") == "failed", "Duplicate check must fail"
    print("  -> [PASS] Scenario 2: Duplicate Invoice BLOCKED")

    # ── Test 3: Quantity Overclaim ──────────────────────────────────────────
    print("\n[Scenario 3] Testing T2 Quantity Overclaim (INV-BW-002)...")
    pdf_path3 = SAMPLE_DIR / "INV-BW-002_QuantityOverclaim.pdf"
    with open(pdf_path3, "rb") as f:
        file_bytes3 = f.read()

    conn = get_connection()
    intake3 = process_intake(
        conn,
        file_bytes=file_bytes3,
        filename=pdf_path3.name,
        vendor_id=1,
        po_id=1
    )
    inv3_id = intake3["invoice_id"]
    conn.close()

    for stage, state, msg in run_pipeline(inv3_id):
        pass

    conn = get_connection()
    inv3 = get_invoice(conn, inv3_id)
    checks3 = {c["check_name"]: c["status"] for c in get_validation_results(conn, inv3_id)}
    conn.close()

    print(f"  Result status: {inv3['status']}")
    print(f"  Quantity check: {checks3.get('quantity_check')}")
    assert inv3["status"] == "review", f"Expected review, got {inv3['status']}"
    assert checks3.get("quantity_check") == "failed", "Quantity check must fail"
    print("  -> [PASS] Scenario 3: Quantity Overclaim routed to REVIEW")

    # ── Test 4: Price Deviation ─────────────────────────────────────────────
    print("\n[Scenario 4] Testing T3 Price Deviation (INV-TP-001)...")
    pdf_path4 = SAMPLE_DIR / "INV-TP-001_PriceDeviation.pdf"
    with open(pdf_path4, "rb") as f:
        file_bytes4 = f.read()

    conn = get_connection()
    intake4 = process_intake(
        conn,
        file_bytes=file_bytes4,
        filename=pdf_path4.name,
        vendor_id=2,  # TechParts
        po_id=2       # PO-2024-002
    )
    inv4_id = intake4["invoice_id"]
    conn.close()

    for stage, state, msg in run_pipeline(inv4_id):
        pass

    conn = get_connection()
    inv4 = get_invoice(conn, inv4_id)
    checks4 = {c["check_name"]: c["status"] for c in get_validation_results(conn, inv4_id)}
    conn.close()

    print(f"  Result status: {inv4['status']}")
    print(f"  Price check: {checks4.get('price_check')}")
    assert inv4["status"] == "review", f"Expected review, got {inv4['status']}"
    assert checks4.get("price_check") == "failed", "Price check must fail"
    print("  -> [PASS] Scenario 4: Price Deviation routed to REVIEW")

    # ── Test 5: Missing Mandatory Fields ────────────────────────────────────
    print("\n[Scenario 5] Testing T4 Missing Mandatory Data (INV-DEGRADED)...")
    pdf_path5 = SAMPLE_DIR / "INV-DEGRADED_MissingData.pdf"
    with open(pdf_path5, "rb") as f:
        file_bytes5 = f.read()

    conn = get_connection()
    intake5 = process_intake(
        conn,
        file_bytes=file_bytes5,
        filename=pdf_path5.name,
        vendor_id=1,
        po_id=1
    )
    inv5_id = intake5["invoice_id"]
    conn.close()

    for stage, state, msg in run_pipeline(inv5_id):
        pass

    conn = get_connection()
    inv5 = get_invoice(conn, inv5_id)
    conn.close()

    print(f"  Result status: {inv5['status']}")
    assert inv5["status"] == "review", f"Expected review, got {inv5['status']}"
    print("  -> [PASS] Scenario 5: Missing Data routed to REVIEW")

    # ── Test 6: Human Review Override (FR-31) ───────────────────────────────
    print("\n[Scenario 6] Testing AP Reviewer Override on Review invoice (inv3)...")
    conn = get_connection()
    override_res = override_review(
        conn,
        invoice_id=inv3_id,
        reviewer_user_id=1, # ap@company.com
        action="approve",
        comment="Discrepancy resolved: warehouse verified additional 10 kg received under supplementary slip."
    )
    inv3_after = get_invoice(conn, inv3_id)
    audit3 = get_audit_trail(conn, inv3_id)
    conn.close()

    print(f"  Status after override: {inv3_after['status']}")
    print(f"  Reviewer note: {inv3_after['reviewer_comment']}")
    assert inv3_after["status"] == "approved", "Status should be approved after override"
    assert any(a["action"] == "review_override_approved" for a in audit3), "Audit log must record override"
    print("  -> [PASS] Scenario 6: Reviewer override committed to DB and audit trail")

    # ── Test 7: Prevent Override on Duplicate (Hard Block) ──────────────────
    print("\n[Scenario 7] Testing security protection: cannot override duplicate...")
    conn = get_connection()
    try:
        override_review(
            conn,
            invoice_id=inv2_id,
            reviewer_user_id=1,
            action="approve",
            comment="Attempting illegal override on duplicate"
        )
        assert False, "Should have thrown ValueError"
    except ValueError as e:
        print(f"  Expected error caught: {e}")
        print("  -> [PASS] Scenario 7: Illegal override on duplicate properly rejected")
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("ALL 7 SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    run_test_suite()
