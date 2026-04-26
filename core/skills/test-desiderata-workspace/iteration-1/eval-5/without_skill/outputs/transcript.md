# Work Transcript

**Task**: Analyze test_cache.ts against Kent Beck's Test Desiderata (baseline run, no skill)
**Date**: 2026-04-26

---

## Step 1 — Read the test file

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_cache.ts`.

The file is 97 lines and contains:
- An inline `LRUCache<K, V>` implementation (capacity + TTL, Map-backed)
- A `describe("LRUCache")` suite with four `it` tests
- A module-level `cache` instance (line 50)
- `afterEach` that calls `vi.useRealTimers()`
- Comments in the file explicitly naming four intended violations: Isolated, Behavioral, Readable, Composable

---

## Step 2 — Identify violations

### Isolated (confirmed)
Line 50: `const cache = new LRUCache<string, number>(3, 1000);` is defined outside the describe block. All four tests share and mutate the same object. Tests that run after `"stores and retrieves a value"` will see `"a" -> 42` already in the cache.

### Composable (confirmed)
Test `"evicts LRU entry and expired TTL"` performs two logically separate checks:
1. Inserting four items into a capacity-3 cache and observing eviction
2. Inserting a "temp" key and checking its TTL behaviour

These are orthogonal concerns that should be in separate tests.

### Behavioral (confirmed)
Inside `"evicts LRU entry and expired TTL"`:
- `vi.useFakeTimers()` is called, which freezes `Date.now()`
- `cache.set("temp", 99)` stores an entry with `expiresAt = frozenTime + 1000`
- No call to `vi.advanceTimersByTime(...)` is made
- `cache.get("temp")` is called; since time has not advanced, `Date.now() < expiresAt`, so the entry is NOT expired
- The assertion is `expect(result).not.toBeUndefined()` — this passes, but for the wrong reason (the entry is fresh, not because TTL was correctly handled)
- The comment on line 80 acknowledges this: "accidentally passes for wrong reason"

### Readable (confirmed)
Magic numbers without named constants:
- `42` in `cache.set("a", 42)` — arbitrary value
- `1000` in the module-level constructor — TTL milliseconds
- `3` in both module-level and `"respects capacity"` constructors — capacity
- `5000` in `"respects capacity"` — a different TTL with no label
- The comment on line 88 mentions `5` but the actual value is `5000` — a minor inconsistency in the seeded comment

---

## Step 3 — Evaluate all 12 properties

| # | Property | Result |
|---|---|---|
| 1 | Isolated | VIOLATED |
| 2 | Composable | VIOLATED |
| 3 | Deterministic | VIOLATED (caused by isolation failure) |
| 4 | Fast | PASS |
| 5 | Writable | PASS |
| 6 | Readable | VIOLATED |
| 7 | Behavioral | VIOLATED |
| 8 | Structure-insensitive | PASS |
| 9 | Automated | PASS |
| 10 | Specific | PARTIAL |
| 11 | Predictive | PARTIAL |
| 12 | Inspiring | VIOLATED |

---

## Step 4 — Draft recommendations

For each violated property a concrete, code-level fix was formulated:

- **Isolated / Deterministic**: Move `cache` into `beforeEach(() => { cache = new LRUCache(...) })`
- **Composable**: Split `"evicts LRU entry and expired TTL"` into two separate `it` blocks
- **Behavioral**: Add `vi.advanceTimersByTime(1001)` after `cache.set("temp", 99)` and change the assertion to `toBeUndefined()`
- **Readable**: Extract named constants (`CAPACITY`, `TTL_MS`, `LONG_TTL_MS`, `SENTINEL_VALUE`)
- **Inspiring**: Rename tests to 1:1 map their single concern; ensure self-contained setup

---

## Step 5 — Write outputs

Wrote full analysis to:
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-1/eval-5/without_skill/outputs/analysis.md`

Wrote this transcript to:
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-1/eval-5/without_skill/outputs/transcript.md`
