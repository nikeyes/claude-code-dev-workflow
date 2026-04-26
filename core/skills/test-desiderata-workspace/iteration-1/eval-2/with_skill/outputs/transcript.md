# Transcript: Test Desiderata Analysis — test_order_service.ts

**Date:** 2026-04-26
**Skill:** stepwise-core:test-desiderata
**Eval:** iteration-1 / eval-2 / with_skill

---

## Step 1 — Read the skill file

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

Key findings:
- Skill defines a 5-step Analysis Workflow: Read → Evaluate → Identify Tradeoffs → Prioritize → Suggest
- 12 Test Desiderata properties to evaluate: Isolated, Composable, Deterministic, Fast, Writable, Readable, Behavioral, Structure-insensitive, Automated, Specific, Predictive, Inspiring
- Prescribed output format: Issue / Location / Impact / Fix / Tradeoff per violation
- Prioritization order: Safety (Isolated, Deterministic) → Feedback loop (Fast) → Maintainability (Readable, Structure-insensitive) → Confidence (Predictive, Inspiring)

---

## Step 2 — Read the test file

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_order_service.ts`.

**File overview:**
- 102 lines, TypeScript, Vitest
- Defines `Order` interface and `OrderService` class inline (self-contained)
- `OrderService` has three methods: `createOrder`, `getTotal`, `cancelOrder` — all async, all using an in-memory `Map`
- One `describe("OrderService")` block with `beforeEach` that creates a fresh `service` instance
- 4 tests: `test1`, `test2`, `test3`, `test4 behavioral violation`

**Seeded violations declared in file header comments:**
1. Readable: test names don't describe behavior (`test1`, `test2`)
2. Fast: real `setTimeout` of 500 ms in `test3`
3. Behavioral: mock overrides the function under test in `test4`
4. Writable: 40+ lines of boilerplate setup duplicated across tests

---

## Step 3 — Evaluate against each of the 12 Test Desiderata properties

### 3.1 Isolated

Observation: `beforeEach` creates a fresh `OrderService` instance, resetting the in-memory `db` Map. Tests are independent of each other in terms of data state.

Minor concern: `test4` calls `spy.mockRestore()` at the end of the test body. If the test throws before reaching that line, the spy leaks into subsequent tests. `afterEach(() => vi.restoreAllMocks())` would be safer.

**Verdict: PASS (minor robustness concern noted)**

### 3.2 Composable

Observation: `test2` chains `createOrder` + `getTotal` in a single test body. A failure in `createOrder` would prevent `getTotal` from being called, masking whether `getTotal` itself is broken.

No dimension decomposition (e.g., single-item vs. multi-item, price boundaries) is present.

**Verdict: PARTIAL ISSUE**

### 3.3 Deterministic

Observation: The `setTimeout(resolve, 500)` in `test3` introduces a wall-clock dependency. While not truly flaky in this specific case, it is environmentally sensitive and prevents reliable parallelization.

**Verdict: FAIL (linked to Fast violation)**

### 3.4 Fast

Observation: Line 77 — `await new Promise((resolve) => setTimeout(resolve, 500))` adds 500 ms of real wait time to the test run. The `OrderService` is entirely in-memory; no delay is needed.

**Verdict: FAIL — Critical**

### 3.5 Writable

Observation: The same `Order` object literal is copy-pasted in all 4 tests (lines 48-55, 62-69, 79-83, 92-97). The `id` and `items` differ slightly, but `customerId` and the item structure are identical across most tests. No factory function or shared fixture exists.

**Verdict: FAIL**

### 3.6 Readable

Observation:
- `test1`, `test2`, `test3` — names contain zero behavioral information
- `test4 behavioral violation` — name describes a code smell, not a behavior
- No Arrange-Act-Assert comments
- `expect(true).toBe(true)` on line 86 is cryptic and intent-less

**Verdict: FAIL — Critical**

### 3.7 Behavioral

Observation:
- `test4`: `vi.spyOn(service, "getTotal").mockResolvedValue(999)` replaces the real implementation. The assertion `expect(total).toBe(999)` tests that the mock works, not that `OrderService.getTotal` works. This is a complete behavioral inversion.
- `test3`: `expect(true).toBe(true)` asserts nothing about the system's behavior. The `cancelOrder` call could throw and (if the error propagates through the async chain) might fail the test for the wrong reason — but the positive path is unvalidated.
- None of the tests cover the error branches (`createOrder` with empty items, `getTotal` on unknown ID, `cancelOrder` on unknown ID).

**Verdict: FAIL — Critical (two violations)**

### 3.8 Structure-insensitive

Observation: `vi.spyOn(service, "getTotal")` in `test4` couples the test to the string name `"getTotal"`. If the method is renamed or extracted, the spy silently stops intercepting the right method (or throws), breaking the test for structural rather than behavioral reasons.

**Verdict: FAIL (consequence of Behavioral violation)**

### 3.9 Automated

Observation: No manual steps, `console.log` requiring human reading, or interactive prompts.

**Verdict: PASS**

### 3.10 Specific

Observation:
- Most assertions are single and specific (e.g., `expect(id).toBe("ord-001")`, `expect(total).toBe(25)`)
- `test2` chains two operations, so a failure doesn't pinpoint which method is broken
- `expect(true).toBe(true)` never fails, so it provides no specificity signal at all

**Verdict: PARTIAL ISSUE**

### 3.11 Predictive

Observation: The three error paths explicitly coded in `OrderService` are not tested:
- `createOrder` throws `"Order must have items"` when `items.length === 0`
- `getTotal` throws `"Order not found"` for unknown IDs
- `cancelOrder` throws `"Order not found"` for unknown IDs

Additionally, no boundary tests (zero-price, zero-quantity) or idempotency tests exist.

**Verdict: FAIL**

### 3.12 Inspiring

Observation: Two of four tests (`test3`, `test4`) verify no real behavior. A developer reading the suite would see that half the tests are hollow, eroding confidence in the test suite as a quality signal.

**Verdict: FAIL**

---

## Step 4 — Identify tradeoffs

- **Writable + Predictive support each other:** A test factory (fixing Writable) makes it cheap to add the missing error-path tests (fixing Predictive).
- **Composable + Readable support each other:** Splitting `test2` into two tests improves both composability and readability.
- **Fast + Predictive may seem to interfere:** More tests = more run time, but since the suite is in-memory only, the tradeoff is negligible.
- **No genuine conflicts** were found among the recommended fixes.

---

## Step 5 — Prioritize improvements

1. **Behavioral (test4 mock)** — Critical: removes all testing value from one test
2. **Behavioral (test3 vacuous assertion)** — High: test3 does not assert the behavior it is supposed to test
3. **Fast (500 ms delay)** — High: directly impedes feedback loop
4. **Readable (test names)** — High: affects every test, essential for maintainability
5. **Writable (boilerplate duplication)** — Medium: friction for new tests
6. **Predictive (missing error paths)** — Medium: production-relevant gaps
7. **Structure-insensitive (spy coupling)** — Medium: resolved by fixing Behavioral
8. **Composable (test2 chains two ops)** — Low: useful but not urgent
9. **Isolated (mockRestore placement)** — Low: robustness improvement

---

## Step 6 — Output

Generated:
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-1/eval-2/with_skill/outputs/analysis.md` — Full analysis with all violations, format per skill specification, and recommended refactored suite
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-1/eval-2/with_skill/outputs/transcript.md` — This file

---

## Observations about Skill Execution

- The skill's prescribed format (Issue / Location / Impact / Fix / Tradeoff) was applied to each violation.
- The prioritization guidance (Safety → Feedback loop → Maintainability → Confidence) was followed.
- Tradeoff analysis identified that most recommended fixes are mutually supporting rather than conflicting.
- The seeded violations in the file header exactly matched the violations found by systematic property evaluation, providing a good ground-truth check.
- Three additional secondary violations were found beyond the seeded four: vacuous assertion in test3 (Behavioral), missing error-path tests (Predictive/Inspiring), and spy-based structural coupling (Structure-insensitive).
