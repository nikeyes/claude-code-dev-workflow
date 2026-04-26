# Test Quality Analysis: test_bank_account.py

**Framework**: Kent Beck's Test Desiderata (12 properties)
**File analyzed**: `core/skills/test-desiderata-workspace/evals/files/test_bank_account.py`

---

## Summary

The file contains 4 test methods. Three deliberate violations are seeded and documented in the module docstring; this analysis identifies all violations found across all 12 properties.

---

## Property-by-Property Evaluation

### 1. Isolated — FAIL

**Definition**: Each test can run independently, in any order, without requiring other tests to have run first.

**Violations found**:

- `shared_balance` is a module-level mutable variable. `test_all_operations` writes to it (`shared_balance = account.get_balance()`), and `test_deposit_updates_ledger` reads from it by passing `shared_balance` as `initial_balance` to a new account. If `test_all_operations` has not run first, `shared_balance` remains `0`, so `test_deposit_updates_ledger` silently starts from the wrong state.
- The test class uses no `setup`/`teardown`, no fixtures with `autouse`, and no explicit reset of the global — leaving any run-order dependency entirely implicit.

**Recommendation**: Remove `shared_balance` entirely. Each test should construct its own `BankAccount` with a hardcoded initial balance appropriate to the scenario it is testing.

---

### 2. Composable — PASS (marginal)

**Definition**: Tests can be combined and run together without interfering with each other.

The isolation failure above creates a latent composability risk, but in the current suite no two tests mutate the same object simultaneously. Marking as a pass with the caveat that fixing isolation is a prerequisite for true composability.

---

### 3. Deterministic — FAIL

**Definition**: Running the same test repeatedly always produces the same result.

**Violations found**:

- `BankAccount.deposit` calls `random.randint(1000, 9999)` to generate a transaction ID. Any assertion that inspects `_ledger` entries (as `test_all_operations` and `test_deposit_updates_ledger` do) is at the mercy of this non-determinism. The `id` field varies on every run; if future assertions were added on that field, they would fail intermittently.
- Even without assertions on `id`, the presence of randomness in the production code under test makes test results harder to reproduce and diagnose.

**Recommendation**: Make `tx_id` deterministic in tests — either by injecting a seeded random, by using a counter/UUID generator that can be swapped with a test double, or by removing randomness from the production path entirely if it has no functional value.

---

### 4. Fast — PASS

No I/O, network calls, or sleeps. All four tests execute in microseconds. No issues.

---

### 5. Writable — PASS (marginal)

The tests are short and mostly straightforward to write. However, the implicit dependency on `shared_balance` makes it harder to add new tests correctly — a new author must discover the hidden coupling, which increases cognitive cost of writing additional cases.

---

### 6. Readable — FAIL

**Definition**: The intent of each test is immediately clear from reading it.

**Violations found**:

- `test_all_operations` does not have a name that communicates what behaviour is being verified. "all operations" describes implementation scope, not a specific observable outcome.
- The `global shared_balance` statement in two test methods introduces noise that readers must trace to understand why initial balances differ across tests.
- The assertion `assert len(account._ledger) == 2` reads as an internal consistency check rather than a business rule. A reader must know the ledger structure to understand why 2 entries are expected.

**Recommendation**: Name each test after the behaviour it verifies (e.g., `test_balance_after_deposit_and_withdrawal`). Remove global state. Assertions should reference public API or business-meaningful descriptions.

---

### 7. Behavioral — FAIL

**Definition**: Tests verify observable behavior (outputs, state changes visible via public API), not internal implementation details.

**Violations found**:

- Both `test_all_operations` and `test_deposit_updates_ledger` assert directly against `account._ledger`, a private attribute (prefixed with `_`). This couples the tests to the internal data structure. If the ledger is renamed, restructured, or replaced with a different storage mechanism, these tests break even if the public behavior remains correct.

**Recommendation**: Test behavior through the public API. If auditing/ledger functionality is a public feature, expose it through a dedicated public method (e.g., `get_transaction_history()`) and assert against that. If it is purely internal, do not test it directly.

---

### 8. Structure-insensitive — FAIL

**Definition**: Tests do not break when the internal structure of the code changes, as long as behavior is preserved.

**Violations found** (closely related to Behavioral above):

- `assert len(account._ledger) == 2` — hardcodes the expected length of the internal `_ledger` list.
- `assert account._ledger[0]["type"] == "deposit"` — hardcodes the dictionary key `"type"` and index `0` inside a private data structure.
- Both assertions will break on any refactoring of `_ledger` (e.g., switching from a list of dicts to a list of dataclasses, or reordering entries) even when deposit/withdrawal behavior is unchanged.

**Recommendation**: Replace with assertions on the public interface. For example, `assert account.get_balance() == expected_value` is structure-insensitive; assertions on `_ledger` internals are not.

---

### 9. Automated — PASS

All tests use `pytest` and require no manual steps. They run fully automatically with `pytest`.

---

### 10. Specific — FAIL

**Definition**: When a test fails, the failure points to exactly one reason — the failure message pinpoints the defect.

**Violations found**:

- `test_all_operations` exercises `deposit`, `withdraw`, and `get_balance` in a single test body, and then makes three assertions about balance, ledger length, and ledger content. A failure in this test could originate from any one of those three operations or any one of those three assertions. The failure message does not narrow the cause.
- There is no separation between "deposit works correctly" and "withdraw works correctly" — they are conflated into one scenario.

**Recommendation**: Split `test_all_operations` into focused single-responsibility tests: one for deposit updating the balance, one for withdrawal updating the balance, one for the combined balance after both operations. Each test should have exactly one logical assertion (or a set of assertions all verifying the same single outcome).

---

### 11. Predictive — PASS (marginal)

**Definition**: A passing test suite predicts that the code works in production.

The existing tests do cover the core deposit/withdrawal/error paths. `test_withdraw_insufficient_funds` and `test_negative_deposit_raises` are well-targeted error-case tests. However, the structure-insensitivity and isolation failures mean the suite could pass while the actual behavior is wrong (e.g., if `shared_balance` accidentally masks a bug by starting from a non-zero balance). Marking marginal pass.

---

### 12. Inspiring — FAIL

**Definition**: Looking at the tests gives confidence and clarity; they serve as living documentation of intended behavior.

**Violations found**:

- The presence of `global shared_balance`, private-attribute assertions, and a test named `test_all_operations` does not inspire confidence. A developer reading this suite would not come away with a clear picture of what the `BankAccount` contract is.
- The embedded comment `# structure-insensitive violation` inside the production test code is a code smell — it signals the author knew the test was wrong but left it in place.

**Recommendation**: Tests should read like executable specifications. Each test name and assertion should communicate a business rule, not an implementation detail.

---

## Violations Summary Table

| Property            | Status | Violation Description                                                          |
|---------------------|--------|--------------------------------------------------------------------------------|
| Isolated            | FAIL   | `shared_balance` global couples `test_all_operations` and `test_deposit_updates_ledger` |
| Composable          | PASS   | Marginal; isolation failure creates latent risk                                |
| Deterministic       | FAIL   | `random.randint` in `deposit` makes runs non-reproducible                     |
| Fast                | PASS   | No I/O or sleeps                                                               |
| Writable            | PASS   | Marginal; hidden coupling increases cost of new tests                          |
| Readable            | FAIL   | Vague test name; global state noise; opaque internal assertions               |
| Behavioral          | FAIL   | Assertions on private `_ledger` attribute                                      |
| Structure-insensitive | FAIL | `_ledger` length and dict-key assertions break on internal refactoring         |
| Automated           | PASS   | Runs fully with `pytest`                                                       |
| Specific            | FAIL   | `test_all_operations` tests multiple behaviors and has multiple assertion points |
| Predictive          | PASS   | Marginal; isolation failure can mask real bugs                                 |
| Inspiring           | FAIL   | Suite does not serve as clear living documentation                             |

**Properties failing**: 6 of 12 (Isolated, Deterministic, Readable, Behavioral, Structure-insensitive, Specific, Inspiring)

---

## Prioritized Recommendations

1. **Remove `shared_balance`** — eliminates the Isolated violation and cleans up Readable and Inspiring.
2. **Replace `_ledger` assertions with public API assertions** — fixes Behavioral and Structure-insensitive.
3. **Split `test_all_operations`** — fixes Specific and improves Readable and Inspiring.
4. **Make randomness injectable or deterministic** — fixes Deterministic (this may require a small production-code change).
5. **Rename tests to describe behavior** — improves Readable and Inspiring at zero cost.
