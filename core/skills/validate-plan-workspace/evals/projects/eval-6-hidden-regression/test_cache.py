from cache import LRUCache


def test_get_returns_none_for_missing_key():
    cache = LRUCache()
    assert cache.get("missing") is None


def test_set_and_get():
    cache = LRUCache()
    cache.set("a", 1)
    assert cache.get("a") == 1


def test_evicts_lru_when_full():
    cache = LRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_access_refreshes_lru_order():
    cache = LRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")
    cache.set("c", 3)
    assert cache.get("a") == 1
    assert cache.get("b") is None


def test_invalidate_removes_entry():
    cache = LRUCache()
    cache.set("x", 42)
    cache.invalidate("x")
    assert cache.get("x") is None


def test_clear_removes_all():
    cache = LRUCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert len(cache) == 0


def test_update_existing_key():
    cache = LRUCache()
    cache.set("a", 1)
    cache.set("a", 2)
    assert cache.get("a") == 2
