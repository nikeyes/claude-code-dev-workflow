import hashlib
import time
from typing import Optional


class AuthService:
    def __init__(self):
        self._users: dict[str, dict] = {}
        self._sessions: dict[str, dict] = {}
        self._max_session_age = 3600

    def register(self, username: str, password: str) -> bool:
        if username in self._users:
            return False
        self._users[username] = {
            "password_hash": self._hash(password),
            "permissions": ["read"],
            "created_at": time.time(),
        }
        return True

    def login(self, username: str, password: str) -> Optional[str]:
        user = self._users.get(username)
        if user is None:
            return None
        if user["password_hash"] != self._hash(password):
            return None
        session_id = hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()[:32]
        self._sessions[session_id] = {
            "username": username,
            "created_at": time.time(),
        }
        return session_id

    def get_session_user(self, session_id: str) -> Optional[str]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if time.time() - session["created_at"] > self._max_session_age:
            del self._sessions[session_id]
            return None
        return session["username"]

    def has_permission(self, username: str, permission: str) -> bool:
        user = self._users.get(username)
        if user is None:
            return False
        return permission in user["permissions"]

    def grant_permission(self, username: str, permission: str) -> bool:
        user = self._users.get(username)
        if user is None:
            return False
        if permission not in user["permissions"]:
            user["permissions"].append(permission)
        return True

    def _hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
