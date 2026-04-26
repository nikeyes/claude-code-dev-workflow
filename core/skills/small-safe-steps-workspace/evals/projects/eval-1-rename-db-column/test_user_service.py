import pytest
from user_service import UserService


@pytest.fixture
def svc():
    return UserService()


def test_create_and_get_user(svc):
    user = svc.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert user["role"] == "viewer"
    assert user["is_active"] == 1


def test_get_user_by_email(svc):
    svc.create_user("bob", "bob@example.com")
    user = svc.get_user_by_email("bob@example.com")
    assert user is not None
    assert user["username"] == "bob"


def test_get_user_by_email_not_found(svc):
    assert svc.get_user_by_email("nobody@example.com") is None


def test_update_email(svc):
    user = svc.create_user("carol", "carol@example.com")
    updated = svc.update_email(user["id"], "carol.new@example.com")
    assert updated["email"] == "carol.new@example.com"


def test_list_users_active_only(svc):
    svc.create_user("active", "active@example.com")
    u = svc.create_user("inactive", "inactive@example.com")
    svc.deactivate_user(u["id"])
    users = svc.list_users(active_only=True)
    assert len(users) == 1
    assert users[0]["username"] == "active"


def test_list_users_all(svc):
    svc.create_user("active", "active@example.com")
    u = svc.create_user("inactive", "inactive@example.com")
    svc.deactivate_user(u["id"])
    users = svc.list_users(active_only=False)
    assert len(users) == 2


def test_deactivate_user(svc):
    user = svc.create_user("dave", "dave@example.com")
    result = svc.deactivate_user(user["id"])
    assert result is True
    updated = svc.get_user(user["id"])
    assert updated["is_active"] == 0


def test_deactivate_nonexistent_user(svc):
    result = svc.deactivate_user(999)
    assert result is False
