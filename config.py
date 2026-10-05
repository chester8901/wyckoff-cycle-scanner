"""
Configuration module for the Wyckoff Screening System.
Safely loads and validates environment variables.
"""

import os
import sys
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def validate_config() -> bool:
    """
    Validates required environment variables.
    Returns True if valid, or logs clear instructions and returns False.
    """
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        print(f"❌ CONFIG ERROR: Missing required environment variable(s): {', '.join(missing)}", file=sys.stderr)
        print("💡 Please configure them in your GitHub Secrets or local .env file.", file=sys.stderr)
        return False

    return True
