# 🛢️ Refinery Arbitrage Engine
**Real-Time Commodity Margin & Equity Valuation Monitor**

**[🚀 Launch Live Dashboard →](https://refinery-arbitrage-engine-uturqbhqngbykahhfonr6k.streamlit.app/)**

### 📊 Business Context
Refineries profit from the **"Crack Spread"**—the economic differential between crude oil input costs and refined product output prices (Gasoline & Diesel). This platform models the industry-standard **3:2:1 Crack Spread** to quantify the "Physical Reality" of the energy market and correlates it to downstream equity valuations.

**The "So What?" for Investors:**
When physical margins compress, refinery valuations contract. This engine answers: *If the crack spread drops by $5/bbl today, what is the implied EBITDA impact for Valero (VLO)?*

---

### 🚀 Key Intelligence Modules

#### 1. The Physical Arbitrage Monitor (`spread_calculator.py`)
* **Logic:** Implements the **3:2:1 Mass Balance** formula: `(2 * Gasoline + 1 * Distillate - 3 * Crude) / 3`.
* **Unit Operations:** Automatically handles unit conversion (Gallons $\to$ Barrels) and aligns Futures contract expirations.
* **Alpha:** Identifies "margin expansion" events in real-time.

#### 2. Valuation Sensitivity Model (`valuation_model.py`)
* **Goal:** Quantify **Operational Leverage**.
* **Methodology:** A "DCF-Lite" engine that simulates EBITDA shocks based on spread volatility.
* **Scenario:** *User Input:* "What if margins crash to $15/bbl?" $\to$ *Output:* "VLO Share Price implied impact: -$12.45".

#### 3. Statistical Correlation Engine (`correlation_engine.py`)
* **Hypothesis:** Downstream equities are mathematically coupled to physical margins.
* **Proof:** Calculates **90-Day Rolling Correlations** to visualize "Regime Changes".
* **Metrics:** Real-time **R-Squared ($R^2$)**, **Z-Score**, and **Percentile Rank**.

#### 4. Automated Reporting (`report_generator.py`)
* **Output:** Auto-generates executive briefings summarizing current market breadth, margin percentile, and valuation impact.

---

### 🛠️ Technical Stack
* **Core Logic:** Python (Pandas, NumPy, SciPy)
* **Visualization:** Streamlit, Plotly Interactive
* **Statistics:** Statsmodels (OLS Regression), Rolling Window Analysis
* **Data Pipeline:** `yfinance` API (Real-time Futures: CL=F, RB=F, HO=F, NG=F)

---

### 💻 Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Refinery-Arbitrage-Engine.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the data pipeline
python src/data_pipeline.py
python src/spread_calculator.py

# 4. Launch the dashboard
streamlit run app/streamlit_app.py
```

---

### 🔑 Key Findings (2020-2025 Data)
- **Average Gross Margin:** $23.80/bbl (3:2:1 crack spread)
- **Current State:** ~$22.56/bbl (77th percentile - historically high)
- **VLO Correlation:** 0.26 (daily returns) vs 0.11 (price levels)
  - *Insight:* VLO reacts to short-term margin volatility but long-term equity is driven more by capital allocation (buybacks) than spot spreads.
- **Valuation Impact:** $5 spread change ≈ **$4.5B annualized EBITDA impact** for Valero.

---

### 📸 Dashboard Preview

#### Full Analytics Platform
![Dashboard Overview](assets/screenshots/dashboard_overview.png)
*Integrated analytics platform featuring auto-generated executive briefing, real-time margin monitoring, and sensitivity analysis.*

#### Correlation Methodology
![Correlation Analysis](assets/screenshots/correlation_analysis.png)
*Dual-methodology approach comparing Price Level vs. Return correlations.*

#### Valuation Sensitivity
![Valuation Model](assets/screenshots/valuation_model.png)
*Interactive scenario testing with Bear/Base/Bull presets.*

---

### ⚖️ Disclaimer
This project is for educational and portfolio purposes only. It uses free-tier data (Yahoo Finance) which may have delays. Not financial advice.

**Built by Liam Egan** | [LinkedIn](https://linkedin.com/in/liam-egan) | [GitHub](https://github.com/ljegan)
