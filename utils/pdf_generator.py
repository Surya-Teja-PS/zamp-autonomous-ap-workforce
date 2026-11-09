"""
utils/pdf_generator.py
----------------------
Generates authentic, high-fidelity commercial invoice PDF documents using ReportLab.
Used to supply downloadable sample test PDFs for the 6 master scenarios and custom chaos invoices.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_invoice_pdf(scenario_data: dict, output_path: str):
    """
    Renders an authentic, crisp enterprise commercial invoice PDF.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom Clean Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#09090B')
    )
    
    vendor_title_style = ParagraphStyle(
        'VendorTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#09090B')
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B')
    )

    meta_bold = ParagraphStyle(
        'MetaBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#09090B')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#475569')
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=2,
        textColor=colors.HexColor('#0F172A')
    )

    table_cell_bold_right = ParagraphStyle(
        'TableCellBoldRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=2,
        textColor=colors.HexColor('#09090B')
    )

    # 1. Header Block (Vendor on Left, Invoice Meta on Right)
    inv_num = scenario_data.get('invoice_number') or 'MISSING INVOICE NUMBER'
    inv_date = scenario_data.get('invoice_date') or 'MISSING STATUTORY DATE'
    po_num = scenario_data.get('po_number') or 'Blank / Implied'
    tax_id = scenario_data.get('tax_id') or 'N/A'
    vendor_name = scenario_data.get('vendor_name') or 'Vendor Entity'
    
    header_data = [
        [
            Paragraph(f"<b>{vendor_name}</b>", vendor_title_style),
            Paragraph("<b>COMMERCIAL INVOICE</b>", title_style)
        ],
        [
            Paragraph(f"Tax ID / EIN: <b>{tax_id}</b><br/>Commercial Accounts Division<br/>Payment Terms: Net 30 Days", meta_style),
            Paragraph(f"Invoice #: <b>{inv_num}</b><br/>Invoice Date: <b>{inv_date}</b><br/>PO Reference: <b>{po_num}</b>", meta_style)
        ]
    ]

    header_table = Table(header_data, colWidths=[320, 220])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # Bill-To Block
    billto_data = [
        [
            Paragraph("<b>BILL TO:</b><br/>Acme Enterprise Global Corp.<br/>500 Financial Center Blvd, Suite 1200<br/>San Francisco, CA 94105<br/>Accounts Payable: ap@acme-enterprise.com", meta_style),
            Paragraph(f"<b>REMITTANCE WIRE INSTRUCTIONS:</b><br/>Bank: Silicon Commercial Bank NA<br/>Account Number: •••• {scenario_data.get('remit_bank_last4', '0000')}<br/>ACH / Wire Routing: 121000358<br/>Status: Standard Commercial Wire", meta_style)
        ]
    ]
    billto_table = Table(billto_data, colWidths=[320, 220])
    billto_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(billto_table)
    story.append(Spacer(1, 15))

    # Line Items Table
    lines = scenario_data.get('line_items', [])
    line_table_data = [
        [
            Paragraph("ITEM / SKU", table_header_style),
            Paragraph("DESCRIPTION", table_header_style),
            Paragraph("QTY", table_header_style),
            Paragraph("UNIT RATE", table_cell_bold_right),
            Paragraph("LINE TOTAL", table_cell_bold_right)
        ]
    ]

    for item in lines:
        line_table_data.append([
            Paragraph(f"<b>{item.get('sku', 'LINE-SKU')}</b>", table_cell_style),
            Paragraph(item.get('description', 'Service / Goods'), table_cell_style),
            Paragraph(f"{item.get('quantity', 1)} {item.get('unit', 'EA')}", table_cell_style),
            Paragraph(f"${item.get('unit_price', 0.0):,.2f}", table_cell_right),
            Paragraph(f"<b>${item.get('amount', 0.0):,.2f}</b>", table_cell_bold_right)
        ])

    line_table = Table(line_table_data, colWidths=[85, 235, 60, 80, 80])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 15))

    # Totals Summary Block (Right Aligned)
    subtotal = scenario_data.get('stated_subtotal', 0.0)
    tax = scenario_data.get('stated_tax', 0.0)
    freight = scenario_data.get('stated_freight', 0.0)
    grand_total = scenario_data.get('stated_grand_total', 0.0)

    summary_data = [
        [Paragraph("Net Subtotal:", meta_bold), Paragraph(f"${subtotal:,.2f}", table_cell_bold_right)],
        [Paragraph("Statutory Sales Tax:", meta_style), Paragraph(f"${tax:,.2f}", table_cell_right)],
        [Paragraph("Freight & Handling:", meta_style), Paragraph(f"${freight:,.2f}", table_cell_right)],
        [Paragraph("<b>TOTAL DUE (USD):</b>", ParagraphStyle('GT', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#09090B'))),
         Paragraph(f"<b>${grand_total:,.2f}</b>", ParagraphStyle('GTR', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=2, textColor=colors.HexColor('#09090B')))]
    ]

    summary_table = Table(summary_data, colWidths=[130, 90], hAlign='RIGHT')
    summary_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, 3), (-1, 3), 1, colors.HexColor('#09090B')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Regulatory & Audit Footer
    footer_text = Paragraph(
        "<i>This is an official commercial invoice document generated for autonomous accounts payable verification under SOX Section 404 guidelines. "
        "Any discrepancies must be submitted in writing within 14 calendar days. Electronic payments are processed via ACH/FedWire.</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=colors.HexColor('#94A3B8'))
    )
    story.append(footer_text)

    doc.build(story)
    return output_path
