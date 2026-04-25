from user_service import UserService


class TestUserService:
    def setup_method(self):
        self.service = UserService()

    def test_create_user(self):
        user = self.service.create_user("alice", "alice@example.com")
        assert user["username"] == "alice"
        assert user["email"] == "alice@example.com"
        assert user["role"] == "viewer"
        assert user["is_active"] == 1

    def test_get_user(self):
        created = self.service.create_user("bob", "bob@example.com")
        fetched = self.service.get_user(created["id"])
        assert fetched["username"] == "bob"

    def test_get_user_not_found(self):
        assert self.service.get_user(999) is None

    def test_get_user_by_username(self):
        self.service.create_user("charlie", "charlie@example.com")
        user = self.service.get_user_by_username("charlie")
        assert user["email"] == "charlie@example.com"

    def test_update_user(self):
        created = self.service.create_user("dave", "dave@example.com")
        updated = self.service.update_user(created["id"], role="admin")
        assert updated["role"] == "admin"

    def test_delete_user(self):
        created = self.service.create_user("eve", "eve@example.com")
        assert self.service.delete_user(created["id"]) is True
        assert self.service.get_user(created["id"]) is None

    def test_list_users_active_only(self):
        self.service.create_user("frank", "frank@example.com")
        inactive = self.service.create_user("grace", "grace@example.com")
        self.service.update_user(inactive["id"], is_active=0)
        active = self.service.list_users(active_only=True)
        assert len(active) == 1
        assert active[0]["username"] == "frank"

    def test_list_users_by_role(self):
        self.service.create_user("heidi", "heidi@example.com", role="admin")
        self.service.create_user("ivan", "ivan@example.com", role="viewer")
        admins = self.service.list_users(role="admin")
        assert len(admins) == 1
        assert admins[0]["username"] == "heidi"

    def test_get_user_count(self):
        assert self.service.get_user_count() == 0
        self.service.create_user("judy", "judy@example.com")
        self.service.create_user("karl", "karl@example.com")
        assert self.service.get_user_count() == 2
