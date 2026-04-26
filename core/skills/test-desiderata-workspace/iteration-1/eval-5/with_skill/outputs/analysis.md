# Test Desiderata Analysis: test_cache.ts

**File analyzed:** `core/skills/test-desiderata-workspace/evals/files/test_cache.ts`
**Framework:** Kent Beck's Test Desiderata (12 properties)
**Date:** 2026-04-26

---

## Summary

The test file covers an `LRUCache` implementation with 4 test cases. The tests contain several significant quality issues spanning **4 of the 12 Test Desiderata properties**. The most critical issue is a behavioral false-positive: a test passes for the wrong reason, providing false confidence. A shared mutable instance also causes isolation failures. Two additional concerns — readability (magic numbers) and composability (mixed concerns) — reduce maintainability.

---

## Violations Found

### 1. Isolated — VIOLATED (Critical)

**Location:** Line 50 — `const cache = new LRUCache<string, number>(3, 1000);`

**Issue:** A single `cache` instance is shared across all tests in the `describe` block. Each `it` block mutates the shared object without resetting it. This means test results depend on execution order.

**Concrete impact:**
- The test at line 63 (`"evicts LRU entry and expired TTL"`) sets keys `"b"`, `"c"`, `"d"` and expects `"a"` to be the evicted entry — but whether `"a"` is even present depends on whether the earlier `"stores and retrieves a value"` test ran first.
- The test at line 83 (`"returns undefined for missing key"`) checks that `"nonexistent"` returns `undefined`. This passes by luck of the key name, not by true isolation.
- If test order changes (e.g., Vitest parallel mode, or a future reorder), tests will produce different results.

**Fix:**
```typescript
// Move cache creation inside each test, or use beforeEach:
describe("LRUCache", () => {
  let cache: LRUCache<string, number>;

  beforeEach(() => {
    cache = new LRUCache<string, number>(3, 1000);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ... tests use the fresh `cache` instance
});
```

**Tradeoff:** Slightly more object allocations per test run; negligible cost for a pure in-memory structure.

---

### 2. Behavioral — VIOLATED (Critical)

**Location:** Lines 72–80 — TTL expiry test within `"evicts LRU entry and expired TTL"`

**Issue:** The test claims to verify that an expired TTL entry returns `undefined`, but the fake timers are activated (`vi.useFakeTimers()`) yet time is **never advanced**. As a result, `cache.get("temp")` returns `99` (the entry is fresh), and the assertion `expect(result).not.toBeUndefined()` passes — but for the wrong reason. The test documents the intent to test expiry without actually exercising the expiry code path.

**This is a false-positive:** The TTL expiry branch (lines 26–29 of the implementation) is never executed by this test suite, yet the test suite passes entirely. A regression in the expiry logic would go undetected.

**Fix:**
```typescript
it("returns undefined for TTL-expired entry", () => {
  vi.useFakeTimers();
  const ttlCache = new LRUCache<string, number>(3, 1000);
  ttlCache.set("temp", 99);

  // Advance time past TTL
  vi.advanceTimersByTime(1001);

  expect(ttlCache.get("temp")).toBeUndefined();
  vi.useRealTimers();
});
```

**Tradeoff:** None — this fix strictly improves behavioral coverage without cost.

---

### 3. Composable — VIOLATED (Moderate)

**Location:** Lines 63–80 — test `"evicts LRU entry and expired TTL"`

**Issue:** A single test covers two orthogonal concerns: (1) LRU eviction when capacity is exceeded, and (2) TTL-based expiry. These are independent dimensions of the cache's behavior. Mixing them in one test makes it impossible to know which concern failed when the test breaks, and harder to extend or reuse the setup logic independently.

**Fix:** Split into two focused tests:
```typescript
it("evicts least-recently-used entry when at capacity", () => {
  const evictCache = new LRUCache<string, number>(3, 5000);
  evictCache.set("a", 1);
  evictCache.set("b", 2);
  evictCache.set("c", 3);
  evictCache.set("d", 4); // should evict "a"
  expect(evictCache.get("a")).toBeUndefined();
  expect(evictCache.size()).toBe(3);
});

it("returns undefined for TTL-expired entry", () => {
  vi.useFakeTimers();
  const ttlCache = new LRUCache<string, number>(3, 1000);
  ttlCache.set("temp", 99);
  vi.advanceTimersByTime(1001);
  expect(ttlCache.get("temp")).toBeUndefined();
  vi.useRealTimers();
});
```

**Tradeoff:** More test count, but each test is narrower, faster to diagnose, and independently reusable.

---

### 4. Readable — VIOLATED (Low-Moderate)

**Locations:**
- Line 59: `cache.set("a", 42)` — the value `42` is a magic number with no explanation of what it represents
- Line 89: `new LRUCache<number, string>(3, 5000)` — `3` (capacity) and `5000` (TTL in ms) appear without any named constants or comments explaining their role

**Issue:** Readers encountering these tests cannot immediately understand whether the specific values are significant to the behavior being tested, or arbitrary placeholders. For `42` in particular, it looks like it might be significant (a well-known sentinel) but the test doesn't clarify. For capacity `3` and TTL `5000`, there is no explanation that `5000ms` is chosen to be "large enough to not expire during the test."

**Fix:**
```typescript
it("stores and retrieves a value", () => {
  const ARBITRARY_VALUE = 42; // value itself is not significant; any number works
  cache.set("a", ARBITRARY_VALUE);
  expect(cache.get("a")).toBe(ARBITRARY_VALUE);
});

// In "respects capacity":
const CAPACITY = 3;
const TTL_LONG_ENOUGH_NOT_TO_EXPIRE_MS = 5000;
const c = new LRUCache<number, string>(CAPACITY, TTL_LONG_ENOUGH_NOT_TO_EXPIRE_MS);
```

**Tradeoff:** Slightly more verbose, but intent is immediately clear to future maintainers.

---

## Properties With No Violations

| Property | Assessment |
|---|---|
| Deterministic | No random data, no uncontrolled external calls. The fake-timer setup is present (if broken). |
| Fast | Pure in-memory operations; no I/O, no network, no sleeps. |
| Writable | Tests are concise and low-boilerplate. Easy to add new cases. |
| Structure-insensitive | Tests access only public API (`get`, `set`, `size`). No internal state assertions. |
| Automated | No manual steps, no console inspection required. |
| Specific | Individual tests are narrow enough to point to specific failure areas (except the composability violation). |
| Predictive | The TTL expiry gap (Behavioral violation) reduces predictiveness, but basic CRUD paths are covered. |
| Inspiring | Once the Behavioral violation is fixed, the coverage of get/set/evict/TTL/missing-key provides a reasonable confidence baseline. |

---

## Prioritized Improvement Plan

Following the skill's priority order (Safety → Feedback Loop → Maintainability → Confidence):

### Priority 1 — Safety (Fix First)

1. **Fix Isolated violation** — add `beforeEach` to create a fresh `cache` instance per test. Eliminates order-dependent failures.
2. **Fix Behavioral violation** — advance fake timers by `1001ms` in the TTL test. Eliminates the false-positive pass and actually exercises the expiry code path.

### Priority 2 — Maintainability

3. **Fix Composable violation** — split `"evicts LRU entry and expired TTL"` into two separate tests. Each test will also benefit from the fresh-instance fix above.

### Priority 3 — Long-term Readability

4. **Fix Readable violation** — replace magic numbers (`42`, `3`, `5000`, `1000`) with named constants that explain their intent.

---

## Tradeoffs Analysis

- **Isolated + Composable support each other here:** Once the cache is created fresh per test, splitting the combined test becomes trivial — each sub-test gets its own fresh instance naturally.
- **Behavioral + Predictive support each other:** Fixing the fake-timer progression makes the test suite actually predictive of production TTL behavior.
- **Readable + Specific support each other:** Named constants make failures easier to understand ("capacity was 3, got 4 entries") than raw numbers.
- **No meaningful tradeoffs against Fast:** All fixes remain pure in-memory; fake timers do not add wall-clock time.
