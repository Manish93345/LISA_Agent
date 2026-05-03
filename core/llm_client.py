"""
LISA — LLM Client (Multi-Provider)
====================================
Provider change karna ho toh sirf .env mein ek line:
    LLM_PROVIDER=cerebras   # ya groq, claude

Koi aur file nahi badlni.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER   = os.getenv("LLM_PROVIDER", "groq").lower()
MAX_TOKENS = 400


def get_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str
) -> str:
    if PROVIDER == "cerebras":
        return _cerebras(system_prompt, conversation_history, user_message)
    elif PROVIDER == "claude":
        return _claude(system_prompt, conversation_history, user_message)
    else:
        return _groq(system_prompt, conversation_history, user_message)


# ── Groq ──────────────────────────────────────────────────────────────

def _groq(system_prompt, history, user_message) -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            role    = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        r = client.chat.completions.create(
            model       = "llama-3.3-70b-versatile",
            messages    = messages,
            temperature = 0.85,
            max_tokens  = MAX_TOKENS,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM/Groq] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."


# ── Cerebras ──────────────────────────────────────────────────────────

def _cerebras(system_prompt, history, user_message) -> str:
    try:
        from cerebras.cloud.sdk import Cerebras
        client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            role    = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        r = client.chat.completions.create(
            model       = "llama3.1-8b",
            messages    = messages,
            temperature = 0.85,
            max_tokens  = MAX_TOKENS,
        )
        return r.choices[0].message.content.strip()
    except ImportError:
        print("[LLM] cerebras SDK nahi hai — pip install cerebras-cloud-sdk")
        return _groq(system_prompt, history, user_message)  # fallback
    except Exception as e:
        print(f"[LLM/Cerebras] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."


# ── Claude (Anthropic) ────────────────────────────────────────────────

def _claude(system_prompt, history, user_message) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

        messages = []
        for msg in history:
            role    = "assistant" if msg.get("role") in ("model", "assistant") else "user"
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        r = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = MAX_TOKENS,
            system     = system_prompt,
            messages   = messages,
        )
        return r.content[0].text.strip()
    except ImportError:
        print("[LLM] anthropic SDK nahi hai — pip install anthropic")
        return _groq(system_prompt, history, user_message)
    except Exception as e:
        print(f"[LLM/Claude] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."