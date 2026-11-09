"""
utils/config.py
---------------
Loads environment variables and system_config from the database.
Single source of truth for all runtime configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")


DEMO_MODE      = is_demo_mode()
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GEMINI_MODEL   = get_env("GEMINI_MODEL", "gemini-3.8-flash")
DATABASE_PATH  = get_env("DATABASE_PATH", "./invoice_processing.db")
UPLOAD_DIR     = get_env("UPLOAD_DIR", "./uploads")


def load_system_config(conn) -> dict:
    """
    Reads all rows from system_config and returns a plain dict.
    Call this at the start of each pipeline run so config changes
    take effect immediately without a restart.
    """
    rows = conn.execute("SELECT config_key, config_value FROM system_config").fetchall()
    cfg = {k: v for k, v in rows}
    return {
        "price_tolerance_pct":       float(cfg.get("price_tolerance_pct", "2.00")),
        "min_extraction_confidence": float(cfg.get("min_extraction_confidence", "0.80")),
        "valid_gst_rates":           [float(r) for r in cfg.get("valid_gst_rates", "0,5,12,18,28").split(",")],
        "max_retry_attempts":        int(cfg.get("max_retry_attempts", "3")),
        "retry_delay_seconds":       int(cfg.get("retry_delay_seconds", "5")),
        "currency":                  cfg.get("currency", "INR"),
    }
