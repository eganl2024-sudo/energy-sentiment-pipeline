import os
import sys
import pandas as pd
import string
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import read_eia_reports, write_eia_sentiment, get_existing_sentiment_dates

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Ensure nltk packages are downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Domain Specific Settings
BULLISH_TERMS = [
    "tight supply", "strong margins", "inventory draw", 
    "crack spread widening", "strong demand", "refinery outage"
]
BEARISH_TERMS = [
    "oversupply", "margin compression", "inventory build", 
    "weak demand", "demand destruction", "capacity expansion"
]
DOMAIN_STOPWORDS = {"oil", "petroleum", "energy", "week", "according", "said", "also", "would", "barrel", "price"}

def compute_net_keyword_score(text, word_count):
    if not text or word_count == 0:
        return 0.0
    text_lower = text.lower()
    
    bullish_count = sum(text_lower.count(term) for term in BULLISH_TERMS)
    bearish_count = sum(text_lower.count(term) for term in BEARISH_TERMS)
    
    return (bullish_count - bearish_count) / word_count

def preprocess_text(text, stop_words, lemmatizer):
    # Lowercase and tokenize simply
    import re
    tokens = re.sub(r'[^a-z\s]', '', text.lower()).split()
    # Remove stopwords and lemmatize
    cleaned = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and t not in DOMAIN_STOPWORDS]
    return cleaned

def run_nlp_pipeline():
    print("🚀 INITIALIZING NLP PIPELINE...")
    
    # 1. Load Data
    reports_df = read_eia_reports()
    if reports_df.empty:
        print("❌ Error: No EIA reports found in DuckDB. Run eia_scraper.py first.")
        return
        
    existing_dates = set(get_existing_sentiment_dates())
    
    # Filter only un-scored reports to respect idempotency
    import numpy as np
    reports_to_score = reports_df[~np.isin(reports_df.index.date, list(existing_dates))].copy()
    total_to_score = len(reports_to_score)
    
    if total_to_score == 0:
        print("Done. 0 new reports scored and saved to eia_sentiment.")
        return
        
    # Setup NLP tools
    analyzer = SentimentIntensityAnalyzer()
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()

    scored_records = []
    processed_docs = [] # For LDA
    
    # PART A: Scoring
    print(f"Scoring sentiment... 0/{total_to_score} reports", end="\r")
    for i, (date, row) in enumerate(reports_to_score.iterrows()):
        text = str(row['raw_text'])
        word_count = int(row['word_count']) if pd.notna(row['word_count']) else 1
        
        # VADER
        vs = analyzer.polarity_scores(text)
        
        # Keyword Score
        net_score = compute_net_keyword_score(text, word_count)
        
        # Preprocess for LDA
        tokens = preprocess_text(text, stop_words, lemmatizer)
        processed_docs.append(tokens)
        
        scored_records.append({
            'report_date': date,
            'compound': vs['compound'],
            'positive': vs['pos'],
            'negative': vs['neg'],
            'neutral': vs['neu'],
            'net_keyword_score': net_score
        })
        
        if (i+1) % 10 == 0 or (i+1) == total_to_score:
            print(f"Scoring sentiment... {i+1}/{total_to_score} reports", end="\r")
            
    print("\n✅ Sentiment Scoring Complete!")
    
    # PART B: LDA Topic Modeling
    print("🧠 Training LDA Topic Model on corpus...")
    
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    # Convert token lists back to strings for CountVectorizer
    joined_docs = [" ".join(tokens) for tokens in processed_docs]
    
    # 1. Use CountVectorizer to build a document-term matrix
    vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=1000, stop_words='english')
    dtm = vectorizer.fit_transform(joined_docs)
    
    # 2. Fit sklearn LDA
    lda = LatentDirichletAllocation(n_components=5, random_state=42)
    lda.fit(dtm)
    
    # 3. For each document get dominant topic
    doc_topics = lda.transform(dtm)
    
    for i in range(len(joined_docs)):
        dominant_topic = int(doc_topics[i].argmax())
        topic_prob = float(doc_topics[i].max())
            
        scored_records[i]['dominant_topic'] = dominant_topic
        scored_records[i]['topic_prob'] = topic_prob

    # 4. Print top 10 words per topic
    print("\n📊 LDA TOPIC SUMMARY:")
    feature_names = vectorizer.get_feature_names_out()
    for i, topic in enumerate(lda.components_):
        top_words = [feature_names[j] for j in topic.argsort()[-10:]]
        print(f"Topic {i}: {top_words}")
    # removed gensim print

    # Save to DuckDB
    final_df = pd.DataFrame(scored_records)
    write_eia_sentiment(final_df)
    
    print(f"\nDone. {total_to_score} reports scored and saved to eia_sentiment")

if __name__ == "__main__":
    run_nlp_pipeline()
