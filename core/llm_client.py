"""
LISA — LLM Client (Groq)
=========================
Groq API use karta hai — free tier: 14,400 requests/day
Model: llama-3.3-70b-versatile — fast + high quality

Agar API switch karna ho toh sirf yahi file badlni hai.
"""

from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
CHAT_MODEL = "llama-3.3-70b-versatile"


def get_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str
) -> str:
    """
    Groq se response lo.
    conversation_history format: [{"role": "user"/"assistant", "content": "..."}]
    """
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]

    # Add history (Groq uses "assistant" not "model")
    for msg in conversation_history:
        # Handle both Gemini format and dict format
        if hasattr(msg, 'role'):
            role    = "assistant" if msg.role == "model" else msg.role
            content = msg.parts[0].text if msg.parts else ""
        else:
            role    = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
            content = msg.get("content", "")
        messages.append({"role": role, "content": content})

    # Add current message
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model       = CHAT_MODEL,
            messages    = messages,
            temperature = 0.85,
            max_tokens  = 500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[LLM] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."