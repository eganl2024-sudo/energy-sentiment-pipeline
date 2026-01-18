import pandas as pd

def calculate_ebitda_impact(throughput_bpd, capture_rate, current_spread, shock_spread):
    """
    Calculates the annualized EBITDA impact of a spread change.
    
    Args:
        throughput_bpd (int): Barrels per day (e.g., 3,000,000 for VLO).
        capture_rate (float): Efficiency % (e.g., 0.90).
        current_spread (float): The baseline 3:2:1 margin ($/bbl).
        shock_spread (float): The user-adjusted scenario margin ($/bbl).
        
    Returns:
        float: Change in Annual EBITDA ($).
    """
    delta_spread = shock_spread - current_spread
    
    # Formula: Delta * Daily Volume * 365 Days * Capture Efficiency
    annual_impact = delta_spread * throughput_bpd * 365 * capture_rate
    
    return annual_impact

def calculate_share_price_impact(current_ebitda, annual_impact, ev_ebitda_multiple, shares_outstanding):
    """
    Calculates the theoretical impact on share price assuming constant multiple.
    """
    # New EBITDA
    pro_forma_ebitda = current_ebitda + annual_impact
    
    # Change in Enterprise Value (EV) = Change in EBITDA * Multiple
    # (Assuming Net Debt remains constant for this short-term shock)
    delta_ev = annual_impact * ev_ebitda_multiple
    
    # Change in Share Price = Delta EV / Shares
    delta_share_price = delta_ev / shares_outstanding
    
    return delta_share_price, pro_forma_ebitda
