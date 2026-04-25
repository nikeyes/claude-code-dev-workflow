## Validation Report: Add IP-Based Rate Limiting to API Gateway

### Implementation Status

Phase 1: IP Rate Limiter Core — Deviations found
Phase 2: IP Allowlist and Monitoring — Deviations found

---

### Automated Verification

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.0.3, pluggy-1.6.0
rootdir: eval-4-semantic-mismatch
collected 8 items

test_api_gateway.py::test_allows_initial_request PASSED                  [ 12%]
test_api_gateway.py::test_blocks_after_max_requests PASSED               [ 25%]
test_api_gateway.py::test_does_not_affect_other_identifiers PASSED       [ 37%]
test_api_gateway.py::test_get_remaining_decreases PASSED                 [ 50%]
test_api_gateway.py::test_allowlisted_bypasses_limit PASSED              [ 62%]
test_api_gateway.py::test_remove_from_allowlist PASSED                   [ 75%]
test_api_gateway.py::test_get_top_offenders PASSED                       [ 87%]
test_api_gateway.py::test_get_remaining_for_allowlisted PASSED           [100%]

============================== 8 passed in 0.01s ===============================
```

8 tests pass, 0 failures.

---

### Findings

#### Critical Semantic Mismatch: IP address replaced by session ID throughout

The plan explicitly and repeatedly specifies **IP address** as the rate limiting key. The implementation instead uses **session_id** everywhere. This is not a renaming detail — it is a fundamental change in what the system does.

| Plan specifies | Implementation provides |
|---|---|
| `check_rate_limit(ip_address)` | `check_rate_limit(session_id)` |
| `record_request(ip_address)` | `record_request(session_id)` |
| `get_remaining(ip_address)` | `get_remaining(session_id)` |
| `is_allowlisted(ip_address)` | `is_allowlisted(session_id)` |
| `add_to_allowlist(ip_address)` | `add_to_allowlist(session_id)` |
| `remove_from_allowlist(ip_address)` | `remove_from_allowlist(session_id)` |
| `get_top_offenders(n)` returns IPs | `get_top_offenders(n)` returns session IDs |
| Internal key: IP address | Internal key: session_id (string like "sess-001") |

The plan states: "Each unique IP should be tracked independently." The implementation tracks session IDs independently — an entirely different identity model. A single client with multiple sessions would bypass limits; a NAT gateway with many clients sharing one IP would not be rate-limited at all.

#### Unused code not in the plan

`api_gateway.py` contains a `_get_session_id(self, request_context)` helper method (line 12–13) that is never called anywhere in the implementation or tests. This method takes a `request_context` dict and extracts or generates a `session_id`. It is dead code and is not mentioned in the plan.

#### Tests validate the wrong behavior

All 8 tests pass, but they test session-based rate limiting rather than IP-based rate limiting. Test identifiers use strings like `"sess-001"`, `"sess-002"`, `"sess-heavy"`, `"sess-vip"` — none use IP address strings (e.g., `"192.168.1.1"`). The tests confirm the implementation works as built, but they do not verify the plan's actual requirement.

Specific plan success criteria that are NOT verified by tests:
- "Rate limiting is per-IP: blocking one IP does not affect another" — `test_does_not_affect_other_identifiers` tests this logic but with session IDs, not IPs. The test name also avoids the word "IP".
- "Allowlisted IPs are never blocked" — tested with session IDs.
- "`get_top_offenders` returns IPs sorted by request count" — returns session IDs, not IPs.

#### Manual verification items: unverifiable as implemented

The plan's manual verification items cannot be assessed against this implementation:

- "Rate limiter handles IPv4 and IPv6 addresses" — The implementation accepts arbitrary strings; there is no IP address parsing, validation, or normalization. It would accept IPv4 and IPv6 strings, but only incidentally. No IPv4/IPv6 test coverage exists.
- "No shared state between different IP addresses" — The implementation has no concept of IP addresses; it has no shared state between session IDs, but that is a different property.
- "Allowlist persists across rate limit window resets" — This can be partially validated: the `_allowlist` set is not cleared when windows reset. However, this is never explicitly tested.

#### What does match the plan

The structural and algorithmic implementation is correct relative to the plan's intent:
- `APIGateway` class exists in `api_gateway.py`.
- Sliding window of 60 seconds with default limit of 100 requests is implemented correctly.
- `get_remaining` correctly returns `max_requests` for allowlisted identifiers.
- `get_top_offenders(n)` correctly sorts by descending request count and returns the top N.
- Allowlist bypasses rate limiting (returns True from `check_rate_limit`).
- `add_to_allowlist` / `remove_from_allowlist` / `is_allowlisted` all work correctly as a set.
- Sliding window correctly prunes expired timestamps on each check.

---

### Recommendations

1. **Rename all method parameters from `session_id` to `ip_address`** across `api_gateway.py`. This is the primary deviation — the plan's public API contract specifies `ip_address` as the parameter name.

2. **Update internal storage key** from `session_id` to `ip_address` in `_requests` and `_allowlist` to match the domain model.

3. **Remove the dead `_get_session_id` method** — it is unused and not in the plan.

4. **Update all test identifiers** from `"sess-XXX"` strings to IP address strings (e.g., `"192.168.1.1"`, `"10.0.0.2"`, `"::1"`). This makes tests verifiable against the plan's success criteria.

5. **Add tests for IPv4 and IPv6** to cover the manual verification item "Rate limiter handles IPv4 and IPv6 addresses."

6. **Add a test verifying allowlist persistence across window resets** to cover the manual verification item "Allowlist persists across rate limit window resets."

The algorithmic logic is sound and does not need to change. Only the naming and test fixtures need to be corrected to satisfy the plan as written.
