# Test Quality Analysis: test_bank_account.py

## Summary

The test file for `BankAccount` contains four deliberately seeded quality violations. The analysis below identifies each problem, explains why it matters, and provides a concrete recommendation with corrected code.

---

## Problem 1 — Shared Mutable Global State (Isolation Violation)

**Location:** Lines 12, 45–49, 56–57

**Description:**
`shared_balance` is a module-level global variable that is mutated inside `test_all_operations` and then consumed in `test_deposit_updates_ledger`. This means the two tests are coupled: the second test's starting conditions depend on the first test running successfully before it. If `test_all_operations` fails mid-way, or if pytest executes tests in a different order, `test_deposit_updates_ledger` will receive unexpected initial state.

**Why it matters:**
Tests must be isolated — each test must set up its own state and must not depend on side-effects produced by other tests. A test suite where order matters is fragile and hard to diagnose.

**Recommendation:**
Remove the global variable entirely. Each test should construct its own `BankAccount` with a known, explicit initial balance.

```python
# Before
shared_balance = 0

class TestBankAccount:
    def test_all_operations(self):
        global shared_balance
        account = BankAccount("Alice", shared_balance)
        ...
        shared_balance = account.get_balance()

    def test_deposit_updates_ledger(self):
        global shared_balance
        account = BankAccount("Bob", shared_balance)  # depends on prior test
        ...

# After
class TestBankAccount:
    def test_all_operations(self):
        account = BankAccount("Alice", 0)
        ...

    def test_deposit_updates_ledger(self):
        account = BankAccount("Bob", 0)  # explicit, independent
        ...
```

---

## Problem 2 — Non-Deterministic Behaviour in Production Code (Determinism Violation)

**Location:** Line 24 (`deposit` method)

**Description:**
The `deposit` method calls `random.randint(1000, 9999)` to generate a transaction ID. This makes tests that inspect the ledger's `id` field non-repeatable: the value changes on every run. While the current tests do not assert on `id` directly, the randomness bleeds into any snapshot or property-based test that might be written later, and it makes reproduction of failures impossible.

**Why it matters:**
Deterministic tests always produce the same result given the same inputs. Non-determinism is a leading cause of flaky tests and hides real bugs.

**Recommendation:**
Replace the random ID generation with a deterministic strategy — a simple auto-incrementing counter is sufficient.

```python
# Before
def deposit(self, amount: float) -> float:
    ...
    tx_id = random.randint(1000, 9999)
    ...

# After
def __init__(self, owner: str, initial_balance: float = 0):
    self.owner = owner
    self._balance = initial_balance
    self._ledger = []
    self._next_tx_id = 1  # deterministic counter

def deposit(self, amount: float) -> float:
    ...
    tx_id = self._next_tx_id
    self._next_tx_id += 1
    ...
```

---

## Problem 3 — One Test Verifying Multiple Independent Behaviours (Specificity Violation)

**Location:** Lines 43–53 (`test_all_operations`)

**Description:**
`test_all_operations` exercises `deposit`, `withdraw`, and `get_balance` in a single test, then asserts on balance, ledger length, and ledger entry type all at once. When this test fails, it is unclear which operation or assertion is the culprit without reading the full traceback.

**Why it matters:**
A specific test targets exactly one behaviour. When it fails, the name alone tells you what is broken. Omnibus tests make failure diagnosis slow and encourage the "fix one, break another" cycle.

**Recommendation:**
Split into focused, single-purpose tests:

```python
# After
def test_deposit_increases_balance(self):
    account = BankAccount("Alice", 0)
    account.deposit(100)
    assert account.get_balance() == 100

def test_withdraw_decreases_balance(self):
    account = BankAccount("Alice", 100)
    account.withdraw(30)
    assert account.get_balance() == 70

def test_deposit_then_withdraw_results_in_correct_balance(self):
    account = BankAccount("Alice", 0)
    account.deposit(100)
    account.withdraw(30)
    assert account.get_balance() == 70
```

---

## Problem 4 — Assertions on Internal Implementation Details (Structure-Sensitivity Violation)

**Location:** Lines 52–53, 59–60

**Description:**
Multiple tests assert directly on `account._ledger`, a private attribute (signalled by the leading underscore convention). The assertions check `len(account._ledger)` and `account._ledger[0]["type"]`. This binds the tests to the current internal data structure. If `_ledger` is renamed, restructured (e.g., changed to a named-tuple list), or removed in favour of event sourcing, all these tests break — even if the observable behaviour is unchanged.

**Why it matters:**
Tests should verify observable outcomes, not implementation internals. Structure-sensitive tests become a maintenance burden and actively discourage refactoring.

**Recommendation:**
Assert on behaviour visible through the public API. If transaction history must be tested, expose it through a public method.

```python
# Add a public method to BankAccount
def transaction_count(self) -> int:
    return len(self._ledger)

def last_transaction_type(self) -> str:
    return self._ledger[-1]["type"] if self._ledger else None

# Tests assert on the public interface
def test_deposit_records_one_transaction(self):
    account = BankAccount("Bob", 0)
    account.deposit(50)
    assert account.transaction_count() == 1

def test_deposit_records_deposit_type(self):
    account = BankAccount("Bob", 0)
    account.deposit(50)
    assert account.last_transaction_type() == "deposit"
```

Alternatively, if the ledger is an intentional public contract, rename `_ledger` to `ledger` (remove the underscore) to signal it is part of the API.

---

## Problem 5 — Weak Error Assertion (Minor)

**Location:** Line 69 (`test_negative_deposit_raises`)

**Description:**
`pytest.raises(ValueError)` without a `match` parameter accepts *any* `ValueError`. The test passes even if the error message is wrong, or if an unrelated `ValueError` is raised by accident (e.g., from a future validation added elsewhere in `deposit`).

**Why it matters:**
Comparing with `test_withdraw_insufficient_funds` (line 64–65), which does use `match="Insufficient funds"`, the inconsistency is clear. Error assertion tests should be precise.

**Recommendation:**

```python
# Before
def test_negative_deposit_raises(self):
    account = BankAccount("Dave", 100)
    with pytest.raises(ValueError):
        account.deposit(-10)

# After
def test_negative_deposit_raises(self):
    account = BankAccount("Dave", 100)
    with pytest.raises(ValueError, match="Amount must be positive"):
        account.deposit(-10)
```

---

## Summary Table

| # | Problem | Violated Property | Severity |
|---|---------|------------------|----------|
| 1 | Shared mutable global `shared_balance` between tests | Isolated | High |
| 2 | `random.randint` in `deposit` makes behaviour non-deterministic | Deterministic | High |
| 3 | `test_all_operations` asserts on deposit, withdraw, and balance together | Specific | Medium |
| 4 | Direct assertions on `_ledger` private attribute | Structure-insensitive | Medium |
| 5 | `pytest.raises(ValueError)` without `match` in `test_negative_deposit_raises` | Specific | Low |

---

## Revised Test File (Full)

```python
import pytest


class BankAccount:
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

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        self._ledger.append({"amount": -amount, "type": "withdrawal"})
        return self._balance

    def get_balance(self) -> float:
        return self._balance

    def transaction_count(self) -> int:
        return len(self._ledger)

    def last_transaction_type(self) -> str:
        return self._ledger[-1]["type"] if self._ledger else None


class TestBankAccount:
    def test_deposit_increases_balance(self):
        account = BankAccount("Alice", 0)
        account.deposit(100)
        assert account.get_balance() == 100

    def test_withdraw_decreases_balance(self):
        account = BankAccount("Alice", 100)
        account.withdraw(30)
        assert account.get_balance() == 70

    def test_deposit_then_withdraw_gives_correct_balance(self):
        account = BankAccount("Alice", 0)
        account.deposit(100)
        account.withdraw(30)
        assert account.get_balance() == 70

    def test_deposit_records_one_transaction(self):
        account = BankAccount("Bob", 0)
        account.deposit(50)
        assert account.transaction_count() == 1

    def test_deposit_records_deposit_type(self):
        account = BankAccount("Bob", 0)
        account.deposit(50)
        assert account.last_transaction_type() == "deposit"

    def test_withdraw_insufficient_funds_raises(self):
        account = BankAccount("Carol", 10)
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.withdraw(100)

    def test_negative_deposit_raises(self):
        account = BankAccount("Dave", 100)
        with pytest.raises(ValueError, match="Amount must be positive"):
            account.deposit(-10)
```
