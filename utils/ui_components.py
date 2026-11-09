"""
utils/ui_components.py
-----------------------
Pixel-perfect design system matching the custom fintech UI mockup:
  - Dark Navy Sidebar (#0b0f19 / #0f172a) with gradient brand logo & avatar footer
  - Top header with search bar (⌘ + K), notification bell, and time selector
  - 4 KPI cards (Auto-Approval Rate, Avg Processing Time, Duplicate Spend Prevented, Exceptions)
  - Processing Trend Line Chart & Recent Activity Feed
  - Bottom-Right Analytics Dashboard (Approval Rate Trend bar chart & Top Exceptions donut chart)
  - Middle-Left Upload Success Card with 5-stage horizontal stepper and cloud illustration
  - Bottom-Left Live Processing Pipeline widget (Live indicator, horizontal stepper, dark terminal log, circular confidence gauge)
  - Top-Right 3-Way Match Successful Document Comparison Table
  - Middle-Right Exception Resolution Card with Quick-Reason pill chips and Approve/Reject buttons
  - PDF Canvas Viewer with dark toolbar, PAID stamp, and variance callouts
"""

from __future__ import annotations
import os
import re
import base64
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

try:
    from utils.config import DEMO_MODE
except Exception:
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")


# ── Formatting Helpers ─────────────────────────────────────────────────────────

def format_inr(amount) -> str:
    """Format a number in Indian numbering style (₹X,XX,XXX.XX)."""
    if amount is None:
        return "—"
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "—"
    s = f"{abs(amount):.2f}"
    integer, decimal = s.split(".")
    n = len(integer)
    if n <= 3:
        result = integer
    else:
        result = integer[-3:]
        remaining = integer[:-3]
        while remaining:
            result = remaining[-2:] + "," + result
            remaining = remaining[:-2]
    res = "₹" + result
    if decimal != "00":
        res += "." + decimal
    if amount < 0:
        res = "-" + res
    return res


def format_date(date_str: str | None) -> str:
    if not date_str:
        return "—"
    try:
        from datetime import datetime
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str[:19], fmt)
                return dt.strftime("%d %b %Y")
            except ValueError:
                continue
        return date_str[:10]
    except Exception:
        return str(date_str)[:10]


def format_datetime(date_str: str | None) -> str:
    if not date_str:
        return "—"
    try:
        from datetime import datetime
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(date_str[:19], fmt)
                return dt.strftime("%d %b %Y · %I:%M %p")
            except ValueError:
                continue
        return date_str[:16]
    except Exception:
        return str(date_str)[:16]


def short_id(sub_id: str) -> str:
    if not sub_id:
        return ""
    return sub_id[:8] + "…" if len(sub_id) > 10 else sub_id


# ── Complete Pixel-Perfect CSS Stylesheet ──────────────────────────────────────

_FULL_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* Reset & Typography */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

/* Hide Streamlit Chrome Completely */
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* Main Container Padding */
.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1550px !important;
}

/* Dark Navy Sidebar (#0b0f19) */
[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
    border-right: 1px solid #1e293b !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.25rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span {
    color: #94a3b8 !important;
}

/* Sidebar navigation buttons */
.ia-nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 0.9rem;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 500;
    color: #94a3b8;
    text-decoration: none;
    cursor: pointer;
    margin-bottom: 0.25rem;
    transition: all 0.15s ease;
}
.ia-nav-item:hover {
    background: #1e293b;
    color: #ffffff;
}
.ia-nav-item.active {
    background: #4f46e5;
    color: #ffffff;
    font-weight: 600;
}
.ia-nav-badge {
    margin-left: auto;
    background: #ef4444;
    color: #ffffff;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.1rem 0.45rem;
    border-radius: 999px;
}

/* Sidebar Streamlit button overrides */
[data-testid="stSidebar"] .stButton > button {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 0.75rem !important;
    padding: 0.65rem 0.9rem !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 0.25rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1e293b !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Sidebar Upgrade Card */
.ia-upgrade-card {
    background: linear-gradient(135deg, #1e1b4b, #172554);
    border: 1px solid #312e81;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 2rem;
    margin-bottom: 1.5rem;
}
.ia-upgrade-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.25rem;
}
.ia-upgrade-desc {
    font-size: 0.75rem;
    color: #94a3b8;
    line-height: 1.4;
    margin-bottom: 0.75rem;
}
.ia-upgrade-btn {
    display: inline-block;
    background: #4f46e5;
    color: #ffffff;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    text-align: center;
    width: 100%;
}

/* Sidebar User Footer */
.ia-sidebar-user {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    border-top: 1px solid #1e293b;
    margin-top: auto;
}
.ia-avatar {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    background: #334155;
    color: #f8fafc;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
}

/* Top Header Bar */
.ia-top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 1rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
}
.ia-search-box {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.5rem 1rem;
    width: 380px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.ia-search-input {
    border: none;
    outline: none;
    background: transparent;
    font-size: 0.85rem;
    color: #0f172a;
    width: 100%;
}
.ia-search-shortcut {
    font-size: 0.7rem;
    background: #f1f5f9;
    color: #64748b;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
    font-family: monospace;
    white-space: nowrap;
}

/* KPI Cards Row (4 cards) */
.ia-kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    margin-bottom: 1.75rem;
}
.ia-kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    position: relative;
}
.ia-kpi-top {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
}
.ia-kpi-icon-circle {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
}
.icon-green  { background: #ecfdf5; color: #059669; }
.icon-blue   { background: #eff6ff; color: #2563eb; }
.icon-indigo { background: #eef2ff; color: #4f46e5; }
.icon-red    { background: #fef2f2; color: #dc2626; }
.ia-kpi-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748b;
}
.ia-kpi-val {
    font-size: 1.85rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.1;
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
}
.ia-kpi-trend {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
}
.trend-up   { background: #ecfdf5; color: #059669; }
.trend-down { background: #fef2f2; color: #dc2626; }

/* Content Card Container */
.ia-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 1.5rem;
}
.ia-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
}
.ia-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
}
.ia-card-sub {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 0.1rem;
}

/* Horizontal Stepper (Matching Mockup) */
.ia-stepper-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    padding: 1rem 2rem 2rem 2rem;
    margin: 1.5rem 0;
}
.ia-stepper-line {
    position: absolute;
    top: 2rem;
    left: 4.5rem;
    right: 4.5rem;
    height: 3px;
    background: #e2e8f0;
    z-index: 0;
}
.ia-step-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    position: relative;
    z-index: 1;
}
.ia-step-circle {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    background: #ffffff;
    border: 2px solid #cbd5e1;
    color: #64748b;
    transition: all 0.2s ease;
}
.node-done .ia-step-circle {
    background: #10b981;
    border-color: #10b981;
    color: #ffffff;
}
.node-running .ia-step-circle {
    background: #4f46e5;
    border-color: #4f46e5;
    color: #ffffff;
    box-shadow: 0 0 0 5px rgba(79, 70, 229, 0.2);
    animation: pulse-ring 1.5s infinite;
}
.ia-step-name {
    font-size: 0.8rem;
    font-weight: 600;
    color: #475569;
    text-align: center;
}
.node-running .ia-step-name {
    color: #4f46e5;
    font-weight: 700;
}
.ia-step-sub {
    font-size: 0.7rem;
    color: #94a3b8;
}

@keyframes pulse-ring {
    0%, 100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); }
    50%      { box-shadow: 0 0 0 8px rgba(79, 70, 229, 0); }
}

/* Live Dark Terminal Execution Log */
.ia-terminal {
    background: #0b0f19;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.25rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #e2e8f0;
    line-height: 1.8;
}
.ia-term-check {
    color: #10b981;
    font-weight: 700;
    margin-right: 0.5rem;
}
.ia-term-run {
    color: #6366f1;
    margin-right: 0.5rem;
    display: inline-block;
    animation: spin 1.5s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Circular SVG Confidence Gauge */
.ia-gauge-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}
.ia-gauge-svg {
    width: 110px;
    height: 110px;
}
.ia-gauge-bg {
    fill: none;
    stroke: #e2e8f0;
    stroke-width: 8;
}
.ia-gauge-progress {
    fill: none;
    stroke: #10b981;
    stroke-width: 8;
    stroke-linecap: round;
    stroke-dasharray: 283;
    stroke-dashoffset: 28;
    transform: rotate(-90deg);
    transform-origin: 50% 50%;
}
.ia-gauge-pct {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0f172a;
    margin-top: -68px;
    margin-bottom: 40px;
}
.ia-gauge-tag {
    font-size: 0.82rem;
    font-weight: 700;
    color: #059669;
}

/* 3-Way Match Successful Card */
.ia-match-success {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
}
.ia-match-head {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}
.ia-match-icon {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    background: #10b981;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 800;
    flex-shrink: 0;
}
.ia-match-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #065f46;
}
.ia-match-sub {
    font-size: 0.78rem;
    color: #047857;
}

/* Clean Comparison Table */
.ia-table-clean {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    margin: 1rem 0;
}
.ia-table-clean th {
    text-align: left;
    padding: 0.65rem 0.75rem;
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 600;
    border-bottom: 1px solid #e2e8f0;
}
.ia-table-clean td {
    padding: 0.75rem;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
}
.pill-ok {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.pill-variance {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.banner-no-var {
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* Exception Resolution Card (Price/Qty Deviation) */
.ia-exception-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 1rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.ia-exc-icon {
    color: #dc2626;
    font-size: 1.25rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
}
.ia-exc-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: #991b1b;
}
.ia-exc-desc {
    font-size: 0.8rem;
    color: #b91c1c;
    margin-top: 0.15rem;
}

/* Quick Reason Chips */
.ia-chip-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.75rem 0;
}
.ia-chip {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #334155;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.15s ease;
}
.ia-chip:hover {
    border-color: #4f46e5;
    color: #4f46e5;
    background: #eef2ff;
}

/* PDF Toolbar Header */
.ia-pdf-toolbar {
    background: #1e293b;
    color: #94a3b8;
    padding: 0.5rem 1rem;
    border-radius: 10px 10px 0 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.8rem;
    font-family: monospace;
}
.ia-pdf-canvas {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: none;
    border-radius: 0 0 10px 10px;
    padding: 0.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    position: relative;
}

/* PAID Stamp Overlay */
.paid-stamp {
    position: absolute;
    bottom: 2rem;
    right: 2.5rem;
    border: 4px solid #10b981;
    color: #10b981;
    font-size: 1.5rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    padding: 0.3rem 1.2rem;
    border-radius: 8px;
    transform: rotate(-12deg);
    opacity: 0.85;
    pointer-events: none;
}

/* Variance Bubble Callout */
.variance-callout {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.5rem;
}

/* Activity Feed List */
.ia-activity-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid #f1f5f9;
}
.ia-activity-icon {
    width: 1.8rem;
    height: 1.8rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    flex-shrink: 0;
}
.ia-act-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #0f172a;
}
.ia-act-time {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-top: 0.1rem;
}

/* Modern Tab List */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 1.5rem !important;
    border-bottom: 1px solid #e2e8f0 !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    padding: 0.5rem 0 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    border: none !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    color: #4f46e5 !important;
    border-bottom: 2px solid #4f46e5 !important;
}

/* Legacy Overrides for clean appearance */
.ia-topbar { display: none !important; }
.ia-role { padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.68rem; font-weight: 600; text-transform: uppercase; }
.role-vendor { background: #dbeafe; color: #1e40af; }
.role-finance { background: #d1fae5; color: #065f46; }
.role-procurement { background: #fef3c7; color: #92400e; }
.role-warehouse { background: #f1f5f9; color: #334155; }

.ia-check {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    margin-bottom: 0.5rem;
    background: #ffffff;
}
.ia-check-passed  { background: #f0fdf4; border-color: #bbf7d0; }
.ia-check-failed  { background: #fff1f2; border-color: #fecdd3; }
.ia-check-warning { background: #fffbeb; border-color: #fde68a; }
.ia-check-skipped { background: #f8fafc; border-color: #e2e8f0; }

.ia-timeline { padding-left: 0.25rem; }
.ia-tl-item { display: flex; gap: 1rem; padding-bottom: 1.25rem; position: relative; }
.ia-tl-item:not(:last-child)::before {
    content: ""; position: absolute; left: 0.55rem; top: 1.3rem;
    width: 2px; height: calc(100% - 0.5rem); background: #e2e8f0;
}
.ia-tl-dot {
    width: 1.1rem; height: 1.1rem; border-radius: 50%;
    margin-top: 0.15rem; z-index: 1; border: 2px solid #fff; flex-shrink: 0;
}
.tl-system { background: #a5b4fc; }
.tl-human  { background: #6ee7b7; }
.tl-vendor { background: #fcd34d; }

.ia-empty { text-align: center; padding: 3rem 1.5rem; color: #64748b; }
.ia-empty-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.ia-empty-title { font-size: 1rem; font-weight: 700; color: #0f172a; margin-bottom: 0.25rem; }
.ia-empty-msg { font-size: 0.82rem; color: #64748b; max-width: 400px; margin: 0 auto; line-height: 1.5; }

.ia-section {
    font-size: 0.95rem; font-weight: 700; color: #0f172a;
    margin: 1.5rem 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;
}
.ia-override-card {
    background: #fffbeb; border: 1px solid #fde68a;
    border-radius: 12px; padding: 1.25rem; margin-top: 1rem;
}
.ia-override-locked {
    background: #f8fafc; border: 1px dashed #cbd5e1;
    border-radius: 12px; padding: 1.25rem; margin-top: 1rem; text-align: center; color: #94a3b8;
}
</style>
"""


# ── Core Component Injections ──────────────────────────────────────────────────


def render_html(html_str: str):
    """
    Safely renders raw HTML via st.html or contiguous st.markdown,
    guaranteeing CommonMark never misinterprets blank lines or indentation as code blocks.
    """
    if not html_str:
        return
    cleaned = re.sub(r'<!--.*?-->', '', str(html_str), flags=re.DOTALL)
    clean_lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    contiguous = "\n".join(clean_lines)
    if hasattr(st, "html"):
        st.html(contiguous)
    else:
        render_html(contiguous)

def inject_css():
    """Injects the complete pixel-perfect stylesheet via st.html."""
    clean_css = "\n".join(line for line in _FULL_CSS.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(clean_css)
    else:
        render_html(clean_css)


def status_badge(status: str) -> str:
    s = (status or "").lower()
    if s == "approved":
        return '<span class="pill-ok">● Approved</span>'
    elif s == "review":
        return '<span class="ia-kpi-trend trend-down" style="background:#fef3c7;color:#92400e;">● In Review</span>'
    elif s == "rejected":
        return '<span class="pill-variance">● Rejected</span>'
    elif s == "duplicate":
        return '<span class="ia-kpi-trend" style="background:#ede9fe;color:#4c1d95;">● Duplicate</span>'
    else:
        return f'<span class="ia-kpi-trend" style="background:#e0e7ff;color:#3730a3;">● {s.title()}</span>'


def role_pill(role: str) -> str:
    r = (role or "").lower()
    if "vendor" in r:
        return '<span class="ia-role role-vendor">Vendor</span>'
    elif "finance" in r:
        return '<span class="ia-role role-finance">Finance / AP</span>'
    elif "procurement" in r:
        return '<span class="ia-role role-procurement">Procurement</span>'
    elif "warehouse" in r:
        return '<span class="ia-role role-warehouse">Warehouse</span>'
    return f'<span class="ia-role">{role}</span>'


# ── Sidebar Matching Mockup Exactly ───────────────────────────────────────────

def render_custom_sidebar(active_tab: str = "Dashboard", exception_count: int = 12, user: dict | None = None):
    """
    Renders the dark navy sidebar from the image:
    Logo, Navigation list with active pill and exception badge,
    bottom Upgrade to Pro card, and user profile footer.
    """
    user_name = user.get("name", "Surya Teja") if user else "Surya Teja"
    user_role = user.get("role", "finance_ap") if user else "finance_ap"
    role_label = "Finance Controller" if user_role == "finance_ap" else user_role.title()
    initials = "".join([part[0].upper() for part in user_name.split()[:2]]) or "ST"

    with st.sidebar:
        # Brand Logo Header
        render_html("""
        <div style="display:flex;align-items:center;gap:0.6rem;padding:0.5rem 0.25rem 1.75rem 0.25rem;">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <rect width="28" height="28" rx="8" fill="url(#grad1)"/>
                <path d="M7 8h14M7 13h10M7 18h14M7 23h8" stroke="white" stroke-width="2" stroke-linecap="round"/>
                <defs>
                    <linearGradient id="grad1" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#4f46e5"/>
                        <stop offset="1" stop-color="#818cf8"/>
                    </linearGradient>
                </defs>
            </svg>
            <span style="font-size:1.15rem;font-weight:800;color:#ffffff;letter-spacing:-0.02em;">InvoiceAI</span>
        </div>
        """)

        # Nav items
        navs = [
            ("Dashboard",  "📊", "finance_dashboard"),
            ("Invoices",   "📑", "all_invoices"),
            ("Exceptions", "⚠️", "exceptions"),
            ("Analytics",  "📈", "analytics"),
            ("Settings",   "⚙️", "settings"),
        ]

        for label, icon, key in navs:
            is_active = (active_tab.lower() == label.lower())
            badge_text = f" ({exception_count})" if label == "Exceptions" and exception_count > 0 else ""
            btn_label = f"{icon}  {label}{badge_text}"
            btn_type = "primary" if is_active else "secondary"

            if st.button(btn_label, key=f"side_btn_{key}", type=btn_type, use_container_width=True):
                st.session_state["finance_tab"] = label.lower()
                st.session_state["nav_page"] = "finance_dashboard"
                st.rerun()

        # Upgrade to Pro Card
        render_html("""
        <div class="ia-upgrade-card">
            <div class="ia-upgrade-title">Upgrade to Pro</div>
            <div class="ia-upgrade-desc">Get advanced insights & priority support.</div>
            <div class="ia-upgrade-btn">View Plans</div>
        </div>
        """)

        # User profile footer
        render_html(f"""
        <div class="ia-sidebar-user">
            <div class="ia-avatar">{initials}</div>
            <div style="flex:1;overflow:hidden;">
                <div style="font-size:0.82rem;font-weight:700;color:#ffffff;line-height:1.2;">{user_name}</div>
                <div style="font-size:0.7rem;color:#64748b;">{role_label} ▾</div>
            </div>
        </div>
        """)

        # Logout button
        if st.button("🚪 Sign Out", key="sidebar_logout_btn", use_container_width=True):
            from core.auth import clear_session
            clear_session()
            st.rerun()


# ── Top Header Matching Mockup ─────────────────────────────────────────────────

def render_top_header(title: str = "Welcome back, Surya Teja!",
                      subtitle: str = "Here's what's happening with your AP this week.",
                      user: dict | None = None):
    """Renders the search bar with (⌘ + K), notifications, and time selector."""
    user_name = user.get("name", "Surya Teja") if user else "Surya Teja"
    initials = "".join([part[0].upper() for part in user_name.split()[:2]]) or "ST"

    c_left, c_search, c_right = st.columns([1.8, 1.4, 0.8])

    with c_left:
        render_html(f"""
        <div>
            <h2 style="font-size:1.45rem;font-weight:800;color:#0f172a;margin:0 0 0.15rem 0;letter-spacing:-0.02em;">
                {title}
            </h2>
            <div style="font-size:0.82rem;color:#64748b;">{subtitle}</div>
        </div>
        """)

    with c_search:
        render_html("""
        <div class="ia-search-box">
            <span style="color:#94a3b8;">🔍</span>
            <input class="ia-search-input" placeholder="Search invoices, PO numbers, vendor..." />
            <span class="ia-search-shortcut">⌘ + K</span>
        </div>
        """)

    with c_right:
        render_html(f"""
        <div style="display:flex;align-items:center;gap:0.75rem;justify-content:flex-end;padding-top:0.3rem;">
            <div style="background:#ffffff;border:1px solid #e2e8f0;padding:0.4rem 0.8rem;border-radius:8px;font-size:0.78rem;font-weight:600;color:#475569;">
                Last 30 days ▾
            </div>
            <div style="font-size:1.1rem;color:#64748b;cursor:pointer;">🔔</div>
            <div class="ia-avatar" style="width:1.9rem;height:1.9rem;font-size:0.72rem;">{initials}</div>
        </div>
        """)


# ── KPI Cards Matching Mockup (4 Cards) ────────────────────────────────────────

def render_mockup_kpis(auto_app_rate: float = 82.0, avg_time: str = "1.8h",
                       fraud_prevented: str = "₹2.4L", exceptions_count: int = 12):
    """Renders the 4 exact KPI cards from the mockup image."""
    render_html(f"""
    <div class="ia-kpi-row">
        <!-- Card 1 -->
        <div class="ia-kpi-card">
            <div class="ia-kpi-top">
                <div class="ia-kpi-icon-circle icon-green">✓</div>
                <div class="ia-kpi-title">Auto-Approval Rate</div>
            </div>
            <div class="ia-kpi-val">
                {auto_app_rate:.0f}%
                <span class="ia-kpi-trend trend-up">↑ +4%</span>
            </div>
        </div>

        <!-- Card 2 -->
        <div class="ia-kpi-card">
            <div class="ia-kpi-top">
                <div class="ia-kpi-icon-circle icon-blue">⏱</div>
                <div class="ia-kpi-title">Avg. Processing Time</div>
            </div>
            <div class="ia-kpi-val">
                {avg_time}
                <span class="ia-kpi-trend trend-up" style="background:#ecfdf5;color:#059669;">↓ -35%</span>
            </div>
        </div>

        <!-- Card 3 -->
        <div class="ia-kpi-card">
            <div class="ia-kpi-top">
                <div class="ia-kpi-icon-circle icon-indigo">🛡️</div>
                <div class="ia-kpi-title">Duplicate Spend Prevented</div>
            </div>
            <div class="ia-kpi-val">
                {fraud_prevented}
            </div>
        </div>

        <!-- Card 4 -->
        <div class="ia-kpi-card">
            <div class="ia-kpi-top">
                <div class="ia-kpi-icon-circle icon-red">📄</div>
                <div class="ia-kpi-title">Exceptions</div>
            </div>
            <div class="ia-kpi-val">
                {exceptions_count}
                <span class="ia-kpi-trend trend-down">↑ +2</span>
            </div>
        </div>
    </div>
    """)


# ── Processing Trend Line Chart (Top-Left Mockup) ──────────────────────────────

def render_processing_trend_chart():
    """Renders the Processing Trend Plotly line chart matching the top-left mockup."""
    dates = ["Oct 30", "Nov 02", "Nov 05", "Nov 08", "Nov 10"]
    auto_approved = [48, 55, 62, 58, 82]
    reviewed = [22, 18, 15, 17, 12]

    fig = go.Figure()

    # Green line: Auto-Approved
    fig.add_trace(go.Scatter(
        x=dates, y=auto_approved,
        mode="lines+markers",
        name="Auto-Approved",
        line=dict(color="#10b981", width=3, shape="spline"),
        marker=dict(size=6, color="#10b981")
    ))

    # Orange line: Reviewed
    fig.add_trace(go.Scatter(
        x=dates, y=reviewed,
        mode="lines+markers",
        name="Reviewed",
        line=dict(color="#f59e0b", width=2.5, shape="spline"),
        marker=dict(size=5, color="#f59e0b")
    ))

    # Target 82% marker badge at Nov 10
    fig.add_annotation(
        x="Nov 10", y=82,
        text="82%",
        showarrow=False,
        font=dict(color="#ffffff", size=10, family="Plus Jakarta Sans"),
        bgcolor="#10b981",
        bordercolor="#10b981",
        borderwidth=1,
        borderpad=4,
        yshift=15
    )

    fig.update_layout(
        title="",
        margin=dict(t=15, b=20, l=35, r=20),
        height=240,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, family="Plus Jakarta Sans", color="#64748b")
        ),
        xaxis=dict(
            showgrid=False,
            color="#94a3b8",
            tickfont=dict(family="Plus Jakarta Sans", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            color="#94a3b8",
            ticksuffix="%",
            range=[0, 105],
            tickfont=dict(family="Plus Jakarta Sans", size=11)
        )
    )

    render_html('<div class="ia-card"><div class="ia-card-title" style="margin-bottom:0.5rem;">Processing Trend</div>')
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    render_html('</div>')


# ── Recent Activity Feed (Top-Left Mockup) ────────────────────────────────────

def render_recent_activity_card():
    """Renders the Recent Activity feed card from the top-left mockup."""
    activities = [
        {"icon": "✓", "cls": "icon-green", "title": "Invoice INV-10423 approved", "time": "2m ago"},
        {"icon": "⚠️", "cls": "icon-blue",   "title": "Invoice INV-10422 sent for review", "time": "5m ago"},
        {"icon": "↑", "cls": "icon-blue",   "title": "Invoice INV-10421 uploaded", "time": "8m ago"},
        {"icon": "✓", "cls": "icon-green", "title": "Invoice INV-10420 approved", "time": "12m ago"},
    ]

    items_html = ""
    for a in activities:
        items_html += f"""
        <div class="ia-activity-item">
            <div class="ia-activity-icon {a['cls']}">{a['icon']}</div>
            <div style="flex:1;">
                <div class="ia-act-title">{a['title']}</div>
                <div class="ia-act-time">{a['time']}</div>
            </div>
        </div>
        """

    render_html(f"""
    <div class="ia-card">
        <div class="ia-card-header">
            <div class="ia-card-title">Recent Activity</div>
            <span style="font-size:0.75rem;font-weight:600;color:#4f46e5;cursor:pointer;">View all →</span>
        </div>
        <div>
            {items_html}
        </div>
    </div>
    """)


# ── Analytics Charts (Bottom-Right Mockup) ─────────────────────────────────────

def render_analytics_dashboard():
    """Renders the bottom-right Analytics Dashboard view."""
    render_top_header(
        title="Analytics Dashboard",
        subtitle="Track performance, reduce exceptions, and optimize your AP workflow."
    )
    render_mockup_kpis(auto_app_rate=82.0, avg_time="1.8h", fraud_prevented="₹2.4L", exceptions_count=12)

    c_bar, c_donut = st.columns([1.5, 1], gap="medium")

    with c_bar:
        render_html('<div class="ia-card"><div class="ia-card-title" style="margin-bottom:0.5rem;">Approval Rate Trend</div>')
        days = [f"Oct {i}" for i in range(25, 32)] + [f"Nov {i:02d}" for i in range(1, 11)]
        rates = [65, 68, 70, 72, 75, 78, 80, 76, 79, 81, 80, 82, 85, 83, 84, 82, 82]

        fig_bar = px.bar(
            x=days, y=rates,
            color_discrete_sequence=["#818cf8"]
        )
        # 82% target horizontal line
        fig_bar.add_shape(
            type="line", x0=0, x1=len(days)-1, y0=82, y1=82,
            line=dict(color="#4f46e5", width=2, dash="dash")
        )
        fig_bar.add_annotation(
            x=len(days)-1, y=82, text="82%", showarrow=False,
            font=dict(color="#ffffff", size=10), bgcolor="#4f46e5", borderpad=3, yshift=12
        )
        fig_bar.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="", yaxis_title="",
            yaxis=dict(range=[0, 100], showgrid=True, gridcolor="#f1f5f9"),
            font=dict(family="Plus Jakarta Sans", size=10)
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        render_html('</div>')

    with c_donut:
        render_html('<div class="ia-card"><div class="ia-card-title" style="margin-bottom:0.5rem;">Top Exception Reasons</div>')
        reasons = ["Price Variance", "Quantity Mismatch", "Duplicate Invoice"]
        pcts = [42, 33, 25]
        colors = ["#f59e0b", "#3b82f6", "#8b5cf6"]

        fig_pie = go.Figure(data=[go.Pie(
            labels=reasons,
            values=pcts,
            hole=0.68,
            marker=dict(colors=colors),
            textinfo="none"
        )])
        fig_pie.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="v",
                yanchor="middle", y=0.5,
                xanchor="left", x=1.05,
                font=dict(family="Plus Jakarta Sans", size=11, color="#475569")
            )
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        render_html('</div>')


# ── Upload Success Card (Middle-Left Mockup) ──────────────────────────────────

def render_upload_success_card(step: int = 3):
    """
    Renders the exact middle-left card from the mockup:
    Soft blue cloud illustration + "Invoice Uploaded Successfully!" + 5-stage horizontal stepper.
    """
    s1 = "node-done" if step > 1 else ("node-running" if step == 1 else "")
    s2 = "node-done" if step > 2 else ("node-running" if step == 2 else "")
    s3 = "node-done" if step > 3 else ("node-running" if step == 3 else "")
    s4 = "node-done" if step > 4 else ("node-running" if step == 4 else "")
    s5 = "node-done" if step > 5 else ("node-running" if step == 5 else "")

    render_html(f"""
    <div class="ia-card" style="text-align:center;padding:2rem;">
        <!-- Cloud illustration -->
        <div style="display:inline-block;background:#eff6ff;padding:1.25rem;border-radius:50%;margin-bottom:0.75rem;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <path d="M19 18a4 4 0 00-3.75-3.98A6 6 0 004 15a4 4 0 002 7h13a4 4 0 000-4z" fill="#dbeafe"/>
                <path d="M12 11v6m-3-3l3-3 3 3" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>

        <div style="font-size:1.35rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em;">
            Invoice Uploaded Successfully!
        </div>
        <div style="font-size:0.85rem;color:#64748b;margin-top:0.25rem;">
            We are now processing your invoice using AI...
        </div>

        <!-- 5-Stage Stepper -->
        <div class="ia-stepper-wrap" style="max-width:700px;margin:2rem auto 1.5rem auto;">
            <div class="ia-stepper-line"></div>

            <div class="ia-step-node {s1}">
                <div class="ia-step-circle">{'✓' if step > 1 else '1'}</div>
                <div class="ia-step-name">Parsing<br>PDF</div>
            </div>

            <div class="ia-step-node {s2}">
                <div class="ia-step-circle">{'✓' if step > 2 else '2'}</div>
                <div class="ia-step-name">Extracting<br>Data</div>
            </div>

            <div class="ia-step-node {s3}">
                <div class="ia-step-circle">{'✓' if step > 3 else '3'}</div>
                <div class="ia-step-name">Running<br>Validations</div>
            </div>

            <div class="ia-step-node {s4}">
                <div class="ia-step-circle">{'✓' if step > 4 else '4'}</div>
                <div class="ia-step-name">3-Way<br>Matching</div>
            </div>

            <div class="ia-step-node {s5}">
                <div class="ia-step-circle">{'✓' if step > 5 else '5'}</div>
                <div class="ia-step-name">Finalizing</div>
            </div>
        </div>

        <div style="display:inline-flex;align-items:center;gap:0.4rem;font-size:0.8rem;color:#6366f1;font-weight:600;background:#eef2ff;padding:0.4rem 0.9rem;border-radius:999px;">
            <span>⚡</span>
            <span>This usually takes less than 30 seconds</span>
        </div>
    </div>
    """)


# ── Live Processing Pipeline (Bottom-Left Mockup) ─────────────────────────────

def render_processing_pipeline_widget(step: int = 3, elapsed: str = "00:00:18",
                                      confidence: float = 98.7,
                                      lines_count: int = 24,
                                      po_matched: str = "PO-45021",
                                      grn_matched: str = "GRN-78112"):
    """
    Renders the exact bottom-left widget from the image:
    Horizontal Stepper + Live terminal log card + Circular Confidence Gauge.
    """
    c_step1 = "node-done" if step > 1 else ("node-running" if step == 1 else "")
    c_step2 = "node-done" if step > 2 else ("node-running" if step == 2 else "")
    c_step3 = "node-done" if step > 3 else ("node-running" if step == 3 else "")
    c_step4 = "node-done" if step > 4 else ("node-running" if step == 4 else "")
    c_step5 = "node-done" if step > 5 else ("node-running" if step == 5 else "")

    render_html(f"""
    <div class="ia-card">
        <!-- Header -->
        <div class="ia-card-header">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <span style="color:#2563eb;font-size:1.1rem;">📈</span>
                <span class="ia-card-title">Processing Pipeline</span>
            </div>
            <span class="pill-ok" style="background:#ecfdf5;color:#059669;">● Live · {elapsed}</span>
        </div>

        <!-- Stepper -->
        <div class="ia-stepper-wrap">
            <div class="ia-stepper-line"></div>

            <div class="ia-step-node {c_step1}">
                <div class="ia-step-circle">{'✓' if step > 1 else '1'}</div>
                <div class="ia-step-name">Invoice Uploaded</div>
                <div class="ia-step-sub">✓ 10:24 AM</div>
            </div>

            <div class="ia-step-node {c_step2}">
                <div class="ia-step-circle">{'✓' if step > 2 else '2'}</div>
                <div class="ia-step-name">Data Extracted</div>
                <div class="ia-step-sub">✓ 10:24 AM</div>
            </div>

            <div class="ia-step-node {c_step3}">
                <div class="ia-step-circle">{'✓' if step > 3 else '⚙️'}</div>
                <div class="ia-step-name">Validations</div>
                <div class="ia-step-sub">{'Running...' if step == 3 else 'Pending'}</div>
            </div>

            <div class="ia-step-node {c_step4}">
                <div class="ia-step-circle">{'✓' if step > 4 else '4'}</div>
                <div class="ia-step-name">3-Way Match</div>
                <div class="ia-step-sub">Pending</div>
            </div>

            <div class="ia-step-node {c_step5}">
                <div class="ia-step-circle">{'✓' if step > 5 else '5'}</div>
                <div class="ia-step-name">Final Decision</div>
                <div class="ia-step-sub">Pending</div>
            </div>
        </div>

        <!-- Bottom Split: Terminal Log & Gauge -->
        <div style="display:grid;grid-template-columns:2.5fr 1fr;gap:1.25rem;margin-top:1rem;">
            <!-- Terminal -->
            <div class="ia-terminal">
                <div><span class="ia-term-check">✓</span>Extracted {lines_count} line items with {confidence:.1f}% confidence</div>
                <div><span class="ia-term-check">✓</span>PO match found: {po_matched}</div>
                <div><span class="ia-term-check">✓</span>GRN match found: {grn_matched}</div>
                <div><span class="ia-term-run">◌</span>Running business rules...</div>
            </div>

            <!-- Radial Gauge -->
            <div class="ia-gauge-card">
                <div style="font-size:0.75rem;font-weight:700;color:#64748b;margin-bottom:0.5rem;">Confidence Score</div>
                <svg class="ia-gauge-svg" viewBox="0 0 100 100">
                    <circle class="ia-gauge-bg" cx="50" cy="50" r="45"></circle>
                    <circle class="ia-gauge-progress" cx="50" cy="50" r="45"></circle>
                </svg>
                <div class="ia-gauge-pct">{confidence:.1f}%</div>
                <div class="ia-gauge-tag">High Confidence</div>
            </div>
        </div>
    </div>
    """)


# ── 3-Way Match Successful Card (Top-Right Mockup) ─────────────────────────────

def render_3way_match_successful(po_num: str = "PO #45021", po_val: float = 62000.0,
                                 grn_num: str = "GRN #78112", grn_val: float = 62000.0,
                                 inv_val: float = 62000.0):
    """Renders the exact 3-Way Match Successful card from the top-right mockup."""
    render_html(f"""
    <div class="ia-match-success">
        <div class="ia-match-head">
            <div class="ia-match-icon">✓</div>
            <div>
                <div class="ia-match-title">3-Way Match Successful</div>
                <div class="ia-match-sub">All documents are consistent</div>
            </div>
        </div>

        <table class="ia-table-clean">
            <thead>
                <tr>
                    <th>Document</th>
                    <th>Value</th>
                    <th style="text-align:right;">Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>{po_num}</strong><br><span style="font-size:0.72rem;color:#64748b;">(Procurement)</span></td>
                    <td><strong>{format_inr(po_val)}</strong></td>
                    <td style="text-align:right;"><span class="pill-ok">✓ OK</span></td>
                </tr>
                <tr>
                    <td><strong>{grn_num}</strong><br><span style="font-size:0.72rem;color:#64748b;">(Warehouse)</span></td>
                    <td><strong>{format_inr(grn_val)}</strong></td>
                    <td style="text-align:right;"><span class="pill-ok">✓ OK</span></td>
                </tr>
                <tr>
                    <td><strong>Invoice</strong><br><span style="font-size:0.72rem;color:#64748b;">(Vendor)</span></td>
                    <td><strong>{format_inr(inv_val)}</strong></td>
                    <td style="text-align:right;"><span class="pill-ok">✓ OK</span></td>
                </tr>
            </tbody>
        </table>

        <div class="banner-no-var">
            <span>✓</span>
            <span>No Variance Detected</span>
        </div>
    </div>
    """)


# ── Exception Resolution Card (Middle-Right Mockup) ────────────────────────────

def render_exception_card(title: str = "Price Deviation Detected",
                          desc: str = "Invoice unit price is 20% higher than PO",
                          chips: list[str] | None = None):
    """Renders the Price/Quantity Deviation card from the middle-right mockup."""
    if chips is None:
        chips = [
            "Price above tolerance",
            "Duplicate Invoice",
            "Missing GRN",
            "Supplementary GRN",
            "Other"
        ]

    chips_html = "".join(f'<span class="ia-chip">{c}</span>' for c in chips)

    render_html(f"""
    <div class="ia-card">
        <div class="ia-exception-banner">
            <div class="ia-exc-icon">⚠️</div>
            <div>
                <div class="ia-exc-title">{title}</div>
                <div class="ia-exc-desc">{desc}</div>
            </div>
        </div>

        <div style="display:flex;gap:1.5rem;font-size:0.85rem;font-weight:600;margin-bottom:0.75rem;border-bottom:1px solid #e2e8f0;padding-bottom:0.5rem;">
            <span style="color:#4f46e5;border-bottom:2px solid #4f46e5;padding-bottom:0.5rem;">Details</span>
            <span style="color:#64748b;">Quick Reasons</span>
        </div>

        <div style="font-size:0.78rem;font-weight:700;color:#64748b;text-transform:uppercase;">Quick Reasons:</div>
        <div class="ia-chip-wrap">
            {chips_html}
        </div>
    </div>
    """)


# ── PDF Canvas Viewer ─────────────────────────────────────────────────────────

def render_pdf_canvas_viewer(pdf_path: str | None, current_page: int = 1, total_pages: int = 1,
                             is_paid: bool = False, variance_label: str | None = None):
    """Renders the PDF canvas preview with dark toolbar matching the mockup."""
    render_html(f"""
    <div class="ia-pdf-toolbar">
        <div>◀ &nbsp; {current_page} / {total_pages} &nbsp; ▶</div>
        <div>— &nbsp; 100% &nbsp; + &nbsp; 🔍 &nbsp; ⤢</div>
        <div>🖨️ &nbsp; ⬇️ &nbsp; ⋮</div>
    </div>
    """)

    paid_badge = '<div class="paid-stamp">PAID</div>' if is_paid else ""
    var_badge = f'<div class="variance-callout">▲ {variance_label}</div>' if variance_label else ""

    if not pdf_path or not Path(pdf_path).exists():
        render_html(f'<div class="ia-pdf-canvas" style="padding:4rem 1rem;text-align:center;color:#94a3b8;">No PDF Available {paid_badge} {var_badge}</div>')
        return

    rendered = False
    try:
        import pypdfium2 as pdfium
        pdf_doc = pdfium.PdfDocument(pdf_path)
        page = pdf_doc[0]
        bitmap = page.render(scale=1.8)
        pil_img = bitmap.to_pil()
        render_html(f'<div class="ia-pdf-canvas">')
        st.image(pil_img, use_container_width=True)
        if paid_badge or var_badge:
            render_html(f'{paid_badge}{var_badge}')
        render_html('</div>')
        rendered = True
    except Exception:
        pass

    if not rendered:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        b64 = base64.b64encode(pdf_bytes).decode()
        render_html(f"""
        <div class="ia-pdf-canvas">
            <iframe src="data:application/pdf;base64,{b64}" width="100%" height="520px" style="border:none;"></iframe>
            {paid_badge}
            {var_badge}
        </div>
        """)


# ── Full Set of Legacy & Helper Components ────────────────────────────────────

def render_topbar(user: dict | None = None):
    """Legacy topbar helper kept for compatibility."""
    pass


def maybe_render_demo_banner():
    if DEMO_MODE:
        render_html("""
        <div style="background:#eef2ff;border:1px solid #c7d2fe;padding:0.4rem 1rem;border-radius:8px;font-size:0.75rem;color:#4338ca;margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;">
            <span>⚡ <strong>Demo Mode Active:</strong> Deterministic evaluation rules engaged.</span>
            <span>Gemini 3.8 Flash + Rule Engine</span>
        </div>
        """)


def render_login_page():
    """Renders the sleek sign-in page."""
    inject_css()
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        render_html("""
        <div class="ia-card" style="margin-top:4rem;padding:2.5rem 2rem;">
            <div style="text-align:center;margin-bottom:2rem;">
                <svg width="40" height="40" viewBox="0 0 28 28" fill="none">
                    <rect width="28" height="28" rx="8" fill="url(#login_grad)"/>
                    <path d="M7 8h14M7 13h10M7 18h14M7 23h8" stroke="white" stroke-width="2" stroke-linecap="round"/>
                    <defs>
                        <linearGradient id="login_grad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#4f46e5"/>
                            <stop offset="1" stop-color="#818cf8"/>
                        </linearGradient>
                    </defs>
                </svg>
                <div style="font-size:1.4rem;font-weight:800;color:#0f172a;margin-top:0.75rem;">Welcome to InvoiceAI</div>
                <div style="font-size:0.82rem;color:#64748b;">Autonomous AP Processing & 3-Way Matching</div>
            </div>
        """)

        with st.form("login_form"):
            email = st.text_input("Work Email", value="ap@company.com")
            password = st.text_input("Password", type="password", value="Demo@1234")
            submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

        if submitted:
            from core.auth import authenticate, set_session_user
            user = authenticate(email.strip(), password)
            if user:
                set_session_user(user)
                st.rerun()
            else:
                st.error("Invalid credentials. Try ap@company.com / Demo@1234")

        render_html("""
        <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid #f1f5f9;font-size:0.75rem;color:#64748b;line-height:1.6;">
            <strong>Demo Quick-Logins (Password: Demo@1234):</strong><br>
            • Finance / AP: <code>ap@company.com</code><br>
            • Vendor (BuildWell): <code>vendor@buildwell.com</code><br>
            • Procurement: <code>procurement@company.com</code><br>
            • Warehouse: <code>warehouse@company.com</code>
        </div>
        </div>
        """)


def render_kpi_grid(kpis: list[dict]):
    """Renders the standard KPI grid."""
    items = ""
    for k in kpis:
        accent = k.get("accent", "blue")
        cls = "icon-green" if accent == "green" else ("icon-red" if accent in ("red", "amber") else "icon-blue")
        items += f"""
        <div class="ia-kpi-card">
            <div class="ia-kpi-top">
                <div class="ia-kpi-icon-circle {cls}">✓</div>
                <div class="ia-kpi-title">{k.get('label', '')}</div>
            </div>
            <div class="ia-kpi-val">{k.get('value', '0')}</div>
            <div style="font-size:0.72rem;color:#64748b;margin-top:0.3rem;">{k.get('sub', '')}</div>
        </div>
        """
    render_html(f'<div class="ia-kpi-row">{items}</div>')


def render_decision_banner(status: str, reason: str):
    s = (status or "").lower()
    if s == "approved":
        render_html(f"""
        <div class="banner-no-var" style="padding:1rem;margin-bottom:1rem;border-radius:10px;">
            <span style="font-size:1.2rem;">✓</span>
            <div>
                <strong>Approved</strong>
                <div style="font-size:0.78rem;font-weight:normal;">{reason}</div>
            </div>
        </div>""")
    elif s == "review":
        render_html(f"""
        <div class="ia-exception-banner">
            <span class="ia-exc-icon">⚠️</span>
            <div>
                <strong class="ia-exc-title">Requires Review</strong>
                <div class="ia-exc-desc">{reason}</div>
            </div>
        </div>""")
    elif s in ("rejected", "duplicate"):
        render_html(f"""
        <div class="ia-exception-banner" style="background:#fef2f2;border-color:#fca5a5;">
            <span class="ia-exc-icon">🛑</span>
            <div>
                <strong class="ia-exc-title">Blocked ({s.title()})</strong>
                <div class="ia-exc-desc">{reason}</div>
            </div>
        </div>""")


def render_validation_checks(checks: list):
    """Renders the 6-way validation checklist."""
    for c in checks:
        st_cls = f"ia-check-{c.get('status', 'skipped')}"
        icon = "✓" if c.get("status") == "passed" else ("✗" if c.get("status") == "failed" else "⚠️")
        color = "#059669" if c.get("status") == "passed" else ("#dc2626" if c.get("status") == "failed" else "#d97706")
        render_html(f"""
        <div class="ia-check {st_cls}">
            <div style="font-weight:700;color:{color};font-size:1rem;width:1.5rem;">{icon}</div>
            <div style="flex:1;">
                <div style="font-size:0.82rem;font-weight:700;color:#0f172a;">{c.get('check_type', '').replace('_', ' ').title()}</div>
                <div style="font-size:0.76rem;color:#475569;">{c.get('details', '')}</div>
            </div>
        </div>
        """)


def render_why_decision_panel(inv: dict, checks: list):
    """Renders the human-readable explanation panel with evidence."""
    render_html('<div class="ia-card" style="padding:1rem;margin-top:1rem;">')
    render_html(f'<div class="ia-card-title">🔍 Decision Explanation & Evidence</div>')
    render_html(f'<div style="font-size:0.82rem;color:#334155;margin-top:0.4rem;">{inv.get("decision_reason") or "No explanation generated."}</div>')
    render_html('</div>')


def render_audit_timeline(entries: list):
    """Renders the immutable audit trail."""
    render_html('<div class="ia-timeline">')
    for e in entries:
        dot_cls = "tl-system" if e.get("actor_type") == "system" else "tl-human"
        render_html(f"""
        <div class="ia-tl-item">
            <div class="ia-tl-dot {dot_cls}"></div>
            <div style="flex:1;">
                <div style="font-size:0.82rem;font-weight:700;color:#0f172a;">{e.get('action', '').title()}</div>
                <div style="font-size:0.75rem;color:#64748b;">{format_datetime(e.get('timestamp'))} · by {e.get('actor_type', '').title()}</div>
                <div style="font-size:0.78rem;color:#334155;margin-top:0.2rem;">{e.get('reason_or_comment', '')}</div>
            </div>
        </div>
        """)
    render_html('</div>')


def render_comparison_table(rows: list[dict], price_tolerance_pct: float = 2.0):
    """Renders the 3-Way comparison table."""
    tbody = ""
    for r in rows:
        tbody += f"""
        <tr>
            <td>Line {r.get('line')}</td>
            <td>{r.get('description')}</td>
            <td>{r.get('po_qty', '—')}</td>
            <td>{format_inr(r.get('po_price'))}</td>
            <td>{r.get('grn_accepted', '—')}</td>
            <td><strong>{r.get('inv_qty')}</strong></td>
            <td><strong>{format_inr(r.get('inv_price'))}</strong></td>
            <td><span class="pill-ok">✓ OK</span></td>
        </tr>
        """
    render_html(f"""
    <table class="ia-table-clean">
        <thead>
            <tr>
                <th>#</th><th>Description</th><th>PO Qty</th><th>PO Price</th>
                <th>GRN Acc</th><th>Inv Qty</th><th>Inv Price</th><th>Status</th>
            </tr>
        </thead>
        <tbody>{tbody}</tbody>
    </table>
    """)


def render_pdf_viewer(pdf_path: str | None):
    """Wrapper calling render_pdf_canvas_viewer."""
    render_pdf_canvas_viewer(pdf_path)


def _step_html(num: int, title: str, state: str, message: str, elapsed_ms: float | None = None) -> str:
    return ""


def build_pipeline_html(step_states: dict, start_times: dict,
                        confidence_score: float | None = None,
                        lines_extracted: int | None = None,
                        overall_status: str | None = None) -> str:
    return ""


def empty_state(icon: str, title: str, message: str = ""):
    render_html(f"""
    <div class="ia-empty">
        <div class="ia-empty-icon">{icon}</div>
        <div class="ia-empty-title">{title}</div>
        <div class="ia-empty-msg">{message}</div>
    </div>
    """)


def section_header(text: str):
    render_html(f'<div class="ia-section">{text}</div>')


def role_banner(text: str, style: str = "read"):
    render_html(f"""
    <div style="background:#f1f5f9;border:1px solid #cbd5e1;padding:0.6rem 1rem;border-radius:8px;font-size:0.78rem;color:#475569;margin-bottom:1rem;">
        {text}
    </div>
    """)


def render_guided_tour():
    pass
