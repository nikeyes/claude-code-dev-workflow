from cache import LRUCache


class UserStore:
    def __init__(self):
        self._users = {}

    def save(self, user_id, data):
        self._users[user_id] = data

    def fetch(self, user_id):
        return self._users.get(user_id)

    def remove(self, user_id):
        self._users.pop(user_id, None)

    def list_all(self):
        return list(self._users.values())


class UserService:
    def __init__(self, store=None, cache_size=64):
        self.store = store or UserStore()
        self._cache = LRUCache(max_size=cache_size)

    def create_user(self, user_id, name, email):
        user = {"id": user_id, "name": name, "email": email}
        self.store.save(user_id, user)
        self._cache.set(user_id, user)
        return user

    def get_user(self, user_id):
        cached = self._cache.get(user_id)
        if cached is not None:
            return cached
        user = self.store.fetch(user_id)
        if user is not None:
            self._cache.set(user_id, user)
        return user

    def update_user(self, user_id, **fields):
        user = self.store.fetch(user_id)
        if user is None:
            return None
        user.update(fields)
        self.store.save(user_id, user)
        self._cache.invalidate(user_id)
        return user

    def delete_user(self, user_id):
        self.store.remove(user_id)
        self._cache.invalidate(user_id)

    def list_users(self):
        return self.store.list_all()

    def get_user_count(self):
        return len(self._cache)

    def search_by_email(self, email):
        for user in self.store.list_all():
            if user.get("email") == email:
                return user
        return None
