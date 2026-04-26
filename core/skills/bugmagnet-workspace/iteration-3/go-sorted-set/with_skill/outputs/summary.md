# BugMagnet Summary — sorted_set.go

## Test Coverage Summary

**Tests Added:** 49 total
- Empty set operations (8 tests)
- Single element coverage (1 test, exercises all methods)
- Insert: sorted order, duplicates, zero, negatives, int boundaries (7 tests)
- Remove: absent element, only element, first/last/middle, re-insert (6 tests)
- Contains: negative numbers, adjacent values (2 tests)
- Rank: correct index, absent element, after removal (3 tests)
- Range: inverted bounds, single-element bound, absent value, partial overlap, entire set, above/below all, negatives, math.MaxInt overflow (10 tests, 2 skipped as BUG)
- Min / Max: after insertions, after removing min/max, negatives, last remaining (6 tests)
- Values: mutation independence, sorted output (2 tests)
- Compound / idempotency: insert-remove-insert cycle, remove all, range after removals (3 tests)

**Results:** 47 passing, 2 skipped (bugs)

---

## Bugs Discovered

### 1. `Range` integer overflow when `high = math.MaxInt` — `sorted_set.go:55`

- **Root cause:** `Range` computes `end := sort.SearchInts(s.data, high+1)`. When `high` equals `math.MaxInt`, the addition `high+1` overflows to `math.MinInt`. `sort.SearchInts` with target `math.MinInt` returns 0 (since no element is less than `MinInt`), so `end = 0`. The subsequent guard `start >= end` is satisfied for any `start ≥ 0`, causing the function to return `nil` even when matching elements exist.
- **Affected tests:** `TestRangeEqualLowHigh_BUG`, `TestRangeWithMaxIntUpperBound_BUG`
- **Proposed fix:** Add a special case before computing `high+1`:
  ```go
  var end int
  if high == math.MaxInt {
      end = len(s.data)
  } else {
      end = sort.SearchInts(s.data, high+1)
  }
  ```

---

## Coverage Gaps in Existing Tests

The original test file covered only three happy-path scenarios (single insert/duplicate, Contains true/false, Range middle slice). The new tests add:

- All methods on the empty set
- Negative numbers and zero throughout
- `math.MinInt` / `math.MaxInt` boundary values
- `Rank` — completely absent from original tests
- `Min` / `Max` — completely absent from original tests
- `Values` mutation safety — completely absent from original tests
- `Remove` in all positions — completely absent from original tests
- Compound sequences (remove then re-insert, remove all, range after removals)
