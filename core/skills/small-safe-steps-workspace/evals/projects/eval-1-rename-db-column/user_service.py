import sqlite3
from typing import Optional


class UserService:
    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._setup_schema()

    def _setup_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def get_user(self, user_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_user_by_email(self, email: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def create_user(self, username: str, email: str, role: str = "viewer") -> dict:
        cursor = self._conn.execute(
            "INSERT INTO users (username, email, role) VALUES (?, ?, ?)",
            (username, email, role),
        )
        self._conn.commit()
        return self.get_user(cursor.lastrowid)  # type: ignore[arg-type]

    def update_email(self, user_id: int, email: str) -> Optional[dict]:
        self._conn.execute(
            "UPDATE users SET email = ? WHERE id = ?", (email, user_id)
        )
        self._conn.commit()
        return self.get_user(user_id)

    def list_users(self, active_only: bool = True) -> list:
        query = "SELECT * FROM users WHERE 1=1"
        if active_only:
            query += " AND is_active = 1"
        rows = self._conn.execute(query).fetchall()
        return [dict(r) for r in rows]

    def deactivate_user(self, user_id: int) -> bool:
        cursor = self._conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0
