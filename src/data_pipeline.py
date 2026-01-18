import yfinance as yf
import pandas as pd
import time
import os
import sys

# Add project root to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import TICKERS

DATA_PATH = "data/raw/market_data.csv"

def fetch_market_data(period="5y", retries=3):
    """
    Fetches historical futures & equity data defined in src/config.py.
    """
    print(f"📡 CONNECTING TO MARKET DATA API (Looking back {period})...")
    
    master_df = pd.DataFrame()
    success_count = 0
    
    for name, ticker in TICKERS.items():
        for attempt in range(retries):
            try:
                print(f"   ...fetching {name} ({ticker})")
                df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
                
                if df.empty: raise ValueError(f"No data returned for {ticker}")
                
                # Handle MultiIndex
                if isinstance(df.columns, pd.MultiIndex):
                    clean_series = df['Close'][ticker]
                else:
                    clean_series = df['Close']
                
                clean_series.name = name
                
                if master_df.empty:
                    master_df = pd.DataFrame(clean_series)
                else:
                    master_df = master_df.join(clean_series, how='outer')
                
                success_count += 1
                break
            except Exception as e:
                print(f"   ⚠️ Attempt {attempt+1} failed for {name}: {e}")
                time.sleep(1)
    
    if success_count == len(TICKERS):
        print("\n✅ DATA INGESTION COMPLETE")
        master_df.ffill(limit=3, inplace=True)
        master_df.dropna(inplace=True)
        
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        master_df.to_csv(DATA_PATH)
        print(f"   • Rows Saved: {len(master_df)}")
        return master_df
    else:
        print("\n❌ CRITICAL FAILURE: Could not fetch all tickers.")
        return None

if __name__ == "__main__":
    fetch_market_data()
