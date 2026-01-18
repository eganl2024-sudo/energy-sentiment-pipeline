import pandas as pd
import numpy as np

def calculate_correlations(df, spread_col='Crack_Spread', equity_col='Valero', rolling_window=90):
    """
    Calculates statistical relationships between the physical spread and equity price.
    
    Args:
        df (pd.DataFrame): The data containing spread and equity columns.
        spread_col (str): Column name for the spread (X-axis).
        equity_col (str): Column name for the stock price (Y-axis).
        rolling_window (int): Days for the rolling window.
        
    Returns:
        float: Overall Pearson Correlation
        float: R-Squared
        Series: Rolling Correlation Series
    """
    # 1. Clean Data (Align timestamps, drop NaNs)
    # We work on a copy to avoid SettingWithCopy warnings
    work_df = df[[spread_col, equity_col]].dropna()
    
    # 2. Static Stats (The Headline Numbers)
    correlation = work_df[spread_col].corr(work_df[equity_col])
    r_squared = correlation ** 2
    
    # 3. Rolling Correlation (The "Regime Change" Detector)
    # This shows how the relationship evolves over time.
    rolling_corr = work_df[spread_col].rolling(window=rolling_window).corr(work_df[equity_col])
    
    return correlation, r_squared, rolling_corr
