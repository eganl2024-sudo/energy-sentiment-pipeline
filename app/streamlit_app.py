import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import datetime
import requests

HF_API_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"

def score_with_finbert(headline: str, api_token: str) -> dict:
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": headline}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=10)
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            # FinBERT returns list of [{label, score}] sorted by score desc
            top = sorted(result[0], key=lambda x: x['score'], reverse=True)[0]
            label = top['label'].lower()  # 'positive', 'negative', 'neutral'
            score = top['score']
            sentiment_map = {'positive': 'Bullish', 'negative': 'Bearish', 'neutral': 'Neutral'}
            return {'sentiment': sentiment_map.get(label, 'Neutral'), 'score': round(score, 3)}
    except Exception:
        pass
    return {'sentiment': 'Neutral', 'score': 0.0}

# --- Configuration ---
st.set_page_config(page_title="3:2:1 Crack Spread Dashboard", layout="wide")

# --- Constants ---
# Tickers for Yahoo Finance
TICKERS = {
    'WTI': 'CL=F',   # Crude Oil
    'RBOB': 'RB=F',  # Gasoline (in $/gallon)
    'HO': 'HO=F'     # Heating Oil (in $/gallon)
}
GAL_TO_BBL = 42.0

# --- Helper Functions ---
@st.cache_data(ttl=300)
def fetch_data(lookback_days: int) -> pd.DataFrame:
    """Fetches live WTI (CL=F), RBOB Gasoline (RB=F), and Heating Oil (HO=F) prices using yfinance"""
    end_date = datetime.date.today() + datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=lookback_days + 150) # Buffer for 90D MA
    
    try:
        # Download data for all tickers
        data = yf.download(list(TICKERS.values()), start=start_date, end=end_date, progress=False)
        
        if data.empty:
            st.warning("Yahoo Finance returned an empty dataset.")
            return pd.DataFrame()
            
        # If the returned dataframe has a MultiIndex on columns (like when using yf.download for multiple tickers)
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' in data.columns.levels[0]:
                df = data['Close'].copy()
            # Fallback for newer yfinance which might return 'Price' level
            elif 'Adj Close' in data.columns.levels[0]:
                df = data['Adj Close'].copy()
            else:
                 df = data.copy()
                 df.columns = df.columns.droplevel(0)
        else:
            df = data.copy()
    
        # Map columns to our internal names
        rename_map = {v: k for k, v in TICKERS.items()}
        df.rename(columns=rename_map, inplace=True)
        df = df.dropna()
    
        # Convert RBOB and Heating Oil to $/bbl
        df['RBOB_bbl'] = df['RBOB'] * GAL_TO_BBL
        df['HO_bbl'] = df['HO'] * GAL_TO_BBL
        df['WTI_bbl'] = df['WTI']
        
        # Calculate 3:2:1 Crack Spread
        df['Crack_Spread'] = (2 * df['RBOB_bbl'] + 1 * df['HO_bbl'] - 3 * df['WTI_bbl']) / 3
        
        # Moving Averages
        df['Crack_Spread_30MA'] = df['Crack_Spread'].rolling(window=30).mean()
        df['Crack_Spread_90MA'] = df['Crack_Spread'].rolling(window=90).mean()
        
        return df
    except Exception as e:
        st.error(f"Error processing yfinance data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def fetch_and_score_news() -> pd.DataFrame:
    """
    Fetches recent energy sector headlines from major refining/oil companies
    and scores them with VADER sentiment. Uses equity tickers which reliably
    return news via yfinance, rather than futures tickers which often return nothing.
    """
    # Energy sector tickers that reliably return news and are 
    # directly tied to refining margins and crack spreads
    NEWS_TICKERS = ["VLO", "PSX", "MPC", "XOM", "CVX", "COP"]
    
    ENERGY_KEYWORDS = [
        "crude", "oil", "refin", "gasoline", "diesel", "distillate", "barrel", "crack", 
        "wti", "brent", "upstream", "downstream", "margin", "lng", "natural gas", "pipeline", 
        "energy", "fuel", "petrochemical", "opec"
    ]
    
    # Needs to be configured in Streamlit Cloud Secrets Manager -> [huggingface] api_token
    try:
        api_token = st.secrets["huggingface"]["api_token"]
    except Exception:
        st.error("HuggingFace API token not found! Please configure st.secrets['huggingface']['api_token'].")
        return pd.DataFrame()
        
    seen_titles = set()
    rows = []

    for symbol in NEWS_TICKERS:
        try:
            t = yf.Ticker(symbol)
            news_list = t.news or []
            for item in news_list:
                # yfinance >=0.2.40 nests content inside a 'content' dict
                # Fall back gracefully if the old flat structure is used
                content = item.get('content', item)
                
                title = (
                    content.get('title') or
                    item.get('title') or
                    ''
                ).strip()
                
                link = (
                    content.get('canonicalUrl', {}).get('url') or
                    content.get('clickThroughUrl', {}).get('url') or
                    item.get('link') or
                    ''
                ).strip()
                
                publisher = (
                    content.get('provider', {}).get('displayName') or
                    item.get('publisher') or
                    ''
                ).strip()
                
                # Timestamp: try multiple locations
                pub_time = (
                    content.get('pubDate') or
                    item.get('providerPublishTime') or
                    0
                )
                
                # Parse timestamp — could be unix int or ISO string
                try:
                    if isinstance(pub_time, str):
                        date_str = pd.to_datetime(pub_time).strftime('%Y-%m-%d')
                    elif isinstance(pub_time, (int, float)) and pub_time > 0:
                        date_str = pd.to_datetime(pub_time, unit='s').strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.date.today().strftime('%Y-%m-%d')
                except Exception:
                    date_str = datetime.date.today().strftime('%Y-%m-%d')
                
                # Skip empty titles and duplicates
                if not title or title in seen_titles:
                    continue
                    
                # Keyword pre-filter
                title_lower = title.lower()
                if not any(kw in title_lower for kw in ENERGY_KEYWORDS):
                    continue
                    
                seen_titles.add(title)
                
                # FinBERT API scoring
                result = score_with_finbert(title, api_token)
                sentiment = result['sentiment']
                score = result['score']
                
                rows.append({
                    'Date': date_str,
                    'title': title,
                    'link': link,
                    'publisher': publisher,
                    'Sentiment': sentiment,
                    'Score': score,
                })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values('Date', ascending=False).head(15).reset_index(drop=True)
    return df

# --- Sidebar ---
st.sidebar.title("Configuration")

# Lookback Mapping
LOOKBACK_OPTIONS = {
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365,
    "2 Years": 730
}
selected_lookback = st.sidebar.selectbox("Lookback Period", list(LOOKBACK_OPTIONS.keys()), index=3) # Default 1 Year
lookback_days = LOOKBACK_OPTIONS[selected_lookback]

st.sidebar.markdown("### 3:2:1 Crack Spread Formula")
st.sidebar.latex(r'''Crack\ Spread = \frac{2 \times RBOB_{bbl} + 1 \times HO_{bbl} - 3 \times WTI}{3}''')
st.sidebar.markdown("*Note: RBOB and HO are converted from \$/gallon to \$/bbl by multiplying by 42.*")


# --- Main Logic ---
st.title("3:2:1 Crack Spread Dashboard")

with st.spinner("Fetching live data from Yahoo Finance..."):
    df_full = fetch_data(lookback_days)

if df_full.empty:
    st.error("Error fetching data. Please try again later.")
    st.stop()

# Filter context for the selected period
df_view = df_full.tail(lookback_days).copy()

if df_view.empty:
    st.error("No data available for the selected period.")
    st.stop()

# Get latest values for KPIs
latest = df_view.iloc[-1]
crack_spread_val = latest['Crack_Spread']
wti_val = latest['WTI_bbl']
rbob_bbl_val = latest['RBOB_bbl']
ho_bbl_val = latest['HO_bbl']
cs_30ma = latest['Crack_Spread_30MA']

val_30d_ago = df_full['Crack_Spread'].iloc[-22] if len(df_full) >= 22 else df_full['Crack_Spread'].iloc[0]
cs_1m_change = crack_spread_val - val_30d_ago

# --- KPI Section ---
st.subheader("Key Performance Indicators (Latest)")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Crack Spread", f"${crack_spread_val:.2f}", f"{crack_spread_val - df_view['Crack_Spread'].iloc[-2]:.2f} (Daily)")
col2.metric("WTI ($/bbl)", f"${wti_val:.2f}", f"{wti_val - df_view['WTI_bbl'].iloc[-2]:.2f}")
col3.metric("RBOB ($/bbl)", f"${rbob_bbl_val:.2f}", f"{rbob_bbl_val - df_view['RBOB_bbl'].iloc[-2]:.2f}")
col4.metric("Heating Oil", f"${ho_bbl_val:.2f}", f"{ho_bbl_val - df_view['HO_bbl'].iloc[-2]:.2f}")
col5.metric("CS vs 30D MA", f"${crack_spread_val - cs_30ma:.2f}", delta_color="normal")


# --- Charts Section ---
st.subheader("Crack Spread Analysis")

# Chart 1: Crack Spread with MAs and shaded fill
fig_cs = go.Figure()

fig_cs.add_trace(go.Scatter(
    x=df_view.index, y=df_view['Crack_Spread'],
    mode='lines', name='Crack Spread',
    line=dict(color='royalblue', width=2),
    fill='tozeroy', fillcolor='rgba(65, 105, 225, 0.1)'
))
fig_cs.add_trace(go.Scatter(
    x=df_view.index, y=df_view['Crack_Spread_30MA'],
    mode='lines', name='30-Day MA',
    line=dict(color='orange', width=2, dash='dash')
))
fig_cs.add_trace(go.Scatter(
    x=df_view.index, y=df_view['Crack_Spread_90MA'],
    mode='lines', name='90-Day MA',
    line=dict(color='red', width=2, dash='dot')
))

fig_cs.update_layout(title="Crack Spread History", xaxis_title="Date", yaxis_title="Crack Spread ($/bbl)", template="plotly_white", margin=dict(l=0, r=0, t=40, b=0))

st.plotly_chart(fig_cs, use_container_width=True)

# Chart 2: Component Prices
st.subheader("Component Prices")
fig_comp = go.Figure()

fig_comp.add_trace(go.Scatter(
    x=df_view.index, y=df_view['WTI_bbl'],
    mode='lines', name='WTI ($/bbl)', line=dict(color='black')
))
fig_comp.add_trace(go.Scatter(
    x=df_view.index, y=df_view['RBOB_bbl'],
    mode='lines', name='RBOB ($/bbl)', line=dict(color='green')
))
fig_comp.add_trace(go.Scatter(
    x=df_view.index, y=df_view['HO_bbl'],
    mode='lines', name='Heating Oil ($/bbl)', line=dict(color='darkred')
))

fig_comp.update_layout(title="Component Price History ($/bbl)", xaxis_title="Date", yaxis_title="Price ($/bbl)", template="plotly_white", margin=dict(l=0, r=0, t=40, b=0))

st.plotly_chart(fig_comp, use_container_width=True)

# --- Data Table Section ---
st.subheader("Recent Daily Data")
st.markdown("Most recent 10 trading days.")

display_df = df_full[['WTI', 'RBOB', 'HO', 'WTI_bbl', 'RBOB_bbl', 'HO_bbl', 'Crack_Spread']].copy()
display_df = display_df.sort_index(ascending=False).head(10)
display_df.index = display_df.index.strftime('%Y-%m-%d')
st.dataframe(display_df.style.format("{:.2f}"))

st.divider()

# --- Market Sentiment Section ---
st.subheader("📰 Market Sentiment — News Headlines")

with st.spinner("Fetching and scoring recent headlines..."):
    df_news = fetch_and_score_news()

if df_news.empty:
    st.info("No recent news headlines available.")
else:
    avg_score = df_news['Score'].mean()
    bullish_count = len(df_news[df_news['Sentiment'] == 'Bullish'])
    bearish_count = len(df_news[df_news['Sentiment'] == 'Bearish'])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Headline Sentiment", f"{avg_score:.2f}")
    c2.metric("Bullish Headlines", bullish_count)
    c3.metric("Bearish Headlines", bearish_count)
    
    # Plotly Bar Chart
    df_plot = df_news.copy()
    # Truncate title for chart
    df_plot['short_title'] = df_plot['title'].apply(lambda x: x[:60] + "..." if len(x) > 60 else x)
    df_plot = df_plot.sort_values(by='Score', ascending=True)
    
    color_map = {'Bullish': 'green', 'Bearish': 'red', 'Neutral': 'gray'}
    colors = df_plot['Sentiment'].map(color_map).tolist()
    
    fig_sent = go.Figure(go.Bar(
        x=df_plot['Score'],
        y=df_plot['short_title'],
        orientation='h',
        marker_color=colors,
    ))
    fig_sent.add_vline(x=0, line_dash="dash", line_color="black")
    fig_sent.update_layout(
        title="Headline Sentiment Scores",
        height=650,
        xaxis_title="Compound Score",
        yaxis_title="",
        yaxis=dict(automargin=True, tickfont=dict(size=11)),
        template="plotly_white",
        margin=dict(l=300, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_sent, use_container_width=True)
    
    # Dataframe Table
    st.markdown("### Recent News")
    df_table = df_news.copy()
    df_table['Headline'] = "[" + df_table['title'] + "](" + df_table['link'].fillna("") + ")"
    df_table = df_table[['Date', 'Headline', 'publisher', 'Sentiment', 'Score']]
    df_table = df_table.rename(columns={'publisher': 'Publisher'})
    
    # Format Score to 2 decimal places
    df_table['Score'] = df_table['Score'].apply(lambda x: f"{x:.2f}")
    
    # Render as HTML to support clickable links
    st.write(df_table.to_html(escape=False, index=False), unsafe_allow_html=True)
