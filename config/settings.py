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
# ══════════════════════════════════════════════════════════════════

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Chat model — LISA jo use karegi baat karne ke liye
CHAT_MODELS = {
    "groq"     : "llama-3.3-70b-versatile",
    "cerebras" : "llama3.1-8b",
    "claude"   : "claude-haiku-4-5-20251001",
}

# Intent model — action detect karne ke liye (fast + cheap)
INTENT_MODELS = {
    "groq"     : "llama-3.3-70b-versatile",
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