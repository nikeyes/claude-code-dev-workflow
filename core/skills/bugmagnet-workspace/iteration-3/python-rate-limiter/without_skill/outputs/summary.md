# Bug Discovery Summary — Python Token Bucket Rate Limiter

## Files analysed
- `rate_limiter.py` — implementation
- `test_rate_limiter.py` — baseline tests (3 happy-path tests only)

---

## Coverage gaps in the baseline suite

The three existing tests exercise only the most basic path:

| Covered | Not covered |
|---------|-------------|
| Single allowed request | Refill over time |
| Drain to zero and block | Fractional / custom cost |
| Token count after one request | Key isolation |
| — | Sliding window cleanup |
| — | `get_wait_time` |
| — | `get_remaining` introspection |
| — | `cleanup_expired` |
| — | `get_all_keys` |
| — | Factory functions |
| — | Boundary / negative inputs |

---

## Confirmed bugs

### BUG-1 — `get_wait_time` divides by zero when `refill_rate=0`

**Location**: `rate_limiter.py:81`  
**Code**: `return deficit / self.refill_rate`  
**Trigger**: Create a limiter with `refill_rate=0.0`, exhaust tokens, then call `get_wait_time`.  
**Effect**: `ZeroDivisionError` at runtime.  
**Fix**: Guard with `if self.refill_rate == 0: return math.inf` (or raise `ValueError`).

```python
# Reproducer
rl = RateLimiter(max_tokens=1, refill_rate=0.0)
rl.is_allowed("u", now=0.0)
rl.get_wait_time("u", now=0.0)   # ZeroDivisionError
```

---

### BUG-2 — `get_wait_time` gives a wrong (finite) answer when `cost > max_tokens`

**Location**: `rate_limiter.py:80-81`  
**Scenario**: `cost=10`, `max_tokens=5`, `refill_rate=1.0`.  
**Current behaviour**: Returns `5.0` seconds (as if waiting will eventually help).  
**Actual behaviour**: `is_allowed` will still return `False` after waiting because tokens are capped at `max_tokens=5`, which is less than `cost=10`.  
**Fix**: Before computing the wait, check `if cost > self.max_tokens: return math.inf`.

---

### BUG-3 — `create_rate_limiter(0)` silently creates a broken limiter

**Location**: `rate_limiter.py:121-127`  
**Effect**: `max_tokens=0` and `refill_rate=0.0` — every request is denied and `get_wait_time` raises `ZeroDivisionError`.  
**Fix**: Validate `requests_per_minute > 0` and raise `ValueError` with a clear message.

---

### BUG-4 — Negative `cost` corrupts the token count

**Location**: `rate_limiter.py:60-63`  
**Scenario**: `cost=-1.0` when the bucket is empty.  
**Effect**: The guard `entry.tokens >= cost` is `0 >= -1 → True`, so the request is admitted and `entry.tokens -= cost` increases the token count above zero — effectively a "free refill via negative cost".  
**Fix**: Validate `cost >= 0` at the top of `is_allowed` (and `get_wait_time`).

---

## Design gaps / edge-case findings

### FINDING-1 — Boundary exclusion in `_clean_window` is inconsistent with common conventions

`_clean_window` uses `ts > cutoff` (strict greater-than), so a timestamp at exactly `now - window_seconds` is excluded from the window. This is correct for a strict sliding window, but callers expecting an inclusive boundary will see one fewer request counted than expected. The behaviour should be documented.

---

### FINDING-2 — `cleanup_expired` uses `last_refill`, not last-request time

Every call to `get_remaining` (or `get_wait_time`) triggers `_refill`, which updates `last_refill`. A key that is frequently polled but never has a request allowed will therefore never be cleaned up. If the intent is to expire truly idle keys, the expiry check should be based on the last *allowed* request timestamp, not `last_refill`.

---

### FINDING-3 — `get_remaining` creates entries as a side-effect

Calling `get_remaining("new_key")` on a key that has never been seen creates an `_Entry` and adds it to `_entries`. This means monitoring/health-check calls silently populate the limiter's memory. Depending on the use-case this may be intentional, but it is not documented and can cause memory growth in systems with many probing calls.

---

### FINDING-4 — `get_all_keys` returns a fresh list (safe), but the docstring does not say so

The implementation `list(self._entries.keys())` correctly returns a copy. This is good, but if callers rely on it being a live view they will be surprised. Worth documenting.

---

### FINDING-5 — No thread safety

All mutable state is in plain Python dicts and floats with no locking. In a multi-threaded environment TOCTOU races exist between the token check and the token decrement in `is_allowed`. This is out of scope for a single-threaded token bucket but should be called out in the docstring.

---

## Test file produced

`test_rate_limiter_edge_cases.py` — 50+ test cases organised into these classes:

| Class | Focus |
|-------|-------|
| `TestConstructorBoundaries` | Zero capacity, zero refill, fractional max |
| `TestTokenRefill` | Time-based refill, cap at max, backward time |
| `TestCostParameter` | Custom cost, zero cost, negative cost, cost > max |
| `TestKeyIsolation` | Independent keys, empty/unicode/long keys |
| `TestSlidingWindow` | Window cleanup, boundary ts, denied vs. allowed counts |
| `TestGetWaitTime` | Correct wait, zero-refill bug, cost > max bug |
| `TestCleanupExpired` | Threshold boundary, multiple entries, last_refill issue |
| `TestGetAllKeys` | Empty, populated, mutation safety |
| `TestFactoryFunctions` | RPM limiter, burst limiter, zero-RPM bug |
| `TestNowParameter` | Explicit `now` in all public methods |
| `TestHighVolumePatterns` | Burst, interleaved allow/deny |
