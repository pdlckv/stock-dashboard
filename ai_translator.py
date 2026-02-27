import os
import time
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini model
# We use gemini-1.5-flash as it's fast and cost-effective for translation and summarization.
try:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    # Using gemini-2.5-flash as it is supported by the provided API key
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=api_key)
except Exception as e:
    print(f"Failed to initialize Gemini: {e}")
    llm = None


@st.cache_data(ttl=3600, show_spinner=False)
def translate_and_summarize(title: str, language: str) -> dict:
    """
    Translates a news title to Korean and provides a 1-2 sentence summary context.
    Since we only have the title and RSS snippet, the summary will be brief.
    """
    if not llm:
        return {"translated_title": f"[번역 불가] {title}", "summary": "API 키를 설정해주세요 (.env 파일에 GEMINI_API_KEY 입력)"}
        
    if language == "English":
        source_lang = "English"
    elif "Japanese" in language:
        source_lang = "Japanese"
    elif "Chinese" in language:
        source_lang = "Chinese"
    elif "Spanish" in language:
        source_lang = "Spanish"
    elif "Arabic" in language:
        source_lang = "Arabic"
    else:
         source_lang = "Unknown"

    prompt = f"""
    You are a professional financial news translator and analyst.
        
    Source Language: {source_lang}
    Original Title: {title}
    
    Task 1: Translate the exact title accurately into natural Korean suitable for a professional economic news dashboard. Keep it concise as a headline.
    Task 2: Based solely on the title, write a 1-2 sentence brief summary in Korean explaining the likely core context or market implication of this news.
    
    Output strictly in the following JSON format:
    {{
        "translated_title": "번역된 제목",
        "summary": "간략한 요약..."
    }}
    """
    
    try:
        # Requesting JSON from the model
        response = llm.invoke(prompt)
        content = response.content
        print(f"Raw AI Output: {content}")
        
        # Simple extraction of JSON
        import json
        # Cleanup potential markdown ticks from the output
        clean_content = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError as je:
             print(f"JSON Parsing Error: {je} from {clean_content}")
             return {"translated_title": title, "summary": "요약 파싱 실패"}
            
    except Exception as e:
        print(f"Error during AI translation: {e}")
        return {"translated_title": title, "summary": "번역/요약 중 오류 발생"}

@st.cache_data(ttl=3600*24, show_spinner=False)
def translate_keyword(keyword: str, target_language: str) -> str:
    """
    Translates a user-provided search keyword into the target language for RSS fetching.
    """
    if not llm:
        return keyword
    
    lang_map = {
        "English": "English",
        "Japanese (日本語)": "Japanese",
        "Chinese (中文)": "Chinese (Simplified)",
        "Spanish (Español)": "Spanish",
        "Arabic (العربية)": "Arabic",
        "German (Deutsch)": "German",
        "French (Français)": "French"
    }
    
    dest_lang = lang_map.get(target_language, "English")
    
    prompt = f"""
    Translate the following search keyword into {dest_lang}.
    It will be used to search for financial or stock market news.
    Return ONLY the translated keyword string, nothing else. Do not add quotes or markdown.
    
    Keyword: {keyword}
    """
    
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error translating keyword: {e}")
        return keyword
