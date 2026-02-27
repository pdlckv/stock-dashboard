import streamlit as st
import os
from news_fetcher import get_news_for_language, NEWS_CONFIG
from ai_translator import translate_and_summarize, translate_keyword
from news_storage import add_article, get_news_by_language, clear_all_news
from datetime import datetime
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Global Stock News Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117; /* Dark theme */
    }
    
    /* Header styling */
    h1 {
        color: #fca311; /* Vibrant accent color */
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #a0aec0;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }

    /* News Card Styling */
    .news-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .news-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    .news-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.5rem;
        text-decoration: none;
    }
    
    .news-title a {
        color: inherit;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    
    .news-title a:hover {
        color: #63b3ed; /* Link hover color */
    }
    
    .news-meta {
        font-size: 0.9rem;
        color: #718096;
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        padding-top: 0.5rem;
    }
    
    .source-badge {
        background-color: #2b6cb0;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.title("🌐 Global Perspective: Korea Stock Market")
st.markdown('<p class="subtitle">Gain insights from reputable international media across 5 different languages.</p>', unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_FILE = os.path.join(BASE_DIR, "saved_keywords.txt")

def load_keywords():
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return [kw.strip() for kw in content.split(",") if kw.strip()]
    return []

def save_keywords(kws_list):
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        f.write(",".join(kws_list))

def add_keywords(new_kws_str):
    existing = load_keywords()
    new_kws = [kw.strip() for kw in new_kws_str.split(",") if kw.strip()]
    for kw in new_kws:
        if kw not in existing:
            existing.append(kw)
    save_keywords(existing)

def clear_keywords():
    if os.path.exists(KEYWORDS_FILE):
        os.remove(KEYWORDS_FILE)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("Customize your news feed.")
    
    saved_kws = load_keywords()
    
    if saved_kws:
        st.markdown("**Saved Keywords:**")
        # Display keywords as small tags using Streamlit columns and markdown styling
        tags_html = "".join([f'<span style="background-color: #2b6cb0; color: white; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.8rem; margin-right: 0.5rem; display: inline-block; margin-bottom: 0.5rem;">{kw}</span>' for kw in saved_kws])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🗑️ Clear All Keywords", use_container_width=True):
            clear_keywords()
            st.rerun()
            
    st.markdown("---")
    new_keyword = st.text_input("Add New Keyword(s)", placeholder="e.g. 삼성전자, 현대차", help="Comma-separated keywords to add to your saved list.")
    
    if st.button("➕ Add Keywords", use_container_width=True):
        if new_keyword:
            add_keywords(new_keyword)
            st.success("Keywords added!")
            import time
            time.sleep(0.5)
            st.rerun()
        else:
            st.warning("Please enter a keyword to add.")
        
    max_articles = st.slider("Max articles per keyword", min_value=1, max_value=20, value=5, help="Depending on the language, total fetched articles might be multiplied by the number of keywords.")
    
    st.markdown("---")
    if st.button("🚀 기사 수집 및 번역 실행", type="primary", use_container_width=True):
        st.session_state.run_fetch = True
        
    if st.button("🗑️ 보관된 기사 전체 삭제", use_container_width=True):
        clear_all_news()
        st.success("All saved news cleared!")
        import time
        time.sleep(0.5)
        st.rerun()
        
    st.markdown("---")
    st.markdown("### Supported Languages")
    for lang in NEWS_CONFIG.keys():
        st.markdown(f"- {lang}")

# Create tabs for each language
language_names = list(NEWS_CONFIG.keys())
tabs = st.tabs(language_names)

if "run_fetch" not in st.session_state:
    st.session_state.run_fetch = False

# Render content for each tab
for i, tab in enumerate(tabs):
    with tab:
        current_language = language_names[i]
        st.subheader(f"Latest News in {current_language}")
        
        # 1. Fetch and save if button clicked
        if st.session_state.run_fetch:
            with st.spinner(f"Fetching and saving new {current_language} articles..."):
                try:
                    search_keywords = None
                    if saved_kws:
                        translated_keywords = []
                        for kw in saved_kws:
                            translated_kw = translate_keyword(kw, current_language)
                            translated_keywords.append(translated_kw)
                            
                        search_keywords = translated_keywords
                        
                        display_queries = ", ".join(translated_keywords)
                        st.caption(f"Search queries: **{display_queries}**")
                        
                    df = get_news_for_language(current_language, max_items=max_articles, search_keywords=search_keywords)
                    
                    if not df.empty:
                        existing_news = get_news_by_language(current_language)
                        existing_links = {n['link'] for n in existing_news}
                        
                        new_count = 0
                        for index, row in df.iterrows():
                            # Translate and save only if not already saved
                            if row['link'] not in existing_links:
                                ai_result = translate_and_summarize(row['title'], current_language)
                                
                                article_data = {
                                    'title': row['title'],
                                    'link': row['link'],
                                    'published': row['published'],
                                    'source': row['source'],
                                    'kr_title': ai_result.get('translated_title', row['title']),
                                    'kr_summary': ai_result.get('summary', ''),
                                    'language': current_language
                                }
                                
                                if add_article(article_data):
                                    new_count += 1
                        
                        if new_count > 0:
                            st.success(f"Added {new_count} new translated articles!")
                            
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")

        # 2. Display saved articles
        saved_articles = get_news_by_language(current_language)
        if not saved_articles:
            st.info("No saved articles yet. Add keywords and click **'🚀 기사 수집 및 번역 실행'** on the left menu.")
        else:
            st.caption(f"Showing {len(saved_articles)} saved articles.")
            # Display each article as a card
            for row in saved_articles:
                html_card = f"""
                <div class="news-card">
                    <div class="news-title">
                        <a href="{row['link']}" target="_blank">{row['kr_title']}</a>
                    </div>
                    <div style="font-size: 0.95rem; color: #cbd5e0; margin-bottom: 0.5rem; font-style: italic;">
                        원문: {row['title']}
                    </div>
                    <div style="font-size: 0.95rem; color: #e2e8f0; margin-bottom: 0.5rem; background: rgba(0,0,0,0.3); padding: 0.8rem; border-radius: 8px; border-left: 4px solid #fca311;">
                        💡 <strong>AI 요약:</strong> {row['kr_summary']}
                    </div>
                    <div class="news-meta">
                        <span class="source-badge">{row['source']}</span>
                        <span>{row['published']}</span>
                    </div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
                
# Reset fetch state after rendering all tabs so it doesn't loop
if st.session_state.run_fetch:
    st.session_state.run_fetch = False

st.markdown("---")
st.caption("Data sourced from Google News RSS. This is a prototype dashboard.")
