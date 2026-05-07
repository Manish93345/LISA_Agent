"""
LISA — Long Term Memory (SQLite)
==================================
3 types of memory:
  1. facts     — CGPA, DOB, naam, preferences
  2. incidents — important events jo Manish ne bataye
  3. summaries — past session summaries

Usage:
  from memory.long_term import save_memory, get_all_memories
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            summary   TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# ── Facts ──────────────────────────────────────────────────────────────

def save_memory(category: str, key: str, value: str):
    conn = _get_conn()
    conn.execute("""
        INSERT INTO memories (category, key, value, timestamp)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(category, key)
        DO UPDATE SET value=excluded.value, timestamp=excluded.timestamp
    """, (category, key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_all_memories() -> str:
    conn  = _get_conn()
    rows  = conn.execute(
        "SELECT category, key, value FROM memories ORDER BY category, key"
    ).fetchall()

    # Last 5 session summaries
    sums  = conn.execute(
        "SELECT summary, timestamp FROM sessions ORDER BY id DESC LIMIT 5"
    ).fetchall()
    conn.close()

    if not rows and not sums:
        return ""

    lines = ["[Manish ke baare mein important facts — hamesha yaad rakho]\n"]

    if rows:
        current_cat = None
        for cat, key, val in rows:
            if cat != current_cat:
                lines.append(f"\n{cat.upper()}:")
                current_cat = cat
            lines.append(f"  - {key}: {val}")

    if sums:
        lines.append("\n\nPAST SESSIONS (recent):")
        for summary, ts in sums:
            date = ts[:10]
            lines.append(f"\n  [{date}] {summary}")

    return "\n".join(lines)


def list_all() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT category, key, value, timestamp FROM memories"
    ).fetchall()
    conn.close()
    return [{"category": r[0], "key": r[1], "value": r[2], "timestamp": r[3]}
            for r in rows]


def delete_memory(category: str, key: str):
    conn = _get_conn()
    conn.execute("DELETE FROM memories WHERE category=? AND key=?", (category, key))
    conn.commit()
    conn.close()


# ── Session summaries ──────────────────────────────────────────────────

def save_session_summary(summary: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (summary, timestamp) VALUES (?, ?)",
        (summary, datetime.now().isoformat())
    )
    # Sirf last 20 sessions rakho
    conn.execute("""
        DELETE FROM sessions WHERE id NOT IN (
            SELECT id FROM sessions ORDER BY id DESC LIMIT 20
        )
    """)
    conn.commit()
    conn.close()


def get_recent_sessions(n: int = 3) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT summary, timestamp FROM sessions ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return [{"summary": r[0], "timestamp": r[1]} for r in rows]