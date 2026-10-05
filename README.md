# 🚀 Wyckoff / Overreaction Cycle Scanner

An indestructible, serverless financial screening pipeline that tracks the **Wyckoff / Overreaction Cycle** across 50 major US equities. Automated via GitHub Actions CRON and delivering real-time signals straight to your Telegram.

---

## ⚡ Architecture Highlights

- **Boredom Filter**: Isolates consolidation phases where `range_width <= 0.15` over a 60-day window.
- **Multi-Index Safe**: Automatically flattens modern `yfinance` multi-index columns to prevent pandas indexing errors.
- **Isolated Rate-Limit Immunity**: Data retrieval is wrapped in an isolated `tenacity` exponential backoff retry (3 attempts) on `yf.download`, preventing cascading failures.
- **DST-Immune CRON (`30 21 * * 1-5`)**: Scheduled at 21:30 UTC (5:30 PM EDT summer / 4:30 PM EST winter) so daily candles are always 100% complete and finalized before calculations run.
- **Robust Telegram HTML Delivery**: Formatted using `ParseMode.HTML` with automatic entity safety and dual-dispatch fallback (`python-telegram-bot` with `requests` failover).

---

## 📁 Repository Structure

```
├── .github/
│   └── workflows/
│       └── daily_scanner.yml  # GitHub Actions automated CRON runner
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules for caches & secrets
├── requirements.txt           # Version-pinned dependencies
├── config.py                  # Environment variable loader & validator
├── trading_logic.py           # Core Wyckoff calculation & isolated tenacity retry
├── bot.py                     # Telegram HTML formatting, chunking & dispatch
├── main.py                    # Pipeline execution orchestrator
└── README.md                  # Documentation & setup guide
```

---

## 🛠️ Step-by-Step Setup

### Step 1: Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts to choose a name and username.
3. Save the **Bot Token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
4. Search for `@userinfobot` on Telegram and send `/start` to get your **Chat ID** (e.g., `987654321`).
5. Open a chat with your newly created bot and click **Start** (or send any message) so it has permission to message you.

### Step 2: Push Code to GitHub
1. Create a new GitHub repository (public or private).
2. Push this codebase:
   ```bash
   git init
   git add .
   git commit -m "feat: indestructible Wyckoff screening pipeline"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

### Step 3: Add GitHub Repository Secrets
1. In your GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add:
   - Name: `TELEGRAM_BOT_TOKEN` | Secret: *(Your Telegram Bot Token)*
   - Name: `TELEGRAM_CHAT_ID` | Secret: *(Your Telegram Chat ID)*

### Step 4: Test Manually (Workflow Dispatch)
1. Go to the **Actions** tab in your GitHub repository.
2. Select **Daily Wyckoff Cycle Scanner** from the left sidebar.
3. Click the **Run workflow** dropdown and select **Run workflow**.
4. Check your Telegram for the `🚨 SYSTEM ONLINE: WYCKOFF CYCLE MATRIX 🚨` notification!

---

## 💻 Local Execution

To run the pipeline locally:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Configure local environment variables
cp .env.example .env
# Edit .env and enter your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

# 4. Run the scanner
python main.py
```
