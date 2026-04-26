# Test Desiderata Analysis: test_bank_account.py

## Summary

File analyzed: `test_bank_account.py`
Framework: Kent Beck's Test Desiderata (12 properties)
Violations found: 5 properties violated (Isolated, Deterministic, Specific, Structure-insensitive, Behavioral)

---

## Violations

### Issue 1

**Issue:** `test_all_operations` and `test_deposit_updates_ledger` violate the **Isolated** property
**Location:** Lines 12, 45–46, 56–57 — module-level `shared_balance = 0` is mutated by `test_all_operations` (line 49) and then read by `test_deposit_updates_ledger` (line 57) as the initial balance for a new account.
**Impact:** Test results depend on execution order. If `test_deposit_updates_ledger` runs before `test_all_operations`, Bob's account starts at 0 and the assertion `len(account._ledger) == 1` passes for the right reason. If it runs after, Bob's account starts at 70 (the side-effect left by the first test), which changes the observable starting state even though the ledger assertion still passes in this specific case. Any future assertion on balance or any reordering that also mutates `shared_balance` would produce order-dependent failures, eroding trust.
**Fix:** Remove `shared_balance` entirely. Each test should construct its `BankAccount` with an explicit, hard-coded initial balance:

```python
# Before
shared_balance = 0  # global mutable state

class TestBankAccount:
    def test_all_operations(self):
        global shared_balance
        account = BankAccount("Alice", shared_balance)
        ...
        shared_balance = account.get_balance()

    def test_deposit_updates_ledger(self):
        global shared_balance
        account = BankAccount("Bob", shared_balance)  # depends on previous test

# After
class TestBankAccount:
    def test_all_operations(self):
        account = BankAccount("Alice", initial_balance=0)
        ...

    def test_deposit_updates_ledger(self):
        account = BankAccount("Bob", initial_balance=0)
        ...
```

---

### Issue 2

**Issue:** `BankAccount.deposit` violates the **Deterministic** property
**Location:** Line 24 — `tx_id = random.randint(1000, 9999)` inside `deposit()`, called by every test that deposits.
**Impact:** The transaction ID assigned to each ledger entry is different on every run. Any test that asserts on the ledger entry's `id` field (e.g., checking a specific transaction ID) will produce a different value each run. Even the current tests, which check `_ledger[0]["type"]` rather than `id`, are indirectly affected: if a future test pins `tx_id` to verify traceability, it will fail non-deterministically. The randomness also makes log-based debugging harder because replaying a failure does not reproduce the exact ledger state.
**Fix:** Inject the ID source so tests can control it, or use a deterministic counter:

```python
# Option A — injectable ID generator (preferred for testing)
class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0, id_generator=None):
        self._id_generator = id_generator or (lambda: random.randint(1000, 9999))
        ...

    def deposit(self, amount: float) -> float:
        tx_id = self._id_generator()
        ...

# In tests, pass a deterministic generator:
account = BankAccount("Alice", id_generator=iter([1001, 1002, 1003]).__next__)

# Option B — sequential counter (simpler, no randomness)
import itertools
_counter = itertools.count(1)

class BankAccount:
    def deposit(self, amount: float) -> float:
        tx_id = next(_counter)
        ...
```

---

### Issue 3

**Issue:** `test_all_operations` violates the **Specific** property
**Location:** Lines 43–53 — a single test method performs a deposit, a withdrawal, checks the resulting balance, checks the ledger length, and checks the ledger entry type.
**Impact:** When this test fails, the failure message points to the entire `test_all_operations` method without indicating which operation caused the problem. A balance assertion failure and a ledger-structure assertion failure look identical at the test-runner level. Developers must read the full test body and mentally simulate the sequence to isolate the root cause, slowing down the feedback loop.
**Fix:** Split into one focused test per behavior:

```python
def test_deposit_increases_balance(self):
    account = BankAccount("Alice", initial_balance=0)
    account.deposit(100)
    assert account.get_balance() == 100

def test_withdraw_decreases_balance(self):
    account = BankAccount("Alice", initial_balance=100)
    account.withdraw(30)
    assert account.get_balance() == 70

def test_deposit_then_withdraw_final_balance(self):
    account = BankAccount("Alice", initial_balance=0)
    account.deposit(100)
    account.withdraw(30)
    assert account.get_balance() == 70
```

---

### Issue 4

**Issue:** `test_all_operations` and `test_deposit_updates_ledger` violate the **Structure-insensitive** property
**Location:** Lines 52–53 (`account._ledger`) and lines 59–60 (`account._ledger`) — both tests assert directly on the private `_ledger` attribute.
**Impact:** `_ledger` is an internal implementation detail. If the implementation changes — e.g., renaming it to `_transactions`, switching from a list to a deque, or adding a wrapper class — these tests break immediately even though the public behavior (balance, deposits, withdrawals) is completely unchanged. This makes safe refactoring painful and discourages structural improvements.
**Fix:** Add a public method for ledger inspection, or verify behavior through the public API only:

```python
# Option A — expose a public read-only view
class BankAccount:
    def transaction_count(self) -> int:
        return len(self._ledger)

    def last_transaction_type(self) -> str:
        return self._ledger[-1]["type"] if self._ledger else None

# In tests:
assert account.transaction_count() == 2
assert account.last_transaction_type() == "deposit"

# Option B — test only observable outcomes (balance) and skip internal state
def test_deposit_updates_balance(self):
    account = BankAccount("Alice", initial_balance=0)
    account.deposit(100)
    assert account.get_balance() == 100  # no _ledger assertions needed
```

---

### Issue 5

**Issue:** `test_deposit_updates_ledger` violates the **Behavioral** property
**Location:** Lines 55–60 — the test only checks the internal ledger structure (an implementation detail) rather than observable behavior. There is no assertion that the deposit actually changed the account balance.
**Impact:** The test could pass even if `deposit` correctly updates the ledger but silently fails to update `_balance`. The core behavioral contract — "depositing money increases the account balance" — is never verified. A bug in `_balance += amount` would go undetected by this test.
**Fix:** Assert on the observable outcome (balance) rather than, or in addition to, internal structure:

```python
def test_deposit_increases_balance(self):
    account = BankAccount("Bob", initial_balance=0)
    account.deposit(50)
    assert account.get_balance() == 50  # behavioral assertion: balance changed
```

---

## Tradeoffs

### Tradeoff 1: Isolated vs. Specific (only seeming to interfere)

The `shared_balance` global creates an Isolated violation: tests depend on each other's side effects. At the same time, `test_all_operations` packs multiple behaviors into one test (a Specific violation). These feel related — it looks as though the test is monolithic *because* it needs to thread state through operations in sequence.

In reality, the coupling is artificial. The multi-step sequence exists only to update `shared_balance` as a side effect. Removing `shared_balance` (fixing Isolated) immediately makes it safe to split `test_all_operations` into focused, single-concern tests (fixing Specific). No tradeoff needs to be accepted.

**Design insight:** Replace the global with explicit, per-test initial balances. Once each test owns its own `BankAccount` instance, splitting the monolithic test carries zero risk of cross-test contamination.

**Priority:** Fix Isolated first — flaky, order-dependent tests erode trust faster than verbose tests. Splitting naturally follows.

---

### Tradeoff 2: Structure-insensitive vs. Behavioral (only seeming to interfere)

Both `test_all_operations` and `test_deposit_updates_ledger` assert on `_ledger` (Structure-insensitive violation). `test_deposit_updates_ledger` then *only* asserts on `_ledger`, missing the balance change entirely (Behavioral violation). These violations appear to be in tension: if we remove the `_ledger` assertions to fix Structure-insensitive, the test becomes even weaker on the behavioral dimension unless we add balance assertions.

But the tension is illusory. The fix for Structure-insensitive (assert on public behavior) and the fix for Behavioral (assert that balance changed) point to the same action: replace `_ledger` assertions with `get_balance()` assertions. Fixing one property directly fulfills the other.

**Design insight:** Asserting `account.get_balance() == 50` after a deposit is simultaneously structure-insensitive (uses the public API) and behavioral (verifies the observable outcome). One change fixes both violations.

**Priority:** Fix Behavioral first for `test_deposit_updates_ledger` — the current test gives a false sense of coverage. Structure-insensitive follows automatically once the assertion target changes to `get_balance()`.

---

### Tradeoff 3: Deterministic vs. Isolated (supporting)

The random `tx_id` in `deposit()` (Deterministic violation) and the `shared_balance` global (Isolated violation) are independent root causes, but they support each other when fixed. Eliminating `shared_balance` ensures each test gets a fresh `BankAccount` instance. A fresh instance means each deposit call is the only one contributing to that instance's ledger — removing the order-dependent ledger accumulation that could interact unpredictably with a non-deterministic `tx_id`. Fixing Isolated does not fix Deterministic (the random call remains), but it limits the blast radius: non-deterministic IDs in one test cannot leak into another test's expectations.

**Priority:** Fix Isolated first (removes cross-test contamination), then fix Deterministic (injects a stable ID generator) to make individual test runs fully reproducible.

---

### Tradeoff 4: Specific vs. Behavioral (supporting)

Splitting `test_all_operations` into focused tests (fixing Specific) also improves Behavioral coverage. The current monolithic test verifies only the final balance after both a deposit and a withdrawal, not the intermediate state after deposit alone. When split, `test_deposit_increases_balance` verifies that `deposit` changes the balance in isolation — a behavioral assertion not currently present anywhere in the suite. Fixing Specific therefore reveals and fills a Behavioral gap at no extra cost.

**Priority:** Fix Specific (split the test) — the Behavioral improvement comes for free as each focused test naturally asserts its own observable outcome.
