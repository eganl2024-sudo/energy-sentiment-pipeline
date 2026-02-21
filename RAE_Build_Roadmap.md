# Refinery Arbitrage Engine — Class Project Build Roadmap
**Unstructured Data Analytics | Liam Egan | Spring 2026**

> **How to use this doc:** Work through each step sequentially with your coding agent. Each step includes the exact context to paste in, what files to hand over, the specific task, and what "done" looks like before you move on.

---

## STEP 1 — Pin All Dependencies in `requirements.txt`
**Time estimate:** 15–20 minutes | **Risk if skipped:** Engine breaks silently on next deploy

### Context to give your agent:
```
I have a Python/Streamlit financial analytics app called the Refinery-Arbitrage-Engine.
The current requirements.txt has unpinned dependencies (e.g., just "pandas" with no version).
This is a critical deployment risk. I need you to:
1. Read the current requirements.txt I'm pasting below.
2. Identify every package listed.
3. Rewrite the file with exact pinned versions compatible with Python 3.11,
   prioritizing: pandas==2.2.2, numpy==1.26.4, streamlit==1.35.0,
   yfinance==0.2.40, statsmodels==0.14.2, scikit-learn==1.4.2,
   plotly==5.22.0, scipy==1.13.1.
4. Add a comment block at the top noting the Python version and pin date.
```

### Files to hand over:
- `requirements.txt` (paste current contents)

### What "done" looks like:
- Every package has `==` with an explicit version number
- A comment block at top: `# Pinned: 2026-02-20 | Python 3.11`
- No package listed twice

---

## STEP 2 — Migrate CSV Storage to SQLite via DuckDB
**Time estimate:** 45–60 minutes | **Risk if skipped:** I/O drag freezes dashboard under load

### Context to give your agent:
```
My Refinery-Arbitrage-Engine currently reads and writes market data to flat CSV files:
- data/raw/market_data.csv
- data/processed/spread_data.csv

This disk I/O approach is slow and not scalable. I need you to:
1. Read src/data_pipeline.py (pasted below).
2. Replace all pd.read_csv() and .to_csv() calls with DuckDB read/write operations.
3. Create a new file: src/db.py that initializes a local DuckDB database at
   data/market_data.duckdb with two tables: raw_market_data and processed_spread_data.
4. Modify data_pipeline.py to use src/db.py for all reads and writes.
5. Add an append-only write pattern (INSERT OR IGNORE based on date index) so we
   don't duplicate rows on each run.
6. Keep all existing function signatures intact so nothing downstream breaks.
```

### Files to hand over:
- `src/data_pipeline.py` (paste full file)
- `src/db.py` (doesn't exist yet — agent creates it)

### What "done" looks like:
- `src/db.py` exists and handles all DB init + connection logic
- `data_pipeline.py` has zero `.to_csv()` or `pd.read_csv()` calls
- The DuckDB file is created on first run if it doesn't exist
- Old CSV files can be deleted without breaking anything

---

## STEP 3 — Move Heavy Calculations Upstream Out of Streamlit
**Time estimate:** 45–60 minutes | **Risk if skipped:** Dashboard freezes on every user interaction

### Context to give your agent:
```
My Streamlit app (app/streamlit_app.py) currently runs pandas/numpy regression and
correlation calculations on every user interaction (every slider move, every tab switch).
This causes UI lag and will freeze with larger datasets.

I need you to:
1. Read both files pasted below (streamlit_app.py and src/spread_calculator.py).
2. Identify every Pandas/NumPy/statsmodels computation block inside streamlit_app.py
   (look for rolling(), corr(), polyfit(), OLS(), z-score math, percentile math).
3. Move each of those computation blocks into src/spread_calculator.py as standalone
   functions that return DataFrames or dicts.
4. In streamlit_app.py, replace the computation blocks with calls to those new functions.
5. Wrap the function calls in streamlit_app.py with @st.cache_data so results are
   cached and only recomputed when the underlying data changes.
6. Leave all chart rendering (st.plotly_chart, st.metric, etc.) in streamlit_app.py.
```

### Files to hand over:
- `app/streamlit_app.py` (paste full file)
- `src/spread_calculator.py` (paste full file)

### What "done" looks like:
- `streamlit_app.py` contains zero raw pandas computation — only `st.*` calls and function imports
- All new functions in `spread_calculator.py` have docstrings
- `@st.cache_data` decorator is on every data-loading call in Streamlit
- Dashboard still renders identically to before

---

## STEP 4 — Build the EIA Weekly Report Scraper
**Time estimate:** 60–90 minutes | **This IS the class project core**

### Context to give your agent:
```
I'm building a text analytics layer on top of a refinery margin analytics engine for a
graduate Unstructured Data Analytics class. The research question is:
"Does sentiment from EIA weekly petroleum commentary predict crack spread movements?"

I need you to build a scraper: src/eia_scraper.py that:
1. Fetches the EIA "This Week in Petroleum" archive page:
   https://www.eia.gov/petroleum/weekly/archive/
2. Parses the page to extract links to individual weekly report pages (going back 2 years).
3. For each report page, extracts the main article text body (strip HTML, navigation,
   headers, footers — plain text paragraphs only).
4. Returns a pandas DataFrame with columns: [report_date, url, raw_text, word_count].
5. Saves the result to the DuckDB database in a new table: eia_reports.
6. Includes retry logic (3 attempts, 2 second backoff) and rate limiting
   (1 second sleep between requests — be polite to EIA servers).
7. Skips reports already in the database (check by report_date before fetching).

Use: requests, BeautifulSoup4, pandas. Do NOT use Selenium.
```

### Files to hand over:
- `src/db.py` (from Step 2 — agent needs to know the DB schema)

### What "done" looks like:
- Running `python src/eia_scraper.py` populates `eia_reports` table in DuckDB
- DataFrame shape is ~100+ rows (2 years of weekly reports)
- `raw_text` column has clean prose (no HTML tags, no nav elements)
- Script is idempotent — safe to run multiple times without duplicating rows

---

## STEP 5 — Build the Sentiment Scoring & Topic Modeling Pipeline
**Time estimate:** 60–90 minutes | **This is the NLP layer**

### Context to give your agent:
```
I have a DuckDB table called eia_reports with columns [report_date, url, raw_text, word_count].
I need to build an NLP pipeline: src/nlp_pipeline.py that:

PART A — Sentiment Scoring:
1. Load all rows from eia_reports.
2. For each row, run VADER sentiment analysis on the raw_text.
3. Store compound, positive, negative, neutral scores in new columns.
4. Also run a domain-specific keyword score: count occurrences of bullish terms
   ("tight supply", "strong margins", "inventory draw", "crack spread widening") and
   bearish terms ("oversupply", "margin compression", "inventory build", "weak demand").
   Net keyword score = (bullish_count - bearish_count) / word_count.
5. Write results back to DuckDB in a new table: eia_sentiment.

PART B — LDA Topic Modeling:
1. Preprocess text: lowercase, remove stopwords (use NLTK), lemmatize.
2. Build a gensim LDA model with n_topics=5 on the full corpus.
3. For each document, extract the dominant topic and its probability.
4. Add dominant_topic and topic_prob columns to eia_sentiment table.
5. Print the top 10 words per topic for manual interpretation.

Use: vaderSentiment, gensim, nltk, sklearn. All should be added to requirements.txt.
```

### Files to hand over:
- `src/db.py` (for DB connection)
- `src/eia_scraper.py` (so agent understands the data structure)

### What "done" looks like:
- `eia_sentiment` table exists in DuckDB with sentiment scores + topic assignments
- Running `python src/nlp_pipeline.py` completes without errors
- Top words per topic are printed and make intuitive sense (e.g., Topic 0: inventory, crude, barrel, storage...)
- No row in `eia_reports` is left unscored

---

## STEP 6 — Run Granger Causality Test (Sentiment → Spread)
**Time estimate:** 30–45 minutes | **This is the academic "finding"**

### Context to give your agent:
```
I have two DuckDB tables:
- eia_sentiment: columns [report_date, compound_sentiment, net_keyword_score, dominant_topic]
- processed_spread_data: columns [date, crack_spread, spread_zscore, spread_percentile]

I need you to build an analysis script: src/causality_analysis.py that:
1. Merges the two tables on date (use nearest-date join — EIA reports weekly, spread data daily).
2. Tests whether EIA sentiment Granger-causes crack spread movements using
   statsmodels.tsa.stattools.grangercausalitytests at lags [1, 2, 3, 4] weeks.
3. Also runs the reverse: does spread Granger-cause sentiment? (bidirectional test)
4. Prints a clean results table: lag | F-stat | p-value | significant? (p<0.05)
5. Computes rolling 90-day Pearson correlation between compound_sentiment and crack_spread.
6. Saves the merged dataset to DuckDB as a new table: sentiment_spread_merged.
7. Saves the rolling correlation series to: sentiment_spread_rolling_corr.

Include a brief interpretation comment block at the top of the output explaining
what Granger causality means in plain English for a non-technical reader.
```

### Files to hand over:
- `src/db.py`
- `src/spread_calculator.py` (for context on spread columns)

### What "done" looks like:
- Script runs and prints a formatted results table
- At least one lag level shows a statistically meaningful result (or the null finding is itself interesting)
- `sentiment_spread_merged` exists in DuckDB — this powers the dashboard tab in Step 7
- You understand what the output means well enough to explain it in a 3-minute presentation

---

## STEP 7 — Add Sentiment & Topics Tab to the Streamlit Dashboard
**Time estimate:** 45–60 minutes | **This makes it visual and presentable**

### Context to give your agent:
```
My Streamlit dashboard (app/streamlit_app.py) currently shows crack spread analytics.
I need to add a new tab called "📰 Sentiment & Topics" that visualizes the NLP layer.

The new tab should contain:
1. A dual-axis time series chart (plotly):
   - Left Y axis: EIA compound sentiment score (line, blue)
   - Right Y axis: 3:2:1 crack spread (line, orange)
   - X axis: date
   - Title: "EIA Sentiment vs. Crack Spread (2-Year History)"

2. A rolling correlation chart (plotly line chart):
   - 90-day rolling Pearson correlation between sentiment and spread
   - Horizontal reference line at 0
   - Title: "Rolling 90-Day Sentiment-Spread Correlation"

3. A topic summary table (st.dataframe):
   - Columns: Topic Number | Top Keywords | % of Reports | Avg Sentiment
   - One row per LDA topic

4. A metrics row at the top (st.metric):
   - Current week's sentiment score
   - 4-week average sentiment
   - Granger causality result (significant at lag X? Yes/No)

All data should be loaded from DuckDB using src/db.py.
All computations should use @st.cache_data.
```

### Files to hand over:
- `app/streamlit_app.py` (current version)
- `src/db.py`

### What "done" looks like:
- New "📰 Sentiment & Topics" tab appears in the dashboard
- All 4 elements render without errors
- Charts are properly labeled with titles, axis labels, and legends
- Tab loads in under 3 seconds (cached data)

---

## STEP 8 — Add Cyclical Multiples + Economic Run-Cut Logic
**Time estimate:** 45–60 minutes | **This is the "wow factor" for recruiters**

### Context to give your agent:
```
My valuation model (src/valuation_model.py) has two known limitations I need to fix:

FIX 1 — Cyclical EV/EBITDA Multiple:
Currently the model uses a hardcoded 6.5x EV/EBITDA multiple regardless of margin environment.
Replace this with a dynamic multiple that adjusts based on the crack spread's Z-score:

  Z-score >= 2.0  (very high margins, peak cycle):  multiple = 4.5x
  Z-score 1.0–2.0 (above average):                  multiple = 5.5x
  Z-score -1.0–1.0 (normal):                        multiple = 6.5x
  Z-score -1.0 to -2.0 (below average):             multiple = 7.5x
  Z-score <= -2.0 (trough):                         multiple = 8.5x

Implement this as a function: get_cyclical_multiple(zscore: float) -> float
Add it to src/valuation_model.py and wire it into the existing EBITDA impact calculation.

FIX 2 — Economic Run-Cut Floor:
Currently the model assumes full throughput (e.g., 2.9M bpd for VLO) even if the
simulated crack spread falls below the operating breakeven (~$7.50/bbl).

Add a function: apply_run_cut(shock_spread: float, base_throughput: float,
                               opex_breakeven: float = 7.50) -> float
Logic:
  - If shock_spread > opex_breakeven: return base_throughput (no cut)
  - If shock_spread between 0 and opex_breakeven: reduce throughput by 20%
  - If shock_spread <= 0: reduce throughput by 40%

Wire this into the scenario testing loop so throughput_bpd becomes dynamic.

In streamlit_app.py, add a callout box (st.info) that appears when a run cut is triggered,
explaining: "⚠️ Run cut applied: margins below breakeven. Throughput reduced by X%."
```

### Files to hand over:
- `src/valuation_model.py` (paste full file)
- `app/streamlit_app.py` (current version, post Step 7)

### What "done" looks like:
- `get_cyclical_multiple()` returns different values for different Z-score inputs (test with a quick unit test)
- `apply_run_cut()` reduces throughput correctly at the boundary cases
- The Bear scenario now shows a lower throughput than Base/Bull when margins dip below breakeven
- The `st.info` callout appears in the Bear scenario and disappears in Base/Bull
- Share price impact in the Bear case is now more pessimistic than before (it should be — lower throughput + compressed multiple)

---

## Final Checklist Before Submission

- [ ] `requirements.txt` fully pinned
- [ ] All data flows through DuckDB (no CSV reads/writes)
- [ ] Streamlit has zero raw computation (all `@st.cache_data`)
- [ ] EIA scraper populates 100+ weekly reports
- [ ] Sentiment + LDA scores stored for every report
- [ ] Granger causality results documented (even null finding is valid)
- [ ] Dashboard has Sentiment & Topics tab
- [ ] Cyclical multiple + run-cut logic live in valuation model
- [ ] GitHub repo README updated to describe the NLP layer
- [ ] You can explain the research question and findings in 3 minutes

---

## The Presentation Narrative (Use This Framing)

*"This project builds on a financial analytics platform I've been developing since early 2026, which is deployed live and monitors real-time refinery margin data. For this class, I extended the platform with a text analytics layer — scraping two years of EIA weekly petroleum commentary — motivated by a simple but real finance question: does institutional energy sentiment lead or lag the price signals my engine already tracks? The answer has implications for whether alternative text data can add alpha on top of a quantitative momentum signal."*

That framing makes this a **portfolio piece with a track record**, not just a homework assignment.
