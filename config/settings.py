"""
LISA — Central Settings
========================
Sab config ek jagah. Kuch bhi change karna ho toh sirf yahan aao.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ── Project paths ──────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
VECTORDB_DIR = BASE_DIR / "data" / "vectordb"
MEMORY_DIR   = BASE_DIR / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── LLM Settings ──────────────────────────────────────────────────────
CHAT_MODEL      = "gemini-2.0-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

# ── RAG Settings ──────────────────────────────────────────────────────
RAG_TOP_K           = 4
RAG_DISTANCE_CUTOFF = 0.7

# ── Conversation ──────────────────────────────────────────────────────
MAX_HISTORY_TURNS = 10

# ── Identity ──────────────────────────────────────────────────────────
AGENT_NAME = "Lisa"
USER_NAME  = "Manish"

# ── Modes ─────────────────────────────────────────────────────────────
MODE_PERSONAL     = "personal"
MODE_PROFESSIONAL = "professional"
DEFAULT_MODE      = MODE_PERSONAL