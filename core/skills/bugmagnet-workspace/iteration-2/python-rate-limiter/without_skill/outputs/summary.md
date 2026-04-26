# Rate Limiter Bug Report and Test Coverage Summary

## Overview

- **Implementation file**: `rate_limiter.py`
- **Original tests**: 3 (happy-path only)
- **New tests added**: 46
- **Total tests**: 49
- **Bugs discovered**: 4 confirmed bugs + 1 design flaw

---

## Bugs Discovered

### Bug 1: Division by zero in `get_wait_time` when `refill_rate=0`

**Severity**: High (crash)
**Location**: `rate_limiter.py`, `get_wait_time` method, line 81
**Root cause**: When `refill_rate=0` and the bucket is empty, the method computes `deficit / self.refill_rate`, which is a division by zero. A limiter with `refill_rate=0` is a valid configuration (fixed quota, no replenishment), but calling `get_wait_time` on it after exhaustion raises `ZeroDivisionError` instead of returning `math.inf` or raising a meaningful error.

**Reproducing test**: `test_get_wait_time_with_refill_rate_zero_raises`

**Proposed fix**:
```python
if self.refill_rate == 0:
    return float("inf")
deficit = cost - entry.tokens
return deficit / self.refill_rate
```

---

### Bug 2: Negative `cost` inflates tokens beyond `max_tokens`

**Severity**: Medium (token integrity violation)
**Location**: `rate_limiter.py`, `is_allowed` method, line 61
**Root cause**: There is no validation that `cost` is positive. A negative cost causes `entry.tokens -= cost` to add tokens instead of removing them, bypassing the `min(max_tokens, ...)` cap applied only during refill. This allows the bucket to hold more tokens than `max_tokens`.

**Reproducing test**: `test_is_allowed_negative_cost_inflates_tokens`

**Proposed fix**: Add a guard at the start of `is_allowed`:
```python
if cost < 0:
    raise ValueError(f"cost must be non-negative, got {cost}")
```

---

### Bug 3: `resets_at` in `get_remaining` is semantically meaningless

**Severity**: Medium (API contract violation / misleading output)
**Location**: `rate_limiter.py`, `get_remaining` method, line 96
**Root cause**: `resets_at` is computed as `entry.last_refill + window_seconds`. However, `last_refill` is updated to `now` on *every* call that invokes `_refill` (including `get_remaining` itself). This means `resets_at` is always `now + window_seconds`, not a stable future reset timestamp. Callers relying on this field to determine when to retry will get incorrect information — each call shifts the apparent reset point forward.

**Reproducing test**: `test_get_remaining_resets_at_is_misleading`

**Proposed fix**: Track the entry creation time or the time the bucket was last fully consumed, and use that as the basis for `resets_at`. Alternatively, remove the field or document that it represents a rolling horizon.

---

### Bug 4: `cleanup_expired` expiry clock is reset by read-only queries

**Severity**: Low-Medium (memory leak)
**Location**: `rate_limiter.py`, `cleanup_expired` method (lines 99-114) and `_refill` method (line 43)
**Root cause**: `_refill` always updates `entry.last_refill = now`. Because `get_remaining` and `get_wait_time` both call `_refill`, any monitoring call on a key resets its expiry clock. An entry that is polled periodically (e.g., by a health check) can never be removed by `cleanup_expired`, even if no actual requests are being made. This causes unbounded memory growth in long-running processes.

**Reproducing test**: `test_cleanup_does_not_remove_freshly_queried_entries`

**Proposed fix**: Track a separate `last_active` timestamp that is only updated when `is_allowed` returns `True`, and use `last_active` in `cleanup_expired`.

---

### Design Flaw (not a crash, but problematic): `cost=0` accepted silently

**Severity**: Low
**Location**: `rate_limiter.py`, `is_allowed`, lines 60-63
**Root cause**: A cost of `0` always satisfies `entry.tokens >= cost`, so `is_allowed` always returns `True` and appends a timestamp, even on a limiter configured with `max_tokens=0`. This can cause unbounded growth of `request_timestamps` without any token consumption and may mask misconfigured callers.

**Reproducing test**: `test_is_allowed_cost_zero_always_allowed`

**Proposed fix**: Treat `cost=0` as a no-op (return `True` without appending a timestamp) or raise a `ValueError`.

---

## Coverage Assessment

| Area | Baseline coverage | After new tests |
|------|------------------|-----------------|
| `is_allowed` — happy path | Yes | Yes |
| `is_allowed` — token exhaustion | Yes | Yes |
| `is_allowed` — token refill over time | No | Yes |
| `is_allowed` — refill cap at max_tokens | No | Yes |
| `is_allowed` — fractional cost | No | Yes |
| `is_allowed` — cost = max_tokens | No | Yes |
| `is_allowed` — cost > max_tokens | No | Yes |
| `is_allowed` — cost = 0 (bug) | No | Yes |
| `is_allowed` — negative cost (bug) | No | Yes |
| `is_allowed` — same timestamp no-op refill | No | Yes |
| `is_allowed` — denied request not in timestamps | No | Yes |
| `is_allowed` — key isolation | No | Yes |
| `get_wait_time` — returns 0 when allowed | No | Yes |
| `get_wait_time` — correct wait time | No | Yes |
| `get_wait_time` — scales with cost | No | Yes |
| `get_wait_time` — zero after refill | No | Yes |
| `get_wait_time` — refill_rate=0 crash (bug) | No | Yes |
| `get_wait_time` — new key | No | Yes |
| `get_remaining` — token count | Yes | Yes |
| `get_remaining` — requests_in_window | No | Yes |
| `get_remaining` — window boundary exclusion | No | Yes |
| `get_remaining` — window_seconds field | No | Yes |
| `get_remaining` — resets_at misleading (bug) | No | Yes |
| `get_remaining` — new key full bucket | No | Yes |
| `cleanup_expired` — removes idle entries | No | Yes |
| `cleanup_expired` — keeps active entries | No | Yes |
| `cleanup_expired` — returns count | No | Yes |
| `cleanup_expired` — query resets clock (bug) | No | Yes |
| `cleanup_expired` — empty limiter | No | Yes |
| `get_all_keys` — empty initially | No | Yes |
| `get_all_keys` — all seen keys | No | Yes |
| `get_all_keys` — after cleanup | No | Yes |
| `create_rate_limiter` factory | No | Yes |
| `create_burst_limiter` factory | No | Yes |
| Time going backwards | No | Yes |
| Very large elapsed time | No | Yes |

### Summary

- **Original tests covered**: 3 tests, ~15% of meaningful behaviours, no edge cases
- **New tests added**: 46 tests covering all public methods, all parameters, boundary conditions, and documented bugs
- **Bugs confirmed**: 4 real defects (1 crash, 1 token integrity, 1 misleading API, 1 memory leak)
- **Design flaw noted**: 1 (cost=0 accepted silently)
