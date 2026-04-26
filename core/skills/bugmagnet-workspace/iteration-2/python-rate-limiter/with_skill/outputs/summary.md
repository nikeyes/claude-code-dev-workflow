# BugMagnet Session Summary — rate_limiter.py

**Date:** 2026-04-26
**File analyzed:** `rate_limiter.py`
**Language / framework:** Python / pytest

---

## Test Coverage Summary

**Tests Added: 57 total** (including 3 original baseline tests)

| Category | Tests |
|---|---|
| Baseline (original) | 3 |
| Token refill behavior | 3 |
| Independent key isolation | 2 |
| `is_allowed` — cost parameter | 4 |
| `is_allowed` — request timestamp tracking | 4 |
| `get_remaining` — full structure | 5 |
| `get_wait_time` | 6 |
| `cleanup_expired` | 5 |
| `get_all_keys` | 3 |
| Factory functions | 4 |
| Phase 4 exploratory (bugmagnet session) | 18 |

**Final Count:**
- **54 passing tests** (expected — not verified due to no Bash execution permission)
- **3 skipped tests** (bugs documented)
- **Total: 57 tests**

> Note: Tests were written and manually traced against the implementation but could not be executed due to tooling restrictions. All assertions were verified by hand-tracing the implementation logic.

---

## Key Findings About Behavior

1. **Token bucket starts full**: New keys are initialized with `max_tokens` tokens.
2. **Sliding window uses strict `>` boundary**: Timestamps exactly at `now - window_seconds` are excluded from the count.
3. **`cleanup_expired` uses strict `>` threshold**: An entry idle for exactly `2 * window_seconds` is NOT removed.
4. **Side effects from read-only methods**: Both `get_remaining` and `get_wait_time` call `_get_or_create`, which creates a new entry for keys that have never been seen. This is documented as a characterization test.
5. **`_refill` guards against backward time**: `elapsed <= 0` is ignored without updating `last_refill`, so clock skew does not corrupt state.
6. **`get_wait_time` does not clean the sliding window**: Unlike `is_allowed` and `get_remaining` (which both call `_clean_window`), `get_wait_time` omits this call. This is a latent inconsistency — the functional result of `get_wait_time` is correct, but stale timestamps in `request_timestamps` are only cleaned lazily on the next `is_allowed` or `get_remaining` call.

---

## Bugs Discovered

### BUG 1 — Negative cost inflates token balance above max_tokens

**Severity:** Medium

**Location:** `rate_limiter.py:60-62`

**Description:** Passing a negative `cost` to `is_allowed` always evaluates `entry.tokens >= cost` as True (any non-negative value >= any negative value), then executes `entry.tokens -= cost`, which ADDS the absolute value to the token balance. This allows the balance to exceed `max_tokens`.

**Root cause:**
```python
# rate_limiter.py:60-62
if entry.tokens >= cost:        # True for any negative cost
    entry.tokens -= cost        # Subtracting a negative = adding
    entry.request_timestamps.append(now)
    return True
```

**Proposed fix:**
```python
def is_allowed(self, key: str, cost: float = 1.0, now: float | None = None) -> bool:
    if cost < 0:
        raise ValueError(f"cost must be non-negative, got {cost}")
    ...
```

**Expected:** `ValueError` raised or `False` returned for negative cost.
**Actual:** `is_allowed` returns `True` and token balance grows above `max_tokens`.

**Minimal reproduction:**
```python
rl = RateLimiter(max_tokens=5, refill_rate=1.0)
rl.is_allowed("user1", cost=-1.0, now=100.0)
status = rl.get_remaining("user1", now=100.0)
assert status["remaining_tokens"] == 6.0  # exceeds max_tokens=5
```

---

### BUG 2 — `get_wait_time` raises `ZeroDivisionError` when `refill_rate=0`

**Severity:** High

**Location:** `rate_limiter.py:81`

**Description:** When `refill_rate=0` and the token bucket is exhausted, `get_wait_time` attempts to divide the deficit by zero.

**Root cause:**
```python
# rate_limiter.py:80-81
deficit = cost - entry.tokens
return deficit / self.refill_rate   # ZeroDivisionError when refill_rate=0
```

**Proposed fix:**
```python
if self.refill_rate == 0:
    return float("inf")   # bucket will never refill
deficit = cost - entry.tokens
return deficit / self.refill_rate
```

**Expected:** Returns `float('inf')` — the request can never be satisfied.
**Actual:** Raises `ZeroDivisionError`.

**Minimal reproduction:**
```python
rl = RateLimiter(max_tokens=1, refill_rate=0.0)
rl.is_allowed("user1", now=100.0)   # exhaust the token
rl.get_wait_time("user1", now=100.0)   # ZeroDivisionError
```

---

### BUG 3 — `get_wait_time` omits `_clean_window` call (design inconsistency)

**Severity:** Low (latent)

**Location:** `rate_limiter.py:66-81`

**Description:** `get_wait_time` calls `_get_or_create` and `_refill` but not `_clean_window`, unlike both `is_allowed` and `get_remaining` which call all three. While `get_wait_time` itself does not use `request_timestamps`, the omission means stale timestamps outside the window are not cleaned up until the next `is_allowed` or `get_remaining` call. Callers relying only on `get_wait_time` between polling intervals will accumulate stale window data.

**Root cause:**
```python
# rate_limiter.py:73-81 — _clean_window is missing
entry = self._get_or_create(key, now)
self._refill(entry, now)
# self._clean_window(entry, now)   ← not called
```

**Proposed fix:** Add `self._clean_window(entry, now)` after `self._refill(entry, now)` in `get_wait_time`.

**Impact:** Low — `get_wait_time`'s return value is not affected. The only observable effect is slightly delayed cleanup of `request_timestamps`, which are eventually cleaned on the next `is_allowed` or `get_remaining` call.

---

## Untested Behaviors / Design Limitations Documented

- **`cost > max_tokens`**: The bucket can never hold that many tokens, so `is_allowed` will always return `False`. `get_wait_time` returns a mathematically correct but practically unreachable wait time (e.g., cost=1000 on a max_tokens=5 bucket → wait=995 s, but the request can never succeed even after waiting).
- **`cost=0`**: Always allowed; the timestamp is still appended to the window. This is a boundary behavior that may or may not be intentional.
- **Side effect of `get_wait_time` / `get_remaining`**: Both methods create an entry for unseen keys. Callers should be aware that these "read" operations have a write side effect.
