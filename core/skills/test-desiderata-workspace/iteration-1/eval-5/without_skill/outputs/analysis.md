# Test Quality Analysis: test_cache.ts

**File**: `core/skills/test-desiderata-workspace/evals/files/test_cache.ts`
**Framework**: Kent Beck's Test Desiderata (12 properties)
**Date**: 2026-04-26

---

## Summary

The test file implements tests for an LRU Cache with TTL support. Four deliberate quality violations are embedded in the file. The analysis below evaluates all 12 Test Desiderata properties and identifies each violation with a concrete recommendation.

---

## Property-by-Property Evaluation

### 1. Isolated
**Status: VIOLATED**

The `cache` instance is declared at module scope (line 50) and shared across all four tests. Tests run sequentially and mutate the same cache, meaning later tests inherit state from earlier ones.

Concrete evidence:
- `"stores and retrieves a value"` sets `cache.set("a", 42)`
- `"evicts LRU entry and expired TTL"` then sets `b`, `c`, `d` and notes that eviction of `"a"` depends on whether `"a"` is still present (comment on line 69)
- `"returns undefined for missing key"` relies on the global cache without resetting it

**Recommendation**: Create a fresh `LRUCache` instance inside each `it` block (or in a `beforeEach`):
```ts
let cache: LRUCache<string, number>;
beforeEach(() => {
  cache = new LRUCache<string, number>(3, 1000);
});
```

---

### 2. Composable
**Status: VIOLATED**

The test `"evicts LRU entry and expired TTL"` (line 63) tests two completely orthogonal concerns in a single test case: LRU eviction policy and TTL expiry. When this test fails it is impossible to determine which concern is broken without reading the implementation carefully.

**Recommendation**: Split into two independent tests:
```ts
it("evicts the least-recently-used entry when capacity is exceeded", () => { ... });
it("returns undefined for a key whose TTL has elapsed", () => { ... });
```

---

### 3. Deterministic
**Status: VIOLATED (indirect consequence of Isolated violation)**

Because the shared cache carries state between tests, the outcome of `"evicts LRU entry and expired TTL"` depends on the order in which tests execute. Running tests in a different order (e.g., if a test runner parallelises within the file or a future test is inserted) can produce different pass/fail results.

**Recommendation**: Fixing the Isolated violation (fresh instance per test) resolves non-determinism at the same time.

---

### 4. Fast
**Status: PASS**

All tests complete synchronously (fake timers are used, no real `setTimeout`). No network or disk I/O. This property is satisfied.

---

### 5. Writable
**Status: PASS**

Tests are concise and straightforward to write. The LRU Cache API is simple. No complex setup scaffolding is required beyond creating an instance.

---

### 6. Readable
**Status: VIOLATED**

Multiple magic numbers appear without named constants or explanatory comments:
- `42` (line 60) — arbitrary sentinel value, purpose unclear
- `1000` (line 50) — TTL in milliseconds, not labelled
- `3` (line 50, 89) — capacity limit, not labelled
- `5000` (line 89) — a different TTL introduced inside `"respects capacity"` without explanation; it is inconsistent with the module-level `1000`
- `5` — referenced in the comment on line 88 but appears to be a copy-paste error referencing `5000`

**Recommendation**: Introduce named constants at the top of the file:
```ts
const CAPACITY = 3;
const TTL_MS = 1_000;
const LONG_TTL_MS = 5_000;
const SENTINEL_VALUE = 42;
```

---

### 7. Behavioral
**Status: VIOLATED**

The TTL expiry test in `"evicts LRU entry and expired TTL"` (lines 72–80) has a logical flaw: `vi.useFakeTimers()` is called but `vi.advanceTimersByTime()` is never invoked. Therefore the TTL never elapses inside the test. The assertion `expect(result).not.toBeUndefined()` then passes — but for the wrong reason (the entry is fresh, not expired). The test's documented intent is to verify that an expired entry returns `undefined`, but it never exercises that path.

**Recommendation**: Advance fake timers past the TTL after inserting the entry:
```ts
vi.useFakeTimers();
cache.set("temp", 99);
vi.advanceTimersByTime(1001); // past TTL_MS
expect(cache.get("temp")).toBeUndefined();
```

---

### 8. Structure-insensitive
**Status: PASS**

Tests call the public API (`get`, `set`, `size`) and do not inspect private fields (`map`, `capacity`, `ttlMs`). Refactoring the internal Map representation would not break the tests.

---

### 9. Automated
**Status: PASS**

Tests are executed by Vitest without manual steps. The `afterEach` hook restores real timers automatically.

---

### 10. Specific
**Status: PARTIALLY VIOLATED**

The Behavioral violation means the TTL branch is not specifically tested — the assertion passes for a reason that differs from the intended scenario. When the test fails in future (e.g., after a real bug in TTL logic), the failure message (`not.toBeUndefined`) will not pinpoint which scenario is broken.

**Recommendation**: After fixing the fake timer advancement, add a positive assertion too:
```ts
expect(cache.get("valid")).toBe(validValue); // within TTL
vi.advanceTimersByTime(TTL_MS + 1);
expect(cache.get("valid")).toBeUndefined();  // after TTL
```

---

### 11. Predictive
**Status: PARTIALLY VIOLATED**

Because the shared `cache` instance leads to order-dependent state, a real regression in eviction logic might still cause one test to pass while another fails depending on what was inserted in prior tests. The test suite does not reliably predict the presence of LRU eviction bugs introduced after the shared-state issue exists.

**Recommendation**: Fixing isolation ensures each test independently exercises a scenario, so the suite collectively predicts regressions across all behaviours.

---

### 12. Inspiring
**Status: VIOLATED**

The combination of hidden state sharing, a TTL test that never expires anything, and magic numbers makes it difficult for a developer to understand what the cache is supposed to do and how to add new tests confidently. The `"evicts LRU entry and expired TTL"` test in particular sends mixed signals about what is actually being verified.

**Recommendation**: Each test should have a single clear name that maps 1:1 to a behaviour. Remove all magic numbers. Ensure each test is self-contained so that reading it tells the full story of setup → action → assertion.

---

## Violations Summary Table

| Property | Status | Root Cause |
|---|---|---|
| Isolated | VIOLATED | Shared `cache` instance at module scope |
| Composable | VIOLATED | Single test covers LRU eviction + TTL expiry |
| Deterministic | VIOLATED | Consequence of shared state; order-dependent |
| Fast | PASS | — |
| Writable | PASS | — |
| Readable | VIOLATED | Magic numbers: 42, 1000, 3, 5000 |
| Behavioral | VIOLATED | Fake timers set up but time never advanced; test passes for wrong reason |
| Structure-insensitive | PASS | — |
| Automated | PASS | — |
| Specific | PARTIAL | TTL assertion does not target the intended failure path |
| Predictive | PARTIAL | Shared state can mask eviction regressions |
| Inspiring | VIOLATED | Misleading test names and hidden state sharing reduce confidence |

---

## Priority Recommendations

1. **Fix isolation first**: move `cache` into `beforeEach`. This resolves Isolated, Deterministic, and Predictive in one change.
2. **Fix the behavioral bug**: add `vi.advanceTimersByTime(TTL_MS + 1)` before asserting expiry.
3. **Split the composable test**: separate eviction and TTL into independent `it` blocks.
4. **Replace magic numbers** with named constants.
