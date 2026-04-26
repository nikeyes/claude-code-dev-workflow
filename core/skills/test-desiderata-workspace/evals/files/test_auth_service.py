"""
Tests for an AuthService (hard — good tests, should score well on all desiderata).
This is the "false positive" eval: the skill should NOT flag major violations.
The tests are well-written across all 12 properties.
Minor note: there's a borderline Predictive gap (brute-force lockout not tested).
"""
import pytest
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import hmac


@dataclass
class User:
    username: str
    password_hash: str
    is_active: bool = True
    failed_attempts: int = 0


class AuthService:
    MAX_FAILED_ATTEMPTS = 5

    def __init__(self):
        self._users: dict[str, User] = {}
        self._sessions: dict[str, str] = {}  # token -> username

    def register(self, username: str, password: str) -> None:
        if username in self._users:
            raise ValueError(f"Username '{username}' already exists")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        self._users[username] = User(username=username, password_hash=pw_hash)

    def login(self, username: str, password: str) -> str:
        user = self._users.get(username)
        if not user or not user.is_active:
            raise PermissionError("Invalid credentials")
        if user.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            raise PermissionError("Account locked")
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if not hmac.compare_digest(user.password_hash, pw_hash):
            user.failed_attempts += 1
            raise PermissionError("Invalid credentials")
        user.failed_attempts = 0
        token = hashlib.sha256(f"{username}:{pw_hash}:session".encode()).hexdigest()
        self._sessions[token] = username
        return token

    def logout(self, token: str) -> None:
        self._sessions.pop(token, None)

    def is_authenticated(self, token: str) -> bool:
        return token in self._sessions

    def deactivate_user(self, username: str) -> None:
        user = self._users.get(username)
        if not user:
            raise KeyError(f"User '{username}' not found")
        user.is_active = False


@pytest.fixture
def service():
    """Fresh AuthService for each test — guarantees isolation."""
    return AuthService()


@pytest.fixture
def registered_user(service):
    service.register("alice", "securepass123")
    return service


class TestRegistration:
    def test_register_new_user_succeeds(self, service):
        service.register("alice", "securepass123")
        # Behavioral: verify the user can subsequently log in
        token = service.login("alice", "securepass123")
        assert service.is_authenticated(token)

    def test_register_duplicate_username_raises(self, service):
        service.register("alice", "securepass123")
        with pytest.raises(ValueError, match="already exists"):
            service.register("alice", "different_password")

    def test_register_short_password_raises(self, service):
        with pytest.raises(ValueError, match="at least 8"):
            service.register("bob", "short")

    def test_register_minimum_length_password_succeeds(self, service):
        service.register("charlie", "12345678")
        token = service.login("charlie", "12345678")
        assert service.is_authenticated(token)


class TestLogin:
    def test_login_valid_credentials_returns_token(self, registered_user):
        token = registered_user.login("alice", "securepass123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_login_wrong_password_raises(self, registered_user):
        with pytest.raises(PermissionError, match="Invalid credentials"):
            registered_user.login("alice", "wrongpassword")

    def test_login_unknown_user_raises(self, service):
        with pytest.raises(PermissionError, match="Invalid credentials"):
            service.login("nobody", "anypassword")

    def test_login_increments_failed_attempts_on_wrong_password(self, registered_user):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrong")
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrong")
        # Behavioral: failed_attempts is observable via lockout behavior
        for _ in range(3):
            try:
                registered_user.login("alice", "wrong")
            except PermissionError:
                pass
        with pytest.raises(PermissionError, match="locked"):
            registered_user.login("alice", "securepass123")

    def test_login_resets_failed_attempts_on_success(self, registered_user):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrong")
        registered_user.login("alice", "securepass123")
        # After successful login, a new wrong attempt should NOT lock the account
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrong_again")
        # Account is not locked after reset
        token = registered_user.login("alice", "securepass123")
        assert registered_user.is_authenticated(token)


class TestLogout:
    def test_logout_invalidates_token(self, registered_user):
        token = registered_user.login("alice", "securepass123")
        assert registered_user.is_authenticated(token)
        registered_user.logout(token)
        assert not registered_user.is_authenticated(token)

    def test_logout_nonexistent_token_does_not_raise(self, service):
        service.logout("nonexistent-token")  # should be a no-op


class TestDeactivation:
    def test_deactivated_user_cannot_login(self, registered_user):
        registered_user.deactivate_user("alice")
        with pytest.raises(PermissionError):
            registered_user.login("alice", "securepass123")

    def test_deactivate_unknown_user_raises(self, service):
        with pytest.raises(KeyError, match="not found"):
            service.deactivate_user("ghost")
