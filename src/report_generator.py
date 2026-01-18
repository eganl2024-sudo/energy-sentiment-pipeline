import pandas as pd
from src.config import VLO_DEFAULTS

def generate_executive_summary(df):
    """
    Generates a natural language summary of the current market state.
    """
    # 1. Get Key Metrics
    latest = df.iloc[-1]
    
    # Safety check for empty or missing columns
    if 'Spread_30D_MA' not in latest or 'Crack_Spread' not in latest:
        return "⚠️ Data insufficient for executive summary."
        
    ma_30 = latest['Spread_30D_MA']
    current_spread = latest['Crack_Spread']
    net_margin = latest.get('Net_Refining_Margin', 0) # Use .get() for safety
    
    # 2. Determine Trend (vs 30-Day MA)
    trend_delta = current_spread - ma_30
    if trend_delta > 1.0:
        trend_str = "trading significantly **above** the 30-day average (+Bullish Momentum)"
    elif trend_delta < -1.0:
        trend_str = "trading **below** the 30-day average (-Bearish Momentum)"
    else:
        trend_str = "consolidating near the 30-day average (Neutral)"
        
    # 3. Determine Profitability Context
    # Breakeven check (Roughly $6-8 fixed cost + gas)
    if net_margin > 15:
        profit_context = "highly profitable"
    elif net_margin > 10:
        profit_context = "healthy"
    elif net_margin > 5:
        profit_context = "moderately profitable"
    else:
        profit_context = "near breakeven/distressed levels"
        
    # 4. Construct the Narrative
    summary = f"""
    **Market Update:**
    Refining margins are currently **${current_spread:.2f}/bbl**, {trend_str}. 
    Net realized margins (after OpEx) are roughly **${net_margin:.2f}/bbl**, indicating a {profit_context} environment for complex refiners like Valero.
    
    **Valuation Implication:**
    With margins at these levels, VLO is generating an estimated **${(net_margin * VLO_DEFAULTS['throughput_bpd'] * 365 / 1e9):.1f}B** in annualized gross profit (pre-tax/corporate). 
    """
    
    return summary
