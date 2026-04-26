# Test Desiderata Analysis: test_auth_service.py

**File analyzed:** `core/skills/test-desiderata-workspace/evals/files/test_auth_service.py`
**Framework:** Kent Beck's Test Desiderata (12 properties)
**Date:** 2026-04-26

---

## Summary

This test file is **well-written** across nearly all 12 Test Desiderata properties. The tests demonstrate strong discipline: each test class groups related concerns, fixtures are scoped per-test for isolation, assertions target observable behavior rather than internal state, and test names clearly communicate intent.

**Overall verdict:** No major violations. One minor gap identified under **Predictive** (borderline — the brute-force lockout path is partially tested via a convoluted test rather than a dedicated, direct test). All other properties are met.

---

## Property-by-Property Assessment

### 1. Isolated — PASS

Each test receives a fresh `AuthService` instance via the `service` fixture, which returns a new object on every invocation. The `registered_user` fixture composes on top of `service`, inheriting the same per-test instantiation.

- No shared mutable state between tests.
- No class-level or module-level state.
- Tests can run in any order with identical results.

**No issues found.**

---

### 2. Composable — PASS

The fixture design demonstrates good composability:
- `service` is a minimal building block (bare `AuthService`).
- `registered_user` composes on top of `service` by adding a pre-registered user.
- Tests that need a bare service use `service`; tests that need a pre-registered user use `registered_user`.

Different test scenarios are covered independently across `TestRegistration`, `TestLogin`, `TestLogout`, and `TestDeactivation`, making it easy to add or combine new dimensions.

**No issues found.**

---

### 3. Deterministic — PASS

All tests are fully deterministic:
- No random data generation (passwords and usernames are hardcoded strings).
- No time-dependent assertions (`time.sleep`, `datetime.now`, etc.).
- No network calls or external service dependencies.
- The `AuthService` is an in-memory implementation with no I/O.

The SHA-256 hash used to produce tokens is deterministic given the same input, so `is_authenticated` checks are stable.

**No issues found.**

---

### 4. Fast — PASS

All operations are in-memory Python:
- No database access, file I/O, or network calls.
- No `sleep` or artificial delays.
- SHA-256 hashing is negligible overhead.
- The full suite should complete in well under 1 second.

**No issues found.**

---

### 5. Writable — PASS

Adding a new test is low-friction:
- The `service` and `registered_user` fixtures abstract away all setup boilerplate.
- `pytest.raises` with `match=` makes exception assertions concise and readable.
- The class-based grouping provides clear homes for new tests without requiring new infrastructure.

**No issues found.**

---

### 6. Readable — PASS

Test names are descriptive and follow the pattern `test_<action>_<condition>_<expected_outcome>`:
- `test_register_duplicate_username_raises`
- `test_login_wrong_password_raises`
- `test_deactivated_user_cannot_login`

Comments inside tests explain non-obvious intent (e.g., `# Behavioral: failed_attempts is observable via lockout behavior`).

The Arrange-Act-Assert structure is clear in most tests. Fixture names (`service`, `registered_user`) communicate their role.

**No issues found.**

---

### 7. Behavioral — PASS (with minor note)

Tests assert on externally observable behavior rather than internal state:
- Registration is verified by successfully logging in afterward (`test_register_new_user_succeeds`).
- Failed attempt counting is verified indirectly through the lockout behavior, not by inspecting `user.failed_attempts` directly (`test_login_increments_failed_attempts_on_wrong_password`).
- Token validity is verified via `is_authenticated`, not by checking the `_sessions` dict.

This is a strong example of behavior-oriented testing.

**Minor note:** `test_login_increments_failed_attempts_on_wrong_password` uses a somewhat roundabout loop to trigger lockout. The intent is correct (observe behavior, not internals), but see Specific section below for a related concern.

**No major issues found.**

---

### 8. Structure-insensitive — PASS

No test accesses private attributes (`_users`, `_sessions`) or internal methods. All assertions go through the public API (`register`, `login`, `logout`, `is_authenticated`, `deactivate_user`). Refactoring the internal storage from a dict to a database, or changing the token generation algorithm, would not break these tests as long as the public contract is preserved.

**No issues found.**

---

### 9. Automated — PASS

All tests are fully automated:
- No `print` statements requiring human inspection.
- No interactive prompts.
- No manual data setup steps.
- pytest fixtures handle all setup and teardown automatically.

**No issues found.**

---

### 10. Specific — MINOR CONCERN

Most tests have a single assertion per test with a clear failure message. However, `test_login_increments_failed_attempts_on_wrong_password` is more complex than necessary:

```python
def test_login_increments_failed_attempts_on_wrong_password(self, registered_user):
    with pytest.raises(PermissionError):
        registered_user.login("alice", "wrong")
    with pytest.raises(PermissionError):
        registered_user.login("alice", "wrong")
    # Behavioral: failed_attempts is observable via lockout behavior
    for _ in range(3):
        try:
            registered_user.login("alice", "wrong")
        except PermissionError:
            pass
    with pytest.raises(PermissionError, match="locked"):
        registered_user.login("alice", "securepass123")
```

This test does several things at once:
1. Makes 2 explicit failed attempts.
2. Makes 3 more attempts in a loop (silencing the errors).
3. Asserts the account is now locked.

If this test fails, it is not immediately obvious whether the failure is in the counting logic or in the lockout-message logic. The loop with `try/except/pass` hides failures that occur during the "setup" phase.

**Issue (minor):**
```
Issue: test_login_increments_failed_attempts_on_wrong_password violates Specific property
Location: Lines 113-125 — loop with silent exception swallowing obscures failure root cause
Impact: If lockout triggers at the wrong threshold (e.g., attempt 4 vs 5), the test failure message
        won't pinpoint which attempt was the trigger.
Fix: Split into: (a) a focused test that reaches exactly 5 failed attempts then asserts locked,
     using explicit repetition rather than a loop; (b) remove silent try/except.
Tradeoff: Slightly more lines, but each failure points directly to the broken assertion.
```

---

### 11. Predictive — MINOR GAP

The test suite covers the main happy paths and common error scenarios well. However, there is one notable gap:

**Brute-force lockout boundary is not tested as a standalone scenario.**

The lockout behavior is only exercised inside `test_login_increments_failed_attempts_on_wrong_password`, which serves double duty as a state-transition test AND a lockout test. There is no dedicated test asserting:
- That exactly `MAX_FAILED_ATTEMPTS` (5) attempts are required before lockout (not 4, not 6).
- That a correct password after fewer than 5 failures resets the counter to zero and prevents lockout.

The second scenario is partially covered by `test_login_resets_failed_attempts_on_success`, but it only tests one wrong attempt before the reset, not a near-boundary case (e.g., 4 wrong attempts, then reset, then 4 more should not lock).

**Issue (minor/borderline):**
```
Issue: Missing boundary test for MAX_FAILED_ATTEMPTS threshold
Location: TestLogin class — no test asserting exactly 5 (not 4, not 6) attempts trigger lockout
Impact: A change from MAX_FAILED_ATTEMPTS = 5 to MAX_FAILED_ATTEMPTS = 4 would not be caught
        by the existing tests if the existing test happens to still lock at its current count.
Fix: Add test_account_locks_after_exactly_max_failed_attempts that explicitly makes
     MAX_FAILED_ATTEMPTS - 1 wrong attempts (asserting no lock), then one more (asserting locked).
Tradeoff: Slightly more tests, stronger regression protection for the security-critical lockout path.
```

---

### 12. Inspiring — PASS (with minor note)

The test suite covers meaningful behaviors that build confidence in the `AuthService`:
- Registration success and failure modes.
- Login with valid and invalid credentials.
- Session invalidation via logout.
- Account deactivation preventing login.
- Failed attempt tracking and reset.

These tests reflect real usage scenarios and give a reader confidence that the service behaves correctly.

**Minor note:** The boundary condition for lockout (see Predictive above) is the primary area where confidence could be slightly stronger, particularly for a security-sensitive feature.

---

## Prioritized Recommendations

Based on the analysis, ordered by impact:

### Priority 1 — Clarify `test_login_increments_failed_attempts_on_wrong_password` (Specific)

Split the complex test into two focused tests:

```python
def test_account_locks_after_max_failed_attempts(self, registered_user):
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
        with pytest.raises(PermissionError, match="Invalid credentials"):
            registered_user.login("alice", "wrongpassword")
    with pytest.raises(PermissionError, match="locked"):
        registered_user.login("alice", "securepass123")

def test_failed_attempts_do_not_lock_before_threshold(self, registered_user):
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrongpassword")
    # One below threshold: correct password should still work
    token = registered_user.login("alice", "securepass123")
    assert registered_user.is_authenticated(token)
```

This makes each test fail for exactly one reason and documents the exact lockout threshold.

### Priority 2 — Add a near-boundary reset test (Predictive)

```python
def test_login_reset_prevents_lockout_after_near_boundary(self, registered_user):
    # Reach MAX - 1 failures
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrong")
    # Successful login resets counter
    registered_user.login("alice", "securepass123")
    # MAX - 1 more failures should NOT lock the account
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrong")
    token = registered_user.login("alice", "securepass123")
    assert registered_user.is_authenticated(token)
```

---

## Tradeoff Analysis

The two improvements above create a small tension:

- **Specific + Fast**: Splitting the test adds test count but each test runs just as fast (all in-memory). No real tradeoff here.
- **Predictive + Writable**: Adding near-boundary tests increases test complexity slightly. The tradeoff is acceptable for a security-critical feature like account lockout.

The existing tests already demonstrate good balance between **Isolated + Deterministic** (both fully satisfied) and **Fast + Predictive** (fast tests with meaningful, but not exhaustive, scenario coverage).

---

## Overall Scorecard

| Property            | Score     | Notes                                              |
|---------------------|-----------|----------------------------------------------------|
| Isolated            | Excellent | Fresh fixture per test, no shared state            |
| Composable          | Excellent | Layered fixtures, independent test classes         |
| Deterministic       | Excellent | No randomness, no I/O, no time dependency          |
| Fast                | Excellent | Fully in-memory                                    |
| Writable            | Excellent | Low-friction fixtures, clear patterns              |
| Readable            | Excellent | Descriptive names, good structure                  |
| Behavioral          | Excellent | Public API only, behavior not internals            |
| Structure-insensitive | Excellent | No access to private attributes                  |
| Automated           | Excellent | Fully automated, no manual steps                   |
| Specific            | Good      | Minor: one test covers too much at once            |
| Predictive          | Good      | Minor gap: lockout threshold boundary not explicit |
| Inspiring           | Good      | Strong coverage; one security boundary could be stronger |

**Conclusion:** This is a high-quality test suite. The two minor improvements identified would strengthen an already well-designed set of tests, particularly for a security-critical feature.
