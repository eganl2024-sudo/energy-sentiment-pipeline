# Energy Sector NLP Sentiment Pipeline
### Unstructured Data Analytics | MSBA | University of Notre Dame | Spring 2026

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
Each headline is deduplicated by title string before scoring to prevent the same article from inflating sentiment counts when it appears across multiple ticker feeds.

### Sentiment Scoring: VADER
Sentiment classification uses **VADER (Valence Aware Dictionary and sEntiment Reasoner)**, a lexicon and rule-based model designed specifically for short-form text. VADER was selected over transformer-based alternatives for three reasons:

1. **Calibration for short text** — Financial headlines average 10–15 words. VADER was built and validated on short-form social and news content, where transformers add complexity without proportionate accuracy gains.
2. **No training data required** — A domain-trained model would require a labeled dataset of energy finance headlines, which does not exist in a ready-to-use form. VADER provides a principled baseline without that dependency.
3. **Interpretability** — The compound score (−1.0 to +1.0) is directly interpretable and maps cleanly to a three-class signal.

Each headline receives a compound score classified as:

| Classification | Threshold |
|---|---|
| Bullish | compound ≥ 0.05 |
| Bearish | compound ≤ −0.05 |
| Neutral | −0.05 < compound < 0.05 |

### Output Signal
The pipeline aggregates individual headline scores into portfolio-level summary metrics: average compound score, bullish count, and bearish count across the most recent 15 headlines. This becomes the quantitative sentiment signal displayed alongside live commodity prices.

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

The application is built in Streamlit and deployed live. All data is fetched in real time on startup with no pre-run pipeline or stored data required.

| Section | Description |
|---|---|
| KPI Row | Live crack spread, WTI, RBOB, Heating Oil, and daily change |
| Crack Spread History | Time-series with 30D and 90D moving average overlays |
| Component Prices | WTI, RBOB, and Heating Oil history in $/bbl |
| Recent Daily Data | Last 10 trading days of raw and converted prices |
| Market Sentiment | VADER-scored headlines with bar chart and sortable table |

**Cache policy:** Futures prices refresh every 5 minutes. News headlines and sentiment scores refresh every 30 minutes.

---

## How to Run Locally

```bash
# 1. Create and activate a Python 3.11 virtual environment
py -3.11 -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
streamlit run app/streamlit_app.py
```

---

## Tech Stack

Python 3.11 · Streamlit · yfinance · VADER · Plotly · Pandas

---

## Limitations and Future Work

**VADER is a general-purpose tool.** It was not trained on commodity finance language. Domain-specific terms like "crack spread compression" or "turnaround season" carry no weight in its lexicon. A fine-tuned model such as FinBERT, trained on financial news, would improve scoring precision on energy-specific language and represents the natural next iteration of this pipeline.

**Headline volume is bounded by yfinance availability.** Typically 10–20 articles per refresh cycle. A production pipeline would aggregate from multiple news APIs to increase signal volume and reduce dependence on a single source.

**Sentiment without causality.** This pipeline produces a contemporaneous signal — it does not establish whether sentiment leads or lags price movements. A lagged correlation analysis between the daily aggregate sentiment score and next-day crack spread changes would be the appropriate next analytical step.
