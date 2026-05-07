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
- open_website      : koi website open karni ho (youtube.com, instagram.com, etc)
- play_youtube      : YouTube pe gaana/video PLAY karna ho (seedha chalana)
- search_youtube    : YouTube pe sirf search/browse karna ho
- search_spotify    : Spotify pe gaana/artist/playlist
- open_app          : koi app open karni ho
- search_google     : Google pe kuch search karna
- open_folder       : koi folder open karni ho
- open_file         : koi specific file open karni ho
- find_file         : koi file ya folder DHUNDHNA ho (file khojo, image dhundho, folder mein file dhundho, file dikhao)
- whatsapp_message  : WhatsApp pe kisi ko MESSAGE bhejne bole
- whatsapp_file     : WhatsApp pe kisi ko FILE/PHOTO/VIDEO bhejne bole
- system_command    : volume, screenshot, brightness
- none              : sirf baat hai, koi action nahi

IMPORTANT — play_youtube vs search_youtube:
- "gaana chala do", "song laga do", "play karo" → play_youtube
- Default gaane ke liye: HAMESHA play_youtube

IMPORTANT — find_file:
- Jab user koi file ya folder dhundhne/kholne bole (fuzzy name se) → find_file
- params mein "folder" aur "file" dono alag alag dena — jo nahi hai wo empty string "" rakhna
- "main_screen" param: default false. Sirf true karo jab user EXPLICITLY bole "mere screen pe", "main desktop pe", "yahi pe kholo", "mere saamne kholo"
- "khol do", "dhundh do", "dikha do", "find karo" → find_file
- Agar user sirf folder ka naam bole bina exact path ke → find_file (not open_folder)
- open_folder SIRF tab use karo jab user seedha "D drive khol do" ya exact known folder bole

IMPORTANT -- whatsapp_message:
- Jab user WhatsApp pe kisi ko message bhejne bole -> whatsapp_message
- params mein "contact" (kisko bhejun) aur "message" (kya bhejun) dena
- "message" mein user ne jo intent bataya hai uska NATURAL message likho -- English ya Hinglish mein
- e.g., "Aniket ko bol meeting join kare" -> message = "Meeting join kar bhai"
- "mummy ko bol main aa rha hoon" -> message = "Main aa rha hoon mummy"
- "send karo", "bhej do", "message karo", "bol do", "likh do" -> whatsapp_message

IMPORTANT -- whatsapp_file:
- Jab user WhatsApp pe kisi ko FILE/PHOTO/IMAGE/VIDEO bhejne bole -> whatsapp_file
- params mein "contact", "folder" (hint), "file" (hint) dena
- file_finder ka same logic: folder aur file hint alag alag
- "ye photo bhej do", "file send karo", "image whatsapp karo" -> whatsapp_file

Agar action nahi hai toh: {"action": "none", "params": {}, "confidence": 1.0}

Examples:
"Arijit Singh ka gaana chala do" -> {"action": "play_youtube", "params": {"query": "Arijit Singh best songs"}, "confidence": 0.95}
"thoda Bollywood gaana laga do" -> {"action": "play_youtube", "params": {"query": "Bollywood hits songs"}, "confidence": 0.9}
"youtube khol do" -> {"action": "open_website", "params": {"query": "youtube.com"}, "confidence": 0.99}
"calculator khol do" -> {"action": "open_app", "params": {"query": "calculator"}, "confidence": 0.99}
"D drive khol do" -> {"action": "open_folder", "params": {"query": "D:\\"}, "confidence": 0.99}
"screenshot lo" -> {"action": "system_command", "params": {"query": "screenshot"}, "confidence": 0.99}
"free fire folder mein divya ki photo dhundho" -> {"action": "find_file", "params": {"folder": "free fire", "file": "divya", "main_screen": false}, "confidence": 0.95}
"downloads mein resume dhundho" -> {"action": "find_file", "params": {"folder": "downloads", "file": "resume", "main_screen": false}, "confidence": 0.9}
"mera resume kholo" -> {"action": "find_file", "params": {"folder": "", "file": "resume", "main_screen": false}, "confidence": 0.85}
"movies folder khol do" -> {"action": "find_file", "params": {"folder": "movies", "file": "", "main_screen": false}, "confidence": 0.9}
"free fire folder mere screen pe khol do" -> {"action": "find_file", "params": {"folder": "free fire", "file": "", "main_screen": true}, "confidence": 0.95}
"Aniket ko message karo ki meeting join kare" -> {"action": "whatsapp_message", "params": {"contact": "aniket", "message": "Meeting join kar bhai"}, "confidence": 0.95}
"mummy ko bol do ki main aa rha hoon" -> {"action": "whatsapp_message", "params": {"contact": "mummy", "message": "Main aa rha hoon mummy"}, "confidence": 0.9}
"Rahul ko whatsapp karo ki kal milte hain" -> {"action": "whatsapp_message", "params": {"contact": "rahul", "message": "Kal milte hain bro"}, "confidence": 0.9}
"free fire folder mein se divya ki photo aniket ko bhej do" -> {"action": "whatsapp_file", "params": {"contact": "aniket", "folder": "free fire", "file": "divya"}, "confidence": 0.95}
"downloads mein se resume ankit ko whatsapp karo" -> {"action": "whatsapp_file", "params": {"contact": "ankit", "folder": "downloads", "file": "resume"}, "confidence": 0.9}
"ye wali photo mummy ko send karo" -> {"action": "whatsapp_file", "params": {"contact": "mummy", "folder": "", "file": "photo"}, "confidence": 0.85}
"kaisi ho tum" -> {"action": "none", "params": {}, "confidence": 1.0}

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
            temperature = 0.1,
            max_tokens  = 200,
        )
        return r.choices[0].message.content.strip()

    else:  # groq default
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        r = client.chat.completions.create(
            model       = "llama-3.3-70b-versatile",
            messages    = messages,
            temperature = 0.1,
            max_tokens  = 200,
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