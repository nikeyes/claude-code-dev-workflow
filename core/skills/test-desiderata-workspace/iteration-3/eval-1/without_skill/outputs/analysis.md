# Test Quality Analysis: test_bank_account.py

## Summary

The test file contains four deliberate quality violations that undermine test reliability, clarity, and maintainability. Each issue is described below with its location, impact, and a concrete recommendation.

---

## Issue 1: Shared Global State Breaks Test Isolation

**Location**: Module-level `shared_balance = 0`, used in `test_all_operations` and `test_deposit_updates_ledger`.

**Problem**: `shared_balance` is a mutable global variable. `test_all_operations` writes to it after running, and `test_deposit_updates_ledger` reads from it as the initial balance for the next account. This creates an implicit execution-order dependency: if `test_deposit_updates_ledger` runs before `test_all_operations`, it starts with `shared_balance = 0` instead of `70`. Changing the test order (which pytest can do, e.g. with `--randomly`) silently produces different results.

**Impact**: Tests are not independent. A failure in one test can propagate phantom failures or false passes into other tests.

**Recommendation**: Remove `shared_balance` entirely. Each test should construct its own `BankAccount` with a hardcoded initial balance that makes the test's intent self-explanatory.

```python
def test_deposit_updates_ledger(self):
    account = BankAccount("Bob", 0)   # independent, explicit
    account.deposit(50)
    assert len(account._ledger) == 1
    assert account._ledger[0]["type"] == "deposit"
```

---

## Issue 2: Non-Deterministic Transaction IDs

**Location**: `BankAccount.deposit` calls `random.randint(1000, 9999)` to generate `tx_id`.

**Problem**: Although no test currently asserts the value of `tx_id`, the production code introduces randomness that makes any future assertion on transaction IDs unreliable without seeding. If a test were added to verify the ledger entry's ID, it would be non-deterministic by design.

**Impact**: Tests relying on the `id` field of a ledger entry would pass or fail randomly. Even without such assertions today, the design encourages writing fragile tests.

**Recommendation**: Replace the random ID with a deterministic strategy, such as a sequential counter or a UUID that can be injected or seeded:

```python
def __init__(self, owner: str, initial_balance: float = 0):
    self.owner = owner
    self._balance = initial_balance
    self._ledger = []
    self._next_tx_id = 1

def deposit(self, amount: float) -> float:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    tx_id = self._next_tx_id
    self._next_tx_id += 1
    self._ledger.append({"id": tx_id, "amount": amount, "type": "deposit"})
    self._balance += amount
    return self._balance
```

---

## Issue 3: One Test Verifies Multiple Unrelated Behaviours

**Location**: `test_all_operations` — verifies deposit, withdraw, and final balance in a single test.

**Problem**: The test exercises three distinct behaviours at once. When it fails, the failure message does not tell you which operation caused the problem. You must read the full test body to diagnose whether the failure is in `deposit`, `withdraw`, or `get_balance`.

**Impact**: Low diagnostic value. A single regression anywhere in the three operations collapses into one undifferentiated failure.

**Recommendation**: Split into three focused tests, each with a descriptive name:

```python
def test_deposit_increases_balance(self):
    account = BankAccount("Alice", 0)
    account.deposit(100)
    assert account.get_balance() == 100

def test_withdraw_decreases_balance(self):
    account = BankAccount("Alice", 100)
    account.withdraw(30)
    assert account.get_balance() == 70

def test_balance_after_deposit_and_withdrawal(self):
    account = BankAccount("Alice", 0)
    account.deposit(100)
    account.withdraw(30)
    assert account.get_balance() == 70
```

---

## Issue 4: Assertions on Internal Implementation Details

**Location**: `test_all_operations` lines 52-53 and `test_deposit_updates_ledger` lines 59-60 assert on `account._ledger` (a private attribute).

**Problem**: `_ledger` is an implementation detail. Any refactoring that renames the attribute, changes its structure, or removes it in favour of a different internal representation will break these tests — even if the observable behaviour (balance, error messages) is unchanged. The leading underscore is a Python convention signalling "internal use only".

**Impact**: Tests become a barrier to refactoring rather than a safety net for it. They test *how* the code works, not *what* it does.

**Recommendation**: Assert only on the public interface. If transaction history is important behaviour, expose it through a public method and test that:

```python
# If transaction history is a required public feature:
def get_transaction_count(self) -> int:
    return len(self._ledger)

# Test the public interface:
def test_deposit_records_one_transaction(self):
    account = BankAccount("Bob", 0)
    account.deposit(50)
    assert account.get_transaction_count() == 1
```

If transaction history is purely internal, remove the assertions entirely.

---

## Issue 5: Missing Match Argument on Exception Assertion

**Location**: `test_negative_deposit_raises` — uses `pytest.raises(ValueError)` without a `match` parameter.

**Problem**: This test passes for *any* `ValueError` raised inside `deposit`, regardless of the message. If the validation message were accidentally changed or a different code path raised a generic `ValueError`, the test would still pass silently.

**Impact**: The test does not verify the intended error condition, reducing its diagnostic specificity.

**Recommendation**: Add `match` to pin down the expected error message, consistent with the pattern already used in `test_withdraw_insufficient_funds`:

```python
def test_negative_deposit_raises(self):
    account = BankAccount("Dave", 100)
    with pytest.raises(ValueError, match="Amount must be positive"):
        account.deposit(-10)
```

---

## Summary Table

| # | Desideratum Violated | Location | Severity |
|---|---------------------|----------|----------|
| 1 | Isolated | `shared_balance` global + `test_deposit_updates_ledger` | High |
| 2 | Deterministic | `random.randint` in `BankAccount.deposit` | Medium |
| 3 | Specific (one reason to fail) | `test_all_operations` | High |
| 4 | Structure-insensitive (behavioural) | `_ledger` assertions in two tests | High |
| 5 | Specific (assertion precision) | `test_negative_deposit_raises` | Low |

---

## Priority Order for Fixes

1. **Split `test_all_operations`** — biggest gain in clarity and diagnosis speed.
2. **Remove `shared_balance`** — eliminates hidden coupling between tests.
3. **Stop asserting on `_ledger`** — decouples tests from implementation internals.
4. **Add `match` to `test_negative_deposit_raises`** — improves assertion precision at zero cost.
5. **Make `tx_id` deterministic** — prevents future fragility if the field is ever tested.
