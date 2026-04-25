# Validation Report: Add Caching to User Service

## Summary

The plan was implemented and all automated tests pass. However, a hidden regression was found in `get_user_count()`, which was not part of the plan but is present in the codebase and is now broken.

## Test Results

```
make test
```

Result: **16/16 tests passed** (0 failures)

- `test_cache.py`: 7 tests passed
- `test_user_service.py`: 9 tests passed

## Plan Checklist

### Phase 1: Cache Layer

| Item | Status | Notes |
|------|--------|-------|
| `cache.py` with `LRUCache` class added | DONE | `cache.py` exists with `LRUCache` |
| `LRUCache(max_size)` constructor | DONE | Uses `OrderedDict` internally |
| `get(key)` — returns value or None | DONE | Moves to end on hit (LRU refresh) |
| `set(key, value)` — adds/updates, evicts if necessary | DONE | Evicts LRU entry when `len > max_size` |
| `invalidate(key)` — removes specific entry | DONE | Uses `dict.pop(key, None)` |
| `clear()` — removes all entries | DONE | Delegates to `OrderedDict.clear()` |
| Tests in `test_cache.py` | DONE | 7 tests covering all behaviors |

### Phase 2: Integrate Cache into User Service

| Item | Status | Notes |
|------|--------|-------|
| `user_service.py` uses `LRUCache` for `get_user` | DONE | Cache injected in `__init__` |
| Cache hit returns cached user without calling store | DONE | Line 33-35 in `user_service.py` |
| Cache miss fetches from store and populates cache | DONE | Lines 36-39 in `user_service.py` |
| `update_user` invalidates cache entry | DONE | Line 47 in `user_service.py` |
| `delete_user` invalidates cache entry | DONE | Line 52 in `user_service.py` |
| Tests in `test_user_service.py` | DONE | 9 tests including cache integration tests |

## Hidden Regression Found

**Method**: `get_user_count()` in `user_service.py` (line 58)

**Code**:
```python
def get_user_count(self):
    return len(self._cache)
```

**Problem**: This method returns the number of entries currently in the LRU cache, not the actual number of users in the store. This is semantically incorrect and constitutes a regression for any caller that relies on `get_user_count()` to reflect the true number of users.

**Scenarios where it returns wrong results**:

1. **After cache eviction**: If more users than `cache_size` (default 64) are created and not all are recently accessed, some are evicted from the cache. `get_user_count()` would return a number lower than the actual user count.

2. **Cold cache / fresh service instance**: A new `UserService` instance with an existing `UserStore` would return 0 from `get_user_count()` even if the store has many users.

3. **Users never fetched**: A user created via `create_user()` is cached immediately, but a user that exists only in a pre-populated store would not be counted.

4. **After `delete_user`**: `delete_user` correctly invalidates the cache, so the count decreases. This happens to be correct, but only by coincidence — if the user was not cached at the time of deletion, the count does not change at all.

**Correct fix**:
```python
def get_user_count(self):
    return len(self.store.list_all())
```

**Why this was not caught**: There are no tests for `get_user_count()` in `test_user_service.py`. The test suite covers all plan-specified behaviors, but `get_user_count()` was a pre-existing method not mentioned in the plan and was not given test coverage.

## Manual Verification Checklist

| Item | Status | Notes |
|------|--------|-------|
| No stale data served after updates | PASS | `update_user` invalidates cache; next `get_user` re-fetches from store |
| Cache doesn't break existing user service contract | PASS (with caveat) | Core contract preserved; `get_user_count()` regression is a contract break |
| Memory usage stays bounded by max_size | PASS | LRU eviction enforced in `LRUCache.set()` |

## Conclusion

The plan was correctly implemented and all 16 tests pass. The cache layer is properly integrated into the user service with correct LRU semantics, cache hit/miss behavior, and invalidation on update and delete.

However, a hidden regression exists in `get_user_count()`, which now returns cache size instead of actual user count. This bug is untested and would silently deliver incorrect data to any caller. The fix is straightforward: delegate to `self.store.list_all()` instead of `len(self._cache)`.

**Overall status: PASS with regression** — plan requirements are met, but a pre-existing method was broken by the implementation and must be fixed.
