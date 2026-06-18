# Energy Sentiment NLP Pipeline — Interview Prep

## 30 Seconds

I built a live NLP sentiment pipeline that pulls energy sector headlines from six major oil and gas company feeds, pre-filters on energy keywords, and scores them with FinBERT via the HuggingFace Inference API. I used FinBERT over VADER because it's fine-tuned on financial and SEC filings — it understands energy-specific language. The key design decision was running inference through the API rather than locally, which let me deploy on Streamlit Cloud without pulling in PyTorch, which would have exceeded the memory limit and killed the deployment.

---

## 60 Seconds

I built a live NLP pipeline for energy sector news sentiment, wired to real-time crack spread data. The system pulls headlines from six companies — Valero, Phillips 66, Marathon, ExxonMobil, Chevron, and ConocoPhillips — applies an energy keyword pre-filter to eliminate off-topic noise, then scores each headline using FinBERT through the HuggingFace Inference API.

The reason I chose FinBERT over VADER, which is the simpler choice, is that FinBERT is pre-trained on a general corpus and then fine-tuned on financial news and SEC filings. It handles energy-specific language better — a headline like 'refinery margins compress on crude spike' will get the valence right in a way a general lexicon won't.

The API-over-local decision was forced: deploying transformers locally on Streamlit Cloud requires PyTorch, which pushed the memory footprint over the limit and broke deployment during initial testing. The API call adds latency but keeps the app stateless and deployable.

An unexpected finding: FinBERT classifies 'refinery maintenance' headlines as Bearish — which makes sense linguistically — but in supply/demand terms, refinery outages tighten product supply and should be Bullish for crack spreads. The model reads sentiment in text, not market mechanics.

---

## 120 Seconds

I built a live NLP sentiment pipeline that classifies energy sector news headlines and overlays sentiment signals on crack spread data. Here are the key technical decisions and what I found.

On model selection: I chose FinBERT over VADER. VADER is a general-purpose sentiment lexicon that works well for social media text but wasn't trained on financial language. FinBERT is BERT fine-tuned on financial news and SEC filings, so it handles the specific vocabulary of energy markets better — 'margin compression,' 'crack spread widening,' 'downstream headwinds' all have valences that a general model mis-classifies. FinBERT's confidence scores are softmax probabilities across Positive, Negative, and Neutral classes, so I sign them: Bullish equals positive score, Bearish equals negative score, Neutral equals zero. That lets me compute a signed average that's actually interpretable, unlike the raw confidence which is always positive.

On deployment architecture: I run inference through the HuggingFace Inference API rather than a local model. The reason is purely practical — Streamlit Cloud has a memory ceiling and pulling in PyTorch exceeded it during initial testing and killed the deployment. The API adds about five seconds of latency on cold start due to model loading, which I handle with a three-attempt retry on 503 responses. That's a production pattern, not a workaround.

The keyword pre-filter matters more than it seems. I pull headlines from tickers like VLO and XOM, but these companies generate a lot of news that has nothing to do with refining margins — shareholder meetings, political donations, diversity initiatives. Without the keyword filter, roughly 40 percent of headlines that come through are irrelevant to crack spreads. The filter checks for terms like crude, refin, crack, margin, distillate, and barrel — energy-specific enough to remove noise without filtering out genuinely relevant news.

Two things surprised me. First, FinBERT consistently classifies 'unplanned refinery maintenance' and 'turnaround' headlines as Bearish — which is correct from a text sentiment perspective, but directionally wrong for crack spreads. Refinery outages tighten product supply and are actually Bullish for margins. The model reads language, not market mechanics, and that's a real limitation of applying general financial NLP to commodity markets. Second, even with a clean FinBERT pipeline and a proper signed sentiment aggregation, the daily sentiment signal is remarkably noisy — most observations cluster between -0.1 and +0.1, with large spikes almost always tied to macro events like Fed rate decisions or geopolitical shocks rather than refinery-specific news. The signal-to-noise ratio in public headlines is lower than I expected, which actually reinforces why the Granger test in the Refinery Engine comes back non-significant.
