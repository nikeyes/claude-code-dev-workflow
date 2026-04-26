# Test Quality Analysis: test_cache.ts

## File Analyzed
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_cache.ts`

---

## Summary

The test suite for `LRUCache` contains four meaningful quality violations. Each one either causes tests to pass for the wrong reason, makes tests fragile due to shared state, or obscures the intent of what is being tested.

---

## Issues Found

### 1. Isolation Violation — Shared Cache Instance Across Tests

**Location:** Line 50

```ts
const cache = new LRUCache<string, number>(3, 1000);
```

**Problem:** A single `cache` instance is created outside the `describe` block and reused across all tests. Each test mutates this shared state. The order in which tests run determines whether they pass or fail. For example, the key `"a"` inserted in `"stores and retrieves a value"` is still in the cache when `"evicts LRU entry and expired TTL"` runs — making the eviction behavior unpredictable.

**Fix:** Create a fresh instance inside each test (or in a `beforeEach` hook):

```ts
describe("LRUCache", () => {
  let cache: LRUCache<string, number>;

  beforeEach(() => {
    cache = new LRUCache<string, number>(3, 1000);
  });
  // ...
});
```

---

### 2. Behavioral Violation — Fake Timers Never Advance Time

**Location:** Lines 73–80

```ts
vi.useFakeTimers();
cache.set("temp", 99);
// time is never advanced
const result = cache.get("temp");
expect(result).not.toBeUndefined(); // accidentally passes for wrong reason
```

**Problem:** The test uses `vi.useFakeTimers()` to presumably test TTL expiry behavior, but it never calls `vi.advanceTimersByTime()` to simulate the passage of time. The entry is set and immediately retrieved — it hasn't expired, so `result` is `99`, and the assertion `not.toBeUndefined()` passes. However, the comment says the intent was to test that the key *had* expired. The test neither documents nor validates expiry correctly: it documents wrong intent and passes for the wrong reason.

**Fix — if testing that a non-expired entry is returned:**

```ts
it("returns value before TTL expires", () => {
  vi.useFakeTimers();
  const cache = new LRUCache<string, number>(3, 1000);
  cache.set("temp", 99);
  vi.advanceTimersByTime(500); // half the TTL
  expect(cache.get("temp")).toBe(99);
  vi.useRealTimers();
});
```

**Fix — if testing that an expired entry returns undefined:**

```ts
it("returns undefined after TTL expires", () => {
  vi.useFakeTimers();
  const cache = new LRUCache<string, number>(3, 1000);
  cache.set("temp", 99);
  vi.advanceTimersByTime(1001); // past the 1000ms TTL
  expect(cache.get("temp")).toBeUndefined();
  vi.useRealTimers();
});
```

---

### 3. Composability Violation — Single Test Covers Two Orthogonal Concerns

**Location:** Lines 63–81 — test named `"evicts LRU entry and expired TTL"`

**Problem:** The test attempts to verify two independent behaviors: LRU eviction (capacity enforcement) and TTL expiry. These are separate axes of functionality. Bundling them together means:
- A failure in either concern makes the entire test fail with an unclear message.
- The intent of each assertion is harder to read in context.
- The eviction sub-test is contaminated by shared state from the previous test (making it hard to reason about which key is actually LRU).

**Fix:** Split into two focused tests:

```ts
it("evicts least recently used entry when capacity is exceeded", () => {
  const cache = new LRUCache<string, number>(3, 1000);
  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("c", 3);
  cache.set("d", 4); // should evict "a"
  expect(cache.get("a")).toBeUndefined();
  expect(cache.size()).toBe(3);
});

it("returns undefined after TTL expires", () => {
  vi.useFakeTimers();
  const cache = new LRUCache<string, number>(3, 1000);
  cache.set("temp", 99);
  vi.advanceTimersByTime(1001);
  expect(cache.get("temp")).toBeUndefined();
  vi.useRealTimers();
});
```

---

### 4. Readability Violation — Magic Numbers Without Explanation

**Locations:** Lines 50, 59, 89

```ts
const cache = new LRUCache<string, number>(3, 1000);  // What is 3? What is 1000?
cache.set("a", 42);                                    // Why 42?
const c = new LRUCache<number, string>(3, 5000);       // Why 5000?
```

**Problem:** Numeric literals appear throughout without explanation. A reader cannot tell at a glance whether `1000` is a timeout in ms, a retry count, or a budget in dollars. The value `42` carries no domain meaning. The inconsistency between `1000` and `5000` in different tests adds to the confusion.

**Fix:** Use named constants that state the intent:

```ts
const CAPACITY = 3;
const TTL_MS = 1_000;
const ANY_VALUE = 42;

const cache = new LRUCache<string, number>(CAPACITY, TTL_MS);
cache.set("a", ANY_VALUE);
```

For the TTL in the capacity test, use a value large enough to not interfere with the test:

```ts
const LONG_TTL_MS = 60_000; // TTL irrelevant for eviction test
const c = new LRUCache<number, string>(3, LONG_TTL_MS);
```

---

## Issues Not Found

- **Size:** The suite is appropriately small.
- **Speed:** Tests are not slow (fake timers are used, which is correct in principle).
- **Specificity:** Most assertions use direct matchers (`toBe`, `toBeUndefined`) rather than vague ones.
- **Structure:** The `describe`/`it` structure is correct.

---

## Prioritized Fix Order

| Priority | Violation | Impact |
|----------|-----------|--------|
| 1 | Shared instance (Isolation) | Tests are order-dependent and can silently pass/fail based on other tests |
| 2 | Fake timers never advance (Behavioral) | Test documents wrong behavior and passes for the wrong reason |
| 3 | Two concerns in one test (Composability) | Failure messages are ambiguous; intent is obscured |
| 4 | Magic numbers (Readability) | Harder to understand intent; maintenance risk |
