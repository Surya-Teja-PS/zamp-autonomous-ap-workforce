"""
core/matching.py
----------------
Phase 4: Relational PO Line-Item Matching
Match each invoice line item to a PO line item using Gemini description similarity.
Stores po_line_id on each invoice_line_item row where confidence >= 0.80.
"""

import json
import logging
import warnings

warnings.filterwarnings("ignore", message=".*google.generativeai.*", category=FutureWarning)

import google.generativeai as genai

from core.database import get_po_lines, execute, fetchall
from utils.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

import difflib

_MODEL = None
_MODEL_NAME = GEMINI_MODEL
if GEMINI_API_KEY and GEMINI_API_KEY.strip() and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        candidate_models = [GEMINI_MODEL, "gemini-3.8-flash", "gemini-1.5-flash", "gemini-pro"]
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m and m != "gemini-2.5-flash"]))
        for m in candidate_models:
            try:
                _MODEL = genai.GenerativeModel(m)
                _MODEL_NAME = m
                break
            except Exception:
                pass
    except Exception as e:
        logger.warning("Could not initialize Gemini model for matching: %s", e)

_MATCH_PROMPT = """You are matching invoice line items to purchase order (PO) line items
for an accounts payable system.

For each invoice line, identify which PO line it corresponds to based on the descriptions.
Return ONLY a valid JSON array — no prose.

Invoice lines:
{invoice_lines}

PO lines:
{po_lines}

Return:
[
  {{"invoice_line_number": 1, "po_line_id": 10, "confidence": 0.95, "reason": "Description matches"}},
  ...
]

If an invoice line cannot be matched to any PO line, set po_line_id to null and confidence to 0.0.
"""

_MATCH_THRESHOLD = 0.75


def run_line_matching(conn, invoice_id: int, po_id: int) -> list[dict]:
    """
    Match invoice line items to PO line items.
    Updates invoice_line_items.po_line_id where match confidence >= threshold.
    Returns list of match results with status.
    """
    invoice_lines = fetchall(conn,
        "SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY line_number",
        (invoice_id,))
    po_lines = get_po_lines(conn, po_id)

    if not invoice_lines or not po_lines:
        logger.warning("No lines to match: invoice_id=%d, po_id=%d", invoice_id, po_id)
        return []

    # Build readable representations for Gemini
    inv_text = "\n".join(
        f"  Line {r['line_number']}: {r['description']} (qty={r['quantity']})"
        for r in invoice_lines
    )
    po_text = "\n".join(
        f"  po_line_id={r['po_line_id']}: {r['description']} (unit={r['unit']}, ordered={r['quantity']})"
        for r in po_lines
    )

    prompt = _MATCH_PROMPT.format(invoice_lines=inv_text, po_lines=po_text)

    matches = []
    if _MODEL is not None:
        try:
            response = _MODEL.generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            matches = json.loads(raw.strip())
        except Exception as e:
            logger.warning("Gemini matching failed (%s); using fallback similarity", e)

    if not matches:
        # Fallback text similarity matching
        for inv in invoice_lines:
            best_po_id = None
            best_ratio = 0.0
            best_desc = ""
            inv_desc = (inv["description"] or "").lower()
            for po in po_lines:
                po_desc = (po["description"] or "").lower()
                ratio = difflib.SequenceMatcher(None, inv_desc, po_desc).ratio()
                # Check keyword overlap
                inv_words = set(inv_desc.split())
                po_words = set(po_desc.split())
                overlap = len(inv_words & po_words) / max(len(inv_words), 1)
                effective_score = max(ratio, overlap)

                if effective_score > best_ratio:
                    best_ratio = effective_score
                    best_po_id = po["po_line_id"]
                    best_desc = po["description"]

            matches.append({
                "invoice_line_number": inv["line_number"],
                "po_line_id": best_po_id if best_ratio >= 0.4 else None,
                "confidence": round(best_ratio, 2) if best_ratio >= 0.4 else 0.0,
                "reason": f"Similarity match ({best_ratio:.2f}) to '{best_desc}'" if best_ratio >= 0.4 else "No match found"
            })

    # Apply matches to DB
    results = []
    matched_po_line_ids = set()

    for m in matches:
        inv_line_num = m.get("invoice_line_number")
        po_line_id = m.get("po_line_id")
        confidence = m.get("confidence", 0.0)
        reason = m.get("reason", "")

        status = "unmatched"
        if po_line_id and confidence >= _MATCH_THRESHOLD:
            if po_line_id in matched_po_line_ids:
                # Prevent two invoice lines mapping to the same PO line
                status = "duplicate_match"
                po_line_id = None
            else:
                execute(conn,
                    "UPDATE invoice_line_items SET po_line_id = ? WHERE invoice_id = ? AND line_number = ?",
                    (po_line_id, invoice_id, inv_line_num))
                matched_po_line_ids.add(po_line_id)
                status = "matched"

        results.append({
            "invoice_line_number": inv_line_num,
            "po_line_id": po_line_id if status == "matched" else None,
            "confidence": confidence,
            "status": status,
            "reason": reason,
        })

    conn.commit()
    logger.info("Line matching done: invoice_id=%d, results=%s", invoice_id, results)
    return results
