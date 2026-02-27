import feedparser
import pandas as pd
from urllib.parse import quote
from dateutil import parser
import pytz
import streamlit as st

def get_google_news_rss_url(keyword: str, language_code: str, country_code: str) -> str:
    """
    Generates the Google News RSS URL for a given keyword, language, and country.
    """
    encoded_keyword = quote(keyword)
    return f"https://news.google.com/rss/search?q={encoded_keyword}&hl={language_code}&gl={country_code}&ceid={country_code}:{language_code}"


def format_date_kst(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = parser.parse(date_str)
        kst = pytz.timezone('Asia/Seoul')
        dt_kst = dt.astimezone(kst)
        return dt_kst.strftime("%Y-%m-%d %H:%M:%S KST")
    except Exception:
        return date_str

def fetch_news(keyword: str, language_code: str, country_code: str, max_items: int = 10) -> pd.DataFrame:
    """
    Fetches news from Google News RSS and returns a Pandas DataFrame.
    """
    url = get_google_news_rss_url(keyword, language_code, country_code)
    feed = feedparser.parse(url)
    
    articles = []
    for entry in feed.entries[:max_items]:
        pub_date = entry.published if hasattr(entry, 'published') else ''
        pub_date_kst = format_date_kst(pub_date)
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': pub_date_kst,
            'source': entry.source.title if hasattr(entry, 'source') else 'Unknown'
        })
        
    return pd.DataFrame(articles)

# Configuration mapping for our 5 languages
NEWS_CONFIG = {
    "English": {
        "language_code": "en-US",
        "country_code": "US",
        "keywords": ["South Korea stock market", "KOSPI", "Korean equities"]
    },
    "Japanese (日本語)": {
        "language_code": "ja",
        "country_code": "JP",
        "keywords": ["韓国株", "韓国株式市場", "コスピ"]
    },
    "Chinese (中文)": {
        "language_code": "zh-CN", # or zh-TW depending on preference, sticking to CN for now
        "country_code": "CN",
        "keywords": ["韩国股市", "韩国KOSPI", "韩国经济"]
    },
    "Spanish (Español)": {
        "language_code": "es",
        "country_code": "ES",
        "keywords": ["Bolsa de Corea del Sur", "Economía surcoreana"]
    },
    "Arabic (العربية)": {
        "language_code": "ar",
        "country_code": "AE", # Using UAE as default Arabic region
        "keywords": ["سوق الأسهم الكورية", "الاقتصاد الكوري"]
    },
    "German (Deutsch)": {
        "language_code": "de",
        "country_code": "DE",
        "keywords": ["Südkoreanischer Aktienmarkt", "KOSPI"]
    },
    "French (Français)": {
        "language_code": "fr",
        "country_code": "FR",
        "keywords": ["Bourse sud-coréenne", "KOSPI"]
    }
}

@st.cache_data(ttl=1800, show_spinner=False)
def get_news_for_language(language_name: str, max_items: int = 10, search_keywords: list = None) -> pd.DataFrame:
    """
    Wrapper function to fetch news based on the predefined language configuration.
    It aggregates news for all keywords of that language, or the provided search_keywords.
    """
    if language_name not in NEWS_CONFIG:
        return pd.DataFrame() # empty df
        
    config = NEWS_CONFIG[language_name]
    all_articles_df = pd.DataFrame()
    
    keywords_to_search = search_keywords if search_keywords else config['keywords']
    
    for keyword in keywords_to_search:
        df = fetch_news(keyword, config['language_code'], config['country_code'], max_items=max_items)
        all_articles_df = pd.concat([all_articles_df, df], ignore_index=True)
        
    # Drop duplicates based on the link
    if not all_articles_df.empty:
         all_articles_df.drop_duplicates(subset=['link'], inplace=True)
         
    return all_articles_df

if __name__ == "__main__":
    # Test fetcher
    print("Testing English Feed...")
    df = get_news_for_language("English", max_items=2)
    print(df.head())
