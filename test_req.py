import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

response = requests.get(url)
print("Status Code:", response.status_code)
try:
    models = response.json().get("models", [])
    print("Available Models:")
    for m in models:
        print(f" - {m.get('name')} (Methods: {m.get('supportedGenerationMethods', [])})")
except Exception as e:
    print("Error parsing:", e)
    print(response.text)
