## Validation Report: Add Caching to User Service

### Implementation Status

Phase 1: Cache Layer — Fully implemented
Phase 2: Integrate Cache into User Service — Deviations found

---

### Automated Verification

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.0.3, pluggy-1.6.0
collected 16 items

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

============================== 16 passed in 0.01s ==============================
```

16 passed, 0 failed.

---

### Findings

#### Phase 1: Cache Layer — matches plan

All five required methods are present and correctly implemented in `cache.py`:

- `LRUCache(max_size)` — uses `OrderedDict` to track insertion/access order; evicts LRU entry when `len > max_size`. Correct.
- `get(key)` — moves accessed entry to end (most-recent), returns `None` on miss. Correct.
- `set(key, value)` — moves existing key to end before updating, then evicts from front if over capacity. Correct.
- `invalidate(key)` — uses `pop(key, None)`, safe on missing keys. Correct.
- `clear()` — delegates to `OrderedDict.clear()`. Correct.

`test_cache.py` covers all plan-specified behaviors: get-miss, get-hit, eviction at boundary, LRU refresh, invalidate, clear, and update of existing key. Test quality is good: assertions are non-trivial and target specific observable outcomes.

#### Phase 2: Cache integration — mostly matches plan, one hidden regression

**Matches plan:**

- `get_user` checks cache first; on hit returns cached value without touching store. On miss, fetches from store and populates cache. Correct.
- `update_user` calls `self._cache.invalidate(user_id)` after saving to store. Correct.
- `delete_user` calls `self._cache.invalidate(user_id)` after removing from store. Correct.

**Deviation — `create_user` populates cache (not in plan):**

`create_user` calls `self._cache.set(user_id, user)` immediately after saving. The plan does not mention this behavior. It is a reasonable optimization but represents an undocumented side-effect: a freshly created user will return a cache hit on the first `get_user` call, which differs from a "cache populated on first access" model. This is not necessarily wrong, but it is unspecified and should be documented.

**Hidden regression — `get_user_count()` counts cache entries, not users:**

```python
def get_user_count(self):
    return len(self._cache)
```

This method is not mentioned in the plan at all, but it exists in `user_service.py` and is semantically broken. `len(self._cache)` counts how many entries are currently in the LRU cache, which is not the same as the number of users in the system. Specifically:

- A user created but whose cache entry was evicted (due to max_size) will not be counted.
- A user deleted from the store but whose cache entry has not yet been accessed/invalidated in a hypothetical edge case would still be counted (though in practice `delete_user` calls `invalidate`, so this is avoided for `delete_user`).
- A fresh `UserService` instance where users were loaded from an external store and not yet accessed would return 0 even if users exist.

The correct implementation to count users should delegate to `self.store` (e.g., `len(self.store._users)` or a dedicated store method), not the cache. Since the plan does not specify `get_user_count`, there is no test for it, and the bug goes undetected by the test suite.

**Extra method — `search_by_email()` not in plan:**

`search_by_email` is implemented but not mentioned in the plan. This is not inherently a problem, but it bypasses the cache entirely — it always scans `self.store.list_all()`. If users are stored only in cache (e.g., after `store._users` is manipulated externally as done in `test_get_user_uses_cache`), `search_by_email` will not find them. This is a design inconsistency but outside the plan scope.

#### Test quality assessment

`test_user_service.py`:

- `test_get_user_uses_cache` — correctly verifies the cache-hit path by clearing the store after population and confirming the result still returns. This is a meaningful assertion.
- `test_update_invalidates_cache` — calls `get_user` after `update_user` and checks the updated name. This correctly verifies that the update is visible on subsequent reads, but it does not explicitly verify the cache was invalidated (it could pass even if the cache returned a stale entry if the update had also refreshed the cache). However, since `update_user` only calls `invalidate` (not `set`), the subsequent `get_user` must fetch from the store. The test is valid, if indirect.
- `test_delete_user` — verifies `get_user` returns `None` after deletion. This implicitly tests cache invalidation on delete. Acceptable.
- No test covers `get_user_count()`. The broken method ships untested.
- No test covers the `create_user` cache-population behavior (i.e., that the first `get_user` after `create_user` is a cache hit without a store fetch).

#### Manual verification criteria (plan-specified)

- "No stale data served after updates" — partially verifiable. Tests confirm `get_user` returns updated data after `update_user`. But `search_by_email` always bypasses the cache and reads from store, so stale data is not a risk there. The manual criterion is met for `get_user`.
- "Cache doesn't break existing user service contract" — `get_user_count()` breaks the user count contract. A caller expecting the total number of stored users will receive an incorrect answer.
- "Memory usage stays bounded by max_size" — the cache correctly evicts at `max_size`. The `UserStore` itself is unbounded; the plan does not require bounding the store.

---

### Recommendations

1. **Fix `get_user_count()`** — This method silently returns the wrong value. It should count actual users in the store, not cache entries. Either add a `count()` method to `UserStore` or use `len(self.store._users)`. Since this method is not part of the plan, it should either be removed or correctly implemented with a test.

2. **Add a test for `get_user_count()`** — Whatever the intended semantics, the method has no test coverage. If it is meant to reflect cache size, document that clearly. If it is meant to count total users, fix the implementation and add a test that creates users, evicts some from cache, and verifies the count still reflects the true total.

3. **Document the `create_user` cache-population behavior** — The plan specifies caching only for `get_user` lookups. The fact that `create_user` also populates the cache is an undocumented deviation. Add it to the plan or a comment, and consider whether this is the intended behavior.

4. **Consider a test for `create_user` cache behavior** — Verify that immediately after `create_user`, a `get_user` call is a cache hit (i.e., does not call the store). This would make the caching contract explicit and catch future regressions.
