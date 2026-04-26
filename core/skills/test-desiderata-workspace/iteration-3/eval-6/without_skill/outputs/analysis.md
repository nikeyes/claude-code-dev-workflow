# Test Quality Analysis: test_auth_service.py

## Overall Assessment

These tests are well-written and demonstrate strong adherence to good testing practices. The suite is largely solid, with only minor gaps worth noting.

---

## Strengths

### Isolation
Each test receives a fresh `AuthService` instance via the `service` fixture. Tests do not share state. The `registered_user` fixture composes cleanly on top of `service` without side effects leaking between tests. No global variables or class-level state are used.

### Determinism
All tests are deterministic. The `AuthService` implementation uses pure hashing (`sha256`) with fixed inputs, so tokens are predictable given the same inputs. No randomness, no time-based logic, and no external I/O are involved. Tests will produce the same result on every run.

### Specificity
Exception assertions use `pytest.raises` with `match=` to pin down the specific error message, not just the exception type (e.g., `match="already exists"`, `match="at least 8"`, `match="locked"`, `match="not found"`). This prevents tests from passing on unrelated exceptions with the same type.

### Behavioral Testing
Tests verify observable behavior rather than internal state. For example, `test_register_new_user_succeeds` does not inspect `_users` directly — it validates registration by successfully logging in. `test_login_increments_failed_attempts_on_wrong_password` tests the lockout effect rather than asserting on `user.failed_attempts`. This is good practice.

### Readability
Test names are long and descriptive, following the `test_<subject>_<scenario>_<expected_outcome>` pattern. The grouping into `TestRegistration`, `TestLogin`, `TestLogout`, and `TestDeactivation` classes provides clear structure. Comments clarify intent where behavior might otherwise seem indirect.

### Boundary Value Testing
`test_register_minimum_length_password_succeeds` tests exactly at the boundary (8 characters), and `test_register_short_password_raises` tests just below it. This is correct boundary analysis.

### Fixture Reuse
The `registered_user` fixture avoids repeating `service.register("alice", "securepass123")` in every test that needs a pre-registered user, reducing duplication without obscuring setup intent.

---

## Issues and Recommendations

### 1. Predictive Gap: Brute-Force Lockout Not Directly Tested

**Severity:** Minor / Borderline

`test_login_increments_failed_attempts_on_wrong_password` tests that lockout eventually occurs, but does so by burning 5 attempts via a loop with silent `try/except`. The test structure is harder to read than necessary, and it does not directly assert what happens at exactly attempt N=5 versus N=4.

**Recommendation:** Add a focused test that drives exactly `MAX_FAILED_ATTEMPTS` wrong attempts and asserts the lockout message. This would also guard against someone changing the constant.

```python
def test_account_locks_after_max_failed_attempts(self, registered_user):
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
        with pytest.raises(PermissionError, match="Invalid credentials"):
            registered_user.login("alice", "wrongpassword")
    with pytest.raises(PermissionError, match="locked"):
        registered_user.login("alice", "securepass123")
```

### 2. Silent Exception Swallowing in test_login_increments_failed_attempts_on_wrong_password

**Severity:** Minor

Lines 119–123 use a bare `try/except` to silently swallow `PermissionError`. This obscures what is happening and could hide unexpected behavior if a different exception is raised. The intent is to accumulate failed attempts, but the silent catch makes the test harder to reason about.

**Recommendation:** Use a helper or replace the loop with a direct approach (as shown above in recommendation 1) that uses `pytest.raises` on each expected-failure call.

### 3. Missing Test: Successful Login After Lockout Reset

**Severity:** Minor / Gap

`test_login_resets_failed_attempts_on_success` verifies that a successful login resets the counter so a single wrong attempt does not immediately lock the account. However, there is no test verifying that a locked account stays locked even with correct credentials (i.e., that unlocking requires administrator intervention, not just a correct password). This is a predictive gap — if someone accidentally changed the login logic to let correct passwords bypass the locked check, no test would catch it.

**Recommendation:**

```python
def test_locked_account_cannot_login_with_correct_password(self, registered_user):
    for _ in range(AuthService.MAX_FAILED_ATTEMPTS):
        with pytest.raises(PermissionError):
            registered_user.login("alice", "wrongpassword")
    with pytest.raises(PermissionError, match="locked"):
        registered_user.login("alice", "securepass123")
```

(This overlaps partially with the brute-force test, but makes the intent explicit: even the correct password is rejected.)

### 4. Missing Test: Deactivated User Token Behavior

**Severity:** Minor / Gap

There is no test for what happens to an active session token when the user is deactivated. If Alice logs in and then is deactivated, should existing tokens be invalidated? The current implementation does not invalidate tokens on deactivation (the `_sessions` dict is not cleared), which may or may not be intentional. A test documenting the expected behavior (either direction) would increase specification coverage.

**Recommendation:** Add a test that logs in, deactivates the user, and asserts whether existing tokens remain valid:

```python
def test_deactivated_user_existing_token_is_invalidated(self, registered_user):
    token = registered_user.login("alice", "securepass123")
    registered_user.deactivate_user("alice")
    assert not registered_user.is_authenticated(token)
```

Or, if the intent is that tokens persist:

```python
def test_deactivated_user_existing_token_remains_valid(self, registered_user):
    token = registered_user.login("alice", "securepass123")
    registered_user.deactivate_user("alice")
    assert registered_user.is_authenticated(token)
```

### 5. Token Assertion is Weak

**Severity:** Very Minor

`test_login_valid_credentials_returns_token` only asserts `isinstance(token, str)` and `len(token) > 0`. While the token format (SHA-256 hex digest = 64 chars) is an implementation detail that should not be over-specified, asserting at minimum a non-empty string misses the chance to at least verify the token is usable:

**Recommendation:** Replace the structural assertion with a behavioral one:

```python
def test_login_valid_credentials_returns_usable_token(self, registered_user):
    token = registered_user.login("alice", "securepass123")
    assert registered_user.is_authenticated(token)
```

This is more meaningful than checking string length.

---

## Summary Table

| Desideratum | Score | Notes |
|---|---|---|
| Isolation | Good | Fresh fixture per test, no shared state |
| Determinism | Good | No randomness or time dependency |
| Specificity | Good | `match=` used on most exception assertions |
| Behavioral | Good | Tests observable effects, not internals |
| Readability | Good | Descriptive names, clear grouping |
| Boundary Values | Good | Min-length password tested |
| Predictive | Borderline | Brute-force lockout path not cleanly covered; deactivation/token interaction missing |
| Completeness | Borderline | Missing: locked account + correct password; deactivated user + existing token |

---

## Conclusion

This is a high-quality test suite. The issues identified are all minor: one instance of silent exception swallowing, a few missing edge-case scenarios, and one token assertion that could be made more behavioral. No major violations of isolation, determinism, or specificity were found. The suite is a good example of well-structured Python tests and requires only small additions to reach full coverage of the stated behavior.
