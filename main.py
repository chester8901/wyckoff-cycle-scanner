"""
Main execution pipeline for the Wyckoff / Overreaction Cycle Screening System.
Runs the mathematical screener and dispatches signals via Telegram.
"""

import sys
import time
from datetime import datetime

# Ensure stdout and stderr handle utf-8 characters smoothly on Windows & Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import validate_config, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from trading_logic import run_scanner, TICKERS
from bot import send_scan_results


def main():
    start_time = time.time()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    print("=" * 60)
    print("🚀 WYCKOFF / OVERREACTION CYCLE SCREENER")
    print(f"🕒 Run Timestamp: {timestamp}")
    print(f"📊 Scanning {len(TICKERS)} tickers...")
    print("=" * 60)

    # 1. Run trading logic scan
    try:
        results = run_scanner()
    except Exception as e:
        print(f"💥 CRITICAL ERROR during scanner execution: {e}", file=sys.stderr)
        sys.exit(1)

    elapsed = round(time.time() - start_time, 2)
    print(f"🏁 Scan complete in {elapsed}s. Found {len(results)} potential setup(s).")

    # 2. Output to console
    if results:
        print("\n--- Identified Setups ---")
        for res in results:
            print(f"  {res}")
        print("-------------------------\n")
    else:
        print("ℹ️ No tickers qualified under the Boredom Filter today.\n")

    # 3. Dispatch to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            send_scan_results(results)
            print("🎉 Telegram notifications sent successfully.")
        except Exception as e:
            print(f"❌ ERROR sending Telegram notification: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("ℹ️ Skipping Telegram dispatch (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set).")

    print("✅ Pipeline execution finished successfully.")


if __name__ == "__main__":
    main()
