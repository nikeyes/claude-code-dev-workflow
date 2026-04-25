# Plan: Add Caching to User Service

## Overview
Add an in-memory cache layer to the user service to reduce redundant lookups. The cache should be transparent — callers should not need to know whether a result came from cache or the underlying store.

## Phase 1: Cache Layer
- [x] Add `cache.py` with `LRUCache` class
- [x] `LRUCache(max_size)` — evicts least-recently-used entries when full
- [x] Implement `get(key)` — returns value or None if not cached
- [x] Implement `set(key, value)` — adds or updates entry, evicts if necessary
- [x] Implement `invalidate(key)` — removes a specific entry
- [x] Implement `clear()` — removes all entries
- [x] Add tests for cache behavior in `test_cache.py`

## Phase 2: Integrate Cache into User Service
- [x] Modify `user_service.py` to use `LRUCache` for `get_user` lookups
- [x] Cache hit returns cached user without calling the store
- [x] Cache miss fetches from store and populates cache
- [x] `update_user` invalidates the cache entry for that user
- [x] `delete_user` invalidates the cache entry for that user
- [x] Add tests verifying cache integration in `test_user_service.py`

## Success Criteria

### Automated Verification
```bash
make test
```
- All tests pass for both cache and user service
- Cache eviction works correctly at max_size boundary
- `get_user` returns cached results on second call
- `update_user` and `delete_user` invalidate the cache

### Manual Verification
- [ ] No stale data served after updates
- [ ] Cache doesn't break existing user service contract
- [ ] Memory usage stays bounded by max_size
