"""
Telegram notification module for the Wyckoff Screening System.
Uses Telegram ParseMode.HTML for rock-solid formatting immunity.
Features dual-dispatch engine (python-telegram-bot with requests HTTP API failover).
Generates super easy-to-understand cards with custom calculated dollar and risk metrics.
"""

import sys
import re
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

HEADER = "<b>🚨 SYSTEM ONLINE: WYCKOFF CYCLE MATRIX 🚨</b>\n"
FOOTER = (
    "\n<b>─────────────────────────</b>\n"
    "<b>💡 2 SIMPLE RULES TO REMEMBER:</b>\n"
    "1️⃣ <b>Be Patient:</b> Do NOT buy today. Wait for the stock to cross the <b>Green Buy Trigger</b> on heavy volume.\n"
    "2️⃣ <b>Protect Your Money:</b> If you enter a trade and price drops below the <b>Red Safety Stop-Loss</b>, exit immediately without hesitation."
)
MAX_MESSAGE_LENGTH = 4000

# Full company names for all 50 tickers
TICKER_NAMES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet (Google)",
    "AMZN": "Amazon",
    "META": "Meta (Facebook)",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "JNJ": "Johnson & Johnson",
    "V": "Visa",
    "WMT": "Walmart",
    "JPM": "JPMorgan Chase",
    "PG": "Procter & Gamble",
    "MA": "Mastercard",
    "UNH": "UnitedHealth Group",
    "DIS": "Walt Disney",
    "HD": "Home Depot",
    "BAC": "Bank of America",
    "VZ": "Verizon",
    "KO": "Coca-Cola",
    "PFE": "Pfizer",
    "MRK": "Merck",
    "PEP": "PepsiCo",
    "ABBV": "AbbVie",
    "T": "AT&T",
    "CVX": "Chevron",
    "XOM": "ExxonMobil",
    "CSCO": "Cisco Systems",
    "INTC": "Intel",
    "MCD": "McDonald's",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "AMD": "Advanced Micro Devices",
    "PYPL": "PayPal",
    "SBUX": "Starbucks",
    "BA": "Boeing",
    "IBM": "IBM",
    "MMM": "3M Company",
    "GE": "General Electric",
    "F": "Ford Motor",
    "GM": "General Motors",
    "TGT": "Target",
    "UBER": "Uber Technologies",
    "ABNB": "Airbnb",
    "SQ": "Block (Square)",
    "COIN": "Coinbase",
    "PLTR": "Palantir Technologies",
    "ROKU": "Roku",
    "ZM": "Zoom Video",
    "DOCU": "DocuSign",
    "DKNG": "DraftKings",
}


def format_card(raw_entry: str) -> str:
    """
    Parses a raw scanner entry and transforms it into a crystal-clear,
    beginner-friendly trading card with custom calculated money and percentage metrics.
    """
    pattern = r"\[(.*?)\] Action: \$([\d\.]+) \| MUST BREAK: \$([\d\.]+) on Vol > (\d+) \| RIP-CORD: \$([\d\.]+)"
    match = re.match(pattern, raw_entry.strip())
    
    if not match:
        return f"• {html.escape(raw_entry)}"

    ticker, current_str, trigger_str, vol_str, stop_str = match.groups()
    current = float(current_str)
    trigger = float(trigger_str)
    vol = int(vol_str)
    stop = float(stop_str)

    company = TICKER_NAMES.get(ticker, ticker)

    # Custom calculated money numbers
    upside_dlr = trigger - current
    upside_pct = (upside_dlr / current * 100) if current > 0 else 0.0

    risk_dlr = current - stop
    risk_pct = (risk_dlr / current * 100) if current > 0 else 0.0

    # Humanized volume format
    if vol >= 1_000_000:
        vol_human = f"{vol / 1_000_000:.2f}M"
    elif vol >= 1_000:
        vol_human = f"{vol / 1_000:.1f}K"
    else:
        vol_human = f"{vol:,}"

    card = (
        f"🎯 <b>{ticker} — {company}</b>\n"
        f"💵 <b>Current Price:</b> ${current:.2f} <i>(Resting in tight coil)</i>\n"
        f"🟢 <b>BUY TRIGGER:</b> Buy ONLY if price climbs past <b>${trigger:.2f}</b> "
        f"(needs +${upside_dlr:.2f} / +{upside_pct:.1f}% rise) on volume &gt; <b>{vol_human} shares</b>.\n"
        f"🛑 <b>SAFETY STOP-LOSS:</b> Exit immediately if price drops below <b>${stop:.2f}</b> "
        f"(Maximum risk is <b>-${risk_dlr:.2f} per share</b> / -{risk_pct:.1f}%).\n"
        f"📋 <b>Next Step:</b> <i>Put on watchlist. Do not buy until the green trigger is crossed.</i>"
    )
    return card


def format_scan_results(results: list[str]) -> list[str]:
    """
    Formats scanner results into HTML messages, chunking them to
    strictly adhere to Telegram's 4096 character payload limit.
    """
    if not results:
        return [f"{HEADER}\n<i>No setups found today. All monitored stocks are either volatile or uncoiled.</i>"]

    intro = f"{HEADER}<i>Found {len(results)} coiled setup(s) ready on the watchlist:</i>\n\n"
    formatted_entries = [format_card(entry) for entry in results]

    chunks = []
    current_chunk = intro

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
