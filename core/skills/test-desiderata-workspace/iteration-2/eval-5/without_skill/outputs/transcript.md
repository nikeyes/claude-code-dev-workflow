# Transcript: Test Quality Analysis for test_cache.ts

## Date
2026-04-26

## Task
Analyze test file `test_cache.ts` for quality issues and provide concrete improvement recommendations.

---

## Step 1: Read the test file

Read the file at:
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_cache.ts`

The file contained:
- 97 lines
- An inline `LRUCache` class implementation (lines 13–47)
- A single `describe("LRUCache")` block with 4 test cases
- Comment annotations in the file header that hinted at planted violations

---

## Step 2: Read the file header comments

The file header (lines 1–10) already declared the intended violations:
- **Isolated**: shared `cache` instance across all tests
- **Behavioral**: fake timers used but time never advanced, so TTL never expires
- **Readable**: magic numbers without explanation (1000, 3, 5)
- **Composable**: `"evicts LRU entry and expired TTL"` covers two orthogonal concerns

These served as hypotheses to verify during analysis.

---

## Step 3: Trace each test case independently

### Test 1 — `"stores and retrieves a value"` (lines 57–61)
- Uses the shared `cache` instance.
- Sets key `"a"` to `42` and checks retrieval.
- Magic number `42` has no semantic meaning.
- Because `cache` is shared, this key persists into subsequent tests.

### Test 2 — `"evicts LRU entry and expired TTL"` (lines 63–81)
- Continues using the shared `cache` — at this point, key `"a"` is already present.
- Sets `"b"`, `"c"`, `"d"`. Comment says this "should evict `a`", but because the cache already has `"a"` from the previous test, that may or may not be LRU depending on test order.
- Calls `vi.useFakeTimers()` then immediately calls `cache.set("temp", 99)` and `cache.get("temp")`.
- **Time is never advanced.** The entry is freshly set and has not expired.
- Asserts `not.toBeUndefined()` — this passes, but it passes because the entry is fresh, not because expiry was tested correctly.
- Two separate concerns (eviction and TTL) are bundled into a single test.

### Test 3 — `"returns undefined for missing key"` (lines 83–85)
- Clean test. Uses shared `cache` but tests a key `"nonexistent"` that was never set.
- This test is safe from isolation issues only by accident (the key was never used by prior tests).

### Test 4 — `"respects capacity"` (lines 87–96)
- Creates its own local `LRUCache` instance — correctly isolated.
- Uses magic numbers: capacity `3` and TTL `5000` without explanation.
- The eviction logic is tested correctly here.

---

## Step 4: Verify the behavioral violation in detail

Traced the TTL expiry path:

```
vi.useFakeTimers()         → freezes Date.now()
cache.set("temp", 99)      → expiresAt = Date.now() + 1000
cache.get("temp")          → Date.now() == Date.now() at set time → NOT expired
                           → returns 99
expect(result).not.toBeUndefined()  → passes (result is 99)
```

The assertion passes, but not because expiry works — it passes because the entry is brand new and the clock was never advanced. The test as written cannot detect a bug where TTL is never enforced.

---

## Step 5: Verify the isolation violation in detail

Traced state across tests in execution order:

| After test | Cache state |
|------------|-------------|
| Test 1     | `{a: 42}` |
| Test 2     | `{b:1, c:2, d:3, temp:99}` — "a" was evicted (capacity 3, "a" was LRU) |
| Test 3     | Same as above (no mutations) |
| Test 4     | Uses own local instance — isolated |

Because test 2 depends on "a" being present (comment says "should evict a"), it silently relies on test 1 having run first. Reversing test order or adding a `beforeEach` without resetting state would change behavior.

---

## Step 6: Draft recommendations

Four concrete recommendations written with before/after code examples:
1. Replace shared instance with `beforeEach` initialization
2. Add `vi.advanceTimersByTime()` call to properly test TTL expiry
3. Split the compound test into two focused tests
4. Replace magic numbers with named constants

---

## Step 7: Write output files

- Wrote `analysis.md` with full issue descriptions, code examples, and a prioritized fix table.
- Wrote this `transcript.md` recording the reasoning steps taken.

---

## Approach Used

No framework was applied explicitly. Analysis proceeded by:
1. Reading the file completely before drawing conclusions
2. Tracing execution flow for each test case
3. Verifying that each hinted violation was real (not just a comment artifact)
4. Checking whether any additional violations were present beyond those hinted
5. Formulating concrete, actionable fixes for each violation
