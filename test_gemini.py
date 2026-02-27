import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"API Key Starts With: {api_key[:10]}")

genai.configure(api_key=api_key)
print("Available Models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
