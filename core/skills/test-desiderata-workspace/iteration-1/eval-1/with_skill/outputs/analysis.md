# Test Desiderata Analysis: test_bank_account.py

**File analyzed:** `core/skills/test-desiderata-workspace/evals/files/test_bank_account.py`
**Framework:** Kent Beck's Test Desiderata (12 properties)
**Date:** 2026-04-26

---

## Summary

The test file contains 4 tests for a `BankAccount` class. Multiple intentional violations are present across 5 of the 12 Test Desiderata properties. The most critical issues are the shared global mutable state (isolation failure) and the non-deterministic production code under test (determinism failure). Two tests also inspect internal implementation details directly.

**Overall assessment:** The test suite has significant quality issues that will lead to flaky, unreliable, and brittle tests. Priority fixes are required for Isolated and Deterministic violations before addressing the remaining issues.

---

## Property-by-Property Evaluation

### 1. Isolated — VIOLATED

**Status:** Fail

**Issues found:**

**Issue 1:**
```
Issue: `test_all_operations` and `test_deposit_updates_ledger` share `shared_balance` global state
Location: Line 12 (declaration), Line 45-49 (read/write in test_all_operations), Line 56-57 (read in test_deposit_updates_ledger)
Impact: If tests run in a different order (e.g., pytest-randomly), `test_deposit_updates_ledger` receives an unexpected initial balance (70 instead of 0), causing incorrect assertions about ledger length or balance state.
Fix: Each test should create its own `BankAccount` with an explicit, fixed initial balance. Remove `shared_balance` entirely.
Tradeoff: None — isolation is strictly better here.
```

**Issue 2:**
```
Issue: `test_deposit_updates_ledger` initialises its account with `shared_balance`, coupling it to `test_all_operations`
Location: Line 57 — `account = BankAccount("Bob", shared_balance)`
Impact: This test is meaningless in isolation; it silently passes or fails depending on the side effect of the previous test.
Fix: Replace with `account = BankAccount("Bob", 0)` (or any explicit, deterministic starting state).
Tradeoff: None.
```

---

### 2. Composable — PARTIAL VIOLATION

**Status:** Warning

**Issues found:**

```
Issue: `test_all_operations` bundles deposit, withdrawal, and balance-check into a single test.
Location: Lines 43-53
Impact: There is no independent test for deposit alone, or for withdrawal alone, making it impossible to identify which operation failed when the test fails. Dimensions cannot be composed or reused.
Fix: Split into `test_deposit_increases_balance`, `test_withdraw_decreases_balance`, and `test_initial_balance_is_zero` (or similar focused tests). Each can then be individually enabled or combined.
Tradeoff: Slightly more test code, but each dimension is independently verifiable.
```

---

### 3. Deterministic — VIOLATED

**Status:** Fail

**Issues found:**

```
Issue: `BankAccount.deposit()` calls `random.randint(1000, 9999)` to generate a transaction ID.
Location: Line 24 (production code) — `tx_id = random.randint(1000, 9999)`
Impact: Every call to `deposit()` produces a different `tx_id`, so any test asserting on the ledger entry's `id` field would be non-deterministic. While the current tests do not assert on `tx_id` directly, the non-determinism is latent and will surface as soon as a developer writes such a test. It also makes debug reproduction harder.
Fix (production code): Use a deterministic ID generator — a counter, a UUID seeded from a known value in tests, or an injected factory. Example:
  - Inject an `id_generator` callable into `__init__` with a default of `lambda: uuid.uuid4()`, and in tests pass `id_generator=itertools.count(1).__next__`.
Tradeoff: Slightly more complex production code, but eliminates entire class of test flakiness.
```

---

### 4. Fast — PASS

**Status:** Pass

No sleep calls, no I/O, no network calls, no database access. All operations are in-memory. Tests should run in milliseconds.

---

### 5. Writable — PARTIAL VIOLATION

**Status:** Warning

```
Issue: The global `shared_balance` pattern and the requirement to understand test execution order increase the cognitive load for writing new tests.
Location: Lines 12, 45-49, 56-57
Impact: A developer adding a new test must understand the implicit ordering dependency to avoid introducing regressions or writing an incorrectly initialised account.
Fix: Remove shared state. Use simple, self-contained fixtures or factory helpers (e.g., a `make_account(balance=0)` helper). This makes it trivial to add new tests.
Tradeoff: None.
```

---

### 6. Readable — PARTIAL VIOLATION

**Status:** Warning

**Issues found:**

**Issue 1:**
```
Issue: `test_all_operations` is an opaque name that does not communicate intent.
Location: Line 43 — `def test_all_operations(self):`
Impact: A reader cannot determine from the name what the expected behavior is or what constitutes failure.
Fix: Replace with names like `test_balance_after_deposit_and_withdrawal_reflects_net_change`.
Tradeoff: Longer name, but much clearer intent.
```

**Issue 2:**
```
Issue: `test_deposit_updates_ledger` does not describe the expected ledger state or why it matters.
Location: Line 55 — `def test_deposit_updates_ledger(self):`
Impact: The name is acceptable, but coupling it to shared state makes the actual scenario opaque.
Fix: Rename to `test_deposit_appends_deposit_entry_to_ledger` and decouple from shared state. The docstring in `test_all_operations` (line 44) is helpful but does not compensate for the method name.
Tradeoff: None.
```

**Issue 3:**
```
Issue: Assertions on `account._ledger` lack explanation of why the ledger state is being verified.
Location: Lines 52-53, 59-60
Impact: A reader unfamiliar with the domain must infer the business rule from the assertion, rather than having it stated.
Fix: Add a brief inline comment or descriptive variable name. Alternatively, expose a public `transaction_count()` method and assert on that.
Tradeoff: Minor verbosity increase.
```

---

### 7. Behavioral — PARTIAL VIOLATION

**Status:** Warning

```
Issue: `test_withdraw_insufficient_funds` and `test_negative_deposit_raises` correctly verify behavioral outcomes (exceptions are raised). However, `test_all_operations` mixes behavioral checks (balance value) with structural checks (ledger length and type), weakening the behavioral signal.
Location: Lines 51-53
Impact: Passing tests do not guarantee correct business behavior if structural assertions are satisfied by accident.
Fix: Separate behavioral assertions (balance is correct) from structural ones. Prefer asserting on observable behavior (public API) over internal structure.
Tradeoff: Behavioral tests may be slightly less exhaustive about implementation details, but that is the correct tradeoff.
```

---

### 8. Structure-insensitive — VIOLATED

**Status:** Fail

**Issues found:**

**Issue 1:**
```
Issue: Tests assert directly on the private `_ledger` attribute.
Location: Line 52 — `assert len(account._ledger) == 2`
         Line 53 — `assert account._ledger[0]["type"] == "deposit"`
         Line 59 — `assert len(account._ledger) == 1`
         Line 60 — `assert account._ledger[0]["type"] == "deposit"`
Impact: Any refactoring that renames `_ledger` to `_transactions`, changes its structure, or wraps it in a property will break these tests even if the external behavior is unchanged. This is the definition of a structure-sensitive test.
Fix: Either expose a public API (`account.transaction_history()` returning a list of transaction objects with a `type` property), or drop the ledger assertions entirely and assert only on the balance. If ledger verification is important business behavior, it should be exposed via the public API.
Tradeoff: Requires a design decision about whether ledger contents are part of the public contract. If yes, expose them properly. If no, remove the assertions.
```

---

### 9. Automated — PASS

**Status:** Pass

All tests are runnable with `pytest` without any manual steps. No print statements requiring human inspection, no interactive prompts.

---

### 10. Specific — VIOLATED

**Status:** Fail

**Issues found:**

```
Issue: `test_all_operations` has three assertions (balance value, ledger length, ledger entry type) in a single test.
Location: Lines 51-53
Impact: When this test fails, it is unclear which operation caused the failure — the deposit, the withdrawal, or the ledger recording. The failure message identifies the line but requires the reader to understand the full sequence of operations to diagnose the root cause.
Fix: Split into three focused tests, one per assertion:
  - `test_deposit_increases_balance_by_deposit_amount`
  - `test_withdraw_decreases_balance_by_withdrawal_amount`
  - `test_deposit_records_entry_in_ledger` (if ledger is part of public contract)
Tradeoff: More test methods, but each failure is immediately actionable.
```

---

### 11. Predictive — PARTIAL VIOLATION

**Status:** Warning

```
Issue: There are no tests for the boundary between valid and invalid withdrawal amounts (e.g., withdrawing exactly the full balance — is that allowed?), no test for zero initial balance with withdrawal, and no test verifying the return value of `withdraw()`.
Location: Missing tests — not present in the file.
Impact: A regression in edge-case handling of exact-balance withdrawal would not be caught.
Fix: Add:
  - `test_withdraw_exact_balance_succeeds` — withdrawing exactly `_balance` should succeed
  - `test_withdraw_returns_remaining_balance` — verify the return value of `withdraw()`
  - `test_deposit_returns_new_balance` — verify the return value of `deposit()`
Tradeoff: More tests to maintain, but higher confidence before deployment.
```

---

### 12. Inspiring — PARTIAL VIOLATION

**Status:** Warning

```
Issue: The test suite covers the happy path and two error paths, but the shared global state and structure-sensitive assertions undermine confidence. A developer running these tests cannot be certain they reflect real usage, because they are order-dependent and tied to implementation details.
Location: Overall test suite
Impact: Low confidence. A developer may not trust a green test run because they know the tests have known fragility points.
Fix: After applying all the fixes above (especially Isolated, Deterministic, Structure-insensitive), the tests will become genuinely inspiring — a green run will mean the account correctly deposits, withdraws, rejects invalid inputs, and maintains correct balance.
Tradeoff: Investment in fixing the suite upfront pays dividends in long-term confidence.
```

---

## Violations Summary Table

| Property             | Status           | Severity  |
|----------------------|------------------|-----------|
| 1. Isolated          | VIOLATED         | Critical  |
| 2. Composable        | WARNING          | Medium    |
| 3. Deterministic     | VIOLATED         | Critical  |
| 4. Fast              | PASS             | —         |
| 5. Writable          | WARNING          | Low       |
| 6. Readable          | WARNING          | Medium    |
| 7. Behavioral        | WARNING          | Medium    |
| 8. Structure-insensitive | VIOLATED     | High      |
| 9. Automated         | PASS             | —         |
| 10. Specific         | VIOLATED         | High      |
| 11. Predictive       | WARNING          | Medium    |
| 12. Inspiring        | WARNING          | Medium    |

---

## Tradeoff Analysis

**Supporting properties that could be improved together:**
- Fixing **Isolated** (remove shared state) simultaneously improves **Writable** and **Inspiring** — lower cognitive load, higher confidence.
- Fixing **Specific** (split `test_all_operations`) simultaneously improves **Composable** and **Readable** — focused tests are both easier to compose and easier to understand.
- Fixing **Structure-insensitive** (remove `_ledger` assertions or expose a public API) simultaneously improves **Behavioral** — tests will then only assert on observable behavior.

**No genuine tradeoffs identified** — all violations in this file can be fixed without sacrificing other properties.

---

## Prioritized Recommendations

### Priority 1 — Safety (Fix first: Isolated + Deterministic)

1. **Remove `shared_balance`** — Replace all uses with explicit, local initial balances in each test.
2. **Fix non-deterministic ID generation** — Inject an `id_generator` into `BankAccount.__init__` so tests can pass a deterministic counter.

### Priority 2 — Feedback loop (Fast already passes)

No changes needed here.

### Priority 3 — Maintainability (Readable + Structure-insensitive)

3. **Remove `_ledger` assertions** — Either expose a public `transaction_history()` API or remove ledger assertions from tests entirely.
4. **Rename `test_all_operations`** — Use a name that describes the expected behavior.
5. **Split `test_all_operations`** — One assertion per test for deposit behavior, withdrawal behavior.

### Priority 4 — Confidence (Predictive + Inspiring)

6. **Add missing edge-case tests** — `test_withdraw_exact_balance_succeeds`, `test_deposit_returns_new_balance`, `test_withdraw_returns_remaining_balance`.

---

## Example Refactored Test (illustrative)

```python
import pytest

class TestBankAccount:
    def make_account(self, balance=0, owner="Test"):
        """Factory helper — keeps tests writable and isolated."""
        return BankAccount(owner, initial_balance=balance)

    # --- Isolated, Specific, Readable ---
    def test_deposit_increases_balance_by_deposited_amount(self):
        account = self.make_account(balance=0)
        account.deposit(100)
        assert account.get_balance() == 100

    def test_withdraw_decreases_balance_by_withdrawn_amount(self):
        account = self.make_account(balance=100)
        account.withdraw(30)
        assert account.get_balance() == 70

    def test_withdraw_exact_balance_succeeds(self):
        account = self.make_account(balance=50)
        account.withdraw(50)
        assert account.get_balance() == 0

    # --- Behavioral, Structure-insensitive ---
    def test_withdraw_insufficient_funds_raises_value_error(self):
        account = self.make_account(balance=10)
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.withdraw(100)

    def test_negative_deposit_raises_value_error(self):
        account = self.make_account(balance=100)
        with pytest.raises(ValueError):
            account.deposit(-10)

    # --- If ledger is part of the public contract, expose it properly ---
    def test_deposit_is_recorded_in_transaction_history(self):
        account = self.make_account(balance=0)
        account.deposit(50)
        history = account.transaction_history()
        assert len(history) == 1
        assert history[0].type == "deposit"
```
