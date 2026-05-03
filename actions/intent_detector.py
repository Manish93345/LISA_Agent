"""
LISA — Intent Detector
=======================
LLM_PROVIDER ke hisaab se Groq ya Cerebras use karta hai.
Client lazy load hota hai — startup pe error nahi aayega.
"""

import json, os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

INTENT_SYSTEM_PROMPT = """
Tum ek intent detector ho. User ka message analyze karo aur decide karo ki koi action lena hai ya sirf conversation hai.

Agar action hai toh STRICTLY is JSON format mein respond karo (kuch aur mat likho):
{"action": "action_type", "params": {"query": "search term ya app name"}, "confidence": 0.9}

Action types:
- open_website    : koi website open karni ho (youtube.com, instagram.com, etc)
- play_youtube    : YouTube pe gaana/video PLAY karna ho (seedha chalana)
- search_youtube  : YouTube pe sirf search/browse karna ho
- search_spotify  : Spotify pe gaana/artist/playlist
- open_app        : koi app open karni ho
- search_google   : Google pe kuch search karna
- open_folder     : koi folder open karni ho
- open_file       : koi specific file open karni ho
- system_command  : volume, screenshot, brightness
- none            : sirf baat hai, koi action nahi

IMPORTANT — play_youtube vs search_youtube:
- "gaana chala do", "song laga do", "play karo" → play_youtube
- Default gaane ke liye: HAMESHA play_youtube

Agar action nahi hai toh: {"action": "none", "params": {}, "confidence": 1.0}

Examples:
"Arijit Singh ka gaana chala do" → {"action": "play_youtube", "params": {"query": "Arijit Singh best songs"}, "confidence": 0.95}
"thoda Bollywood gaana laga do" → {"action": "play_youtube", "params": {"query": "Bollywood hits songs"}, "confidence": 0.9}
"youtube khol do" → {"action": "open_website", "params": {"query": "youtube.com"}, "confidence": 0.99}
"calculator khol do" → {"action": "open_app", "params": {"query": "calculator"}, "confidence": 0.99}
"D drive khol do" → {"action": "open_folder", "params": {"query": "D:\\"}, "confidence": 0.99}
"screenshot lo" → {"action": "system_command", "params": {"query": "screenshot"}, "confidence": 0.99}
"kaisi ho tum" → {"action": "none", "params": {}, "confidence": 1.0}

SIRF JSON return karo — koi explanation nahi.
"""


def _call_llm(user_message: str) -> str:
    """Provider ke hisaab se LLM call karo."""
    messages = [
        {"role": "system", "content": INTENT_SYSTEM_PROMPT},
        {"role": "user",   "content": user_message}
    ]

    if PROVIDER == "cerebras":
        from cerebras.cloud.sdk import Cerebras
        client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
        r = client.chat.completions.create(
            model       = "llama3.1-8b",
            messages    = messages,
            temperature = 0.1,
            max_tokens  = 100,
        )
        return r.choices[0].message.content.strip()

    else:  # groq default
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        r = client.chat.completions.create(
            model       = "llama-3.3-70b-versatile",
            messages    = messages,
            temperature = 0.1,
            max_tokens  = 100,
        )
        return r.choices[0].message.content.strip()


def detect_intent(user_message: str) -> dict:
    try:
        raw = _call_llm(user_message)

        # Clean markdown if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        if "action" not in result:
            return {"action": "none", "params": {}, "confidence": 1.0}
        return result

    except json.JSONDecodeError:
        return {"action": "none", "params": {}, "confidence": 1.0}
    except Exception as e:
        print(f"[Intent] Error: {e}")
        return {"action": "none", "params": {}, "confidence": 1.0}