# Plan: Add In-Memory Cache to `get_user`

## Goal

Add an in-memory cache to `UserService.get_user` so that repeated lookups for the same `user_id` do not hit the database. The cache must stay consistent when users are updated or deactivated.

## Risk Assessment

This is **not a risky breaking change**. There is no rename, no API contract change, no data migration, and no service replacement. The public interface of `get_user` remains identical. The risk is behavioural: a stale cache could return outdated data after `update_email` or `deactivate_user`. This is managed by invalidating (or updating) the cache in every write method.

Pattern to apply: **Performance improvement** (Baseline → Implement → Verify), not Expand-Contract.

---

## Phase 1: Establish Baseline (Learning Step)

### Step 1.1 — Document current behaviour and identify cache invalidation points (1h)

**Type:** Learning

**What to do:**
- Read all methods in `UserService` that write to the database: `create_user`, `update_email`, `deactivate_user`.
- For each writer, decide: does it need to invalidate or update the cache entry for the affected `user_id`? Answer:
  - `create_user` — no existing cache entry; no action needed.
  - `update_email(user_id, email)` — must invalidate cache entry for `user_id`.
  - `deactivate_user(user_id)` — must invalidate cache entry for `user_id`.
- Write these decisions down (as a comment or a doc) so the implementation step has no ambiguity.
- Check the existing tests to confirm they exercise all four code paths above. They do (see `test_update_email`, `test_deactivate_user`).

**Artifact:** Written list of invalidation points (inline comment in code is fine).

**Reversibility:** Nothing is changed; fully reversible.

---

## Phase 2: Implement the Cache (Earning Steps)

### Step 2.1 — Add a failing test that proves the cache prevents a second DB hit (1h)

**Type:** Earning (TDD Red step)

**What to do:**
- In `test_user_service.py`, add a test that:
  1. Creates a user.
  2. Calls `svc.get_user(user_id)` twice.
  3. Asserts both calls return identical results.
  4. Asserts the cache was used on the second call (simplest proxy: monkey-patch or count `_conn.execute` calls, or expose a `_cache` dict and assert it has an entry after the first call).
- Run the test; it should fail because no cache exists yet.

**Example test sketch:**
```python
def test_get_user_uses_cache_on_second_call(svc):
    user = svc.create_user("cached", "cached@example.com")
    uid = user["id"]
    result1 = svc.get_user(uid)
    # After first call, cache should hold the entry
    assert uid in svc._cache
    result2 = svc.get_user(uid)
    assert result1 == result2
```

**Deployable:** Test files are deployable artifacts (they verify intent before code changes land).

**Reversibility:** Delete the test if the approach changes.

---

### Step 2.2 — Implement the cache in `get_user` (1h)

**Type:** Earning (TDD Green step)

**What to do:**
- In `UserService.__init__`, add `self._cache: dict[int, dict] = {}`.
- In `get_user`, before querying the DB, check the cache:
  ```python
  def get_user(self, user_id: int) -> Optional[dict]:
      if user_id in self._cache:
          return self._cache[user_id]
      row = self._conn.execute(
          "SELECT * FROM users WHERE id = ?", (user_id,)
      ).fetchone()
      if row is None:
          return None
      result = dict(row)
      self._cache[user_id] = result
      return result
  ```
- Run all existing tests plus the new one from Step 2.1. All must pass.

**Deployable:** The change is isolated to one method. Existing public interface unchanged.

**Reversibility:** Revert this one method to its original form; tests instantly confirm correctness.

---

### Step 2.3 — Invalidate the cache in write methods (1h)

**Type:** Earning

**What to do:**
- Add cache invalidation in the two write methods identified in Step 1.1:

  ```python
  def update_email(self, user_id: int, email: str) -> Optional[dict]:
      self._conn.execute(
          "UPDATE users SET email = ? WHERE id = ?", (email, user_id)
      )
      self._conn.commit()
      self._cache.pop(user_id, None)   # invalidate stale entry
      return self.get_user(user_id)    # re-fetch and re-cache fresh data

  def deactivate_user(self, user_id: int) -> bool:
      cursor = self._conn.execute(
          "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,)
      )
      self._conn.commit()
      self._cache.pop(user_id, None)   # invalidate stale entry
      return cursor.rowcount > 0
  ```

- Run the full test suite. All tests must pass, including `test_update_email` and `test_deactivate_user`.

**Deployable:** Each method change is independent and small.

**Reversibility:** Remove the `_cache.pop` calls and the cache dict; tests revert to confirming DB-only behaviour.

---

## Phase 3: Verify Correctness and Cache Consistency (Earning Steps)

### Step 3.1 — Add tests for cache invalidation after writes (1h)

**Type:** Earning

**What to do:**
- Add two tests that confirm the cache does not serve stale data:

  ```python
  def test_cache_invalidated_after_update_email(svc):
      user = svc.create_user("eve", "eve@example.com")
      uid = user["id"]
      svc.get_user(uid)              # populate cache
      svc.update_email(uid, "eve.new@example.com")
      fresh = svc.get_user(uid)
      assert fresh["email"] == "eve.new@example.com"

  def test_cache_invalidated_after_deactivate(svc):
      user = svc.create_user("frank", "frank@example.com")
      uid = user["id"]
      svc.get_user(uid)              # populate cache
      svc.deactivate_user(uid)
      fresh = svc.get_user(uid)
      assert fresh["is_active"] == 0
  ```

- Run full test suite. All must pass.

**Deployable:** Tests are the verification artifact.

**Reversibility:** Tests can be deleted if the cache is removed.

---

### Step 3.2 — Handle cache miss for non-existent users (30 min — bundled into 3.1 slot)

**Type:** Earning

**What to do:**
- Verify (by reading the code from Step 2.2) that `get_user` already returns `None` and does **not** cache the `None` result. Caching `None` would mean a user created after the first miss would not be visible — which would be a bug.
- The implementation in Step 2.2 only caches when `row is not None`, so this is already correct.
- Add or confirm an existing test covers this:
  ```python
  def test_get_user_not_found_returns_none(svc):
      assert svc.get_user(999) is None
  ```
  (This is already covered implicitly by `test_deactivate_nonexistent_user` but an explicit `get_user` miss test is valuable.)

**Deployable:** Verification step, no code change needed.

**Reversibility:** N/A.

---

## Summary

| Step | Type | Duration | Deployable | Reversible |
|------|------|----------|------------|------------|
| 1.1 Identify invalidation points | Learning | 1h | Yes (doc artifact) | Yes |
| 2.1 Failing test for cache hit | Earning | 1h | Yes | Yes |
| 2.2 Implement cache in `get_user` | Earning | 1h | Yes | Yes |
| 2.3 Invalidate cache in write methods | Earning | 1h | Yes | Yes |
| 3.1 Tests for cache invalidation | Earning | 1h | Yes | Yes |
| 3.2 Verify None not cached | Earning | 0.5h | Yes | Yes |

**Total estimated time:** ~5.5 hours across 2 sessions.

---

## Self-Check

- [x] Every step takes 1-3 hours (no step exceeds this)
- [x] Every step is deployable (test file, or code change that keeps all tests green)
- [x] Every step is reversible (cache can be removed without data loss)
- [x] No expand-contract needed (this is not a breaking/risky change)
- [x] Learning step (1.1) comes before earning steps
- [x] Cache invalidation covered in write methods (`update_email`, `deactivate_user`)
- [x] `None` result is not cached (avoids false-miss bug)
- [x] Existing tests (`test_update_email`, `test_deactivate_user`) remain green throughout
