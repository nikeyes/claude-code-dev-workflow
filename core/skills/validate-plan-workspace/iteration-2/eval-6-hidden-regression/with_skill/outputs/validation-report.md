## Validation Report: Add Caching to User Service

### Implementation Status

Phase 1: Cache Layer - Fully implemented
Phase 2: Integrate Cache into User Service - Fully implemented (with a hidden regression in an extra method)

---

### Automated Verification Results

`make test` — **16/16 tests PASSED**

```
test_cache.py::test_get_returns_none_for_missing_key PASSED
test_cache.py::test_set_and_get PASSED
test_cache.py::test_evicts_lru_when_full PASSED
test_cache.py::test_access_refreshes_lru_order PASSED
test_cache.py::test_invalidate_removes_entry PASSED
test_cache.py::test_clear_removes_all PASSED
test_cache.py::test_update_existing_key PASSED
test_user_service.py::test_create_and_get_user PASSED
test_user_service.py::test_get_user_returns_none_for_missing PASSED
test_user_service.py::test_get_user_uses_cache PASSED
test_user_service.py::test_update_user PASSED
test_user_service.py::test_update_invalidates_cache PASSED
test_user_service.py::test_delete_user PASSED
test_user_service.py::test_list_users PASSED
test_user_service.py::test_search_by_email PASSED
test_user_service.py::test_search_by_email_not_found PASSED
```

---

### Code Review Findings

#### Matches Plan

- `cache.py` correctly implements `LRUCache` using `OrderedDict` with `get`, `set`, `invalidate`, and `clear` methods.
- LRU eviction at `max_size` boundary works correctly: when full, the least-recently-used entry is popped with `popitem(last=False)`.
- `get()` correctly refreshes LRU order by calling `move_to_end(key)` on hit.
- `user_service.py` integrates `LRUCache` as a cache-aside for `get_user`: cache hit returns without hitting the store; cache miss fetches from store and populates cache.
- `update_user` correctly invalidates the cache entry (`self._cache.invalidate(user_id)`).
- `delete_user` correctly invalidates the cache entry (`self._cache.invalidate(user_id)`).
- Tests in `test_cache.py` cover all cache behaviors specified in the plan.
- Tests in `test_user_service.py` cover cache integration scenarios including cache-hit verification and invalidation after update.
- `create_user` also populates the cache (not specified in plan, but a reasonable enhancement — avoids a cache miss on the first `get_user` after creation).

#### Deviations from Plan

- `user_service.py` adds two methods not mentioned in the plan: `get_user_count()` and `search_by_email()`. Extra methods are not necessarily a problem, but see the bug below.
- `create_user` caches the new user immediately (plan only specified caching for `get_user` lookups). This is an improvement, not a problem.

#### Potential Issues — CRITICAL BUG

**`get_user_count()` returns wrong values (hidden regression)**

Location: `user_service.py`, line 58

```python
def get_user_count(self):
    return len(self._cache)
```

This method returns the number of entries currently in the LRU cache, NOT the total number of users in the system. This is semantically incorrect and will silently produce wrong answers in all of these scenarios:

1. **After cache eviction**: If more than `cache_size` users exist, evicted users are not counted.
2. **After delete**: `delete_user` removes the user from the store AND invalidates the cache entry. On a fresh `UserService` instance where users are deleted without prior `get_user` calls, the count may still be wrong.
3. **Cold start**: If `UserService` is freshly instantiated with a pre-populated store (injected via `store=`), the cache is empty and `get_user_count()` returns 0, not the actual user count.
4. **Partial warming**: If only a subset of users have been accessed, the cache reflects only those, not the total.

**Example of failing scenario:**
```python
svc = UserService()
svc.create_user('u1', 'Alice', 'alice@example.com')  # cache: {u1}
svc.create_user('u2', 'Bob', 'bob@example.com')      # cache: {u1, u2}
svc.delete_user('u1')  # store: {u2}, cache: {u2}
# get_user_count() == 1  -- correct in this case

# But with cache_size=1:
svc2 = UserService(cache_size=1)
svc2.create_user('u1', 'Alice', 'alice@example.com')  # cache: {u1}
svc2.create_user('u2', 'Bob', 'bob@example.com')      # cache: {u2}, u1 evicted
svc2.get_user_count()  # returns 1, but 2 users exist in store
```

The correct implementation should be:
```python
def get_user_count(self):
    return len(self.store.list_all())
```

No test exists for `get_user_count()`, which is why this bug is not caught by the test suite.

#### Secondary Concern — In-Place Mutation in `update_user`

Location: `user_service.py`, lines 42-47

```python
def update_user(self, user_id, **fields):
    user = self.store.fetch(user_id)
    if user is None:
        return None
    user.update(fields)          # mutates the dict in-place in the store
    self.store.save(user_id, user)  # redundant; store already holds same reference
    self._cache.invalidate(user_id)
    return user
```

`UserStore.fetch()` returns the dict object by reference. Calling `user.update(fields)` mutates the dict already held by `_store`. The subsequent `store.save()` call is a no-op since the reference is the same object. This works correctly now but would break if the store ever returned copies (e.g., for serialization or DB backing). Low severity but worth noting for maintainability.

---

### Manual Testing Required

1. User count correctness:
   - [ ] Verify `get_user_count()` returns the correct total after creating more users than `cache_size`
   - [ ] Verify `get_user_count()` returns the correct total after deleting users that were never accessed (not in cache)
   - [ ] Verify `get_user_count()` works correctly when `UserService` is initialized with a pre-populated store

2. Cache transparency:
   - [ ] Confirm callers receive identical user data whether from cache or store
   - [ ] Verify no stale data is served after `update_user` calls

3. Memory bounds:
   - [ ] Confirm cache never grows beyond `max_size` entries under sustained load

---

### Recommendations

1. **Fix `get_user_count()` immediately** — it silently returns wrong values. Replace `len(self._cache)` with `len(self.store.list_all())`. This is a semantic bug masked by the absence of tests.

2. **Add a test for `get_user_count()`** — test that it reflects the store count, not the cache count, especially after eviction and after operating with a `cache_size` smaller than the total number of users.

3. **Consider defensive copying in `UserStore.fetch()`** — returning `dict(user)` instead of the raw reference would prevent accidental mutation and make the store's contract clearer.

4. **`create_user` caching** — The extra caching in `create_user` is beneficial but not tested. A test verifying that `create_user` populates the cache (so the first `get_user` is a cache hit) would be valuable.

---

### Validation Checklist

- [x] All phases marked complete are actually done
- [x] Automated tests pass (16/16)
- [x] Cache layer follows existing Python patterns (OrderedDict-based LRU)
- [ ] No regressions introduced — **FAIL: `get_user_count()` is semantically broken**
- [x] Error handling is robust (None returns for missing users)
- [ ] Documentation updated if needed — no docstrings on public methods
- [ ] Manual test steps are clear — provided above
