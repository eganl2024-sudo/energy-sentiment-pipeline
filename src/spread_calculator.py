import pandas as pd
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import OPEX_DEFAULTS

INPUT_PATH = "data/raw/market_data.csv"
OUTPUT_PATH = "data/processed/spread_data.csv"

def calculate_spread():
    print("⚙️ STARTING REFINERY PROCESS SIMULATION...")
    
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Error: Input file not found at {INPUT_PATH}")
        return
        
    df = pd.read_csv(INPUT_PATH, index_col=0, parse_dates=True)
    
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
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH)
    
    latest_gross = df['Crack_Spread'].iloc[-1]
    latest_net = df['Net_Refining_Margin'].iloc[-1]
    
    print(f"✅ CALCULATION COMPLETE")
    print(f"   • Gross Margin: ${latest_gross:.2f}/bbl")
    print(f"   • Net Margin:   ${latest_net:.2f}/bbl (After OpEx)")

if __name__ == "__main__":
    calculate_spread()
