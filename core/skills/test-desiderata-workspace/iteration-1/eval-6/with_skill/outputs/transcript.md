# Transcript: Test Desiderata Analysis — eval-6

**Skill:** stepwise-core:test-desiderata
**Eval file:** test_auth_service.py (hard — good tests, false positive eval)
**Date:** 2026-04-26

---

## Step 1: Read the Skill File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

Key takeaways from the skill:
- 12 properties to evaluate: Isolated, Composable, Deterministic, Fast, Writable, Readable, Behavioral, Structure-insensitive, Automated, Specific, Predictive, Inspiring.
- Analysis workflow: Read → Evaluate → Identify tradeoffs → Prioritize → Suggest specific changes.
- Recommendations format: Issue, Location, Impact, Fix, Tradeoff.
- Prioritization order: Safety issues (Isolated, Deterministic) → Feedback loop (Fast) → Maintainability (Readable, Structure-insensitive) → Confidence (Predictive, Inspiring).

---

## Step 2: Read and Understand the Test File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_auth_service.py`.

**File metadata note:** The file's docstring explicitly marks it as a "false positive" eval — the tests are intentionally well-written and the skill should NOT flag major violations. There is a noted borderline gap on Predictive (brute-force lockout not tested in isolation).

**Code structure observed:**
- Implementation and tests in the same file (common in eval fixtures for self-containment).
- Two fixtures: `service` (fresh `AuthService` per test) and `registered_user` (composes on `service` with one pre-registered user).
- Four test classes: `TestRegistration`, `TestLogin`, `TestLogout`, `TestDeactivation`.
- Total: 13 tests across 4 classes.

**Key behaviors under test:**
1. Registering a new user (success, duplicate, short password, minimum length boundary).
2. Login (valid credentials, wrong password, unknown user, failed attempt increment, reset on success).
3. Logout (token invalidation, graceful handling of unknown token).
4. Deactivation (deactivated user cannot log in, unknown user raises).

---

## Step 3: Evaluate Against Each Property

### Isolated
- `service` fixture returns `AuthService()` each time → no shared state.
- `registered_user` builds on `service` → inherits per-test isolation.
- No class-level variables.
- **Verdict: PASS**

### Composable
- `service` is the base building block.
- `registered_user` is a composed fixture for tests needing a pre-existing user.
- Test classes group independent dimensions cleanly.
- **Verdict: PASS**

### Deterministic
- No `random`, no `time.time()`, no `datetime.now()`, no network calls.
- SHA-256 is deterministic.
- **Verdict: PASS**

### Fast
- Entirely in-memory. No I/O. SHA-256 hashing is negligible.
- **Verdict: PASS**

### Writable
- Two fixtures handle all setup. New tests are easy to add.
- `pytest.raises(match=...)` is concise.
- **Verdict: PASS**

### Readable
- Test names follow `test_<action>_<condition>_<outcome>` pattern clearly.
- Inline comments explain non-obvious behavioral choices.
- Arrange-Act-Assert structure visible in most tests.
- **Verdict: PASS**

### Behavioral
- `test_register_new_user_succeeds` confirms via a subsequent login, not by inspecting `_users`.
- `test_login_increments_failed_attempts_on_wrong_password` observes counter via lockout behavior, not `user.failed_attempts`.
- Token validity checked via `is_authenticated`, not via `_sessions` inspection.
- **Verdict: PASS**

### Structure-insensitive
- No access to `_users`, `_sessions`, or any private method.
- All assertions go through public API only.
- **Verdict: PASS**

### Automated
- No `print`, no interactive steps, no manual data setup.
- **Verdict: PASS**

### Specific
- Most tests: single focused assertion.
- **Exception:** `test_login_increments_failed_attempts_on_wrong_password` (lines 113-125):
  - Makes 2 explicit failed attempts.
  - Then a loop of 3 more with silent `try/except/pass`.
  - Then asserts lockout.
  - The silent loop obscures whether the pre-lockout attempts succeed or fail at the right point.
  - If lockout triggered at attempt 4 vs 5, the failure message would be confusing.
- **Verdict: GOOD (minor concern on one test)**

### Predictive
- Main happy paths and error cases covered.
- **Gap:** No standalone test for the exact `MAX_FAILED_ATTEMPTS` (5) boundary.
  - The existing lockout test reaches 5 attempts, but through a convoluted path (2 explicit + 3 in a loop).
  - No test verifies that 4 attempts do NOT lock the account.
  - No near-boundary reset test (4 wrong, then reset, then 4 more = should not lock).
- This matters for a security-critical feature: a one-off error in the constant (4 instead of 5) would not be caught.
- **Verdict: GOOD (minor gap at lockout boundary)**

### Inspiring
- Tests cover meaningful real-world flows: registration, login, session management, lockout, deactivation.
- A reader gains confidence in the service.
- The lockout boundary gap slightly reduces confidence for the security feature.
- **Verdict: GOOD (follows from Predictive gap)**

---

## Step 4: Identify Tradeoffs

- **Specific vs. Behavioral:** The complex lockout test was written to avoid inspecting internal state (good for Behavioral), but at the cost of Specific. A design improvement (see recommendations) can satisfy both without contradiction.
- **Predictive vs. Fast/Writable:** Adding boundary tests adds lines, but all tests are in-memory so no speed tradeoff. Minor Writable cost is worth it for a security-critical path.

---

## Step 5: Prioritize and Draft Recommendations

**Priority 1 (Specific):** Refactor `test_login_increments_failed_attempts_on_wrong_password` into two focused tests using `AuthService.MAX_FAILED_ATTEMPTS` directly for the threshold count.

**Priority 2 (Predictive):** Add a near-boundary reset test to verify the counter-reset behavior prevents lockout even when a user approaches the threshold.

Both improvements are low-effort (add ~15-20 lines total) and high-value for a security feature.

---

## Step 6: Final Assessment

This is a **high-quality test suite** that correctly scores well on all 12 properties. The two minor issues identified are:
1. One test that does too much at once (Specific — minor).
2. Missing explicit lockout threshold boundary test (Predictive — borderline).

No major violations were found. The skill correctly produced a positive assessment without false-flagging the well-written tests.

---

## Files Written

- `analysis.md` — Full Test Desiderata analysis with property-by-property assessment, scorecard, and recommendations.
- `transcript.md` — This file, documenting the analysis process step by step.
