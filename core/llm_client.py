"""
LISA — LLM Client (Centralized Multi-Provider)
=================================================
SIRF ye ek file provider logic handle karti hai.
Baaki SAARI files sirf is file ke functions call karengi.

Provider change: .env mein LLM_PROVIDER=claude (ya groq/gemini/cerebras)
Koi aur file nahi badlni.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


# ══════════════════════════════════════════════════════════════════════
#  PUBLIC API — Baaki saari files SIRF ye functions call karengi
# ══════════════════════════════════════════════════════════════════════

def get_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str,
    temperature: float = 0.85,
    max_tokens: int = 400,
) -> str:
    """
    Main chat response — agent.py isko call karta hai.
    Supports: groq, gemini, cerebras, claude
    """
    return _call_provider(
        system_prompt=system_prompt,
        history=conversation_history,
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def call_llm_simple(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.1,
    max_tokens: int = 250,
) -> str:
    """
    Simple single-shot call (no conversation history).
    Intent detection, memory extraction, message drafting — sab isko use karo.
    """
    return _call_provider(
        system_prompt=system_prompt,
        history=[],
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ══════════════════════════════════════════════════════════════════════
#  INTERNAL — Provider dispatch
# ══════════════════════════════════════════════════════════════════════

def _call_provider(
    system_prompt: str,
    history: list,
    user_message: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Route to correct provider. If provider fails, NO fallback — fail clearly."""

    if PROVIDER == "gemini":
        return _gemini(system_prompt, history, user_message, temperature, max_tokens)
    elif PROVIDER == "cerebras":
        return _cerebras(system_prompt, history, user_message, temperature, max_tokens)
    elif PROVIDER == "claude":
        return _claude(system_prompt, history, user_message, temperature, max_tokens)
    elif PROVIDER == "groq":
        return _groq(system_prompt, history, user_message, temperature, max_tokens)
    else:
        return f"Unknown LLM_PROVIDER: '{PROVIDER}'. Options: groq | gemini | cerebras | claude"


# ── Gemini ────────────────────────────────────────────────────────────

def _gemini(system_prompt, history, user_message, temperature, max_tokens) -> str:
    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "GEMINI_API_KEY set nahi hai .env mein."

        client = genai.Client(api_key=api_key)

        contents = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("assistant", "model"):
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        r = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
        )
        return r.text.strip()
    except Exception as e:
        print(f"[LLM/Gemini] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."


# ── Groq ──────────────────────────────────────────────────────────────

def _groq(system_prompt, history, user_message, temperature, max_tokens) -> str:
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "GROQ_API_KEY set nahi hai .env mein."

        client = Groq(api_key=api_key)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            role    = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        r = client.chat.completions.create(
            model       = "llama-3.3-70b-versatile",
            messages    = messages,
            temperature = temperature,
            max_tokens  = max_tokens,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM/Groq] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."


# ── Cerebras ──────────────────────────────────────────────────────────

def _cerebras(system_prompt, history, user_message, temperature, max_tokens) -> str:
    try:
        from cerebras.cloud.sdk import Cerebras

        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            return "CEREBRAS_API_KEY set nahi hai .env mein."

        client = Cerebras(api_key=api_key)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            role    = "assistant" if msg.get("role") == "model" else msg.get("role", "user")
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        r = client.chat.completions.create(
            model       = "llama3.1-8b",
            messages    = messages,
            temperature = temperature,
            max_tokens  = max_tokens,
        )
        return r.choices[0].message.content.strip()
    except ImportError:
        print("[LLM] cerebras SDK nahi hai — pip install cerebras-cloud-sdk")
        return "Cerebras SDK install nahi hai."
    except Exception as e:
        print(f"[LLM/Cerebras] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."


# ── Claude (Anthropic) ────────────────────────────────────────────────

def _claude(system_prompt, history, user_message, temperature, max_tokens) -> str:
    try:
        import anthropic

        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            return "CLAUDE_API_KEY set nahi hai .env mein."

        client = anthropic.Anthropic(api_key=api_key)

        messages = []
        for msg in history:
            role    = "assistant" if msg.get("role") in ("model", "assistant") else "user"
            content = msg.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        r = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = max_tokens,
            system     = system_prompt,
            messages   = messages,
            temperature = temperature,
        )
        return r.content[0].text.strip()
    except ImportError:
        print("[LLM] anthropic SDK nahi hai — pip install anthropic")
        return "Anthropic SDK install nahi hai."
    except Exception as e:
        print(f"[LLM/Claude] Error: {e}")
        return "Yaar abhi kuch technical problem aa gayi, thoda baad mein try karo."