import pandas as pd
import numpy as np

def calculate_signal_metrics(series, window=None):
    """
    Calculates Z-Score and Percentile Rank for a given series.
    
    Args:
        series (pd.Series): The data series (e.g., Crack Spread).
        window (int, optional): Lookback window. If None, uses full history.
        
    Returns:
        dict: {
            'z_score': float,
            'percentile': float,
            'signal': str ('BUY'/'SELL'/'NEUTRAL')
        }
    """
    if window:
        # Use only the last 'window' days for calculation
        calc_series = series.tail(window)
    else:
        calc_series = series
        
    current_val = series.iloc[-1]
    mean = calc_series.mean()
    std = calc_series.std()
    
    # Z-Score
    z_score = (current_val - mean) / std
    
    # Percentile (0-100)
    # We calculate the rank of the current value relative to the history
    percentile = (calc_series < current_val).mean() * 100
    
    # Signal Logic (Mean Reversion)
    # Low Spread = Buy Refiners (Expect Reversion Up)? OR Sell Refiners (Bad Margins)?
    # Interpretation: 
    # High Z-Score (>2) -> Spread is expensive -> Margins are peak -> Good for VLO (Momentum) OR Sell Signal (Mean Reversion)?
    # Let's stick to "Margin Strength":
    if z_score > 1.0:
        signal = "BULLISH (Margins High)"
    elif z_score < -1.0:
        signal = "BEARISH (Margins Low)"
    else:
        signal = "NEUTRAL"
        
    return {
        'z_score': z_score,
        'percentile': percentile,
        'signal': signal
    }
