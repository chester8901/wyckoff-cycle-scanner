import time
import warnings
import yfinance as yf
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

warnings.filterwarnings('ignore')

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JNJ", "V", "WMT", "JPM", "PG", "MA", "UNH", "DIS", "HD", "BAC", "VZ", "KO", "PFE", "MRK", "PEP", "ABBV", "T", "CVX", "XOM", "CSCO", "INTC", "MCD", "NFLX", "CRM", "AMD", "PYPL", "SBUX", "BA", "IBM", "MMM", "GE", "F", "GM", "TGT", "UBER", "ABNB", "SQ", "COIN", "PLTR", "ROKU", "ZM", "DOCU", "DKNG"]

LOOKBACK_DAYS = 60
MAX_VOLATILITY = 0.15
VOLUME_MULTIPLIER = 1.5
ATR_PERIOD = 14
STOP_MULTIPLIER = 2.5


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def fetch_data(ticker: str) -> pd.DataFrame:
    """Download market data with isolated retry on rate limits or temporary network issues."""
    data = yf.download(ticker, period="6mo", progress=False)
    if data is None or data.empty:
        raise RuntimeError(f"Rate limited or empty data returned for {ticker}")
    return data


def run_scanner():
    results = []
    for ticker in TICKERS:
        try:
            # Download data
            data = fetch_data(ticker)
            if data.empty or len(data) < LOOKBACK_DAYS: continue

            # Auto-flatten Multi-index columns to prevent pandas errors
            data.columns = [col[0] for col in data.columns] if isinstance(data.columns, pd.MultiIndex) else data.columns

            recent_data = data.tail(LOOKBACK_DAYS)
            highest_high = float(recent_data['High'].max())
            lowest_low = float(recent_data['Low'].min())
            avg_volume = float(recent_data['Volume'].mean())

            current_price = float(data['Close'].iloc[-1])
            range_width = (highest_high - lowest_low) / lowest_low

            # ROTOR 1: Boredom Filter
            if range_width <= MAX_VOLATILITY:
                
                # ATR CALCULATION (Rotors 3 & 4)
                high_low = data['High'] - data['Low']
                high_close = (data['High'] - data['Close'].shift()).abs()
                low_close = (data['Low'] - data['Close'].shift()).abs()
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                current_atr = float(true_range.rolling(ATR_PERIOD).mean().iloc[-1])
                
                failsafe_price = current_price - (current_atr * STOP_MULTIPLIER)
                
                # TARGET GENERATED
                results.append(f"[{ticker}] Action: ${round(current_price, 2)} | MUST BREAK: ${round(highest_high, 2)} on Vol > {int(avg_volume * VOLUME_MULTIPLIER)} | RIP-CORD: ${round(failsafe_price, 2)}")
                
        except Exception as e:
            # Silently pass errors (delistings, bad API fetches) to ensure uninterrupted run
            pass
        finally:
            time.sleep(0.2)
            
    return results
