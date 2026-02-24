# Energy Sector NLP Sentiment Pipeline
### Unstructured Data Analytics | MSBA | University of Notre Dame | Spring 2026

---

## What is the Project

The project implements a live natural language processing (NLP) sentiment pipeline for the energy sector. Real-time financial news headlines are collected from six major energy equity tickers (VLO, PSX, MPC, XOM, CVX, COP) using the yfinance API, filtered for energy relevance, and scored using FinBERT, a transformer model trained on financial news. The resulting quantitative sentiment signal is displayed alongside a live 3:2:1 crack spread monitor, facilitating direct comparison between market sentiment and actual prices.

---

## What is the Problem

Financial news is inherently unstructured, continuous, and frequently noisy. Commodity markets, including crude oil and refined products, are forward-looking, with futures prices reflecting consensus expectations. However, these prices often lag behind real-time news developments. In some cases, refinery margins may appear robust based on structured data, even when news coverage of major refiners is highly negative. This discrepancy cannot be captured by structured price data alone.

Three primary challenges were encountered. Initially, reliance on pre-downloaded CSV files of commodity prices rendered the dashboard outdated upon launch. Additionally, extracting a clear, energy-focused signal from noisy news feeds that often combine sector-specific and general-market stories required rigorous filtering. Finally, accurately scoring news headlines proved difficult, as general sentiment tools such as VADER frequently misinterpret financial language. For example, VADER may rate a headline about an Exxon court case as positive because it lacks negative words, even though the headline does not convey favorable news for refining margins.

Addressing these challenges required replacing static data with live API feeds, implementing robust noise filtering to isolate relevant signals, and upgrading the NLP component to a domain-specific model.

---

## How Was It Solved

News is sourced from equity tickers instead of futures tickers, as the latter (`CL=F`, `RB=F`, `HO=F`) consistently returned empty news feeds during testing. An energy-specific keyword filter (crude, oil, refin, gasoline, diesel, distillate, barrel, crack, WTI, Brent, upstream, downstream, margin, LNG, natural gas, pipeline, OPEC) is applied to eliminate off-topic articles before sentiment scoring.

For sentiment scoring, VADER was replaced with **FinBERT** (`ProsusAI/finbert`), a BERT-based transformer trained on 10,000 labeled sentences from the Financial PhraseBank. Rather than loading model weights locally, which previously caused deployment failures on Streamlit Cloud due to the large PyTorch dependency, the model is now accessed via the HuggingFace Inference API. This approach maintains a lightweight deployment.

---

## Why Does it Matter

Energy analysts and traders currently read news manually and form qualitative judgments about market tone. This pipeline automates that process and makes it quantitative. A daily aggregate sentiment score across the major refiners and integrated majors could serve as an early warning signal, flagging when the news narrative diverges from what crack spread levels would suggest. The longer-term extension of this work is a lagged-correlation analysis to determine whether the sentiment signal statistically leads or lags margin movements, thereby establishing whether it has predictive value as a trading signal.

---

## Research Question

**How can unstructured financial news data be transformed into a quantitative market sentiment signal for energy commodity markets, such as crude oil and refined products?**

While futures prices reflect consensus expectations, they often lag behind real-time news. In some instances, refinery margins may appear strong based on structured data, even when news about major refiners is highly negative. This discrepancy is not captured by structured data alone. By extracting sentiment from raw headline text using NLP techniques and displaying it alongside price data, users can directly compare market sentiment with actual price movements.

---

## The Problem with Relying on Prices Alone

Commodity markets, including crude oil and refined products, are inherently forward-looking. Although futures prices reflect consensus expectations, they often lag behind prevailing news narratives. As a result, refinery margins may appear robust in structured data even when news coverage of major refiners is sharply negative, representing a divergence that structured data alone cannot capture.

This project treats financial news as a primary data source and constructs a pipeline that transforms raw text into a meaningful sentiment signal.

---

## NLP Pipeline

### Data Source

Raw headline text is collected using the `yfinance` news API for six major energy sector equities: **VLO, PSX, MPC, XOM, CVX, and COP**. These tickers were chosen because news about them is closely tied to refining margin economics and the crack spread environment, not just general market trends.

Futures tickers (`CL=F`, `RB=F`, `HO=F`) were tested for news sourcing and consistently returned empty feeds. Equity tickers proved to be a reliable proxy for energy sector news volume.

### Text Processing

Each headline is deduplicated by title string before scoring to prevent repeated articles from inflating sentiment counts across multiple ticker feeds. Headlines are subsequently filtered using an energy-specific keyword list; only those containing at least one domain-relevant term (crude, oil, refin, gasoline, diesel, distillate, barrel, crack, WTI, Brent, upstream, downstream, margin, LNG, natural gas, pipeline, energy, fuel, petrochemical, OPEC) proceed to sentiment scoring. This process eliminates general market noise present in energy equity news feeds that does not pertain to refining economics.

### Sentiment Scoring: FinBERT

Sentiment classification uses **FinBERT** (`ProsusAI/finbert`), a BERT-based transformer trained on 10,000 sentences from the Financial PhraseBank dataset. FinBERT was chosen instead of general tools like VADER for two main reasons:

1. **Domain calibration**: FinBERT interprets financial language within its proper context. For example, a headline such as “US Supreme Court to hear Exxon bid for compensation” is recognized as contextually complex, rather than being incorrectly classified as positive due to neutral word valence.
2. **Proven financial NLP benchmark**: FinBERT is a strong benchmark for financial sentiment analysis and demonstrates strong performance on energy-sector equity news.

Each headline is labeled as **Bullish**, **Bearish**, or **Neutral**, along with a confidence score (0.0 to 1.0) indicating how confident the model is. This is different from VADER’s compound score, which ranges from -1.0 to +1.0. For example, a 0.97 Bearish score means the model is 97% confident the headline is bearish, not that it is extremely bearish on a scale.

The pipeline utilizes the HuggingFace Inference API, eliminating the need to load model weights locally and ensuring a lightweight deployment.

---

## Structured Context Layer: 3:2:1 Crack Spread

To facilitate interpretation of the sentiment signal, the pipeline operates alongside a live crack spread monitor. The **3:2:1 crack spread** is the standard metric for US refinery gross margin, representing the profit from converting 3 barrels of crude oil into 2 barrels of gasoline and 1 barrel of distillate.

```
Crack Spread ($/bbl) = (2 × RBOB_bbl + 1 × HO_bbl − 3 × WTI) / 3
```

RBOB Gasoline and Heating Oil are fetched in $/gallon and converted to $/bbl by multiplying by 42 (gallons per barrel).

This structured layer provides essential market context for evaluating the unstructured sentiment signal. Both structured and unstructured layers are necessary, as neither alone offers a comprehensive perspective.

---

## Dashboard

**Live Demo:** [https://energy-sentiment-pipeline.streamlit.app/](https://energy-sentiment-pipeline.streamlit.app/)

The application is developed using Streamlit and operates in real time. All data is retrieved dynamically upon application startup, eliminating the need for pre-run pipelines or stored datasets.

| Section | Description |
|---|---|
| KPI Row | Live crack spread, WTI, RBOB, Heating Oil, and daily change |
| Crack Spread History | Time-series with 30D and 90D moving average overlays |
| Component Prices | WTI, RBOB, and Heating Oil history in $/bbl |
| Recent Daily Data | Last 10 trading days of raw and converted prices |
| Market Sentiment | FinBERT-scored headlines with bar chart and sortable table |

**Cache policy:** Futures prices refresh every 5 minutes. News headlines and sentiment scores refresh every 30 minutes.

---

## Quickstart

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

---

## Tech Stack

Python 3.11 · Streamlit · yfinance · FinBERT (HuggingFace Inference API) · Plotly · Pandas

---

## Limitations and Future Work

- **FinBERT confidence scores do not reflect the strength of the sentiment.** A 0.97 Bullish score means the model is very sure the headline is Bullish, but it does not mean the headline is more bullish than one with a 0.75 Bullish score. It is important to understand this difference when interpreting the scores.
- **The yfinance availability bounds headline volume.** Typically, 10–20 articles per refresh cycle. In a production setting, the pipeline would combine news from several APIs (Bloomberg, Reuters, Refinitiv) to obtain more articles and avoid relying on a single free-tier source.
- **Sentiment without causality.** The pipeline generates a real-time sentiment signal; however, it does not determine whether sentiment leads or follows price changes. The subsequent step involves analyzing the lagged correlation between daily sentiment scores and subsequent changes in the crack spread to assess the predictive capability of the sentiment signal for price movements.