# Caching Layer for UserService — Implementation Plan

## Overview

Add an in-memory cache to `UserService` so that repeated lookups by ID
(`get_user`) avoid hitting SQLite on every call. The cache must stay
consistent when a user is updated or deleted.

## Current State Analysis

`UserService` in `user_service.py` wraps a SQLite connection.
Every read triggers a database round-trip, even when the same user record is
fetched multiple times in a single service lifetime.

### Key Discoveries

- `get_user(user_id: int) -> Optional[dict]` (`user_service.py:24`) — the
  primary target; it executes a SELECT on every invocation.
- `update_user(user_id, **fields)` (`user_service.py:48`) — ends by calling
  `get_user`, so after a write the refreshed dict is already available to
  cache.
- `delete_user(user_id)` (`user_service.py:61`) — must evict the entry from
  the cache.
- `create_user(username, email, role)` (`user_service.py:40`) — ends by
  calling `get_user`; the newly created dict can be inserted into the cache.
- `get_user_by_username` and `list_users` do NOT look up by ID so they are
  out of scope for this cache.
- All existing tests live in `test_user_service.py` and run via `make test`
  (`python -m pytest test_user_service.py -v`).
- Each test method creates a fresh `UserService()` instance
  (`setup_method`), so the cache is effectively empty at the start of every
  test.

## Desired End State

`UserService` maintains a `dict` cache keyed by `user_id`. After this plan
is complete:

1. A second call to `get_user(same_id)` returns the cached dict without
   touching the database.
2. `update_user` stores the refreshed dict in the cache.
3. `delete_user` removes the entry from the cache.
4. `create_user` populates the cache for the new user.
5. All 9 existing tests continue to pass.
6. New tests document and verify the cache behaviour.

### Verification

```
make test   # all tests (existing + new) pass
```

## What We Are NOT Doing

- No TTL / time-based expiry.
- No cache for `get_user_by_username`, `list_users`, or `get_user_count`.
- No external cache (Redis, Memcached).
- No thread-safety primitives (the existing service is single-threaded).
- No cache-size limit / eviction policy.
- No persistence of the cache between `UserService` instances.

## Implementation Approach

Add a private `dict` attribute `_cache: dict[int, dict]` to `UserService.__init__`.
Modify the four mutating / reading methods to consult or update that dict.
All changes are contained within `user_service.py`.

New tests are added to `test_user_service.py` to verify cache hits and
cache invalidation. Because the service uses an in-memory SQLite DB
(`:memory:`), tests can inspect database call counts by subclassing or by
monkey-patching `self.service._conn.execute`.

---

## Phase 1: Add Cache to UserService

### Overview

Introduce `_cache` in `__init__` and update `get_user`, `create_user`,
`update_user`, and `delete_user` to keep it consistent.

### Changes Required

#### 1. `UserService.__init__`

**File**: `user_service.py`  
**Changes**: Initialise `_cache` as an empty dict.

```python
def __init__(self, db_path: str = ":memory:"):
    self._conn = sqlite3.connect(db_path)
    self._conn.row_factory = sqlite3.Row
    self._cache: dict[int, dict] = {}
    self._setup_schema()
```

#### 2. `UserService.get_user`

**File**: `user_service.py`  
**Changes**: Return cached value when present; store DB result on cache miss.

```python
def get_user(self, user_id: int) -> Optional[dict]:
    if user_id in self._cache:
        return self._cache[user_id]
    row = self._conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    user = dict(row)
    self._cache[user_id] = user
    return user
```

#### 3. `UserService.create_user`

**File**: `user_service.py`  
**Changes**: `create_user` already calls `get_user` at the end; because
`get_user` now caches the result, no extra change is needed here. The new
user will be in the cache immediately after creation.

*(No code change required — the cache is populated by the `get_user` call
inside `create_user`.)*

#### 4. `UserService.update_user`

**File**: `user_service.py`  
**Changes**: Evict the stale entry before calling `get_user`, so `get_user`
re-fetches from the DB and re-caches the fresh data.

```python
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
    self._cache.pop(user_id, None)   # evict stale entry
    return self.get_user(user_id)    # re-fetches and re-caches
```

#### 5. `UserService.delete_user`

**File**: `user_service.py`  
**Changes**: Remove the entry from the cache after deletion.

```python
def delete_user(self, user_id: int) -> bool:
    cursor = self._conn.execute(
        "DELETE FROM users WHERE id = ?", (user_id,)
    )
    self._conn.commit()
    self._cache.pop(user_id, None)
    return cursor.rowcount > 0
```

### Success Criteria

- [ ] All existing tests pass: `make test`
- [ ] No linting errors (if project uses a linter)

---

## Phase 2: Add Cache-Behaviour Tests

### Overview

Write new tests in `test_user_service.py` that verify the cache works
correctly, without relying on implementation internals wherever possible.
Where necessary to assert a cache hit, we patch `_conn.execute` to count
calls.

### Changes Required

#### New test class `TestUserServiceCache` in `test_user_service.py`

**File**: `test_user_service.py`

```python
from unittest.mock import patch, wraps


class TestUserServiceCache:
    def setup_method(self):
        self.service = UserService()

    def test_repeated_get_user_returns_same_data(self):
        created = self.service.create_user("lara", "lara@example.com")
        uid = created["id"]
        first = self.service.get_user(uid)
        second = self.service.get_user(uid)
        assert first == second

    def test_cache_is_populated_after_create(self):
        created = self.service.create_user("marc", "marc@example.com")
        # After create, the id must be in _cache
        assert created["id"] in self.service._cache

    def test_second_get_user_does_not_hit_db(self):
        created = self.service.create_user("nina", "nina@example.com")
        uid = created["id"]
        self.service.get_user(uid)  # populate cache

        original_execute = self.service._conn.execute
        call_count = {"n": 0}

        def counting_execute(sql, *args, **kwargs):
            if "SELECT" in sql.upper() and "WHERE id" in sql:
                call_count["n"] += 1
            return original_execute(sql, *args, **kwargs)

        with patch.object(self.service._conn, "execute", side_effect=counting_execute):
            self.service.get_user(uid)

        assert call_count["n"] == 0, "Expected cache hit, but DB was queried"

    def test_update_user_refreshes_cache(self):
        created = self.service.create_user("omar", "omar@example.com")
        uid = created["id"]
        self.service.get_user(uid)  # warm cache
        self.service.update_user(uid, role="admin")
        cached = self.service._cache.get(uid)
        assert cached is not None
        assert cached["role"] == "admin"

    def test_delete_user_removes_from_cache(self):
        created = self.service.create_user("petra", "petra@example.com")
        uid = created["id"]
        self.service.get_user(uid)  # warm cache
        self.service.delete_user(uid)
        assert uid not in self.service._cache

    def test_get_user_not_found_not_cached(self):
        result = self.service.get_user(9999)
        assert result is None
        assert 9999 not in self.service._cache
```

### Success Criteria

- [ ] All tests (existing and new) pass: `make test`

---

## Testing Strategy

### Unit Tests

- Existing `TestUserService` exercises all CRUD operations and must remain
  green throughout.
- New `TestUserServiceCache` verifies:
  - Cache is populated on `create_user` and `get_user`.
  - Cache is evicted/updated on `update_user`.
  - Cache is evicted on `delete_user`.
  - Miss-on-not-found does not pollute the cache.
  - Second call to `get_user` does not query the database.

### Integration Tests

Not applicable — the service is self-contained with an in-memory SQLite DB.

## Performance Considerations

The cache trades memory for speed. For a short-lived `UserService` instance
(e.g. per-request in a web framework), the cache provides the most benefit
when the same user IDs are accessed multiple times within the same request.
For long-lived instances, the cache grows unboundedly; a future iteration
could add LRU eviction if memory becomes a concern.

## Migration Notes

No schema changes, no migrations required. The caching layer is purely
additive in-process state.

## References

- Source file: `user_service.py`
- Test file: `test_user_service.py`
- Test runner: `make test` → `python -m pytest test_user_service.py -v`
