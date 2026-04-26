# Test Desiderata Analysis: test_auth_service.py

## Overview

**File analyzed:** `test_auth_service.py`
**Subject under test:** `AuthService` — a simple authentication service supporting register, login, logout, and user deactivation.
**Test classes:** `TestRegistration` (4 tests), `TestLogin` (5 tests), `TestLogout` (2 tests), `TestDeactivation` (2 tests)
**Total tests:** 13

**Overall verdict:** These tests are well-written. They score strongly across all 12 Test Desiderata properties. One genuine minor gap exists in **Predictive** coverage (brute-force lockout not tested as a first-class scenario), but it does not undermine confidence in the suite. No manufactured violations are listed below.

---

## Property-by-Property Assessment

### 1. Isolated — PASS

Each test receives a fresh `AuthService` instance via the `service` pytest fixture (line 65–68), which returns a new object on every invocation. The `registered_user` fixture composes on top of `service`, so it also gets a clean instance per test.

No shared mutable state exists between tests. Tests can run in any order with identical results.

### 2. Composable — PASS

The test suite decomposes the system cleanly along behavioral boundaries: registration, login, logout, and deactivation are each isolated in their own class. The `service` and `registered_user` fixtures are independent, reusable building blocks that compose naturally. Tests avoid covering multiple concerns in a single assertion block.

`test_login_increments_failed_attempts_on_wrong_password` (lines 113–125) is the most complex test — it loops to trigger lockout behavior — but this complexity reflects the nature of the behavior under test (requiring 5 failures) rather than a decomposition failure. The behavior it checks (lockout after exactly MAX_FAILED_ATTEMPTS) cannot be more granularly split without losing the behavioral signal.

### 3. Deterministic — PASS

No random data, time dependencies, or external service calls are present. All test inputs are hardcoded literals. The `AuthService` uses deterministic hashing (`sha256`) with no entropy sources. Tests will produce the same result on every run.

### 4. Fast — PASS

All operations are pure in-memory. There are no database calls, file I/O, network requests, or sleep/wait calls. The entire suite will complete in milliseconds.

### 5. Writable — PASS

The fixture pattern is lean and effective. Adding a new test requires at most one or two lines of setup beyond the fixture injection. The test structure is regular enough that a developer can write a new scenario by following the existing pattern without needing to understand framework internals.

### 6. Readable — PASS

Test names are descriptive and follow a consistent `test_<subject>_<condition>_<outcome>` convention throughout:
- `test_register_duplicate_username_raises`
- `test_login_unknown_user_raises`
- `test_deactivated_user_cannot_login`

Inline comments like `# Behavioral: verify the user can subsequently log in` (line 81) and `# After successful login, a new wrong attempt should NOT lock the account` (line 131) explain the "why" clearly. Arrange-Act-Assert structure is present and consistent. Test data uses plausible, human-readable values (`"alice"`, `"securepass123"`).

### 7. Behavioral — PASS

Tests verify outcomes through the public API rather than inspecting internal fields directly. For example:

- `test_register_new_user_succeeds` (line 78) does not assert that `_users` contains the user; it proves registration worked by successfully logging in afterwards.
- `test_login_increments_failed_attempts_on_wrong_password` (line 113) does not read `user.failed_attempts` directly; it validates the observable consequence — account lockout — after 5 failures.
- `test_login_resets_failed_attempts_on_success` (line 127) verifies the reset behaviorally: a subsequent failed attempt does not lock the account.

This is a notable strength. The comment on line 118 explicitly flags the intent: `# Behavioral: failed_attempts is observable via lockout behavior`.

### 8. Structure-insensitive — PASS

No test accesses private attributes (`_users`, `_sessions`) or internal implementation details. All assertions go through the public interface (`register`, `login`, `logout`, `is_authenticated`, `deactivate_user`). Renaming `_users` to `_registry`, switching the session store to Redis, or changing the hashing algorithm would not break any test — only behavior changes would.

### 9. Automated — PASS

All tests are fully automated. No console output requires human inspection, no manual steps are present, and no interactive prompts exist. The suite is runnable with `pytest` with zero human intervention.

### 10. Specific — PASS

Each test covers a single, well-named scenario. Assertions use `pytest.raises` with `match=` patterns to pinpoint exact error messages (`match="already exists"`, `match="at least 8"`, `match="locked"`, `match="not found"`). When a test fails, the failure message will point directly to the broken behavior.

`test_login_increments_failed_attempts_on_wrong_password` is the longest test (lines 113–125). It does cover more steps than the others, but all steps serve the single behavioral assertion (lockout after MAX_FAILED_ATTEMPTS), and they are not independent assertions on different behaviors. This is acceptable.

### 11. Predictive — PASS WITH MINOR GAP

The suite covers all primary paths and the most important edge cases:
- Duplicate registration, short password
- Wrong password, unknown user, account lockout, failed-attempt reset
- Token invalidation on logout, no-op logout on unknown token
- Deactivated user blocked from login, unknown user deactivation error

**Minor gap:** The lockout behavior is tested via `test_login_increments_failed_attempts_on_wrong_password`, but there is no dedicated test asserting that a *correct* password is rejected once the account is locked (i.e., `login("alice", "securepass123")` raises after 5 failures). The existing test does end with a correct-password attempt post-lockout on line 124, but that call uses `"securepass123"` only implicitly through the `match="locked"` assertion. A developer reading the suite might not immediately see this edge case covered. A dedicated `test_login_correct_password_rejected_when_account_locked` test would make this explicit.

This is a minor gap — the behavior is exercised but not directly named.

### 12. Inspiring — PASS

The tests cover the meaningful behaviors that matter for an authentication service: credentials validation, account state management, session lifecycle, and lockout policy. The suite is comprehensive enough to inspire confidence before deploying. The behavioral testing approach (testing through observable outcomes rather than internal state) adds additional trustworthiness.

---

## Tradeoffs Analysis

### Behavioral ↔ Readable (supporting)

The choice to test `failed_attempts` through observable lockout behavior (Behavioral) rather than reading `user.failed_attempts` directly also makes tests more Readable — the tests describe what the system *does* for the user, not how it stores internal counters. These properties reinforce each other here.

### Composable ↔ Fast (supporting)

The fixture composition (`registered_user` building on `service`) gives composability at no speed cost because the setup is pure in-memory object creation. There is no real tension between these properties in this suite.

### Isolated ↔ Writable (only seeming to interfere — resolved)

Fresh instances per test could require verbose setup in each test body. The `service` and `registered_user` fixtures resolve this entirely: isolation is maintained without any per-test boilerplate. This is the textbook resolution of the Isolated ↔ Writable apparent conflict.

### Predictive ↔ Specific (minor real tension)

The single minor Predictive gap (no dedicated test for correct-password rejection when locked) could be addressed by adding a focused test. This would not conflict with Specific — a dedicated, single-assertion test would actually improve both properties. No real tension exists here; it is simply a missing test.

---

## Prioritized Recommendations

### Priority 1 (minor): Add explicit lockout-with-correct-password test

**Property:** Predictive
**Location:** `TestLogin` class
**Impact:** Makes the lockout-blocks-correct-credentials behavior explicitly named and directly visible in the test suite.

```python
def test_login_correct_password_rejected_when_account_locked(self, registered_user):
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrongpassword")
    with pytest.raises(PermissionError, match="locked"):
        registered_user.login("alice", "securepass123")
```

This is the only meaningful recommendation. All other properties are in good shape.

---

## Summary Scorecard

| Property            | Score   | Notes                                                       |
|---------------------|---------|-------------------------------------------------------------|
| Isolated            | PASS    | Fresh fixture per test, no shared state                     |
| Composable          | PASS    | Clean decomposition by concern, reusable fixtures           |
| Deterministic       | PASS    | No randomness, time, or external dependencies               |
| Fast                | PASS    | Pure in-memory, no I/O                                      |
| Writable            | PASS    | Low boilerplate, consistent patterns                        |
| Readable            | PASS    | Descriptive names, clear intent comments, good AAA structure|
| Behavioral          | PASS    | All assertions via public API and observable outcomes       |
| Structure-insensitive | PASS  | No internal state access, no private method testing         |
| Automated           | PASS    | Fully automated, no human intervention needed               |
| Specific            | PASS    | Single-concern tests, precise error message matching        |
| Predictive          | PASS*   | One minor gap: explicit locked-account correct-password test|
| Inspiring           | PASS    | Comprehensive, meaningful coverage of auth behaviors        |

\* Minor gap only — overall coverage is strong.

**Conclusion:** This is a high-quality test suite. It demonstrates correct application of behavioral testing, proper fixture-based isolation, and clear intent throughout. The single recommended addition is a low-effort, high-clarity improvement rather than a fix for a significant defect.
