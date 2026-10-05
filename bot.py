"""
Telegram notification module for the Wyckoff Screening System.
Uses Telegram ParseMode.HTML for rock-solid formatting immunity.
Features dual-dispatch engine (python-telegram-bot with requests HTTP API failover).
"""

import sys
import html
import asyncio
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from telegram import Bot
    from telegram.constants import ParseMode
    TELEGRAM_LIB_AVAILABLE = True
except ImportError:
    Bot = None
    ParseMode = None
    TELEGRAM_LIB_AVAILABLE = False

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

HEADER = "<b>🚨 SYSTEM ONLINE: WYCKOFF CYCLE MATRIX 🚨</b>\n\n"
FOOTER = (
    "\n<b>─────────────────────────</b>\n"
    "<b>📖 HOW TO TRADE THESE SETUPS:</b>\n"
    "• <b>Action:</b> Current market price coiled inside the 60-day consolidation.\n"
    "• <b>MUST BREAK:</b> Price resistance & minimum volume needed to confirm breakout. <i>(Trigger: Buy only when price crosses this level on volume surge).</i>\n"
    "• <b>RIP-CORD:</b> Volatility stop-loss (2.5x ATR). <i>(Failsafe: Exit immediately if price drops below this level).</i>"
)
MAX_MESSAGE_LENGTH = 4000


def format_scan_results(results: list[str]) -> list[str]:
    """
    Formats scanner results into HTML messages, chunking them to
    strictly adhere to Telegram's 4096 character payload limit.
    Includes an easy-to-understand trader cheat sheet.
    """
    if not results:
        return [f"{HEADER}<i>No setups found today.</i>"]

    formatted_entries = []
    for entry in results:
        # html.escape ensures characters like '<', '>', '&' never break HTML tags
        safe_entry = html.escape(entry)
        if safe_entry.startswith("[") and "]" in safe_entry:
            ticker_end = safe_entry.find("]")
            ticker = safe_entry[1:ticker_end]
            body = safe_entry[ticker_end + 1:]
            formatted_entries.append(f"🎯 <b>[{ticker}]</b>{body}")
        else:
            formatted_entries.append(f"• {safe_entry}")

    chunks = []
    current_chunk = HEADER

    for entry in formatted_entries:
        entry_block = f"{entry}\n\n"
        if len(current_chunk) + len(entry_block) > MAX_MESSAGE_LENGTH:
            chunks.append(current_chunk.strip())
            current_chunk = entry_block
        else:
            current_chunk += entry_block

    # Append explanatory cheat sheet to the final chunk
    if len(current_chunk) + len(FOOTER) <= MAX_MESSAGE_LENGTH:
        current_chunk += FOOTER
        chunks.append(current_chunk.strip())
    else:
        chunks.append(current_chunk.strip())
        chunks.append(FOOTER.strip())

    return chunks


def _send_via_requests(token: str, chat_id: str, message: str) -> None:
    """Fallback / direct HTTP dispatch via Telegram Bot REST API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _send_single_message(token: str, chat_id: str, message: str) -> None:
    """
    Sends a single message using python-telegram-bot when available,
    falling back to standard HTTPS requests.
    Protected by tenacity retry against temporary network drops.
    """
    if TELEGRAM_LIB_AVAILABLE and Bot is not None and ParseMode is not None:
        try:
            async def _async_send():
                bot = Bot(token=token)
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

            asyncio.run(_async_send())
            return
        except Exception as primary_err:
            logger.warning("python-telegram-bot send failed (%s). Attempting requests fallback...", primary_err)

    # Direct REST API fallback
    _send_via_requests(token, chat_id, message)


def send_scan_results(results: list[str]) -> bool:
    """
    Sends formatted scan results to the configured Telegram chat.
    Returns True if successfully sent, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not configured. Skipping Telegram dispatch.")
        return False

    messages = format_scan_results(results)
    print(f"📡 Dispatching {len(messages)} message chunk(s) to Telegram...")

    for i, msg in enumerate(messages, 1):
        try:
            _send_single_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
            print(f"✅ Chunk {i}/{len(messages)} delivered successfully.")
        except Exception as err:
            err_str = str(err).lower()
            if "chat not found" in err_str:
                print("⚠️ TELEGRAM ACTIVATION REQUIRED: Please open @Enegma_machine_bot in Telegram and tap START to authorize messages.", file=sys.stderr)
            else:
                print(f"❌ Failed to deliver message chunk {i}: {err}", file=sys.stderr)
            raise err

    return True
