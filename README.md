# Energy Sector Sentiment Pipeline

Transforming unstructured financial news into a quantitative market sentiment signal for the energy sector.

## Overview
Commodity prices reflect forward-looking expectations but can lag behind the real-time narrative. This project ingests financial news headlines, scores them using FinBERT, and surfaces an aggregated sentiment signal alongside live commodity prices (using the 3:2:1 crack spread). This allows a side-by-side comparison of market *sentiment* versus market *prices*.

## Core Pipeline
- **News Ingestion:** Fetches real-time headlines for major energy equities (VLO, PSX, MPC, XOM, CVX, COP) via `yfinance`.
- **Keyword Filtering:** Discards headlines lacking energy-specific keywords (e.g., crude, oil, gasoline, refineries) to eliminate market noise.
- **Sentiment Scoring:** Evaluates filtered headlines using the `ProsusAI/finbert` Transformer model via HuggingFace's Inference API. Classifies each headline as Bullish, Bearish, or Neutral.
- **Commodity Context:** Calculates the live 3:2:1 crack spread using WTI, RBOB Gasoline, and Heating Oil futures.

## Dashboard
The Streamlit application visualizes the data without requiring a persistent database:
- Live KPI row with current commodity pricing.
- Interactive crack spread charts with 30-day and 90-day moving averages.
- A live feed of recent news, scored and categorized by sentiment.

**Live Demo:** [https://energy-sentiment-pipeline.streamlit.app/](https://energy-sentiment-pipeline.streamlit.app/)

## Quickstart
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Tech Stack
Python 3.11 · Streamlit · yfinance · FinBERT (HuggingFace API) · Plotly · Pandas

## Future Work
- Expand news sources beyond `yfinance` to increase signal volume.
- Conduct a lagged correlation analysis to determine if this sentiment signal leads or lags margin changes.
