# create-plan — Session Response

**Task**: Add a caching layer to the user service so that repeated lookups by ID don't hit the database

---

## Step 1: Context Gathering & Initial Analysis

I read the following files in full:

- `user_service.py` — `UserService` class with methods:
  `__init__`, `_setup_schema`, `get_user`, `get_user_by_username`,
  `create_user`, `update_user`, `delete_user`, `list_users`, `get_user_count`
- `test_user_service.py` — 9 tests in `TestUserService`, all using an
  in-memory SQLite DB, one test per CRUD operation or query variant
- `Makefile` — single `test` target: `python -m pytest test_user_service.py -v`

### Understanding

The only method that does a lookup **by ID** is `get_user(user_id: int)`.
It executes a raw `SELECT` on every call. Three other methods
(`create_user`, `update_user`, `delete_user`) write to the database and
must keep any cache consistent.

`get_user_by_username` and `list_users` are not ID-based lookups and are
explicitly out of scope.

---

## Step 2: Research & Design Options

### Option A — Dict cache on the instance (chosen)

Add `self._cache: dict[int, dict] = {}` to `__init__`.
- `get_user`: check dict first; on miss, query DB and store result.
- `update_user`: evict stale entry, then call `get_user` (which re-fetches
  and re-caches).
- `delete_user`: `dict.pop(user_id, None)`.
- `create_user`: no extra code needed — it already calls `get_user`, which
  will cache the new record.

Pros: zero new dependencies, trivially understandable, consistent with the
existing single-connection design.  
Cons: no TTL, unbounded growth for long-lived instances.

### Option B — `functools.lru_cache` on `get_user`

Pros: one decorator.  
Cons: `lru_cache` doesn't support per-instance methods cleanly; invalidation
requires calling `get_user.cache_clear()` which is awkward inside the class.
Also caches `None` for missing IDs, which conflicts with the "do not cache
misses" requirement.

**Option A selected** as the simplest, most readable, most testable approach.

---

## Step 3 & 4: Plan Structure and Detailed Plan

The plan is written to:

```
core/skills/create-plan-workspace/iteration-2/eval-3-feature-planning/with_skill/outputs/plan.md
```

### Phase overview

| Phase | What it does |
|-------|-------------|
| 1 | Add `_cache` dict and update `get_user`, `update_user`, `delete_user` |
| 2 | Add `TestUserServiceCache` tests to `test_user_service.py` |

### Phase 1 — Changes to `user_service.py`

1. `__init__`: add `self._cache: dict[int, dict] = {}`
2. `get_user`: return `self._cache[user_id]` if present; otherwise query DB,
   store result in cache, return it. Do **not** cache `None` (missing user).
3. `update_user`: call `self._cache.pop(user_id, None)` before the final
   `get_user` call so the stale entry is evicted and the fresh record is
   fetched and cached.
4. `delete_user`: call `self._cache.pop(user_id, None)` after the DELETE.
5. `create_user`: no change needed — the trailing `get_user` call already
   populates the cache.

### Phase 2 — New tests in `test_user_service.py`

New class `TestUserServiceCache` covers:

- Cache is populated after `create_user`
- Second `get_user` call does not hit the database
- `update_user` stores the refreshed record in the cache
- `delete_user` removes the entry from the cache
- `get_user` on a missing ID does not insert `None` into the cache

---

## Step 5: Final Checklist

### Automated Verification

- [ ] All existing tests pass: `make test`
- [ ] All new cache tests pass: `make test`

### What We Are NOT Doing

- No TTL / expiry
- No cache for `get_user_by_username`, `list_users`, `get_user_count`
- No external cache (Redis, Memcached)
- No thread-safety primitives
- No cache-size limit or LRU eviction
- No persistence between `UserService` instances

---

Implementation plan complete:
`core/skills/create-plan-workspace/iteration-2/eval-3-feature-planning/with_skill/outputs/plan.md`

Next steps in the workflow:
- Review and approve the plan
- Use `/stepwise-core:implement-plan` with the plan file to execute it
- Or use `/stepwise-core:iterate-plan` to refine further

Tip: Use `/clear` to free up context before starting implementation.
