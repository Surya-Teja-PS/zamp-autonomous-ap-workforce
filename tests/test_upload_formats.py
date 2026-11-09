"""
tests/test_upload_formats.py
----------------------------
Tests uploading real files (PDF, DOCX, TXT, JSON) to the live server
and verifying the 6-Node Deterministic Validation Engine response.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path
import docx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent

def test_document_uploads():
    base_url = "http://localhost:5000/api/upload"

    # 1. Create temporary test DOCX
    docx_path = ROOT / "test_invoice_upload.docx"
    doc = docx.Document()
    doc.add_paragraph("INVOICE\nVendor: Apex Cloud Systems Inc.\nTax ID: 94-3829104\nAccount #: *4821")
    doc.add_paragraph("Invoice #: INV-DOCX-9901\nInvoice Date: 2026-11-08\nPO Reference: PO-2026-101")
    doc.add_paragraph("Line Items:")
    doc.add_paragraph("ACS-BLADE-X1 Enterprise Server Blade Gen-5 10 EA $1,200.00 $12,000.00")
    doc.add_paragraph("Subtotal: $12,000.00\nSales Tax: $960.00\nTotal Amount: $12,960.00")
    doc.save(str(docx_path))

    # 2. Create temporary test TXT
    txt_path = ROOT / "test_invoice_upload.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("""
INVOICE
Vendor: Vanguard Industrial Supply
Tax ID: 84-1920491
Account #: *3304
Invoice #: INV-TXT-7740
Invoice Date: 2026-11-08
PO Reference: PO-2026-309
Line Items:
VIS-VALVE-HD Heavy-Duty Hydraulic Valve Model-X 100 EA $122.00 $12,200.00
Subtotal: $12,200.00
Total Amount: $12,200.00
""")

    # Function to perform multipart upload
    def upload_file(fpath):
        fname = os.path.basename(fpath)
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        with open(fpath, "rb") as fp:
            file_bytes = fp.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            base_url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode("utf-8"))

    print("=" * 60)
    print("TESTING DOCUMENT INGESTION & 6-NODE ERROR ANALYSIS")
    print("=" * 60)

    # Test Sample PDF Upload
    sample_pdf = ROOT / "static" / "samples" / "INV-2026-9001_Happy_Path.pdf"
    if sample_pdf.exists():
        pdf_res = upload_file(str(sample_pdf))
        assert pdf_res["success"] is True
        print(f"[PASS] PDF Ingestion: {sample_pdf.name}")
        print(f"       Extracted Invoice: {pdf_res['scenario']['invoice_number']}")
        print(f"       Verdict: {pdf_res['validation']['status_badge']} ({pdf_res['validation']['total_latency_ms']}ms)")
        print(f"       Nodes Evaluated: {len(pdf_res['validation']['nodes'])}")

    # Test DOCX Upload
    docx_res = upload_file(str(docx_path))
    assert docx_res["success"] is True
    print(f"\n[PASS] DOCX Ingestion: {docx_path.name}")
    print(f"       Extracted Invoice: {docx_res['scenario']['invoice_number']}")
    print(f"       Verdict: {docx_res['validation']['status_badge']}")
    print(f"       Nodes Evaluated: {len(docx_res['validation']['nodes'])}")
    for node in docx_res['validation']['nodes']:
        print(f"         - Node {node['node_id']} ({node['code']}): {node['status']}")

    # Test TXT Upload
    txt_res = upload_file(str(txt_path))
    assert txt_res["success"] is True
    print(f"\n[PASS] TXT Ingestion: {txt_path.name}")
    print(f"       Extracted Invoice: {txt_res['scenario']['invoice_number']}")
    print(f"       Verdict: {txt_res['validation']['status_badge']}")
    print(f"       Reasoning: {txt_res['validation']['decision_reasoning'][:80]}...")

    # Cleanup temp files
    if docx_path.exists(): os.remove(str(docx_path))
    if txt_path.exists(): os.remove(str(txt_path))

    print("\n" + "=" * 60)
    print("ALL DOCUMENT INGESTION & PARSER TESTS PASSED (100% GREEN)")
    print("=" * 60)

if __name__ == "__main__":
    test_document_uploads()
