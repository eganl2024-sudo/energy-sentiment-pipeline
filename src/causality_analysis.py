import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import read_processed, get_eia_sentiment, write_sentiment_spread_merged, write_sentiment_spread_rolling_corr

def run_causality_analysis():
    print("🔬 INITIALIZING GRANGER CAUSALITY TESTS...")
    
    # 1. Load Data
    sentiment_df = get_eia_sentiment()
    spread_df = read_processed()
    
    if sentiment_df.empty or spread_df.empty:
        print("❌ Error: Missing data. Ensure scraper, pipeline, and spread calculator have been run.")
        return
        
    # Prepare DataFrames for merge
    sentiment_df = sentiment_df.reset_index().rename(columns={'report_date': 'date'})
    sentiment_df = sentiment_df.sort_values('date')
    
    spread_df = spread_df.reset_index().rename(columns={'Date': 'date'})
    # We only need specific columns for the merge and analysis
    cols_to_keep = ['date', 'Crack_Spread', 'Spread_30D_MA', 'Net_Refining_Margin']
    # Filter columns safely based on what actually exists in spread_df
    available_cols = [c for c in cols_to_keep if c in spread_df.columns]
    spread_df = spread_df[available_cols].sort_values('date')
    
    # 2. Merge Data
    # Match each EIA report to the nearest trading day within a 7-day window
    merged_df = pd.merge_asof(
        sentiment_df, 
        spread_df, 
        on='date', 
        tolerance=pd.Timedelta('7D'),
        direction='nearest'
    )
    
    # Drop rows where the gap exceeded 7 days (i.e. 'Crack_Spread' will be NaN)
    # or if we are missing the sentiment score
    merged_df = merged_df.dropna(subset=['Crack_Spread', 'compound'])
    
    if merged_df.empty:
        print("❌ Error: No overlapping dates found within tolerance.")
        return
        
    # Write merged data to DuckDB. Rename the date column back to report_date for schema conformity
    db_merge = merged_df.rename(columns={'date': 'report_date'})
    # Also we need to supply 'Date' as an explicit column for the schema
    db_merge['Date'] = db_merge['report_date'] 
    write_sentiment_spread_merged(db_merge)
    
    print("\n📊 GRANGER CAUSALITY TEST RESULTS:")
    print(f"{'Direction':<20} | {'Lag':<3} | {'F-stat':<7} | {'p-value':<7} | {'Significant?'}")
    print("-" * 60)
    
    # Set up test data
    # format: a 2D array where the first column is the target variable (to be predicted)
    # and the second column is the predictor variable.
    
    test_lags = [1, 2, 3, 4]
    
    # Test A: Does Sentiment predict Spread? (Target = Crack_Spread, Predictor = compound)
    test_a_data = merged_df[['Crack_Spread', 'compound']].values
    try:
        results_a = grangercausalitytests(test_a_data, maxlag=test_lags, verbose=False)
    except Exception as e:
        print(f"Test A failed: {e}")
        results_a = None
        
    # Test B: Does Spread predict Sentiment? (Target = compound, Predictor = Crack_Spread)
    test_b_data = merged_df[['compound', 'Crack_Spread']].values
    try:
        results_b = grangercausalitytests(test_b_data, maxlag=test_lags, verbose=False)
    except Exception as e:
        print(f"Test B failed: {e}")
        results_b = None
        
    significant_a = False
    significant_b = False

    # Print Results for Test A
    if results_a:
        for lag in test_lags:
            f_test = results_a[lag][0]['ssr_ftest']
            f_stat = f_test[0]
            p_val = f_test[1]
            is_sig = p_val < 0.05
            if is_sig: significant_a = True
            print(f"{'Sentiment → Spread':<20} | {lag:<3} | {f_stat:<7.2f} | {p_val:<7.4f} | {'Yes' if is_sig else 'No'}")
            
    # Print Results for Test B
    if results_b:
        for lag in test_lags:
            f_test = results_b[lag][0]['ssr_ftest']
            f_stat = f_test[0]
            p_val = f_test[1]
            is_sig = p_val < 0.05
            if is_sig: significant_b = True
            print(f"{'Spread → Sentiment':<20} | {lag:<3} | {f_stat:<7.2f} | {p_val:<7.4f} | {'Yes' if is_sig else 'No'}")

    # 3. Rolling Correlation
    # Compute 90-day rolling Pearson correlation between compound sentiment and crack_spread.
    # Note: Because the merged data is weekly, 90 days is roughly ~12 weeks. We approximate using window=12
    # on the sorted weekly data.
    merged_df = merged_df.sort_values('date')
    rolling_corr = merged_df['compound'].rolling(window=12, min_periods=4).corr(merged_df['Crack_Spread'])
    
    corr_df = pd.DataFrame({
        'date': merged_df['date'],
        'rolling_corr': rolling_corr
    }).dropna()
    
    write_sentiment_spread_rolling_corr(corr_df)
    
    # 4. Interpretation Block
    print("\nINTERPRETATION:")
    if significant_a and not significant_b:
        print("A significant result (p<0.05) in Test A means EIA commentary tends to move before crack spreads — suggesting text sentiment has predictive value.")
    elif significant_b and not significant_a:
        print("A significant result in Test B means spreads move first and EIA reports react to market conditions rather than lead them.")
    elif significant_a and significant_b:
        print("Significant results in both directions suggest a strong feedback loop: sentiment predicts future spreads, but spreads also dictate future sentiment.")
    else:
        print("No significant causal relationship found at these lags. Current tests suggest neither EIA sentiment nor crack spreads strictly lead the other.")

if __name__ == "__main__":
    run_causality_analysis()
