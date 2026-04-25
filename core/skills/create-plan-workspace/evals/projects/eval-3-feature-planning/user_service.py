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

    def get_user_by_username(self, username: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
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
        return self.get_user(cursor.lastrowid)

    def update_user(self, user_id: int, **fields) -> Optional[dict]:
        allowed = {"username", "email", "role", "is_active"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_user(user_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        self._conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?", values
        )
        self._conn.commit()
        return self.get_user(user_id)

    def delete_user(self, user_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM users WHERE id = ?", (user_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def list_users(self, role: Optional[str] = None, active_only: bool = True) -> list:
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        if role:
            query += " AND role = ?"
            params.append(role)
        if active_only:
            query += " AND is_active = 1"
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_user_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        return row["cnt"]
