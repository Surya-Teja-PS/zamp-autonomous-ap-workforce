"""
tests/generate_sample_invoices.py
---------------------------------
Generates realistic sample PDF invoices for the 5 demo scenarios:
  1. Happy Path: INV-BW-001 (Buildwell, PO-2024-001, 50kg Steel @ Rs 500) -> Approved
  2. Duplicate: INV-BW-001 (Identical resubmission) -> Blocked
  3. Qty Overclaim: INV-BW-002 (Buildwell, 40kg Steel, but only 30kg available) -> Review
  4. Price Deviation: INV-TP-001 (TechParts, PO-2024-002, 100 Caps @ Rs 26.50 vs Rs 25.00) -> Review
  5. Missing Data / Degraded: Incomplete details, missing invoice number -> Review
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

OUT_DIR = Path(__file__).resolve().parent.parent / "sample_invoices"
OUT_DIR.mkdir(exist_ok=True)


def create_invoice_pdf(
    filename: str,
    vendor_name: str,
    vendor_gstin: str,
    vendor_address: str,
    invoice_number: str | None,
    invoice_date: str | None,
    po_reference: str | None,
    line_items: list[dict],
    subtotal: float | None,
    tax_amount: float | None,
    total_amount: float | None,
    notes: str = "",
    degraded: bool = False,
):
    path = OUT_DIR / filename
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#1e293b"))
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#64748b"))
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=9, leading=12, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=9, leading=12)

    story = []

    # Header
    story.append(Paragraph(f"<b>{vendor_name}</b>", title_style))
    story.append(Paragraph(f"GSTIN: {vendor_gstin}", subtitle_style))
    story.append(Paragraph(vendor_address, subtitle_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>TAX INVOICE</b>", ParagraphStyle('TaxInv', parent=styles['Heading2'], fontSize=14, leading=16, textColor=colors.HexColor("#2563eb"))))
    story.append(Spacer(1, 10))

    # Meta table
    meta_data = [
        [
            Paragraph("<b>Invoice No:</b>", bold_style),
            Paragraph(invoice_number if invoice_number else "[UNREADABLE / MISSING]", normal_style),
            Paragraph("<b>Invoice Date:</b>", bold_style),
            Paragraph(invoice_date if invoice_date else "[UNREADABLE / MISSING]", normal_style)
        ],
        [
            Paragraph("<b>PO Reference:</b>", bold_style),
            Paragraph(po_reference if po_reference else "N/A", normal_style),
            Paragraph("<b>Payment Terms:</b>", bold_style),
            Paragraph("Net 30 Days", normal_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[90, 170, 90, 170])
    t_meta.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1e293b")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    # Line Items Table
    headers = ["#", "Item Description", "Qty", "Unit Price (Rs)", "GST %", "Tax (Rs)", "Total (Rs)"]
    table_data = [[Paragraph(f"<b>{h}</b>", bold_style) for h in headers]]

    for item in line_items:
        table_data.append([
            Paragraph(str(item.get("line", 1)), normal_style),
            Paragraph(item.get("desc", ""), normal_style),
            Paragraph(f"{item.get('qty', 0):.1f} {item.get('unit', '')}", normal_style),
            Paragraph(f"{item.get('price', 0):,.2f}", normal_style),
            Paragraph(f"{item.get('tax_rate', 0):.0f}%", normal_style),
            Paragraph(f"{item.get('tax_amount', 0):,.2f}", normal_style),
            Paragraph(f"{item.get('total', 0):,.2f}", normal_style),
        ])

    col_widths = [25, 200, 55, 75, 45, 60, 65]
    t_items = Table(table_data, colWidths=col_widths)
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 15))

    # Totals table
    totals_data = []
    if subtotal is not None:
        totals_data.append(["Taxable Value (Subtotal):", f"Rs. {subtotal:,.2f}"])
    if tax_amount is not None:
        totals_data.append(["Total Tax (GST):", f"Rs. {tax_amount:,.2f}"])
    if total_amount is not None:
        totals_data.append(["Invoice Total (INR):", f"Rs. {total_amount:,.2f}"])

    if totals_data:
        t_totals = Table(totals_data, colWidths=[380, 145])
        t_totals.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,-1), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor("#1e293b")),
        ]))
        story.append(t_totals)

    if notes:
        story.append(Spacer(1, 15))
        story.append(Paragraph(f"<b>Notes:</b> {notes}", subtitle_style))

    doc.build(story)
    print(f"[OK] Generated: {path.name}")


def generate_all():
    # ── Scenario 1: Happy Path (INV-BW-001) ──────────────────────────────────
    # Buildwell Supplies | PO-2024-001 | 50 kg Steel @ Rs 500, GST 18%
    create_invoice_pdf(
        filename="INV-BW-001_HappyPath.pdf",
        vendor_name="Buildwell Supplies Pvt Ltd",
        vendor_gstin="29AABCB1234F1Z5",
        vendor_address="12, Industrial Area, Bengaluru, Karnataka 560099",
        invoice_number="INV-BW-001",
        invoice_date="2024-10-25",
        po_reference="PO-2024-001",
        line_items=[{
            "line": 1,
            "desc": "MS Steel Rods 12mm dia (TMT Fe500)",
            "qty": 50.0,
            "unit": "kg",
            "price": 500.00,
            "tax_rate": 18.0,
            "tax_amount": 4500.00,
            "total": 29500.00
        }],
        subtotal=25000.00,
        tax_amount=4500.00,
        total_amount=29500.00,
        notes="Delivered against Site A procurement order."
    )

    # ── Scenario 2: Duplicate of Happy Path ─────────────────────────────────
    create_invoice_pdf(
        filename="INV-BW-001_Duplicate.pdf",
        vendor_name="Buildwell Supplies Pvt Ltd",
        vendor_gstin="29AABCB1234F1Z5",
        vendor_address="12, Industrial Area, Bengaluru, Karnataka 560099",
        invoice_number="INV-BW-001",
        invoice_date="2024-10-25",
        po_reference="PO-2024-001",
        line_items=[{
            "line": 1,
            "desc": "MS Steel Rods 12mm dia (TMT Fe500)",
            "qty": 50.0,
            "unit": "kg",
            "price": 500.00,
            "tax_rate": 18.0,
            "tax_amount": 4500.00,
            "total": 29500.00
        }],
        subtotal=25000.00,
        tax_amount=4500.00,
        total_amount=29500.00,
        notes="Resubmission test copy."
    )

    # ── Scenario 3: Quantity Overclaim (INV-BW-002) ──────────────────────────
    # Buildwell Supplies | PO-2024-001 | Invoiced 40 kg (only 30 kg remaining from 80 accepted)
    create_invoice_pdf(
        filename="INV-BW-002_QuantityOverclaim.pdf",
        vendor_name="Buildwell Supplies Pvt Ltd",
        vendor_gstin="29AABCB1234F1Z5",
        vendor_address="12, Industrial Area, Bengaluru, Karnataka 560099",
        invoice_number="INV-BW-002",
        invoice_date="2024-10-28",
        po_reference="PO-2024-001",
        line_items=[{
            "line": 1,
            "desc": "MS Steel Rods 12mm dia (TMT Fe500)",
            "qty": 40.0,
            "unit": "kg",
            "price": 500.00,
            "tax_rate": 18.0,
            "tax_amount": 3600.00,
            "total": 23600.00
        }],
        subtotal=20000.00,
        tax_amount=3600.00,
        total_amount=23600.00,
        notes="Final batch delivery."
    )

    # ── Scenario 4: Price Deviation (INV-TP-001) ─────────────────────────────
    # TechParts | PO-2024-002 | 100 Capacitors @ Rs 26.50 (PO agreed is Rs 25.00, +6% > 2% tol)
    create_invoice_pdf(
        filename="INV-TP-001_PriceDeviation.pdf",
        vendor_name="TechParts India Pvt Ltd",
        vendor_gstin="27AABCT5678G1Z3",
        vendor_address="45, MIDC, Pune, Maharashtra 411019",
        invoice_number="INV-TP-001",
        invoice_date="2024-10-26",
        po_reference="PO-2024-002",
        line_items=[{
            "line": 1,
            "desc": "Ceramic Capacitors 100nF 50V SMD",
            "qty": 100.0,
            "unit": "pcs",
            "price": 26.50,
            "tax_rate": 18.0,
            "tax_amount": 477.00,
            "total": 3127.00
        }],
        subtotal=2650.00,
        tax_amount=477.00,
        total_amount=3127.00,
        notes="Price adjusted for raw material surcharge."
    )

    # ── Scenario 5: Missing / Degraded Data ──────────────────────────────────
    # Missing invoice number and date
    create_invoice_pdf(
        filename="INV-DEGRADED_MissingData.pdf",
        vendor_name="Buildwell Supplies Pvt Ltd",
        vendor_gstin="29AABCB1234F1Z5",
        vendor_address="12, Industrial Area, Bengaluru, Karnataka 560099",
        invoice_number=None,
        invoice_date=None,
        po_reference="PO-2024-001",
        line_items=[{
            "line": 1,
            "desc": "MS Steel Rods 12mm dia (TMT Fe500)",
            "qty": 20.0,
            "unit": "kg",
            "price": 500.00,
            "tax_rate": 18.0,
            "tax_amount": 1800.00,
            "total": 11800.00
        }],
        subtotal=10000.00,
        tax_amount=1800.00,
        total_amount=11800.00,
        notes="Damaged original slip."
    )


if __name__ == "__main__":
    generate_all()
