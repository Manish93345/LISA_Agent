"""
LISA — Smart Memory Extractor
================================
Conversation ke end mein ya beech mein Groq/Cerebras se
automatically important facts aur incidents extract karta hai.

Ye agent.py call karega — manually kuch nahi karna.
"""

import json
from config.settings import (
    LLM_PROVIDER, INTENT_MODEL,
    GROQ_API_KEY, CEREBRAS_API_KEY
)
from memory.long_term import save_memory, save_session_summary

EXTRACT_PROMPT = """
Tum ek memory extractor ho. Conversation history padho aur important facts nikalo.

Sirf JSON return karo — koi explanation nahi:
{
  "facts": [
    {"category": "personal", "key": "naam", "value": "Manish"},
    {"category": "academic", "key": "cgpa", "value": "9.24"},
    {"category": "incident", "key": "divya_unfriend_oct2025", "value": "Divya ne Oct 2025 mein unfriend kiya Free Fire mein"}
  ],
  "session_summary": "Manish ne aaj apne CGPA ke baare mein bataya aur Free Fire ki ek incident share ki"
}

Categories:
- personal   : naam, dob, city, relationship info
- academic   : cgpa, semester, college, subjects
- incident   : koi important event jo Manish ne bataya
- preference : pasand/napasand — food, music, hobbies
- goal       : koi future plan ya goal bataya
- health     : health related koi info

Rules:
- Sirf clearly stated facts lo — assume mat karo
- Agar koi important fact nahi hai toh facts = []
- session_summary hamesha 1-2 lines mein likho
- Keys lowercase, underscore se separate karo
- Values concise rakho (max 100 chars)
"""


def _call_llm(conversation_text: str) -> dict:
    messages = [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user",   "content": f"Ye conversation hai:\n\n{conversation_text}"}
    ]

    try:
        if LLM_PROVIDER == "cerebras":
            from cerebras.cloud.sdk import Cerebras
            r = Cerebras(api_key=CEREBRAS_API_KEY).chat.completions.create(
                model=INTENT_MODEL, messages=messages,
                temperature=0.1, max_tokens=400
            )
        else:
            from groq import Groq
            r = Groq(api_key=GROQ_API_KEY).chat.completions.create(
                model=INTENT_MODEL, messages=messages,
                temperature=0.1, max_tokens=400
            )

        raw = r.choices[0].message.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        return json.loads(raw)

    except Exception as e:
        print(f"[Memory Extractor] Error: {e}")
        return {"facts": [], "session_summary": ""}


def extract_and_save(conversation_history: list) -> int:
    """
    Conversation history se facts extract karo aur save karo.

    Returns: kitne facts save hue
    """
    if not conversation_history or len(conversation_history) < 4:
        return 0   # Too short to extract

    # Conversation ko readable text mein convert karo
    lines = []
    for msg in conversation_history:
        role    = "Manish" if msg.get("role") == "user" else "Lisa"
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")

    conversation_text = "\n".join(lines[-20:])  # Last 20 messages

    result = _call_llm(conversation_text)

    saved = 0

    # Facts save karo
    for fact in result.get("facts", []):
        cat = fact.get("category", "").strip()
        key = fact.get("key", "").strip()
        val = fact.get("value", "").strip()
        if cat and key and val:
            save_memory(cat, key, val)
            print(f"  [Memory] Saved: {cat}/{key} = {val}")
            saved += 1

    # Session summary save karo
    summary = result.get("session_summary", "").strip()
    if summary:
        save_session_summary(summary)
        print(f"  [Memory] Session summary saved")

    return saved