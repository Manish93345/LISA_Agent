"""
LISA — Long Term Memory (SQLite)
==================================
Important facts yaad rakhti hai:
- CGPA, semester info
- Incidents jo Manish ne bataye
- Preferences, important dates
- Koi bhi cheez jo LISA ko "hamesha yaad" rahni chahiye

Usage:
    from memory.long_term import save_memory, get_all_memories, search_memories
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config.settings import MEMORY_DIR

DB_PATH = MEMORY_DIR / "lisa_memory.db"


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            category  TEXT NOT NULL,
            key       TEXT NOT NULL,
            value     TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(category, key)
        )
    """)
    conn.commit()
    return conn


def save_memory(category: str, key: str, value: str):
    """
    Ek fact save karo.
    Example: save_memory("academic", "cgpa", "9.24")
             save_memory("incident", "divya_unfriend", "Divya ne Oct 2025 mein unfriend kiya...")
    """
    conn = _get_conn()
    conn.execute("""
        INSERT INTO memories (category, key, value, timestamp)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(category, key) DO UPDATE SET value=excluded.value, timestamp=excluded.timestamp
    """, (category, key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_all_memories() -> str:
    """
    Saari memories ek formatted string mein return karo.
    Ye LISA ke system prompt mein inject hogi.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT category, key, value FROM memories ORDER BY category, key"
    ).fetchall()
    conn.close()

    if not rows:
        return ""

    lines = ["[Manish ke baare mein important facts — inhe hamesha yaad rakho]\n"]
    current_cat = None
    for cat, key, val in rows:
        if cat != current_cat:
            lines.append(f"\n{cat.upper()}:")
            current_cat = cat
        lines.append(f"  - {key}: {val}")

    return "\n".join(lines)


def search_memories(keyword: str) -> list[dict]:
    """Keyword se memory dhundho."""
    conn  = _get_conn()
    rows  = conn.execute(
        "SELECT category, key, value, timestamp FROM memories WHERE key LIKE ? OR value LIKE ?",
        (f"%{keyword}%", f"%{keyword}%")
    ).fetchall()
    conn.close()
    return [{"category": r[0], "key": r[1], "value": r[2], "timestamp": r[3]} for r in rows]


def delete_memory(category: str, key: str):
    conn = _get_conn()
    conn.execute("DELETE FROM memories WHERE category=? AND key=?", (category, key))
    conn.commit()
    conn.close()


def list_all() -> list[dict]:
    """Sab memories list karo (for debugging)."""
    conn = _get_conn()
    rows = conn.execute("SELECT category, key, value, timestamp FROM memories").fetchall()
    conn.close()
    return [{"category": r[0], "key": r[1], "value": r[2], "timestamp": r[3]} for r in rows]