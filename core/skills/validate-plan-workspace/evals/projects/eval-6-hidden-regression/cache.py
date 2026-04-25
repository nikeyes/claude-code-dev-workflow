from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size=128):
        self.max_size = max_size
        self._store = OrderedDict()

    def get(self, key):
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def set(self, key, value):
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def invalidate(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def __len__(self):
        return len(self._store)
