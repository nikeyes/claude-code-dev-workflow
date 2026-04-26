import sqlite3
import json
from datetime import datetime
from typing import Optional


class EventLog:
    """Stores application events. The 'metadata' column is a plain string field
    that was originally used for short notes, but is now being stuffed with
    JSON-encoded dictionaries by callers — without any schema enforcement.
    """

    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._setup_schema()

    def _setup_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                metadata TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def log(self, event_type: str, user_id: Optional[int] = None, metadata: str = "") -> dict:
        cursor = self._conn.execute(
            "INSERT INTO events (event_type, user_id, metadata) VALUES (?, ?, ?)",
            (event_type, user_id, metadata),
        )
        self._conn.commit()
        return self.get_event(cursor.lastrowid)

    def get_event(self, event_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_events_by_type(self, event_type: str) -> list:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE event_type = ? ORDER BY created_at DESC",
            (event_type,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_events_by_user(self, user_id: int) -> list:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_events(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as cnt FROM events").fetchone()
        return row["cnt"]
