import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import date, timedelta
import os
import sys
import re
from dateutil import parser

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import write_eia_reports, get_existing_eia_dates

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_with_retry(url, retries=3, backoff_factor=2):
    """Fetches a URL with exponential backoff for resilience."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                return None  # Legitimate miss, no need to retry
        except requests.RequestException:
            pass
        if attempt < retries - 1:
            time.sleep(backoff_factor)
    return None

def extract_text_from_report(html_content):
    """Strips HTML and returns the clean text paragraphs."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try multiple common article container selectors for EIA
    container = (soup.find('div', class_='pagemain') or 
                 soup.find('div', id='main-content') or 
                 soup.find('article') or 
                 soup.find('div', class_='article'))
    
    if not container:
        container = soup
        
    paragraphs = container.find_all('p')
    
    clean_paragraphs = []
    for p in paragraphs:
        text = p.get_text(separator=' ', strip=True)
        if len(text.split()) > 10:
            clean_paragraphs.append(text)
            
    return "\n\n".join(clean_paragraphs)

def get_wednesday_dates_range(start_date, end_date):
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() == 2:  # Wednesday
            dates.append(current)
        current += timedelta(days=1)
    return dates

def scrape_twip_history(existing_dates):
    reports = []
    start_date = date(2022, 1, 1)
    end_date = date(2023, 12, 31)
    dates = get_wednesday_dates_range(start_date, end_date)
    
    for d in dates:
        # YYMMDD
        yymmdd = d.strftime('%y%m%d')
        url = f"https://www.eia.gov/petroleum/weekly/archive/{d.year}/{yymmdd}/includes/analysis_print.php"
        
        if d in existing_dates:
            print(f"[TWIP] ⏭️ {d} — Already in DB")
            continue
            
        res = fetch_with_retry(url)
        if not res:
            print(f"[TWIP] ⏭️ {d} — Skipped (404 / Error)")
            time.sleep(1)
            continue
            
        raw_text = extract_text_from_report(res.content)
        word_count = len(raw_text.split())
        
        if word_count > 0:
            reports.append({
                'report_date': pd.to_datetime(d),
                'url': url,
                'raw_text': raw_text,
                'word_count': word_count
            })
            print(f"[TWIP] ✅ {d} — saved ({word_count} words)")
        else:
            print(f"[TWIP] ⏭️ {d} — Skipped (Empty DOM text)")
            
        time.sleep(1)
        
    return reports

def scrape_today_in_energy(existing_dates):
    reports = []
    base_url = "https://www.eia.gov/todayinenergy/"
    archive_url = f"{base_url}archive.php"
    
    res = fetch_with_retry(archive_url)
    if not res:
        print("❌ Failed to load Today in Energy archive.")
        return reports
        
    soup = BeautifulSoup(res.content, 'html.parser')
    all_links = soup.find_all('a', href=True)
    
    target_terms = ['petroleum', 'crude', 'refin']
    
    article_links = []
    for a in all_links:
        href = a['href'].lower()
        text = a.get_text(strip=True).lower()
        if 'detail.php' in href and any(term in href or term in text for term in target_terms):
            full_url = href if href.startswith('http') else base_url + a['href']
            # Attempt to find a date near the link (e.g., in a sibling or parent tag)
            parent_text = a.parent.get_text(strip=True)
            try:
                # Naive date extraction from text like "August 24, 2024" 
                # Just take the first few words of the parent text which might be the date
                date_match = re.search(r'[A-Z][a-z]+\s\d{1,2},\s202[45]', parent_text)
                if date_match:
                    r_date = parser.parse(date_match.group()).date()
                else:
                    r_date = None
            except:
                r_date = None
                
            article_links.append((r_date, full_url))
            
    # Deduplicate URLS
    seen_urls = set()
    unique_links = []
    for d, url in article_links:
        if url not in seen_urls:
            unique_links.append((d, url))
            seen_urls.add(url)
            
    # Need a fallback date if we didn't parse one. Just use today as a fallback for sorting/id.
    # In reality we want the actual date. Let's try to extract from the article page if missing.
    
    for r_date, url in unique_links:
        # We need a date for DB. If we didn't get it from archive, we'll try from page.
        res = fetch_with_retry(url)
        if not res:
            continue
            
        page_soup = BeautifulSoup(res.content, 'html.parser')
        
        if not r_date:
            date_div = page_soup.find('div', class_='date') or page_soup.find('span', class_='date')
            if date_div:
                try:
                    r_date = parser.parse(date_div.get_text(strip=True)).date()
                except:
                    pass
        
        if not r_date:
            # If still no date, skip
            continue
            
        # Only want 2024-2025
        if r_date.year not in [2024, 2025]:
            continue
            
        if r_date in existing_dates:
            print(f"[TIE]  ⏭️ {r_date} — Already in DB")
            continue
            
        raw_text = extract_text_from_report(res.content)
        word_count = len(raw_text.split())
        
        if word_count > 0:
            reports.append({
                'report_date': pd.to_datetime(r_date),
                'url': url,
                'raw_text': raw_text,
                'word_count': word_count
            })
            print(f"[TIE]  ✅ {r_date} — saved ({word_count} words)")
            
        time.sleep(1)
        
    return reports

def scrape_eia():
    print("📡 INIT HYBRID EIA COMMENTARY SCRAPING...")
    existing_dates = get_existing_eia_dates()
    
    # 1. Source 1: TWIP (2022-2023)
    print("\n--- Scraping Source 1: This Week in Petroleum (2022-2023) ---")
    twip_reports = scrape_twip_history(existing_dates)
    
    # 2. Source 2: Today In Energy (2024-Present)
    print("\n--- Scraping Source 2: Today In Energy (2024-Present) ---")
    tie_reports = scrape_today_in_energy(existing_dates)
    
    all_reports = twip_reports + tie_reports
    
    if all_reports:
        df = pd.DataFrame(all_reports)
        # Handle duplicates on report_date by keeping last
        df = df.drop_duplicates(subset=['report_date'], keep='last')
        write_eia_reports(df)
        print(f"\nComplete: {len(df)} reports saved to eia_reports")
    else:
        print("\nComplete: 0 new reports saved to eia_reports")

if __name__ == "__main__":
    scrape_eia()
