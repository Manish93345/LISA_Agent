"""
LISA — Central Settings
========================
SIRF YE FILE CHANGE KARO — kuch aur nahi.
API, model, limits — sab kuch yahan se control hota hai.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
VECTORDB_DIR = BASE_DIR / "data" / "vectordb"
MEMORY_DIR   = BASE_DIR / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CLAUDE_API_KEY   = os.getenv("CLAUDE_API_KEY")

# ══════════════════════════════════════════════════════════════════
#  YE 3 LINES CHANGE KARO — PROVIDER, CHAT MODEL, INTENT MODEL
#  Options: groq | gemini | cerebras | claude
# ══════════════════════════════════════════════════════════════════

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Chat model — LISA jo use karegi baat karne ke liye
CHAT_MODELS = {
    "groq"     : "llama-3.3-70b-versatile",
    "gemini"   : "gemini-2.0-flash",
    "cerebras" : "llama3.1-8b",
    "claude"   : "claude-haiku-4-5-20251001",
}

# Intent model — action detect karne ke liye (fast + cheap)
INTENT_MODELS = {
    "groq"     : "llama-3.3-70b-versatile",
    "gemini"   : "gemini-2.0-flash",
    "cerebras" : "llama3.1-8b",
    "claude"   : "claude-haiku-4-5-20251001",
}

CHAT_MODEL   = CHAT_MODELS.get(LLM_PROVIDER, "llama-3.3-70b-versatile")
INTENT_MODEL = INTENT_MODELS.get(LLM_PROVIDER, "llama-3.3-70b-versatile")

# ══════════════════════════════════════════════════════════════════

# ── RAG Settings ──────────────────────────────────────────────────────
RAG_TOP_K           = 3
RAG_DISTANCE_CUTOFF = 0.75
EMBEDDING_MODEL     = "gemini-embedding-001"

# ── Conversation ──────────────────────────────────────────────────────
MAX_HISTORY_TURNS = 8
MAX_TOKENS        = 400

# ── Identity ──────────────────────────────────────────────────────────
AGENT_NAME = "Lisa"
USER_NAME  = "Manish"

# ── Modes ─────────────────────────────────────────────────────────────
MODE_PERSONAL     = "personal"
MODE_PROFESSIONAL = "professional"
DEFAULT_MODE      = MODE_PERSONAL


# ── Voice Settings ─────────────────────────────────────────────────────
WHISPER_MODEL_SIZE = "medium"

# gTTS language — "hi" handles Hinglish best
# "hi" = Hindi/Hinglish | "en" = English
TTS_LANG = "en"

# Speed — gTTS mein slow=False means normal speed
TTS_RATE = "+0%"

# ffplay path (backup playback)
FFPLAY_PATH = r"C:\ffmpeg\bin\ffplay.exe"

LISA_DESKTOP_INDEX = 2   # Desktop 3 = index 2

# ── WhatsApp Automation ────────────────────────────────────────────────
# Lisa ka dedicated Edge profile -- primary Edge ko disturb nahi karega.
# Note: Edge ek hi profile 2 instances mein run nahi karne deta, isi liye
# Lisa apna alag profile rakhti hai. Same WhatsApp account hi rahega
# (ek baar QR scan, fir permanent).
WHATSAPP_PROFILE_DIR  = str(BASE_DIR / "data" / "whatsapp_profile")
WHATSAPP_URL          = "https://web.whatsapp.com"
WHATSAPP_LOAD_TIMEOUT = 60          # seconds for first load (badhaya naya UI slow hai)
WHATSAPP_SIDEBAR_WAIT = 8           # seconds — sidebar fully render hone ka wait
WHATSAPP_ACTION_DELAY = (0.5, 1.5)  # human-like delay
WHATSAPP_CONFIRM_SEND = True        # True = Lisa pehle confirmation maangti hai

# Headless mode -- TRUE = invisible, lekin QR scan tricky
# Recommended: False
WHATSAPP_HEADLESS = False
