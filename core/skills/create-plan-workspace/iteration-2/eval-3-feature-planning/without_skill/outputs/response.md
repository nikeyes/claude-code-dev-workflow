# Response: Add a Caching Layer to UserService

## What I read

- `user_service.py` – a `UserService` class backed by SQLite with methods: `get_user`, `get_user_by_username`, `create_user`, `update_user`, `delete_user`, `list_users`, `get_user_count`.
- `test_user_service.py` – pytest tests covering all public methods.
- `Makefile` – single `test` target that runs pytest.

## Summary of the plan

The plan adds an instance-level `dict` cache (`self._user_cache`) to `UserService`. The cache is checked before every `get_user` call; on a miss the DB is queried and the result is stored. Cache entries are evicted when `update_user` or `delete_user` is called for that ID.

The approach is TDD: write failing tests first, then make them pass with the minimal production change.

## Full plan

See [plan.md](./plan.md) for the complete step-by-step implementation plan.

## Key decisions

- **Cache only positive results** – `None` (not found) is not cached; this avoids a sentinel-value complication and keeps the logic simple.
- **Instance-level cache** – each `UserService` owns its own SQLite connection, so a per-instance cache is correct and safe.
- **No new dependencies** – a plain Python `dict` is sufficient; no external cache library needed.
- **Invalidate on write, not on read** – evict on `update_user` and `delete_user` rather than using TTL, because the service has direct knowledge of all mutations.
- **Scope: `get_user` only** – the task specifically asks for lookups by ID; `get_user_by_username` and list operations are excluded to keep the change minimal and the invalidation logic straightforward.
