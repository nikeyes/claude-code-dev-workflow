# Sorted Set — Test Coverage Analysis & Bug Report

## Overview

Analysis of `sorted_set.go` and `sorted_set_test.go`. The existing test file contains only 3 tests covering `Insert` (basic duplicate rejection), `Contains` (basic hit/miss), and `Range` (one happy-path case). This leaves significant coverage gaps across all seven public methods.

---

## Bugs Discovered

### BUG-1: Integer overflow in `Range` when `high == math.MaxInt`

**Severity:** High  
**File:** `sorted_set.go`, line 55  
**Root cause:** The `Range` method computes `high+1` to find the exclusive upper bound for `sort.SearchInts`. When `high` is `math.MaxInt` (9223372036854775807 on 64-bit systems), `high+1` overflows to `math.MinInt` (-9223372036854775808). `sort.SearchInts` then searches for `math.MinInt` in a slice of numbers that are all greater than it, and returns `0` as the insertion point. The `end` variable becomes `0`, which is less than or equal to any valid `start`, so the guard `start >= end` triggers and `Range` returns `nil` — even when elements exist in the range.

**Reproducer:**
```go
s := New()
s.Insert(1); s.Insert(100); s.Insert(1000)
got := s.Range(1, math.MaxInt)
// got == nil  (BUG: should be []int{1, 100, 1000})
```

**Proposed fix:**
```go
func (s *SortedSet) Range(low, high int) []int {
    if low > high {
        return nil
    }
    start := sort.SearchInts(s.data, low)
    var end int
    if high == math.MaxInt {
        end = len(s.data)
    } else {
        end = sort.SearchInts(s.data, high+1)
    }
    if start >= len(s.data) || start >= end {
        return nil
    }
    result := make([]int, end-start)
    copy(result, s.data[start:end])
    return result
}
```

---

## Total Tests Added

**File:** `sorted_set_extra_test.go`  
**Count:** 57 new test functions

### Coverage by method

| Method    | Existing tests | New tests added |
|-----------|---------------|-----------------|
| `Insert`  | 1             | 7               |
| `Remove`  | 0             | 8               |
| `Contains`| 1             | 3               |
| `Rank`    | 0             | 8               |
| `Range`   | 1             | 12              |
| `Min`     | 0             | 6               |
| `Max`     | 0             | 6               |
| `Len`     | 0             | 2               |
| `Values`  | 0             | 3               |
| Integration | 0           | 4               |

---

## Coverage Assessment

### What the original tests covered
- `Insert` inserts a value and rejects duplicates
- `Contains` returns true for present / false for absent
- `Range` returns the correct slice for a mid-range query

### What was missing (now covered)
- **Empty-set behavior** for every method
- **Single-element sets** (min == max, rank == 0, etc.)
- **Negative numbers** throughout
- **Zero** as a value (a common boundary)
- **`math.MaxInt` / `math.MinInt`** boundary values
- **Remove**: all positions (first, middle, last), missing element, empty set, double-remove, remove-then-reinsert
- **Rank**: shift after insert/remove, absent value, negative values
- **Range**: `low > high`, `low == high` (present / absent), all-elements, no-elements, boundaries inclusive, overflow bug with `MaxInt`, negative ranges, result is a copy
- **Min / Max**: empty, single element, after removing min/max, negative values
- **Len**: empty, after mixed operations
- **Values**: empty, returns independent copy, sorted order
- **Integration**: full insert/remove/contains cycle, many-element sort order, rank consistent with `Values`, range after removals

### Confidence in correctness of remaining implementation
All methods other than `Range` with `MaxInt` are correct. The internal binary-search invariant is maintained correctly by `Insert` and `Remove`. `copy` with overlapping slices is safe in Go. `Values` returns a fresh copy, so external mutations are isolated.
