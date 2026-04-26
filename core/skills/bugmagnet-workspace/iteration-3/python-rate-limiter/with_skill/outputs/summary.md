## Test Coverage Summary

**Tests Added:** 44 total
- Token bucket boundary conditions (5 tests)
- Zero and negative cost inputs (3 tests)
- Refill logic (5 tests)
- `get_wait_time` behaviour (6 tests)
- Sliding window boundary conditions (4 tests)
- Key isolation (4 tests)
- `cleanup_expired` (7 tests)
- `get_remaining` (5 tests)
- Factory helpers (5 tests)
- Multi-step sequences (3 tests)

**Results:** 41 passing, 3 skipped (bugs)

**Bugs Discovered:**

1. `get_wait_time` ZeroDivisionError when `refill_rate=0` — `rate_limiter.py:81`
   - Root cause: `deficit / self.refill_rate` is executed unconditionally; when `refill_rate` is `0.0` this raises `ZeroDivisionError`.
   - Proposed fix: Guard with `if self.refill_rate == 0: return math.inf` (or raise a descriptive `ValueError`) before the division.

2. `create_rate_limiter(0)` + `get_wait_time` ZeroDivisionError — `rate_limiter.py:81` (triggered via `rate_limiter.py:125`)
   - Root cause: The factory `create_rate_limiter` accepts `requests_per_minute=0`, producing `refill_rate=0.0`. Any subsequent call to `get_wait_time` on an exhausted key hits the same division-by-zero as bug #1.
   - Proposed fix: Either raise `ValueError` in the factory for `requests_per_minute <= 0`, or apply the same `refill_rate == 0` guard in `get_wait_time`.

3. Negative `cost` silently inflates tokens beyond `max_tokens` — `rate_limiter.py:61-62`
   - Root cause: `is_allowed` subtracts `cost` from `entry.tokens` without validating that `cost >= 0`. A negative value increases the token count, which is never clamped to `max_tokens` at the deduction site (only at refill time).
   - Proposed fix: Add `if cost < 0: raise ValueError("cost must be non-negative")` at the top of `is_allowed` and `get_wait_time`.

---

**Additional observations (not bugs, but worth noting):**

- **`cost > max_tokens` can never be satisfied**: `is_allowed` silently returns `False` forever and `get_wait_time` returns a non-zero wait time, but the request would still fail after waiting. No API-level signal distinguishes "throttled" from "impossible". Callers may loop forever.
- **`get_wait_time` creates a side-effect entry**: calling `get_wait_time` on an unknown key calls `_get_or_create`, inserting a full-token entry into `_entries`. This shows up in `get_all_keys()` even though no request was made. This is unlikely to be the intended design.
- **`_clean_window` uses strict `>` at the cutoff boundary**: a timestamp exactly equal to `now - window_seconds` is excluded from the window. Whether this is a bug depends on the spec (inclusive vs exclusive boundary), but it is worth documenting as a deliberate choice.
- **`resets_at` in `get_remaining` is misleading after partial refills**: after any `_refill` call, `last_refill` is set to `now`, making `resets_at = now + window_seconds`. This represents the end of the sliding request window, not when the token bucket will be fully replenished, which callers might reasonably expect.
