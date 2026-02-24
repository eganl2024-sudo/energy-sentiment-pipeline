# Energy Sector NLP Sentiment Pipeline
### Unstructured Data Analytics | MSBA | University of Notre Dame | Spring 2026

---

## What is the Project

This project builds a live NLP sentiment pipeline for the energy sector. It scrapes real-time financial news headlines from six major energy equity tickers (VLO, PSX, MPC, XOM, CVX, COP) via the yfinance API, filters them for energy relevance, and scores each headline using FinBERT — a transformer model pre-trained on financial news. The output is a quantitative sentiment signal displayed alongside a live 3:2:1 crack spread monitor, enabling side-by-side comparison of what the market *says* versus what prices *show*.

---

## What is the Problem

Financial news is unstructured, continuous, and full of noise. Commodity markets like crude oil and refined products are forward-looking — futures prices reflect consensus expectations, but they lag the real-time narrative. A refinery margin can look healthy on paper while the news flow surrounding major refiners has turned sharply negative, a divergence that structured price data alone cannot capture.

The challenge was threefold: first, the project originally relied on stagnant, pre-downloaded CSV files for commodity price data — a structured but static foundation that made the dashboard immediately outdated the moment it was deployed. Second, extracting a clean, energy-relevant signal from noisy news feeds that mix sector-specific coverage with general market content required deliberate filtering. Third, scoring that text accurately enough to be useful proved harder than expected — general-purpose sentiment tools like VADER misclassify financial language, scoring a headline about an Exxon court case as falsely positive simply because it contains no negative words, not because it is actually bullish for refining margins.

The project required solving all three: replacing static data with live API feeds, filtering noise from signal, and upgrading the NLP layer to a domain-trained model.

---

## How Was It Solved

News is sourced from equity tickers rather than futures tickers, because futures tickers (CL=F, RB=F, HO=F) consistently returned empty news feeds during testing. An energy-specific keyword filter (crude, oil, refin, gasoline, diesel, distillate, barrel, crack, WTI, Brent, upstream, downstream, margin, LNG, natural gas, pipeline, OPEC) eliminates off-topic articles before any scoring occurs.

For sentiment scoring, VADER was replaced with FinBERT (ProsusAI/finbert), a BERT-based transformer pre-trained on 10,000 labeled sentences from the Financial PhraseBank. Rather than loading model weights locally — which caused Streamlit Cloud to fail during deployment due to the size of the PyTorch dependency — the model is called via the HuggingFace Inference API, keeping the deployment footprint minimal.

---

## Why Does it Matter

Energy analysts and traders currently read news manually and form qualitative judgments about market tone. This pipeline automates that process and makes it quantitative. A daily aggregate sentiment score across the major refiners and integrated majors could serve as an early warning signal — flagging when the news narrative is diverging from what crack spread levels would suggest. The longer-term extension of this work is a lagged correlation analysis to determine whether the sentiment signal statistically leads or lags margin movements, which would establish whether it has predictive value as a trading signal.

---

## Research Question

**How can unstructured financial news data be transformed into a quantitative market sentiment signal for the energy sector?**

Financial news headlines are produced continuously and contain real-time market opinion that does not appear in any structured data feed. This project builds a pipeline that ingests raw, unstructured headline text, applies NLP sentiment scoring, and surfaces a quantitative signal alongside structured commodity market data — enabling side-by-side comparison of what the market *says* versus what prices *show*.

---

## The Problem with Relying on Prices Alone

Commodity markets like crude oil and refined products are forward-looking. Futures prices reflect consensus expectations, but they lag the narrative. A refinery margin can look healthy on paper while the news flow surrounding major refiners has turned sharply negative — a divergence that structured data alone cannot capture.

This project treats financial news as a primary data source, not an afterthought, and builds the transformation pipeline from raw text to a usable signal.

---

## NLP Pipeline

### Data Source
Raw headline text is collected via the `yfinance` news API across six major energy sector equities: **VLO, PSX, MPC, XOM, CVX, COP**. These tickers were deliberately chosen because their equity coverage directly reflects refining margin economics — news about these companies is structurally linked to the crack spread environment, not just general market noise.

Futures tickers (`CL=F`, `RB=F`, `HO=F`) were tested for news sourcing and consistently returned empty feeds. Equity tickers proved the reliable proxy for energy sector news volume.

### Text Processing
Each headline is deduplicated by title string before scoring to prevent the same article from inflating sentiment counts when it appears across multiple ticker feeds. Headlines are then passed through an energy-specific keyword filter — only headlines containing at least one domain-relevant term (crude, oil, refin, gasoline, diesel, distillate, barrel, crack, WTI, Brent, upstream, downstream, margin, LNG, natural gas, pipeline, energy, fuel, petrochemical, OPEC) proceed to scoring. This eliminates general market noise that appears in energy equity news feeds but has no bearing on refining economics.

### Sentiment Scoring: FinBERT
Sentiment classification uses **FinBERT** (`ProsusAI/finbert`), a BERT-based transformer pre-trained on 10,000 sentences from the Financial PhraseBank dataset. FinBERT was selected over general-purpose tools like VADER for two reasons:

1. **Domain calibration** — FinBERT understands financial language in context. A headline like "US Supreme Court to hear Exxon bid for compensation" is correctly read as contextually complex rather than scored as falsely positive due to neutral word valence.
2. **Proven financial NLP benchmark** — FinBERT is the established baseline for financial sentiment classification and is directly appropriate for energy sector equity news.

Each headline receives a classification of **Bullish**, **Bearish**, or **Neutral**, paired with a **confidence score (0.0–1.0)** representing the model's certainty in that classification. This is distinct from VADER's compound score (-1.0 to +1.0) — a score of 0.97 Bearish means the model is 97% confident the headline is bearish, not that it is "very bearish" on a continuous scale.

The pipeline is called via the HuggingFace Inference API, eliminating the need to load model weights locally and keeping the deployment footprint minimal.

---

## Structured Context Layer: 3:2:1 Crack Spread

To make the sentiment signal interpretable, the pipeline runs alongside a live crack spread monitor. The **3:2:1 crack spread** is the industry benchmark for US refinery gross margin, representing the profit from processing 3 barrels of crude oil into 2 barrels of gasoline and 1 barrel of distillate.
```
Crack Spread ($/bbl) = (2 × RBOB_bbl + 1 × HO_bbl − 3 × WTI) / 3
```

RBOB Gasoline and Heating Oil are fetched in $/gallon and converted to $/bbl by multiplying by 42 (gallons per barrel).

This structured layer provides the factual market context against which the unstructured sentiment signal can be evaluated. The combination is the point — neither layer is sufficient alone.

---

## Dashboard

**Live Demo:** [https://energy-sentiment-pipeline.streamlit.app/](https://energy-sentiment-pipeline.streamlit.app/)

The application is built in Streamlit and deployed live. All data is fetched in real time on startup with no pre-run pipeline or stored data required.

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

**FinBERT confidence scores are not sentiment magnitude scores.** A 0.97 Bullish score means the model is highly confident in its Bullish classification — it does not mean the headline is "more bullish" than a 0.75 Bullish headline. Interpreting the score axis requires understanding this distinction.

**Headline volume is bounded by yfinance availability.** Typically 10–20 articles per refresh cycle. A production pipeline would aggregate from multiple news APIs (Bloomberg, Reuters, Refinitiv) to increase signal volume and reduce dependence on a single free-tier source.

**Sentiment without causality.** This pipeline produces a contemporaneous signal — it does not establish whether sentiment leads or lags price movements. A lagged correlation analysis between the daily aggregate sentiment score and next-day crack spread changes would be the appropriate next analytical step and the natural extension of this work.
