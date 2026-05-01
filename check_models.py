"""
Run this first to see which embedding models are available for your API key.
Usage: python check_models.py
"""
from dotenv import load_dotenv
import os
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("\nAvailable embedding models:\n")
for model in client.models.list():
    if "embed" in model.name.lower():
        print(f"  {model.name}")
print()