import json
import os
import streamlit as st
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_FILE = os.path.join(BASE_DIR, "saved_news.json")

# Initialize Supabase Client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Failed to initialize Supabase: {e}")

# --- Supabase Functions ---

def fetch_supabase_news(language=None):
    if not supabase:
        return []
    try:
        query = supabase.table("saved_news").select("*")
        if language:
            query = query.eq("language", language)
        
        # Order by created_at descending (newest first)
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return []

def add_article_supabase(article_data):
    if not supabase:
        return False
    
    try:
        # Supabase will handle uniqueness if the 'link' column was set to unique in the dashboard.
        # We can just attempt to insert and catch duplicates.
        response = supabase.table("saved_news").insert(article_data).execute()
        return len(response.data) > 0
    except Exception as e:
        # Usually means it caught a unique constraint violation (duplicate link)
        print(f"Error inserting to Supabase (might be duplicate): {e}")
        return False

def clear_all_supabase_news():
    if not supabase:
        return
    try:
        # Supabase doesn't have a simple "delete all" without a filter in the SDK sometimes,
        # so we delete everything where id is not null
        supabase.table("saved_news").delete().neq("id", -1).execute()
    except Exception as e:
        print(f"Error clearing Supabase: {e}")

# --- Local JSON Fallback Functions ---

def load_local_news():
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_local_news(news_list):
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=4)

def add_article_local(article_data):
    news = load_local_news()
    if not any(n['link'] == article_data['link'] for n in news):
        article_data['created_at'] = datetime.now().isoformat()
        news.insert(0, article_data)
        save_local_news(news)
        return True
    return False

def get_local_news_by_language(language):
    news = load_local_news()
    return [n for n in news if n.get('language') == language]

def clear_all_local_news():
    if os.path.exists(NEWS_FILE):
         os.remove(NEWS_FILE)


# --- Main Exported Wrapper Functions ---

def get_news_by_language(language):
    if supabase:
        return fetch_supabase_news(language)
    return get_local_news_by_language(language)

def add_article(article_data):
    """
    article_data must be a dict with:
    link, title, published, source, kr_title, kr_summary, language
    """
    # Remove 'saved_at' if it exists to let Supabase handle 'created_at' default timestamp
    if 'saved_at' in article_data:
        del article_data['saved_at']
        
    if supabase:
        return add_article_supabase(article_data)
    return add_article_local(article_data)

def clear_all_news():
    if supabase:
        clear_all_supabase_news()
    clear_all_local_news()

