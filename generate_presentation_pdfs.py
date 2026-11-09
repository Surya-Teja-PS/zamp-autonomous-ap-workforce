"""
generate_presentation_pdfs.py
------------------------------
Generates 3 publication-quality executive presentation PDFs for Zamp:
1. Zamp_AP_Video_Recording_Demo_Script.pdf (Turnkey Video Screen Walkthrough & Script)
2. Zamp_AP_Executive_Interview_Playbook.pdf (Strategic Architecture & Technical Defense)
3. Zamp_AP_Live_Product_Walkthrough_Guide.pdf (Live Interactive Demo & Stakeholder Walkthrough)
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# ── NUMBERED CANVAS HELPER ──────────────────────────────────────────────────

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "ZAMP / AP-AUTONOMOUS-WORKFORCE — EXECUTIVE PLAYBOOK")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "STRICT CONFIDENTIAL & PROPRIETARY")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Footer (All pages)
        self.setFont("Helvetica", 8)
        self.drawString(54, 34, "P. S. Surya Teja — AI Solutions Architect | Zamp Problem Statement 1")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 34, page_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 46, 8.5 * inch - 54, 46)
        
        self.restoreState()


# ── STYLE FACTORY ───────────────────────────────────────────────────────────

def setup_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor("#0F172A")
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    meta_badge_style = ParagraphStyle(
        'MetaBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#059669")
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'h1': h1_style,
        'h2': h2_style,
        'body': body_style,
        'bullet': bullet_style,
        'callout': callout_style,
        'code': code_style,
        'meta': meta_badge_style
    }

def create_callout(text, styles, bg_color="#F8FAFC", border_color="#10B981"):
    p = Paragraph(text, styles['callout'])
    t = Table([[p]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('LINEBEFORE', (0,0), (0,-1), 3.5, colors.HexColor(border_color)),
    ]))
    return t


# ── PDF 1: VIDEO RECORDING DEMO SCRIPT ──────────────────────────────────────

def build_video_script_pdf(output_path):
    styles = setup_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []

    # Title & Metadata
    story.append(Paragraph("ZAMP AP-AUTONOMOUS-WORKFORCE", styles['meta']))
    story.append(Paragraph("Turnkey Video Recording Demo Script & Screen Walkthrough", styles['title']))
    story.append(Paragraph("<b>Target Length:</b> 4:30 – 5:15 Minutes | <b>Format:</b> 1080p Full-Screen Screencast (Loom / YouTube) | <b>Presenter:</b> P. S. Surya Teja (AI Solutions Architect)", styles['subtitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=10))

    # Pre-Flight Setup
    story.append(Paragraph("1. Pre-Recording Technical Checklist", styles['h1']))
    story.append(Paragraph("Before hitting record, ensure your local environment is pristine:", styles['body']))
    checklist_items = [
        "<b>Server URL:</b> Open Google Chrome / Brave to <code>http://localhost:5000</code> in full screen (F11 or maximized window).",
        "<b>Reset State:</b> Click the <code>Reset ERP</code> button in the top navbar once so all 6 scenarios and PO budgets are at master seed state.",
        "<b>Audio Setup:</b> Use a dedicated external mic. Speak with confident, authoritative executive cadence (like a Senior Director of AI Solutions at Ramp / Stripe).",
        "<b>Cursor Visibility:</b> Set your screen recorder to show a high-contrast mouse pointer or subtle click-glow."
    ]
    for item in checklist_items:
        story.append(Paragraph(f"• {item}", styles['bullet']))

    story.append(Spacer(1, 8))

    # Detailed Timeline Script
    story.append(Paragraph("2. Minute-by-Minute Narration & Action Walkthrough", styles['h1']))

    acts = [
        {
            "time": "[0:00 – 0:35] Act 0: The Executive Hook & Problem Statement",
            "action": "Browser resting on the AP Command Dashboard (http://localhost:5000). Hover cursor near Zamp Monogram.",
            "script": "<i>\"Hi everyone, I’m <b>P. S. Surya Teja</b>, and this is the <b>Zamp Autonomous AP Workforce Platform</b> built for Problem Statement 1.<br/><br/>In corporate finance, manual Accounts Payable is a critical operational liability: the average enterprise spends <b>4.2 days</b> per invoice, suffers a <b>3.8% error rate</b>, and loses millions to <b>Business Email Compromise (BEC) wire fraud</b> and duplicate billings.<br/><br/>Instead of relying on naive, non-deterministic LLM prompts that hallucinate arithmetic and fail SOX 404 audit compliance, I engineered an <b>Institutional FinTech Reconciler</b>. It pairs multimodal document extraction with a <b>deterministic 6-Node Financial Validation Gate Pipeline</b>, achieving <b>sub-100ms latency</b>, <b>33.3% autonomous straight-through processing (STP)</b>, and <b>100% cryptographic auditability</b>.\"</i>"
        },
        {
            "time": "[0:35 – 1:15] Act 1: Two-Tier Command Header & ⌘K Command Palette",
            "action": "Hover across the top header. Point out the live pulse pill. Press ⌘K (or Ctrl+K), filter for 'Scenario 6', then hit ESC.",
            "script": "<i>\"To deliver a top-tier institutional fintech feel inspired by Stripe and Ramp, the interface uses a <b>Strict Zero-Wrap Two-Tier Command Header</b>.<br/><br/>Tier 1 houses our global utilities: brand monogram, live operational protocol heartbeat, and quick jump triggers. Pressing <b>⌘K</b> opens our keyboard-first Command Palette, allowing finance controllers to instantly navigate between workspaces, specific test scenarios, or corporate tolerance presets in milliseconds.<br/><br/>Tier 2 houses our <b>5 Primary Workspaces</b> alongside a live financial telemetry ticker tracking mean pipeline latency (<b>76.7ms</b>), autonomous STP clearance, and SOX 404 compliance.\"</i>"
        },
        {
            "time": "[1:15 – 2:05] Act 2: AP Command Dashboard & Dynamic Tolerance Sensitivity",
            "action": "Point to 5 KPI cards. Scroll to Tolerance Workbench. Click 'Zero Tolerance (0%)' — watch Scenario 2 quarantine live. Click 'Standard Corporate (3%)' — watch it auto-approve. Scroll to Ledger, filter by Quarantined then All.",
            "script": "<i>\"On the <b>AP Command Dashboard</b>, finance leaders gain instant operational visibility. Across our commercial dataset of $69,565, the autonomous engine cleared valid spend while quarantining <b>$26,660 in fraud, duplicate, and arithmetic threats</b>.<br/><br/>Now observe our <b>Dynamic Corporate Tolerance Workbench</b>: enterprise policies enforce dual thresholds—a percentage ceiling Δ% and an absolute dollar ceiling Δ$.<br/><br/>Watch what happens when I switch to <b>Zero Tolerance (0% / $0)</b>: instantly in memory, the engine re-evaluates all 6 invoices without a page reload. Scenario 2—which carries a legitimate $185 courier freight charge—is immediately quarantined. When I restore Standard Corporate (3% / $250), it straight-through clears.<br/><br/>Down below, our <b>Master AP Processing Ledger</b> categorizes every finding by its deterministic root-cause vector—whether it is BEC wire diversion, fuzzy suffix collisions, or unit price drift.\"</i>"
        },
        {
            "time": "[2:05 – 3:10] Act 3: Live Execution Studio & Industrial 3-Way Match",
            "action": "Click 'Live Execution Studio' in navbar. Scenario 1 loads. Point out Left Pane extraction (99.2%) & Right Pane 3-Way Match card. Click Node 5. Switch to Scenario 6, show Node 2 BEC wire alert (*7749 != *9910). Return to Scenario 1, click [Post NetSuite GL Voucher].",
            "script": "<i>\"Stepping into our <b>Live Execution Studio</b>, we see a split-screen reconciler bridging document extraction with ERP truth.<br/><br/>On the left, our multimodal parser extracts document tokens with <b>99.2% confidence</b>. On the right, we execute an <b>Industrial 3-Way Match</b>: reconciling Contracted PO-2026-101, Warehouse Receiving Dock GRN-2026-881, and billed invoice line items with 100% quantity and rate parity.<br/><br/>Notice how the engine handles taxes in Scenario 1: instead of naively comparing the $12,960 gross amount to the $12,000 PO, <b>Node 5</b> backs out the 8% embedded sales tax ($960) to reconcile net-to-net at exactly 0.0% variance.<br/><br/>Now, look at <b>Scenario 6</b>: the math is valid and the PO exists, but the footer wire remittance directs funds to account <b>*7749</b> instead of verified <b>*9910</b>. <b>Node 2</b> triggers an immediate hard quarantine—locking payment before funds leave treasury.<br/><br/>Finally, this is a closed-loop system: clicking <code>Post NetSuite GL Voucher</code> generates a balanced double-entry journal entry with a cryptographic SHA-256 audit hash.\"</i>"
        },
        {
            "time": "[3:10 – 3:55] Act 4 & 5: 6-Gate Matrix & 6 Scenario Bento Registry",
            "action": "Click '6-Gate Matrix', scroll across the 6 gates. Then click '6 Scenario Payloads'. Show the 2-column bento grid, 4-metric strip, 6-gate dots, and click '{ } Raw JSON' on Card 1.",
            "script": "<i>\"In the <b>6-Gate Matrix</b>, controllers inspect the sub-120ms sequential pipeline: Math Integrity → Duplicate & BEC Fraud → PO Resolution → Line Rates → Tolerance → Action Dispatch.<br/><br/>Next, our <b>6 Scenario Payloads Registry</b> features a high-density 2-column forensic bento grid. Each card presents a 4-metric financial strip and a 6-node micro-pipeline status strip. Clicking <b>{ } Raw JSON</b> expands the syntax-highlighted OCR payload directly on the card.\"</i>"
        },
        {
            "time": "[3:55 – 4:40] Act 6: Zero-Overlay Self-Driving Guided Product Tour",
            "action": "Click '▶ Interactive Tour' in header. Highlight that the page remains 100% unblurred and bright. Watch the virtual beacon glide and navbar active tab pulse in emerald. Step through 2 steps, then hit ESC.",
            "script": "<i>\"To make reviewing effortless, I built an <b>Interactive Guided Tour Engine</b>.<br/><br/>Notice the clean presentation: there are <b>zero full-screen dark or blurry overlays</b> washing out the website. We use <b>Positive Visual Elevation</b> to spotlight components while keeping the two-tier navbar and canvas 100% crisp. As we step through, our virtual AI Guide glides across the viewport, the Tier 2 navbar visibly pulses, and state mutations execute hands-free.\"</i>"
        },
        {
            "time": "[4:40 – 5:10] Act 7: Intake & Chaos Studio + Executive Closing",
            "action": "Click '✦ Intake & Chaos Studio', show PDF uploads and Interviewer Chaos Builder, close modal, and look at camera for closing.",
            "script": "<i>\"Finally, with our <b>Intake & Chaos Studio</b>, interviewers can upload real invoice PDFs or inject custom overcharges and wire diversions on the fly.<br/><br/>By combining deterministic multi-gate verification with an institutional design system, this platform proves that enterprise AP automation must be <b>fast, mathematically provable, and fraud-immune</b>.<br/><br/>Thank you, and I look forward to our technical deep dive!\"</i>"
        }
    ]

    for act in acts:
        story.append(Paragraph(act['time'], styles['h2']))
        story.append(Paragraph(f"<b>Visual Cue & Action:</b> {act['action']}", styles['bullet']))
        story.append(create_callout(act['script'], styles, bg_color="#F8FAFC", border_color="#6366F1"))
        story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated: {output_path}")


# ── PDF 2: EXECUTIVE INTERVIEW PLAYBOOK ──────────────────────────────────────

def build_interview_playbook_pdf(output_path):
    styles = setup_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []

    # Title & Metadata
    story.append(Paragraph("ZAMP / AP-AUTONOMOUS-WORKFORCE", styles['meta']))
    story.append(Paragraph("Executive Interview Playbook & Technical Defense Manual", styles['title']))
    story.append(Paragraph("<b>Target Audience:</b> Zamp Founding Team, VP of Engineering, & Principal Architects | <b>Candidate:</b> P. S. Surya Teja (AI Solutions Architect)", styles['subtitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=10))

    # Section 1: Executive Elevator Pitches
    story.append(Paragraph("1. High-Impact Pitch Frameworks", styles['h1']))
    
    story.append(Paragraph("A. The 30-Second Executive Pitch (System Value Architecture)", styles['h2']))
    pitch_30 = (
        "\"I built an autonomous Accounts Payable workforce platform that resolves the enterprise invoice reconciliation bottleneck. "
        "While naive AI demos use brittle LLM prompts that hallucinate math and fail audit scrutiny, my platform implements a "
        "<b>deterministic 6-Node Financial Validation Gate Pipeline</b>. It parses commercial invoices, backs out embedded taxes, "
        "verifies 3-way matches against warehouse dock receipts, blocks BEC wire fraud, and posts balanced NetSuite journal vouchers in "
        "<b>under 100 milliseconds</b>—delivering <b>33.3% autonomous straight-through processing</b> and <b>100% cryptographic SOX 404 auditability</b>.\""
    )
    story.append(create_callout(pitch_30, styles, bg_color="#ECFDF5", border_color="#10B981"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("B. The 2-Minute Solution Architecture Pitch (For Engineering Leads)", styles['h2']))
    pitch_2min = (
        "\"Our system architecture enforces a strict separation of concerns between <b>Multimodal Document Extraction</b> and <b>Deterministic Financial Validation</b>:<br/><br/>"
        "1. <b>Multimodal Token Extraction:</b> Ingestion handles OCR via PyMuPDF/pdfplumber, extracting structured field tokens (vendor, PO, line items, bank wire routing) with 99.2% confidence.<br/>"
        "2. <b>6-Node Sequential Audit Pipeline:</b> The invoice passes sequentially through Document Forensics (math & statutory dates), Duplicate & BEC Fraud Guard, Semantic PO Resolution, Milestone Budget Drawdown, Tax Separation & Tolerance Matrix, and AOP Action Synthesis.<br/>"
        "3. <b>Relational In-Memory ERP Master:</b> Validation rules evaluate against normalized relational stores (Vendors, POs with cumulative billing history, and Settled Ledgers) in sub-120ms total latency.<br/>"
        "4. <b>Closed-Loop NetSuite/SAP Dispatch:</b> Approved spend produces double-entry balanced GL vouchers with ISO-20022 Fedwire IDs and immutable SHA-256 SOX 404 compliance hashes.\""
    )
    story.append(create_callout(pitch_2min, styles, bg_color="#F8FAFC", border_color="#6366F1"))
    story.append(Spacer(1, 8))

    # Section 2: Technical Curveball Defense
    story.append(Paragraph("2. Technical Curveball Defense & Battle-Tested Q&A", styles['h1']))

    qa_list = [
        {
            "q": "Why didn't you just pass the entire invoice PDF to an LLM (Gemini 1.5 Pro / GPT-4) and ask 'Should this be approved?'",
            "a": "In corporate finance, pure LLM decisioning is an immediate disqualifier for 3 reasons:<br/>"
                 "• <b>Hallucination Risk:</b> LLMs predict token probabilities; they cannot guarantee arithmetic invariant verification. Comparing $20,185 against a $20,000 budget with a 3% tolerance ceiling requires exact arithmetic, not fuzzy probabilities.<br/>"
                 "• <b>Latency & Unit Economics:</b> LLM calls take 1,500ms to 4,000ms and cost fractions of a cent per token. Our deterministic 6-gate engine executes in <b>76.7 milliseconds</b> at zero marginal cost.<br/>"
                 "• <b>SOX 404 Auditability:</b> Auditors require reproducible deterministic proofs, not conversational explanations. Our engine produces a verifiable telemetry vector and SHA-256 digest."
        },
        {
            "q": "How does your platform prevent Business Email Compromise (BEC) wire fraud?",
            "a": "BEC wire fraud occurs when a bad actor alters only the bank account routing number on an otherwise legitimate PDF invoice.<br/>"
                 "In our engine, <b>Node 2</b> isolates remittance banking forensics before querying purchase orders. We extract the remit-to IBAN/routing number and cross-reference it against verified banking coordinates stored in the ERP Vendor Master. In Scenario 6, the invoice bills against an active PO, but footer wire remittance directs funds to <code>*7749</code> instead of verified <code>*9910</code>. Node 2 triggers a hard halt, quarantining the $10,000 payment before treasury release."
        },
        {
            "q": "How do you handle cumulative milestone billing across split POs?",
            "a": "In enterprise services, projects bill across multiple milestones on a single blanket PO. In Scenario 2, PO-2026-204 is a $50,000 contract where $30,000 was disbursed across two prior invoices, leaving $20,000 capacity. Our <b>Node 4</b> tracks cumulative ledger drawdowns. When INV-KS-103 bills $20,000 base plus $185 rush freight, Node 4 confirms capacity, while <b>Node 5</b> checks the +$185 (+0.925%) delta against dual-gate corporate tolerance (Δ% ≤ 3.0% and Δ$ ≤ $250), straight-through clearing it safely."
        },
        {
            "q": "What happens when an invoice arrives with no PO number on it?",
            "a": "Up to 15% of supplier invoices omit PO numbers. In Scenario 3, Vanguard Industrial bills 80 hydraulic valves with a blank PO field. <b>Node 3</b> executes an Implied PO Discovery algorithm: filtering open POs for Vanguard and running semantic line-item matching against open contract line items, resolving to PO-2026-309 with <b>96.4% confidence</b>. Node 4 then immediately catches that the vendor billed $122/unit vs contracted $100/unit (+22% price creep), auto-routing to Procurement with a pre-drafted dispute memo."
        }
    ]

    for item in qa_list:
        story.append(Paragraph(f"<b>Q: {item['q']}</b>", styles['h2']))
        story.append(Paragraph(item['a'], styles['body']))
        story.append(Spacer(1, 4))

    # Section 3: Industry Glossary Table
    story.append(Spacer(1, 6))
    story.append(Paragraph("3. Institutional FinTech Terminology Reference", styles['h1']))

    table_data = [
        [Paragraph("<b>Term</b>", styles['body']), Paragraph("<b>FinTech Definition & System Implementation</b>", styles['body'])],
        [Paragraph("<b>STP Rate</b>", styles['body']), Paragraph("Straight-Through Processing: % of invoices audited and approved with zero manual analyst touch (Baseline: 33.3%, Relaxed: 50.0%).", styles['bullet'])],
        [Paragraph("<b>3-Way Match</b>", styles['body']), Paragraph("Triangulating Contracted PO (rates/terms) ↔ Warehouse GRN (dock receipt quantities) ↔ Billed Commercial Invoice.", styles['bullet'])],
        [Paragraph("<b>Dual-Gate Tolerance</b>", styles['body']), Paragraph("Enforcing both a relative ceiling (Δ% ≤ 3.0%) AND an absolute dollar ceiling (Δ$ ≤ $250.00) to stop penny-leakage and large dollar errors.", styles['bullet'])],
        [Paragraph("<b>Embedded Tax Backout</b>", styles['body']), Paragraph("Extracting jurisdiction sales tax from gross totals to ensure PO line matching occurs on a clean net-to-net basis.", styles['bullet'])],
        [Paragraph("<b>SOX 404 Audit Hash</b>", styles['body']), Paragraph("SHA-256 cryptographic digest binding invoice, vendor EIN, amounts, timestamps, and gate verdicts into an immutable audit trail.", styles['bullet'])],
    ]
    t = Table(table_data, colWidths=[1.8 * inch, 5.2 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated: {output_path}")


# ── PDF 3: LIVE PRODUCT WALKTHROUGH GUIDE ───────────────────────────────────

def build_live_walkthrough_pdf(output_path):
    styles = setup_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []

    # Title & Metadata
    story.append(Paragraph("ZAMP / AP-AUTONOMOUS-WORKFORCE", styles['meta']))
    story.append(Paragraph("Live Product Walkthrough & Audience Engagement Guide", styles['title']))
    story.append(Paragraph("<b>Objective:</b> Conducting a High-Conviction, Interactive Live Demonstration on Zoom / In-Person | <b>Presenter:</b> P. S. Surya Teja", styles['subtitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=10))

    # Section 1: Presentation Psychology
    story.append(Paragraph("1. The Psychology of Pitching Technical Interviewers", styles['h1']))
    story.append(Paragraph(
        "Technical interviewers and engineering managers do not want a passive slide deck. They want to see a <b>live, responsive system</b>, "
        "understand how state mutates, and verify that you understand real-world edge cases. Follow these 3 rules:",
        styles['body']
    ))
    rules = [
        "<b>Rule 1: Hook with the Metric:</b> Open with $69,565 audited in 76.7ms and $26,660 fraud prevented.",
        "<b>Rule 2: Don't Just Talk, Mutate:</b> Move the tolerance slider live on screen. Interviewers love seeing state mutate across the app without page reloads.",
        "<b>Rule 3: Frame Anomaly Detection as Business Value:</b> When showing Scenario 6, emphasize that stopping a $10,000 BEC wire fraud saves the company 10x the annual cost of the software."
    ]
    for r in rules:
        story.append(Paragraph(f"• {r}", styles['bullet']))

    story.append(Spacer(1, 8))

    # Section 2: Phase-by-Phase Interactive Demo Script
    story.append(Paragraph("2. The 7-Phase Live Demonstration Flow", styles['h1']))

    phases = [
        {
            "phase": "Phase 1: Setting the Executive Baseline (AP Command Dashboard)",
            "action": "Land on AP Command Dashboard. Point to 5 KPI cards. Point to the Two-Tier header.",
            "talk": "\"Let's start on the AP Command Dashboard. You can see we have audited $69,565 across 6 commercial invoices in 76.7ms mean latency. 33.3% cleared autonomously, while $26,660 in fraud, duplicate, and arithmetic errors were quarantined at the gate.\""
        },
        {
            "phase": "Phase 2: The Interactive Aha! Moment (Tolerance Sensitivity)",
            "action": "Scroll down to Dynamic Corporate Tolerance Workbench. Move slider from 3% to 0%, then back to 3%.",
            "talk": "\"Watch how corporate tolerance operates dynamically. Our dual-threshold policy enforces 3.0% and $250 ceilings. When I tighten this slider to Zero Tolerance, notice how the STP rate immediately drops to 16.7% in memory: Scenario 2 (with a $185 courier freight) is instantly quarantined. Sliding back to 3% restores autonomous approval without any database reload.\""
        },
        {
            "phase": "Phase 3: The Deep Forensic Reconciler (Live Execution Studio)",
            "action": "Click 'Live Execution Studio'. Scenario 1 is loaded. Point out Left Pane extraction and Right Pane 3-Way Match.",
            "talk": "\"Now let's look under the hood in the Live Execution Studio. On the left is our multimodal extraction showing 99.2% confidence. On the right is our Industrial 3-Way Match: comparing contracted PO-2026-101, Warehouse Receiving Dock GRN-881, and the billed commercial invoice. In Scenario 1, the invoice states $12,960 gross, but Node 5 separates the 8% embedded sales tax ($960) to reconcile net-to-net with exactly $0 variance.\""
        },
        {
            "phase": "Phase 4: Threat Simulation — Catching BEC Wire Fraud",
            "action": "Select Scenario 6 (Kinetic Studio). Click Node 2. Highlight red alert banner: unverified *7749 != master *9910.",
            "talk": "\"Now observe our defense against Business Email Compromise in Scenario 6. The math is valid and PO-2026-204 is active. However, Node 2 detects that the remit bank account in the footer is *7749, whereas our verified ERP record specifies *9910. The engine triggers an immediate hard halt, locking the $10,000 disbursement before money leaves treasury.\""
        },
        {
            "phase": "Phase 5: Closed-Loop Dispatch & NetSuite GL Mutation",
            "action": "Return to Scenario 1. Click [Post NetSuite GL Voucher & Disburse]. Show the modal popup.",
            "talk": "\"This isn't a mock dashboard—it's a closed-loop system. When I click 'Post NetSuite GL Voucher', the engine synthesizes a balanced double-entry journal entry—debiting Software Hardware Expense and Prepaid Tax while crediting Accounts Payable—complete with a cryptographic SHA-256 SOX audit hash and Fedwire wire ID.\""
        },
        {
            "phase": "Phase 6: The 2-Column Forensic Bento Registry",
            "action": "Click '6 Scenario Payloads' in navbar. Show 2-column bento grid. Click '{ } Raw JSON' on Card 1.",
            "talk": "\"In our 6 Scenario Payloads tab, we built a 2-column forensic bento grid. Each card features a 4-metric financial strip and a 6-node micro-pipeline status strip. Clicking '{ } Raw JSON' expands the exact syntax-highlighted OCR payload evaluated by our engine.\""
        },
        {
            "phase": "Phase 7: The Zero-Overlay Self-Driving Guided Tour",
            "action": "Click '▶ Interactive Tour' in header. Let it run for 15 seconds. Point out zero blur/dark overlay.",
            "talk": "\"Finally, for executive reviewers, I built a zero-overlay Guided Product Tour. Notice how the page remains 100% crisp and unblurred: our virtual AI Guide glides across the viewport, the Tier 2 navbar pulses to indicate page shifts, and live actions execute automatically.\""
        }
    ]

    for p in phases:
        story.append(Paragraph(p['phase'], styles['h2']))
        story.append(Paragraph(f"<b>Live Screen Action:</b> {p['action']}", styles['bullet']))
        story.append(create_callout(p['talk'], styles, bg_color="#F8FAFC", border_color="#10B981"))
        story.append(Spacer(1, 5))

    # Section 3: Steering the Conversation
    story.append(Spacer(1, 8))
    story.append(Paragraph("3. Interactive Prompts to Involve the Interviewer", styles['h1']))
    prompts = [
        "<i>\"Would you like me to inject a custom edge case using our Interviewer Chaos Builder, such as a 25% price drift or a missing PO?\"</i>",
        "<i>\"Would you like to see how the engine handles a fuzzy duplicate suffix like INV-2026-8821-R submitted 3 days after payment?\"</i>",
        "<i>\"Shall we dive into the Python source code for Node 5 (Dual-Gate Tolerance) or inspect the SQLite schema?\"</i>"
    ]
    for pr in prompts:
        story.append(Paragraph(f"• {pr}", styles['bullet']))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated: {output_path}")


# ── MAIN EXECUTION ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    base_dir = r"C:\Users\surya\OneDrive\Documents\Projects\Zamp Case"
    pdf1 = os.path.join(base_dir, "Zamp_AP_Video_Recording_Demo_Script.pdf")
    pdf2 = os.path.join(base_dir, "Zamp_AP_Executive_Interview_Playbook.pdf")
    pdf3 = os.path.join(base_dir, "Zamp_AP_Live_Product_Walkthrough_Guide.pdf")

    print("Generating 3 Dedicated Presentation PDFs...")
    build_video_script_pdf(pdf1)
    build_interview_playbook_pdf(pdf2)
    build_live_walkthrough_pdf(pdf3)
    print("All 3 PDFs generated successfully!")
