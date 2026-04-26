# Plan: Add In-Memory Cache to `get_user`

## Goal

Add an in-memory cache to `UserService.get_user` so that repeated lookups for the same `user_id` do not execute a database query. The cache must stay consistent when users are mutated (email updated, deactivated).

---

## Step 1 — Write a failing test that proves the cache is used

Add a test to `test_user_service.py` that calls `get_user` twice for the same ID and asserts the second call does not hit the database.

Use `unittest.mock.patch.object` to spy on `self._conn.execute`. After the first `get_user` call, reset the mock's call count, then call `get_user` again. Assert `execute` was **not** called the second time.

Expected result: test fails because the current implementation always calls `execute`.

---

## Step 2 — Initialize the cache in `__init__`

In `UserService.__init__`, add a private attribute:

```python
self._user_cache: dict[int, Optional[dict]] = {}
```

No other changes yet. Tests still pass (no behaviour change).

---

## Step 3 — Populate the cache on cache miss in `get_user`

Modify `get_user` to:

1. Return the cached value if `user_id` is present in `_user_cache`.
2. On a cache miss, execute the existing database query.
3. Store the result (`dict` or `None`) in `_user_cache[user_id]` before returning it.

```python
def get_user(self, user_id: int) -> Optional[dict]:
    if user_id in self._user_cache:
        return self._user_cache[user_id]
    row = self._conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    result = dict(row) if row is not None else None
    self._user_cache[user_id] = result
    return result
```

Expected result: the new cache-hit test from Step 1 now passes, and all existing tests continue to pass.

---

## Step 4 — Invalidate the cache in `update_email`

`update_email` mutates the user record and then calls `get_user` to return the refreshed data. If the cache is not invalidated first, `get_user` will return the stale cached value.

Before the `get_user` call at the end of `update_email`, delete the entry from the cache:

```python
def update_email(self, user_id: int, email: str) -> Optional[dict]:
    self._conn.execute(
        "UPDATE users SET email = ? WHERE id = ?", (email, user_id)
    )
    self._conn.commit()
    self._user_cache.pop(user_id, None)   # invalidate stale entry
    return self.get_user(user_id)
```

Expected result: `test_update_email` continues to return the updated email address.

---

## Step 5 — Invalidate the cache in `deactivate_user`

`deactivate_user` sets `is_active = 0`. A subsequent `get_user` call must reflect this change, as verified by `test_deactivate_user`.

Delete the cache entry after the UPDATE:

```python
def deactivate_user(self, user_id: int) -> bool:
    cursor = self._conn.execute(
        "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,)
    )
    self._conn.commit()
    self._user_cache.pop(user_id, None)   # invalidate stale entry
    return cursor.rowcount > 0
```

Expected result: `test_deactivate_user` still passes (the refreshed `get_user` call reads from DB and re-populates the cache with `is_active == 0`).

---

## Step 6 — Run the full test suite

```bash
pytest test_user_service.py -v
```

All tests must be green:

- `test_create_and_get_user`
- `test_get_user_by_email`
- `test_get_user_by_email_not_found`
- `test_update_email`
- `test_list_users_active_only`
- `test_list_users_all`
- `test_deactivate_user`
- `test_deactivate_nonexistent_user`
- `test_get_user_cache_hit` (new)

---

## Summary of changes

| File | Change |
|------|--------|
| `user_service.py` | Add `_user_cache` dict in `__init__`; cache-and-return in `get_user`; invalidate in `update_email` and `deactivate_user` |
| `test_user_service.py` | Add `test_get_user_cache_hit` to verify DB is not queried on repeated lookups |

## Notes

- `create_user` does not need explicit invalidation: it inserts a new row and immediately calls `get_user`, which will populate the cache on first access.
- `get_user_by_email` and `list_users` are not cached; they are separate query paths and are out of scope for this change.
- The cache lives for the lifetime of the `UserService` instance. There is no TTL or size limit, which is acceptable for this in-process, in-memory SQLite use case.
