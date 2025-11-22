import sqlite3
from pathlib import Path
import json

DB_PATH = Path(__file__).parent.parent / "vocab_mvp.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS texts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        word TEXT,
        accepted INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def add_text_for_user(user_id, text):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    cur.execute("INSERT INTO texts (user_id, text) VALUES (?,?)", (user_id, text))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), MAX(timestamp) FROM texts WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"texts_count": row[0], "last_text_at": row[1]}
    return {"texts_count": 0, "last_text_at": None}
