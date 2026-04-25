# Implementation Plan: Caching Layer for UserService.get_user

## Goal

Add an in-memory cache to `UserService` so that repeated lookups of the same user ID do not hit the SQLite database. The cache must stay consistent when users are updated or deleted.

---

## Context

`UserService` (`user_service.py`) is a thin wrapper over a SQLite database. The only read path that benefits from caching by ID is `get_user(user_id)`. The other read paths (`get_user_by_username`, `list_users`, `get_user_count`) are not included in scope.

The cache must be invalidated on:
- `update_user` – the cached entry is stale after a write.
- `delete_user` – the entry no longer exists.

`create_user` calls `get_user` internally, so the freshly-created record will naturally be placed in the cache at creation time.

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Cache storage | Plain `dict` keyed by `user_id` | Simplest structure; no external dependency |
| Cache scope | Instance-level (`self._cache`) | Each `UserService` instance owns its DB connection; instance cache is correct |
| Cache miss sentinel | `None` is a valid "not found" return value, so we must distinguish "not cached" from "cached as not found" | Use a sentinel object `_MISSING` or only cache existing users |
| Caching negative results | No – do not cache `None` | Keeps it simple; a not-found lookup is rarely repeated in hot paths |
| Cache size / TTL | Unbounded, no TTL | Scope: avoid DB hits in the same service instance; eviction is out of scope |

---

## Steps

### Step 1 – Add failing tests that verify cache behaviour

Before touching production code, extend `test_user_service.py` with tests that will initially fail:

1. **`test_get_user_returns_cached_result`** – create a user, fetch it twice, assert the second call returns the same data without a second DB hit. (We can verify this by patching `self.service._conn.execute` after the first call and confirming it is not called again, or by inspecting a call counter.)
2. **`test_cache_invalidated_on_update`** – create a user, fetch it (prime the cache), update it, fetch again – must return the updated value.
3. **`test_cache_invalidated_on_delete`** – create a user, fetch it (prime the cache), delete it, fetch again – must return `None`.
4. **`test_cache_not_populated_for_missing_user`** – call `get_user(999)`, expect `None`; no negative result should be stored.

Run `make test` – these four tests should fail (cache does not exist yet).

### Step 2 – Implement the cache in `UserService`

**`__init__`** – initialise the cache dict:

```python
self._user_cache: dict[int, dict] = {}
```

**`get_user`** – check cache before hitting the DB:

```python
def get_user(self, user_id: int) -> Optional[dict]:
    if user_id in self._user_cache:
        return self._user_cache[user_id]
    row = self._conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    self._user_cache[user_id] = result
    return result
```

**`update_user`** – evict entry after a successful write:

```python
def update_user(self, user_id: int, **fields) -> Optional[dict]:
    ...  # existing logic
    self._conn.commit()
    self._user_cache.pop(user_id, None)   # <-- invalidate
    return self.get_user(user_id)         # re-fetches and re-caches
```

**`delete_user`** – evict entry after deletion:

```python
def delete_user(self, user_id: int) -> bool:
    cursor = self._conn.execute(
        "DELETE FROM users WHERE id = ?", (user_id,)
    )
    self._conn.commit()
    self._user_cache.pop(user_id, None)   # <-- invalidate
    return cursor.rowcount > 0
```

No changes are needed to `create_user` – it already calls `get_user` at the end, which will populate the cache.

### Step 3 – Run all tests

```bash
make test
```

All original tests plus the four new cache tests must pass. There should be no regressions.

### Step 4 – Review and clean up

- Confirm type annotation (`dict[int, dict]`) is consistent with the rest of the file.
- No public API changes; the cache is fully internal.
- No new dependencies introduced.

---

## Files Changed

| File | Change |
|---|---|
| `user_service.py` | Add `self._user_cache` in `__init__`; update `get_user`, `update_user`, `delete_user` |
| `test_user_service.py` | Add 4 cache-behaviour tests |

---

## Out of Scope

- Caching `get_user_by_username` (different key space; cross-invalidation adds complexity).
- Cache size limits or TTL.
- Thread safety (the existing service is not thread-safe; no regression introduced).
- External cache backends (Redis, Memcached).
