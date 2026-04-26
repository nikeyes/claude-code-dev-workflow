# Test Quality Analysis: test_cache.ts

## Overview

The file tests an LRU Cache implementation with TTL support. The test suite contains four significant quality issues that are intentionally seeded (as documented in the file's own comment block): shared state, a broken behavioral test, magic numbers, and a test that covers two unrelated concerns. This analysis covers each in detail.

---

## Issue 1: Broken Test Isolation — Shared Cache Instance

**Location**: Line 50, used across all tests in the describe block.

```ts
const cache = new LRUCache<string, number>(3, 1000);
```

The `cache` instance is declared at module scope and shared across every test. No `beforeEach` resets it, so each test inherits whatever state the previous test left behind.

**Consequence**: The eviction test on line 63 comments this directly: "should evict 'a' (LRU), but 'a' may or may not be present (result depends on previous test)". The test outcome depends on execution order. Running tests in isolation or reordering them can change results without any code change.

**Recommendation**: Create a fresh instance inside each `it` block, or use `beforeEach` to reinitialise the shared instance:

```ts
let cache: LRUCache<string, number>;

beforeEach(() => {
  cache = new LRUCache<string, number>(3, 1000);
});
```

---

## Issue 2: Non-Deterministic / Incorrect Behavioral Test — TTL Expiry

**Location**: Lines 63–81, inside "evicts LRU entry and expired TTL".

```ts
vi.useFakeTimers();
cache.set("temp", 99);
// time is never advanced
const result = cache.get("temp");
expect(result).not.toBeUndefined(); // accidentally passes for wrong reason
```

The test calls `vi.useFakeTimers()` but never advances the clock (no `vi.advanceTimersByTime()` or equivalent). The entry was just set, so `Date.now()` is still within TTL. The assertion `expect(result).not.toBeUndefined()` passes, but it documents the intent as expiry testing without actually testing expiry. The real intent — that an expired entry returns `undefined` — is never verified.

**Consequence**: The TTL path in `get()` (lines 26–29) has zero meaningful coverage. A bug there would go undetected.

**Recommendation**: Write two focused tests with explicit time control:

```ts
it("returns the value before TTL expires", () => {
  vi.useFakeTimers();
  const ttlMs = 1000;
  const c = new LRUCache<string, number>(3, ttlMs);
  c.set("key", 42);
  vi.advanceTimersByTime(ttlMs - 1);
  expect(c.get("key")).toBe(42);
  vi.useRealTimers();
});

it("returns undefined after TTL expires", () => {
  vi.useFakeTimers();
  const ttlMs = 1000;
  const c = new LRUCache<string, number>(3, ttlMs);
  c.set("key", 42);
  vi.advanceTimersByTime(ttlMs + 1);
  expect(c.get("key")).toBeUndefined();
  vi.useRealTimers();
});
```

---

## Issue 3: Poor Readability — Magic Numbers

**Locations**: Lines 50, 59, 63–68, 89.

Examples:
- `new LRUCache<string, number>(3, 1000)` — what does 3 mean? what unit is 1000?
- `cache.set("a", 42)` — why 42?
- `new LRUCache<number, string>(3, 5000)` — a different TTL appears with no explanation.

**Consequence**: A reader cannot tell whether `1000` and `5000` are the same TTL written inconsistently, different intentional values, or a mistake. The purpose of specific numbers is unclear.

**Recommendation**: Use named constants or variables with descriptive names:

```ts
const CAPACITY = 3;
const TTL_MS = 1_000;

const cache = new LRUCache<string, number>(CAPACITY, TTL_MS);

// In tests, the value used matters less than what is being asserted:
const ARBITRARY_VALUE = 42;
cache.set("a", ARBITRARY_VALUE);
expect(cache.get("a")).toBe(ARBITRARY_VALUE);
```

---

## Issue 4: Low Composability — Single Test Covers Two Orthogonal Concerns

**Location**: Lines 63–81, "evicts LRU entry and expired TTL".

The test is named to cover two completely different cache behaviors: LRU eviction (a capacity concern) and TTL expiry (a time concern). These behaviors are independent and should be tested separately.

**Consequence**: When this test fails, it is not immediately clear which behavior broke. The test is also harder to read because the reader must track two different scenarios simultaneously.

**Recommendation**: Split into two tests with focused names:

```ts
it("evicts the least recently used entry when capacity is full", () => {
  // test only LRU eviction
});

it("expires entries after TTL elapses", () => {
  // test only TTL expiry
});
```

---

## Issue 5: Incomplete afterEach Cleanup

**Location**: Lines 53–55.

```ts
afterEach(() => {
  vi.useRealTimers();
});
```

The `afterEach` restores real timers, which is good practice. However, it does not reset the shared `cache` instance. This means the afterEach partially addresses cleanup while missing the more impactful isolation problem.

**Recommendation**: Once the shared instance is replaced with `beforeEach` initialisation (Issue 1), this cleanup pattern should be extended or the timer restoration should be moved inside each test that uses fake timers, to keep each test fully self-contained.

---

## Summary Table

| # | Category       | Location        | Severity | Description                                                    |
|---|----------------|-----------------|----------|----------------------------------------------------------------|
| 1 | Isolation      | Line 50         | High     | Shared cache instance allows cross-test state contamination    |
| 2 | Behavioral     | Lines 63–81     | High     | Fake timers never advanced; TTL expiry path never tested       |
| 3 | Readability    | Lines 50, 59, 89| Medium   | Magic numbers with no explanation (capacity, TTL, values)      |
| 4 | Composability  | Lines 63–81     | Medium   | One test covers two orthogonal concerns (eviction + TTL)       |
| 5 | Isolation      | Lines 53–55     | Low      | afterEach cleans timers but not shared cache state             |

---

## Priority Order for Fixes

1. **Fix the shared instance** (Issue 1) — this is the root cause of non-deterministic results across the suite.
2. **Fix the TTL test** (Issue 2) — the most dangerous issue because it produces false confidence; the expiry code path is untested.
3. **Split the combined test** (Issue 4) — improves clarity and makes future failures easier to diagnose.
4. **Replace magic numbers** (Issue 3) — improves maintainability and communicates intent.
5. **Align afterEach with the new isolation approach** (Issue 5) — minor cleanup once the bigger issues are resolved.
