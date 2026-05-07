"""
LISA — Intent Detector
=======================
LLM_PROVIDER ke hisaab se Groq ya Cerebras use karta hai.
Client lazy load hota hai — startup pe error nahi aayega.

WHATSAPP MESSAGE DRAFTING:
- Intent detector ab message ko KHUD draft karta hai user ke intent ke base pe
- "Aniket ko bol agar computer graphics ka notes hai toh bhej de" -> proper Hinglish/English message draft
- Confirmation flow agent.py mein handle hota hai
"""

import json, os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

INTENT_SYSTEM_PROMPT = """
Tum ek intent detector ho. User ka message analyze karo aur decide karo ki koi action lena hai ya sirf conversation hai.

Agar action hai toh STRICTLY is JSON format mein respond karo (kuch aur mat likho):
{"action": "action_type", "params": {...}, "confidence": 0.9}

Action types:
- open_website      : koi website open karni ho (youtube.com, instagram.com, etc)
- play_youtube      : YouTube pe gaana/video PLAY karna ho
- search_youtube    : YouTube pe sirf search/browse karna ho
- search_spotify    : Spotify pe gaana/artist/playlist
- open_app          : koi app open karni ho
- search_google     : Google pe kuch search karna
- open_folder       : koi folder open karni ho
- open_file         : koi specific file open karni ho
- find_file         : koi file ya folder DHUNDHNA ho
- whatsapp_message  : WhatsApp pe kisi ko MESSAGE bhejne bole
- whatsapp_file     : WhatsApp pe kisi ko FILE/PHOTO/VIDEO bhejne bole
- system_command    : volume, screenshot, brightness
- none              : sirf baat hai, koi action nahi

══════════════════════════════════════════════════════════════
WHATSAPP MESSAGE DRAFTING — BAHUT IMPORTANT
══════════════════════════════════════════════════════════════

Jab user WhatsApp message bhejne bole, params mein DO cheezein dena:
  1. "contact" : kisko bhejna hai (just naam, lowercase)
  2. "message" : ACTUAL DRAFTED MESSAGE — natural, friendly, recipient ke saath
                 jaisa relation hai uss tone mein

DRAFTING RULES:
- User Manish hai -- message uske POV se likhna hai
- Recipient ke naam/relation ke hisaab se tone:
    * "bro", "yaar", "bhai" wale contacts -> casual Hinglish
    * "mummy", "papa", "mom", "dad" -> respectful but warm
    * "sir", "ma'am", professional contacts -> formal English/Hinglish
- Jo bhi user ne BOLA hai uska intent samjho aur natural message draft karo
- Greeting add karo agar appropriate ho (e.g., "Hey bhai", "Hi Aniket")
- "please" ya "thoda" jaisi soft language use karo jab favor maang rhe ho
- Message end karna ho toh bhi naturally -- emoji avoid karo unless casual

Example drafts:

User: "Aniket ko whatsapp par message kar do ki agar computer graphics ka notes hai uske pass toh mujhe send kar de"
{"action": "whatsapp_message", "params": {"contact": "aniket", "message": "Hey bhai, agar tere paas Computer Graphics ke notes hain to please mujhe bhej de zara, kaafi help ho jayegi."}, "confidence": 0.95}

User: "mummy ko bol do main 9 baje tak ghar aa jaunga"
{"action": "whatsapp_message", "params": {"contact": "mummy", "message": "Mummy main 9 baje tak ghar aa jaunga, thoda late ho rha hoon. Khaana ready rakhna please :)"}, "confidence": 0.9}

User: "Rahul bhai ko message karo ki kal milte hain coffee pe"
{"action": "whatsapp_message", "params": {"contact": "rahul", "message": "Bhai kal milte hain coffee pe, time fix kar lete hain. Tu free kab hai?"}, "confidence": 0.9}

User: "Sir ko bol do ki assignment kal tak submit kar dunga"
{"action": "whatsapp_message", "params": {"contact": "sir", "message": "Good evening Sir, I will submit the assignment by tomorrow. Apologies for the delay."}, "confidence": 0.9}

User: "Aniket NIT ko message karo meeting join kare"
{"action": "whatsapp_message", "params": {"contact": "aniket", "message": "Bhai meeting join kar zara, sab wait kar rhe hain."}, "confidence": 0.95}

══════════════════════════════════════════════════════════════
OTHER ACTIONS
══════════════════════════════════════════════════════════════

play_youtube vs search_youtube:
- "gaana chala do", "song laga do", "play karo" -> play_youtube
- Default gaane ke liye: HAMESHA play_youtube

find_file:
- params mein "folder" aur "file" alag alag dena (jo nahi hai wo "")
- "main_screen": default false. True jab user explicitly bole "mere screen pe"
- "khol do", "dhundh do", "dikha do", "find karo" -> find_file

whatsapp_file:
- "ye photo bhej do aniket ko", "file send karo" -> whatsapp_file
- params mein "contact", "folder", "file"

Other examples:
"Arijit Singh ka gaana chala do" -> {"action": "play_youtube", "params": {"query": "Arijit Singh best songs"}, "confidence": 0.95}
"youtube khol do" -> {"action": "open_website", "params": {"query": "youtube.com"}, "confidence": 0.99}
"calculator khol do" -> {"action": "open_app", "params": {"query": "calculator"}, "confidence": 0.99}
"D drive khol do" -> {"action": "open_folder", "params": {"query": "D:\\\\"}, "confidence": 0.99}
"screenshot lo" -> {"action": "system_command", "params": {"query": "screenshot"}, "confidence": 0.99}
"free fire folder mein divya ki photo dhundho" -> {"action": "find_file", "params": {"folder": "free fire", "file": "divya", "main_screen": false}, "confidence": 0.95}
"free fire folder mein se divya ki photo aniket ko bhej do" -> {"action": "whatsapp_file", "params": {"contact": "aniket", "folder": "free fire", "file": "divya"}, "confidence": 0.95}
"kaisi ho tum" -> {"action": "none", "params": {}, "confidence": 1.0}

Agar action nahi hai toh: {"action": "none", "params": {}, "confidence": 1.0}

SIRF JSON return karo -- koi explanation nahi.
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
            temperature = 0.3,   # thoda creative drafting ke liye
            max_tokens  = 300,
        )
        return r.choices[0].message.content.strip()

    else:  # groq default
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        r = client.chat.completions.create(
            model       = "llama-3.3-70b-versatile",
            messages    = messages,
            temperature = 0.3,
            max_tokens  = 300,
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
