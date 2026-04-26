# Transcript: Test Desiderata Analysis of test_cache.ts

**Date:** 2026-04-26
**Skill:** stepwise-core:test-desiderata
**Eval:** iteration-1 / eval-5

---

## Step 1: Read the Skill File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

Key takeaways:
- 12 properties to evaluate: Isolated, Composable, Deterministic, Fast, Writable, Readable, Behavioral, Structure-insensitive, Automated, Specific, Predictive, Inspiring
- Analysis workflow: Read → Evaluate → Identify tradeoffs → Prioritize → Recommend
- Recommended output format: Issue / Location / Impact / Fix / Tradeoff per violation

---

## Step 2: Read the Test File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_cache.ts`.

**Observations while reading:**

The file header comment (lines 1–10) explicitly labels its own violations. This is a deliberately seeded test file for eval purposes, but the analysis proceeds against the code as written — the embedded comments are treated as noise that a real reviewer might not have.

**Code structure identified:**
- `LRUCache<K, V>` implementation embedded in the test file (lines 13–47)
- 4 test cases inside a single `describe("LRUCache")` block
- 1 `afterEach` hook that restores real timers
- Shared module-level `cache` constant (line 50)

**Key code paths in the implementation:**
- `get()`: checks existence, checks TTL expiry (deletes + returns undefined if expired), then moves to end (LRU promotion), returns value
- `set()`: if key exists, delete it; else if at capacity, evict LRU (first map entry); then insert with `expiresAt = Date.now() + ttlMs`
- `size()`: returns map size

---

## Step 3: Evaluate Each Property

### 1. Isolated

**Question:** Do tests return the same results regardless of execution order?

Identified: `const cache = new LRUCache<string, number>(3, 1000)` at line 50 is declared at module scope, outside any `beforeEach` or `describe`-level factory. All four `it` blocks share this single instance.

- Test 1 (`"stores and retrieves a value"`) sets `"a" = 42`
- Test 2 (`"evicts LRU entry and expired TTL"`) sets `"b"`, `"c"`, `"d"` — comment at line 69 acknowledges the `"a"` dependency explicitly
- Test 3 (`"returns undefined for missing key"`) relies on `"nonexistent"` not existing by luck of naming

The `afterEach` only calls `vi.useRealTimers()` — it does not reset the cache state.

**Verdict: VIOLATED**

---

### 2. Composable

**Question:** Are dimensions of variability tested separately?

Test `"evicts LRU entry and expired TTL"` (line 63) mixes:
- LRU eviction (capacity overflow behavior)
- TTL expiry (time-based invalidation)

These are completely independent behavioral dimensions. LRU eviction has nothing to do with TTL, and TTL expiry has nothing to do with capacity limits.

**Verdict: VIOLATED**

---

### 3. Deterministic

**Question:** Does nothing changing mean results don't change?

No random data generation. `Date.now()` is used in the implementation, but fake timers are activated before any TTL-sensitive test. The timer control is broken (never advanced), but if fixed, the test would be deterministic.

The `afterEach` restores real timers, preventing timer state from leaking between tests.

**Verdict: PASSES** (though the Behavioral issue is related, it is categorized there)

---

### 4. Fast

**Question:** Do tests run quickly?

All operations are pure in-memory `Map` operations. No I/O, no network, no sleep calls, no disk access.

**Verdict: PASSES**

---

### 5. Writable

**Question:** Are tests cheap to write?

Tests are concise. The framework (Vitest) has a familiar API. No complex DSL or heavy fixture setup.

**Verdict: PASSES**

---

### 6. Readable

**Question:** Are tests comprehensible with clear intent?

Issues found:
- Line 59: `cache.set("a", 42)` — value `42` unexplained
- Line 89: `new LRUCache<number, string>(3, 5000)` — `3` and `5000` unexplained
- Line 50: `new LRUCache<string, number>(3, 1000)` — `3` capacity and `1000`ms TTL unexplained

Test names are reasonably descriptive (`"stores and retrieves a value"`, `"evicts LRU entry and expired TTL"`, etc.). The Arrange-Act-Assert structure is implicit but present. The main readability gap is unexplained literals.

**Verdict: VIOLATED** (magic numbers)

---

### 7. Behavioral

**Question:** Are tests sensitive to behavior changes?

Critical issue found at lines 72–80:
- `vi.useFakeTimers()` is called at line 73
- `cache.set("temp", 99)` at line 74 stores with `expiresAt = Date.now() + 1000` (where `Date.now()` is now under fake timer control, defaulting to 0 or current time but frozen)
- `cache.get("temp")` at line 77 — since time has NOT been advanced, `Date.now() <= expiresAt`, the entry is not expired, and returns `99`
- `expect(result).not.toBeUndefined()` at line 80 — this passes because the entry IS present (returns 99), not because the expiry logic was exercised

The expiry branch (`if (Date.now() > entry.expiresAt)`) at lines 26–29 of the implementation is **never executed** by this test. The test passes for the wrong reason, giving false confidence that expiry is tested.

**Verdict: VIOLATED** (false-positive; expiry code path not exercised)

---

### 8. Structure-insensitive

**Question:** Do tests break during refactoring despite unchanged behavior?

All tests use only the public API: `cache.get()`, `cache.set()`, `cache.size()`. No access to `this.map`, `this.capacity`, `this.ttlMs`, or any private internals.

**Verdict: PASSES**

---

### 9. Automated

**Question:** Do tests run without human intervention?

No manual steps, no `console.log` outputs requiring human interpretation, no interactive prompts.

**Verdict: PASSES**

---

### 10. Specific

**Question:** When a test fails, is the cause obvious?

With the Isolated violation present, failures can be misleading (failure in test 2 might actually be caused by test 1's side effects). Once that is fixed, individual tests are focused enough to pinpoint failures. The combined test (`"evicts LRU entry and expired TTL"`) is the main concern — if it fails, you can't immediately tell whether eviction or TTL logic is broken.

**Verdict: PARTIALLY VIOLATED** (primarily attributable to the Composable violation; once split, both tests become specific)

---

### 11. Predictive

**Question:** If all tests pass, is the code suitable for production?

With the Behavioral violation, TTL expiry can be broken and all tests still pass. This is a direct predictive gap: the test suite provides false confidence that time-based invalidation works.

**Verdict: PARTIALLY VIOLATED** (due to Behavioral false-positive)

---

### 12. Inspiring

**Question:** Do passing tests inspire confidence?

Once the Behavioral and Isolated violations are fixed, the 4 test cases cover: basic get/set, LRU eviction, TTL expiry, missing-key returns, and capacity limits. This is a reasonable confidence baseline for a cache implementation.

**Verdict: PASSES** (contingent on fixing Behavioral violation)

---

## Step 4: Identify Tradeoffs

- Fixing **Isolated** makes fixing **Composable** easier (no shared state to worry about when splitting)
- Fixing **Behavioral** directly improves **Predictive** and **Inspiring** with no cost
- **Fast** is unaffected by any fix (all in-memory)
- **Readable** improvements (named constants) also help **Specific** (clearer failure messages)

No significant tradeoffs exist between the proposed fixes — they are mutually reinforcing.

---

## Step 5: Prioritize Improvements

1. **Isolated** — Critical safety issue; enables all other fixes
2. **Behavioral** — Critical false-positive; expiry logic untested
3. **Composable** — Moderate; split combined test into two focused ones
4. **Readable** — Low-moderate; replace magic numbers with named constants

---

## Output

Full analysis written to:
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-1/eval-5/with_skill/outputs/analysis.md`
