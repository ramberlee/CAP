"""SQLite database layer for the content pipeline."""

import sqlite3
from pathlib import Path
from typing import Optional


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    heat INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new'
);

CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
"""


class Database:
    def __init__(self, db_path: str = "db/pipeline.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(DB_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ---- Topics ----

    def add_topic(self, source: str, title: str, url: str = "", heat: int = 0) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO topics (source, title, url, heat) VALUES (?, ?, ?, ?)",
                (source, title, url, heat),
            )
            return cursor.lastrowid

    def get_topics(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM topics WHERE status = ? ORDER BY heat DESC, created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM topics ORDER BY heat DESC, created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def topic_exists(self, title: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM topics WHERE title = ?", (title,)
            ).fetchone()
            return row is not None

    def update_topic_status(self, topic_id: int, status: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE topics SET status = ? WHERE id = ?", (status, topic_id)
            )

    def get_stats(self) -> dict:
        with self._connect() as conn:
            topics_total = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            topics_new = conn.execute("SELECT COUNT(*) FROM topics WHERE status = 'new'").fetchone()[0]
            return {
                "topics_total": topics_total,
                "topics_new": topics_new,
            }
