# Transcript: Test Desiderata Analysis (Baseline — No Skill)

## Run Metadata
- Date: 2026-04-26
- Mode: Baseline (no skill invocation)
- Framework: Kent Beck's Test Desiderata (12 properties)
- Analyst: Claude (baseline, own knowledge only)

---

## Step 1: Read the test file

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_order_service.ts`.

The file is 103 lines. It contains:
- An `Order` interface and `OrderService` class (inline, not imported from production code)
- A `describe("OrderService")` block with 4 test cases: `test1`, `test2`, `test3`, `test4 behavioral violation`
- The file header comment explicitly lists 4 planted violations: Readable, Fast, Behavioral, Writable

---

## Step 2: Understand the system under test

`OrderService` has three methods:
- `createOrder(order)` — validates items are non-empty, stores by id, returns id
- `getTotal(orderId)` — retrieves order and computes `sum(qty * price)`
- `cancelOrder(orderId)` — deletes order by id

The implementation is correct and self-contained.

---

## Step 3: Evaluate each of the 12 Test Desiderata properties

### Isolated
- `beforeEach` creates a fresh `OrderService`, so no shared mutable state between tests.
- Minor risk: `test4` calls `spy.mockRestore()` inside the test body; if an earlier assertion throws, cleanup won't run.
- Verdict: PASS with minor caveat

### Composable
- Tests can run in any order or subset without impacting each other.
- No cross-test dependencies.
- Verdict: PASS

### Deterministic
- `test3` uses a real `setTimeout(resolve, 500)`.
- The 500ms delay is wall-clock time, not controlled by fake timers.
- Result is always the same but execution characteristics vary across environments.
- The vacuous assertion (`expect(true).toBe(true)`) means the test has no meaningful pass/fail signal.
- Verdict: FAIL (marginal on timing, clear on vacuous assertion)

### Fast
- `test3` introduces a hard-coded 500ms delay with no test-relevant purpose.
- This slows every test run by at least 500ms.
- There is no use of `vi.useFakeTimers()` or any injectable clock.
- Verdict: FAIL (clear violation)

### Writable
- The same order fixture (6–8 lines) is copy-pasted into `test1`, `test2`, `test3`, `test4`.
- Adding a new test requires duplicating the entire fixture.
- No shared factory function or builder exists.
- Verdict: FAIL (clear violation)

### Readable
- Test names: `test1`, `test2`, `test3`, `test4 behavioral violation`.
- None of these names express the behavior under test or the expected outcome.
- `test4 behavioral violation` names the problem but not the intended behavior.
- Verdict: FAIL (clear violation)

### Behavioral
- `test4` uses `vi.spyOn(service, "getTotal").mockResolvedValue(999)` and then asserts the mock returns 999.
  - This is testing the mock, not the implementation. If `getTotal` had a severe bug, this test still passes.
- `test3` ends with `expect(true).toBe(true)`.
  - This assertion is vacuous. It passes unconditionally and verifies nothing about `createOrder` or `cancelOrder`.
- Verdict: FAIL (critical violation in two tests)

### Structure-insensitive
- Tests use only the public API (`createOrder`, `getTotal`, `cancelOrder`).
- No inspection of private `db` field.
- Internal refactoring would not break these tests.
- Verdict: PASS

### Automated
- All tests use vitest (`describe`, `it`, `expect`).
- No manual steps required.
- Verdict: PASS

### Specific
- `test3`'s `expect(true).toBe(true)` cannot fail and points to nothing specific.
- `test4`'s `expect(total).toBe(999)` is precise only about the mock's return value.
- `test1` and `test2` have specific, meaningful assertions.
- Verdict: FAIL (two tests)

### Predictive
- A passing `test3` and `test4` give false confidence: they would pass even if the implementation were completely broken.
- No tests for error paths (empty items, non-existent order).
- `test1` and `test2` are genuinely predictive.
- Verdict: FAIL (partial — two tests reduce overall predictive value)

### Inspiring
- Opaque names discourage new test writing.
- Boilerplate duplication makes adding tests tedious.
- Vacuous assertion and mock-testing-mock are anti-patterns that could be learned from.
- No error-path tests to model how to test exceptional behavior.
- Verdict: FAIL

---

## Step 4: Compile violations

Total violations: 7 out of 12 properties
- FAIL: Deterministic, Fast, Writable, Readable, Behavioral, Specific, Predictive, Inspiring
- PASS: Isolated (minor caveat), Composable, Structure-insensitive, Automated

Most critical: Behavioral (test4 mocks method under test; test3 uses vacuous assertion)
High severity: Fast, Writable, Readable, Specific, Predictive
Medium severity: Inspiring, Deterministic

---

## Step 5: Formulate recommendations

1. Rename tests to describe behavior: `"createOrder stores order and returns id"`, etc.
2. Extract `makeOrder()` factory to eliminate fixture duplication.
3. Remove 500ms `setTimeout` from `test3`; add meaningful assertion (e.g., getTotal throws after cancel).
4. Remove mock from `test4`; test real `getTotal` calculation.
5. Add error-path tests for `createOrder` (empty items), `getTotal` (missing order), `cancelOrder` (missing order).
6. Move `spy.mockRestore()` to `afterEach` for safe cleanup.

---

## Step 6: Write outputs

- Analysis saved to: `outputs/analysis.md`
- Transcript saved to: `outputs/transcript.md`
