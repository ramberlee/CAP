"""SQLite database layer for the content pipeline."""

import sqlite3
import json
from datetime import datetime
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

CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER REFERENCES topics(id),
    platform TEXT NOT NULL,
    title TEXT,
    body TEXT,
    tags TEXT,
    media_urls TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    publish_result TEXT
);

CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
CREATE INDEX IF NOT EXISTS idx_contents_status ON contents(status);
CREATE INDEX IF NOT EXISTS idx_contents_platform ON contents(platform);
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

    # ---- Contents ----

    def add_content(
        self,
        topic_id: int,
        platform: str,
        title: str,
        body: str,
        tags: list[str] | None = None,
        media_urls: list[str] | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO contents (topic_id, platform, title, body, tags, media_urls) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    topic_id,
                    platform,
                    title,
                    body,
                    json.dumps(tags or [], ensure_ascii=False),
                    json.dumps(media_urls or [], ensure_ascii=False),
                ),
            )
            return cursor.lastrowid

    def get_contents(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        query = "SELECT * FROM contents WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["tags"] = json.loads(d["tags"]) if d["tags"] else []
                d["media_urls"] = json.loads(d["media_urls"]) if d["media_urls"] else []
                results.append(d)
            return results

    def get_content_by_id(self, content_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM contents WHERE id = ?", (content_id,)
            ).fetchone()
            if row:
                d = dict(row)
                d["tags"] = json.loads(d["tags"]) if d["tags"] else []
                d["media_urls"] = json.loads(d["media_urls"]) if d["media_urls"] else []
                return d
            return None

    def update_content(self, content_id: int, **kwargs):
        allowed = {"title", "body", "tags", "media_urls", "status", "published_at", "publish_result"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        # Serialize list/dict fields
        for key in ("tags", "media_urls", "publish_result"):
            if key in updates and isinstance(updates[key], (list, dict)):
                updates[key] = json.dumps(updates[key], ensure_ascii=False)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [content_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE contents SET {set_clause} WHERE id = ?", values)

    def get_stats(self) -> dict:
        with self._connect() as conn:
            topics_total = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            topics_new = conn.execute("SELECT COUNT(*) FROM topics WHERE status = 'new'").fetchone()[0]
            contents_total = conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0]
            contents_draft = conn.execute("SELECT COUNT(*) FROM contents WHERE status = 'draft'").fetchone()[0]
            contents_approved = conn.execute("SELECT COUNT(*) FROM contents WHERE status = 'approved'").fetchone()[0]
            contents_published = conn.execute("SELECT COUNT(*) FROM contents WHERE status = 'published'").fetchone()[0]
            return {
                "topics_total": topics_total,
                "topics_new": topics_new,
                "contents_total": contents_total,
                "contents_draft": contents_draft,
                "contents_approved": contents_approved,
                "contents_published": contents_published,
            }
