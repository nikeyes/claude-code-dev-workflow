# Work Transcript: Test Desiderata Evaluation

**Task:** Analyze `test_bank_account.py` using Kent Beck's Test Desiderata framework
**Date:** 2026-04-26

---

## Step 1: Read the skill file

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

**Key findings:**
- The skill defines the Analysis Workflow as: Read → Evaluate → Identify tradeoffs → Prioritize → Suggest changes
- 12 properties to evaluate: Isolated, Composable, Deterministic, Fast, Writable, Readable, Behavioral, Structure-insensitive, Automated, Specific, Predictive, Inspiring
- Each recommendation should follow the format: Issue / Location / Impact / Fix / Tradeoff
- Prioritization order: Safety (Isolated+Deterministic) → Feedback loop (Fast) → Maintainability (Readable+Structure-insensitive) → Confidence (Predictive+Inspiring)

---

## Step 2: Read the test file

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_bank_account.py`.

**File summary:**
- 71 lines including the `BankAccount` class (production code embedded) and 4 test methods in `TestBankAccount`
- The file header comment explicitly lists intended violations: Isolated, Deterministic, Specific, Structure-insensitive
- 4 test methods: `test_all_operations`, `test_deposit_updates_ledger`, `test_withdraw_insufficient_funds`, `test_negative_deposit_raises`

**Initial observations from reading:**
1. `shared_balance = 0` at module level — global mutable state
2. `random.randint(1000, 9999)` inside `deposit()` — non-deterministic ID generation
3. `test_all_operations` runs deposit + withdraw + balance assertion in one test
4. `account._ledger` accessed directly in two tests — private attribute access

---

## Step 3: Evaluate against all 12 properties

### Property 1: Isolated
- **Observed:** `shared_balance` is declared at module level (line 12). `test_all_operations` reads it as initial balance and writes back `account.get_balance()` (70) into it after operations (lines 46, 49). `test_deposit_updates_ledger` then reads `shared_balance` (now 70) as its initial balance (line 57).
- **Verdict:** VIOLATED — tests are order-dependent. If pytest runs `test_deposit_updates_ledger` first, Bob's account starts at 0, not 70. The ledger assertions may still pass but the setup intent is broken.

### Property 2: Composable
- **Observed:** `test_all_operations` covers deposit, withdrawal, and balance check in one test. There are no focused single-operation tests.
- **Verdict:** WARNING — cannot test deposit and withdrawal dimensions independently.

### Property 3: Deterministic
- **Observed:** `BankAccount.deposit()` calls `random.randint(1000, 9999)` to assign `tx_id` (line 24). Current tests don't assert on `tx_id`, so no test currently fails. But the non-determinism is latent.
- **Verdict:** VIOLATED — the production code under test introduces non-determinism. Any future test asserting on transaction IDs would be flaky.

### Property 4: Fast
- **Observed:** All operations are pure Python, in-memory. No I/O, no sleep, no network.
- **Verdict:** PASS

### Property 5: Writable
- **Observed:** The global state coupling increases cognitive load for writing new tests. A new developer must understand `shared_balance` ordering to write a correct test.
- **Verdict:** WARNING (minor)

### Property 6: Readable
- **Observed:** `test_all_operations` name is opaque. The docstring helps but compensating for a bad name with a docstring is a smell. Assertions on `_ledger` lack context.
- **Verdict:** WARNING (medium)

### Property 7: Behavioral
- **Observed:** Error-path tests (`test_withdraw_insufficient_funds`, `test_negative_deposit_raises`) correctly verify behavior. `test_all_operations` mixes behavioral assertions (balance) with structural assertions (ledger length, ledger entry type).
- **Verdict:** WARNING — structural assertions weaken the behavioral signal.

### Property 8: Structure-insensitive
- **Observed:** Four direct assertions on `account._ledger` (lines 52, 53, 59, 60). This is a private attribute.
- **Verdict:** VIOLATED — renaming or restructuring `_ledger` breaks tests without changing observable behavior.

### Property 9: Automated
- **Observed:** All tests runnable via `pytest`. No manual steps, no print-and-inspect patterns.
- **Verdict:** PASS

### Property 10: Specific
- **Observed:** `test_all_operations` has 3 assertions on lines 51-53. A failure in any one does not clearly identify which operation (deposit or withdrawal) is broken.
- **Verdict:** VIOLATED

### Property 11: Predictive
- **Observed:** Missing tests for: exact-balance withdrawal (boundary), return values of `deposit()` and `withdraw()`.
- **Verdict:** WARNING — gaps in edge-case coverage.

### Property 12: Inspiring
- **Observed:** Overall suite has known fragility (shared state, private attribute access). A green run does not inspire confidence.
- **Verdict:** WARNING

---

## Step 4: Identify tradeoffs

- No genuine tradeoffs found — all violations can be fixed simultaneously without sacrificing any other property.
- Main supporting relationships:
  - Fixing Isolated → also improves Writable and Inspiring
  - Fixing Specific → also improves Composable and Readable
  - Fixing Structure-insensitive → also improves Behavioral

---

## Step 5: Prioritize improvements

Applied the skill's prioritization framework:
1. **Safety first** — Isolated (shared state) and Deterministic (random ID) are critical
2. **Feedback loop** — Fast already passes, no action needed
3. **Maintainability** — Structure-insensitive (private ledger access) and Readable (opaque test names) are next
4. **Confidence** — Predictive gap (missing edge cases) last

---

## Step 6: Write recommendations

Followed the skill's prescribed format (Issue / Location / Impact / Fix / Tradeoff) for each violation. Prepared a refactored example showing the end state.

---

## Output files

- `analysis.md` — Full property-by-property analysis with all violations, recommendations, summary table, tradeoff analysis, prioritized action list, and example refactored test
- `transcript.md` — This file

---

## Violations found (summary)

| Property             | Verdict  |
|----------------------|----------|
| Isolated             | VIOLATED |
| Composable           | WARNING  |
| Deterministic        | VIOLATED |
| Fast                 | PASS     |
| Writable             | WARNING  |
| Readable             | WARNING  |
| Behavioral           | WARNING  |
| Structure-insensitive | VIOLATED |
| Automated            | PASS     |
| Specific             | VIOLATED |
| Predictive           | WARNING  |
| Inspiring            | WARNING  |

4 hard violations (Isolated, Deterministic, Structure-insensitive, Specific), 6 warnings, 2 passes.
