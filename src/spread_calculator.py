import pandas as pd
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import OPEX_DEFAULTS
from src.db import read_raw, write_processed

def calculate_spread():
    print("⚙️ STARTING REFINERY PROCESS SIMULATION...")
    
    df = read_raw()
    
    if df.empty:
        print(f"❌ Error: No raw market data found in DuckDB.")
        return
    
    # 1. Gross Margin (The 3:2:1 Crack Spread)
    df['Gasoline_bbl'] = df['Gasoline'] * 42
    df['Heating_Oil_bbl'] = df['Heating_Oil'] * 42
    
    product_value = (2 * df['Gasoline_bbl']) + (1 * df['Heating_Oil_bbl'])
    input_cost = 3 * df['Crude_Oil']
    
    df['Crack_Spread'] = (product_value - input_cost) / 3
    
    # 2. Net Margin (Phase 7 Upgrade)
    # Variable Cost = Natural Gas Price * Intensity
    # Fixed Cost = Constant
    if 'Natural_Gas' in df.columns:
        df['Variable_OpEx'] = df['Natural_Gas'] * OPEX_DEFAULTS['nat_gas_intensity']
    else:
        print("⚠️ Warning: Natural_Gas data missing. Assuming $0 variable energy cost.")
        df['Variable_OpEx'] = 0.0
        
    df['Total_OpEx'] = df['Variable_OpEx'] + OPEX_DEFAULTS['fixed_opex']
    df['Net_Refining_Margin'] = df['Crack_Spread'] - df['Total_OpEx']
    
    # 3. Moving Averages
    df['Spread_30D_MA'] = df['Crack_Spread'].rolling(window=30).mean()
    df['Net_Margin_30D_MA'] = df['Net_Refining_Margin'].rolling(window=30).mean()
    
    # Save to DuckDB
    write_processed(df)
    
    latest_gross = df['Crack_Spread'].iloc[-1]
    latest_net = df['Net_Refining_Margin'].iloc[-1]
    
    print(f"✅ CALCULATION COMPLETE")
    print(f"   • Gross Margin: ${latest_gross:.2f}/bbl")
    print(f"   • Net Margin:   ${latest_net:.2f}/bbl (After OpEx)")

def compute_correlation_returns(df, col1='Crack_Spread', col2='Valero'):
    """Computes the Pearson correlation of daily percentage returns between two columns."""
    returns = df[[col1, col2]].pct_change().dropna()
    return returns[col1].corr(returns[col2])

if __name__ == "__main__":
    calculate_spread()
