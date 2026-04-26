# Test Desiderata Analysis: test_cache.ts

## Summary

The test file covers an LRU cache implementation with TTL support. Four properties are meaningfully violated: **Isolated**, **Behavioral**, **Readable**, and **Composable**. One additional property — **Predictive** — is weakened as a consequence of the Behavioral violation. The remaining properties (Deterministic, Fast, Writable, Structure-insensitive, Automated, Specific, Inspiring) are either satisfied or not significantly impacted.

---

## Violations

### Issue 1: Isolated — Shared cache instance across all tests

**Location:** Line 50

```ts
const cache = new LRUCache<string, number>(3, 1000);
```

**Impact:** Every test in the `describe` block mutates the same `cache` object. The "evicts LRU entry and expired TTL" test (line 63) explicitly acknowledges the problem in a comment: `"a" may or may not be present` depending on whether the previous test ran. Tests are therefore order-dependent. Adding, removing, or reordering a single test can silently change results in others. The `afterEach` only restores timers — it never resets the cache, so state accumulated by one test leaks into the next.

**Fix:** Create a fresh cache instance in `beforeEach` (or at the top of each test). Remove the module-level `const cache` declaration.

```ts
describe("LRUCache", () => {
  let cache: LRUCache<string, number>;

  beforeEach(() => {
    cache = new LRUCache<string, number>(3, 1000);
  });

  afterEach(() => {
    vi.useRealTimers();
  });
  // ...
});
```

---

### Issue 2: Behavioral — TTL expiry test passes for the wrong reason

**Location:** Lines 73–80

```ts
vi.useFakeTimers();
cache.set("temp", 99);
// time is never advanced, so entry hasn't expired
const result = cache.get("temp");
expect(result).not.toBeUndefined(); // accidentally passes for wrong reason
```

**Impact:** The comment in the file reveals the intent: the author wanted to verify that an expired key returns `undefined`. But `vi.advanceTimersByTime()` (or equivalent) is never called, so `Date.now()` stays at the moment `set()` was called, the entry never expires, and `get("temp")` correctly returns `99`. The assertion `not.toBeUndefined()` then passes — but it asserts the opposite of what was intended for an expiry scenario. If the TTL logic were completely removed from `LRUCache.get()`, this test would still pass. The behavior under test (TTL expiry returns `undefined`) is not actually exercised.

**Fix:** Split the TTL concern into its own test and advance fake timers past the TTL:

```ts
it("returns undefined for a key whose TTL has expired", () => {
  vi.useFakeTimers();
  const ttlMs = 1000;
  const ttlCache = new LRUCache<string, number>(3, ttlMs);
  ttlCache.set("temp", 99);
  vi.advanceTimersByTime(ttlMs + 1);
  expect(ttlCache.get("temp")).toBeUndefined();
});
```

---

### Issue 3: Readable — Magic numbers without context

**Location:** Lines 50, 59, 89

```ts
const cache = new LRUCache<string, number>(3, 1000);  // line 50
cache.set("a", 42);                                   // line 59
const c = new LRUCache<number, string>(3, 5000);       // line 89
```

**Impact:** Readers cannot tell what `3`, `1000`, `5000`, or `42` represent without inspecting the implementation. `3` is the cache capacity; `1000` and `5000` are TTL values in milliseconds; `42` is an arbitrary cached value. The lack of labels increases cognitive load when modifying tests and makes failure messages harder to interpret. A reviewer seeing `expect(c.size()).toBe(3)` alongside capacity `3` may not immediately understand why the expected size equals the capacity.

**Fix:** Use named constants or inline comments that explain the significance:

```ts
const CAPACITY = 3;
const TTL_MS = 1_000; // 1 second
const cache = new LRUCache<string, number>(CAPACITY, TTL_MS);

// In "stores and retrieves a value":
const STORED_VALUE = 42;
cache.set("a", STORED_VALUE);
expect(cache.get("a")).toBe(STORED_VALUE);

// In "respects capacity":
const LARGE_TTL_MS = 5_000; // TTL irrelevant to this test, set high to avoid interference
const c = new LRUCache<number, string>(CAPACITY, LARGE_TTL_MS);
```

---

### Issue 4: Composable — Single test covers two orthogonal concerns

**Location:** Lines 63–80, test name "evicts LRU entry and expired TTL"

**Impact:** LRU eviction and TTL expiry are independent cache behaviors. Combining them in one test means:

1. A failure in the eviction logic hides whether TTL works.
2. A failure in the TTL logic makes the eviction assertion harder to diagnose.
3. The test setup is more complex, making it harder to reproduce or extend each concern independently.
4. The Behavioral violation (fake timers never advanced) is partly enabled by the cramped structure — adding the TTL concern to an already-crowded test made it easy to forget `advanceTimersByTime`.

**Fix:** Split into two focused tests:

```ts
it("evicts the least-recently-used entry when capacity is exceeded", () => {
  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("c", 3);
  cache.set("d", 4); // evicts "a"
  expect(cache.get("a")).toBeUndefined();
  expect(cache.size()).toBe(3);
});

it("returns undefined for a key whose TTL has expired", () => {
  vi.useFakeTimers();
  cache.set("temp", 99);
  vi.advanceTimersByTime(TTL_MS + 1);
  expect(cache.get("temp")).toBeUndefined();
});
```

---

### Issue 5: Predictive — TTL expiry behavior not actually covered

**Location:** Entire test suite (consequence of Issue 2)

**Impact:** Because the Behavioral violation means the expiry path in `get()` is never executed, a bug that disables TTL expiry entirely would go undetected. The production path `if (Date.now() > entry.expiresAt) { ... return undefined; }` is dead code from the test suite's perspective. The suite would pass a green build for a cache that never expires entries.

**Fix:** Addressed by fixing Issue 2 (writing a correct TTL expiry test with `vi.advanceTimersByTime`).

---

## Tradeoffs

### Tradeoff 1: Isolated ↔ Composable (only seeming to interfere)

The shared `cache` instance (Isolated violation) and the combined eviction+TTL test (Composable violation) reinforce each other. Because the cache is shared, the state entering "evicts LRU entry and expired TTL" is unpredictable — the comment on line 69 acknowledges `"a"` may or may not be present. This unpredictability makes splitting the test *feel* harder: the author may have bundled concerns together to make the setup state more controllable within one test.

This is a design opportunity, not a real tension. Fixing the Isolated violation (fresh cache per test) removes the unpredictable shared state, making it safe and natural to split the test into independent, focused cases. Fix Isolated first — it is the root cause that makes Composable harder to achieve.

---

### Tradeoff 2: Behavioral ↔ Composable (only seeming to interfere)

The Behavioral violation (fake timers never advanced) lives inside the same test as the eviction logic. Splitting the test (Composable fix) directly exposes the Behavioral bug: once TTL expiry has its own test, it becomes immediately obvious that `advanceTimersByTime` is missing, because the TTL test has no eviction scaffolding to distract from it. The combined test obscures the omission.

This is not a real conflict. Improving Composable enables fixing Behavioral as a consequence. Fix Composable alongside the Isolated fix; the Behavioral issue will be naturally forced to the surface.

---

### Tradeoff 3: Readable ↔ Writable (only seeming to interfere)

The magic numbers (`3`, `1000`, `5000`, `42`) reduce the cost of writing each test slightly — no constants to define. But they make every test harder to read and harder to change safely (if capacity changes, every literal `3` must be found and updated). Named constants extracted into `beforeEach` scope or at the top of the describe block improve Readable without increasing the per-test writing cost. Once the constants exist, new tests are actually easier to write because the intent is captured. There is no real tradeoff here.

---

### Tradeoff 4: Isolated ↔ Writable (real, manageable tension)

Creating a fresh cache instance per test (Isolated fix) requires a `beforeEach` block that was not needed before. This is a small but real increase in boilerplate. However, the cost is minimal: a two-line `beforeEach` eliminates an entire class of order-dependent failures. For a short test suite like this one, the maintenance benefit far outweighs the writing overhead. Prioritize Isolated.

---

## Priority Order

1. **Isolated** (line 50) — root cause enabling several other violations; fix first.
2. **Behavioral** (lines 73–80) — a passing test that validates the wrong behavior is worse than a failing test; fix immediately after Isolated.
3. **Composable** (lines 63–80) — splitting the test is a natural consequence of fixing Isolated and Behavioral.
4. **Readable** (lines 50, 59, 89) — low effort, high clarity gain; fix alongside the refactor.
5. **Predictive** — resolved automatically when Behavioral is fixed.
