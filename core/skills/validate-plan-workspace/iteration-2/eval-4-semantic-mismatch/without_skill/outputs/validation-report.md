# Validation Report: Add IP-Based Rate Limiting to API Gateway

## Summary

**Plan**: `thoughts/shared/plans/add-ip-rate-limiting.md`
**Implementation**: `api_gateway.py`, `test_api_gateway.py`
**Test result**: 8/8 passed
**Overall verdict**: FAIL — Tests pass but the implementation does not match the plan. The plan specifies IP-based rate limiting; the implementation uses session IDs throughout.

---

## Test Results

```
8 passed in 0.01s
```

All 8 tests pass. No failures, no errors.

---

## Plan vs. Implementation Analysis

### Critical Semantic Mismatch: IP addresses vs. Session IDs

The plan is unambiguous: every feature is defined in terms of **IP addresses**.

| Plan requirement | Implementation reality |
|---|---|
| `check_rate_limit(ip_address)` | `check_rate_limit(session_id)` |
| `record_request(ip_address)` | `record_request(session_id)` |
| `get_remaining(ip_address)` | `get_remaining(session_id)` |
| `is_allowlisted(ip_address)` | `is_allowlisted(session_id)` |
| `add_to_allowlist(ip_address)` | `add_to_allowlist(session_id)` |
| `remove_from_allowlist(ip_address)` | `remove_from_allowlist(session_id)` |
| `get_top_offenders(n)` returns IP addresses | `get_top_offenders(n)` returns session IDs |

The parameter names, internal variable names, docstrings (none exist), and the helper method `_get_session_id(request_context)` all use session-ID semantics. The class also contains an unused helper `_get_session_id` that is never called, suggesting the implementation was adapted from a session-management design rather than written fresh for IP rate limiting.

### Tests reflect session-ID semantics, not IP addresses

The test file uses identifiers like `"sess-001"`, `"sess-002"`, etc. — not IP addresses. The test for isolation (`test_does_not_affect_other_identifiers`) would have used IPv4/IPv6 addresses to match the plan's intent but instead tests session isolation.

Because the tests mirror the (incorrect) implementation, they all pass — but they do not verify any IP-address-specific behaviour.

### Missing plan requirement: IPv4/IPv6 handling

The plan's Manual Verification section requires:
- Rate limiter handles IPv4 and IPv6 addresses

There is no code or test addressing IP address format validation, normalisation, or dual-stack handling. This is a gap even within the session-ID implementation.

### Unused code

`_get_session_id(self, request_context)` (line 12–13) is defined but never called anywhere in the class or tests. It appears to be dead code left over from a different design.

---

## Checklist Against Plan

### Phase 1: IP Rate Limiter Core

| Item | Status | Notes |
|---|---|---|
| `api_gateway.py` with `APIGateway` class | PASS | File and class exist |
| `check_rate_limit(ip_address)` returns True if within limits | FAIL | Signature uses `session_id`, not `ip_address` |
| Track requests per IP using a 60-second sliding window | PARTIAL | Sliding window is correctly implemented, but keyed on session ID not IP |
| Default limit: 100 requests per IP per window | PASS | `max_requests=100`, `window_seconds=60` defaults are correct |
| `record_request(ip_address)` | FAIL | Signature uses `session_id` |
| `get_remaining(ip_address)` | FAIL | Signature uses `session_id` |

### Phase 2: IP Allowlist and Monitoring

| Item | Status | Notes |
|---|---|---|
| `is_allowlisted(ip_address)` | FAIL | Signature uses `session_id` |
| `add_to_allowlist(ip_address)` | FAIL | Signature uses `session_id` |
| `remove_from_allowlist(ip_address)` | FAIL | Signature uses `session_id` |
| `get_top_offenders(n)` returns IPs sorted by request count | FAIL | Returns session IDs; no IP-address semantics |
| Tests in `test_api_gateway.py` covering all functionality | PARTIAL | Tests cover all methods but use session-ID identifiers, not IP addresses |

### Success Criteria (Automated)

| Criterion | Status | Notes |
|---|---|---|
| All tests pass | PASS | 8/8 pass |
| Rate limiting is per-IP: blocking one IP does not affect another | FAIL | The isolation property is tested, but for session IDs, not IP addresses |
| Allowlisted IPs are never blocked | FAIL | Allowlisting works, but for session IDs |
| `get_top_offenders` returns IPs sorted by request count | FAIL | Returns session IDs sorted by count |

### Manual Verification (from plan)

| Item | Status |
|---|---|
| Rate limiter handles IPv4 and IPv6 addresses | NOT IMPLEMENTED |
| No shared state between different IP addresses | NOT VERIFIED (session IDs used instead) |
| Allowlist persists across rate limit window resets | NOT TESTED |

---

## Issues Found

### Issue 1 — Semantic mismatch: session IDs used instead of IP addresses (CRITICAL)

**Severity**: Critical  
**Location**: `api_gateway.py`, entire file; `test_api_gateway.py`, entire file  
**Description**: The plan specifies an IP-based rate limiter. The implementation tracks by session ID. All public method signatures, internal data structures, and tests use `session_id` instead of `ip_address`. The two concepts are not interchangeable: session IDs are typically application-layer tokens, while IP addresses are network-layer identifiers. A session ID rate limiter does not protect against abuse from a single IP that spawns multiple sessions, which is the core threat model the plan is designed to address.

### Issue 2 — Unused helper method (LOW)

**Severity**: Low  
**Location**: `api_gateway.py` lines 12–13  
**Description**: `_get_session_id(self, request_context)` is defined but never called. It should be removed.

### Issue 3 — No IPv4/IPv6 normalisation (MEDIUM)

**Severity**: Medium  
**Location**: Missing from `api_gateway.py`  
**Description**: The plan's manual verification requires handling both IPv4 and IPv6 addresses. There is no normalisation logic (e.g., treating `"::ffff:192.0.2.1"` and `"192.0.2.1"` as the same address), no format validation, and no tests for dual-stack scenarios.

### Issue 4 — Allowlist persistence across window resets not tested (LOW)

**Severity**: Low  
**Location**: `test_api_gateway.py`  
**Description**: The plan explicitly requires verifying that the allowlist persists across rate limit window resets. No such test exists.

---

## Conclusion

The implementation is functionally coherent and all tests pass, but it implements **session-ID-based rate limiting**, not **IP-based rate limiting** as required by the plan. This is a fundamental semantic mismatch — the wrong abstraction was used throughout. The tests were written to match the (incorrect) implementation rather than to validate the plan's requirements, which is why they all pass despite the implementation being wrong.

The code needs to be rewritten to use IP addresses as the tracking key, with tests using actual IP address strings (e.g., `"192.168.1.1"`, `"::1"`), and additional tests added for IPv4/IPv6 handling and allowlist persistence.
