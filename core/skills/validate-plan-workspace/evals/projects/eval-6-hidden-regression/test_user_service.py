from user_service import UserService


def test_create_and_get_user():
    svc = UserService()
    svc.create_user("u1", "Alice", "alice@example.com")
    user = svc.get_user("u1")
    assert user["name"] == "Alice"


def test_get_user_returns_none_for_missing():
    svc = UserService()
    assert svc.get_user("nonexistent") is None


def test_get_user_uses_cache():
    svc = UserService()
    svc.create_user("u2", "Bob", "bob@example.com")
    svc.get_user("u2")
    svc.store._users.clear()
    cached = svc.get_user("u2")
    assert cached["name"] == "Bob"


def test_update_user():
    svc = UserService()
    svc.create_user("u3", "Carol", "carol@example.com")
    updated = svc.update_user("u3", name="Caroline")
    assert updated["name"] == "Caroline"


def test_update_invalidates_cache():
    svc = UserService()
    svc.create_user("u4", "Dave", "dave@example.com")
    svc.get_user("u4")
    svc.update_user("u4", name="David")
    user = svc.get_user("u4")
    assert user["name"] == "David"


def test_delete_user():
    svc = UserService()
    svc.create_user("u5", "Eve", "eve@example.com")
    svc.delete_user("u5")
    assert svc.get_user("u5") is None


def test_list_users():
    svc = UserService()
    svc.create_user("u6", "Frank", "frank@example.com")
    svc.create_user("u7", "Grace", "grace@example.com")
    users = svc.list_users()
    assert len(users) == 2


def test_search_by_email():
    svc = UserService()
    svc.create_user("u8", "Hank", "hank@example.com")
    found = svc.search_by_email("hank@example.com")
    assert found["name"] == "Hank"


def test_search_by_email_not_found():
    svc = UserService()
    assert svc.search_by_email("nobody@example.com") is None
