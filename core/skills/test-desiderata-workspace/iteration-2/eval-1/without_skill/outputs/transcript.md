# Transcript: Test Quality Analysis — test_bank_account.py

## Task

Analyze the test file at `core/skills/test-desiderata-workspace/evals/files/test_bank_account.py` for quality issues and produce a concrete improvement report.

---

## Step 1 — Read the target file

**Tool:** Read  
**Path:** `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_bank_account.py`

**Observations from the file header (lines 1–8):**
The docstring itself announces four seeded violations:
- `Isolated`: shared global balance between tests
- `Deterministic`: `random.randint` used to generate a transaction ID
- `Specific`: a single test verifies deposit, withdraw, and balance together
- `Structure-insensitive`: assertion on internal `_ledger` attribute

**Full file contents reviewed:** 71 lines — one class `BankAccount` and one test class `TestBankAccount` with four test methods.

---

## Step 2 — Check output directory existence

**Tool:** Bash (`ls`)  
**Result:** `/iteration-2/eval-1/without_skill/outputs/` directory exists and is empty.

---

## Step 3 — Analyse each violation in detail

### 3.1 Shared mutable global `shared_balance` (Isolation)

Lines 12, 45–49, 56–57.  
`shared_balance = 0` is declared at module level. `test_all_operations` mutates it (sets it to the balance after a deposit+withdraw cycle, i.e. 70). `test_deposit_updates_ledger` then constructs `BankAccount("Bob", shared_balance)` — meaning Bob starts with a balance of 70, not 0. The two tests are order-dependent.

**Conclusion:** High-severity isolation violation. Removing the global and giving each test its own explicit initial state fixes it entirely.

### 3.2 `random.randint` in `deposit` (Determinism)

Line 24.  
The production code under test calls `random.randint(1000, 9999)` for every deposit. No existing test asserts on `id`, but this is still a violation: any test that serialises or snapshots a ledger entry will produce a different value each run, and reproduction of failures becomes impossible.

**Conclusion:** High-severity determinism violation in the implementation being tested. Recommend replacing with a deterministic counter. No monkey-patching or seeding required with this fix.

### 3.3 `test_all_operations` covers three behaviours (Specificity)

Lines 43–53.  
The test deposits 100, withdraws 30, then asserts on balance (70), ledger length (2), and the type of the first ledger entry ("deposit"). Three orthogonal behaviours in one test. If any assertion fails, the name `test_all_operations` gives no diagnostic signal.

**Conclusion:** Medium-severity specificity violation. Split into at minimum three focused tests.

### 3.4 Assertions on `_ledger` private attribute (Structure-sensitivity)

Lines 52–53 and 59–60.  
`account._ledger` is a private list. Both `test_all_operations` and `test_deposit_updates_ledger` read `len(account._ledger)` and index into it to inspect `["type"]`. Any refactoring of the internal ledger representation (rename, change to a dataclass, convert to an event log, etc.) will break these tests without any behaviour change.

**Conclusion:** Medium-severity structure-sensitivity violation. Expose transaction count and last-transaction-type through a public method, then assert on those.

### 3.5 Weak error assertion in `test_negative_deposit_raises` (Specificity, minor)

Line 69.  
`pytest.raises(ValueError)` with no `match` parameter accepts any `ValueError`. The sibling test `test_withdraw_insufficient_funds_raises` already uses `match="Insufficient funds"`, creating an inconsistency. The fix is trivial: add `match="Amount must be positive"`.

**Conclusion:** Low-severity specificity violation.

---

## Step 4 — Draft recommendations

For each problem, a before/after code snippet was written to make the recommendation concrete and actionable. A revised full test file was also produced that incorporates all fixes.

---

## Step 5 — Write output files

**analysis.md** — Full structured analysis with problem descriptions, rationale, before/after code, summary table, and revised complete test file.  
**transcript.md** — This file.

---

## Tools Used

| Step | Tool | Purpose |
|------|------|---------|
| 1 | Read | Read test file |
| 2 | Bash (ls) | Verify output directory exists |
| 3–4 | (reasoning) | Analyse violations, draft recommendations |
| 5 | Write (x2) | Save analysis.md and transcript.md |
