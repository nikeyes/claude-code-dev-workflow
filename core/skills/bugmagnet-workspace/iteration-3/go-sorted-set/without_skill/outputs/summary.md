# Bug Discovery & Test Coverage Gap Analysis — Go Sorted Set

## Implementation Overview

The sorted set stores integers in a sorted `[]int` slice. Core operations:
- `Insert` — binary search + in-place shift; deduplication via equality check
- `Remove` — binary search + `append`-based splice
- `Contains`, `Rank`, `Range`, `Len`, `Min`, `Max`, `Values`

---

## Confirmed Bug

### Slice Aliasing in `Remove` Corrupts Prior `Values()` Snapshots

**Location**: `sorted_set.go:33`

```go
s.data = append(s.data[:i], s.data[i+1:]...)
```

`append` overwrites elements in the underlying array in-place when the slice has capacity. Any `[]int` slice previously returned by `Values()` shares the same backing array, so its contents are silently mutated after a `Remove`.

`Values()` does copy correctly:
```go
result := make([]int, len(s.data))
copy(result, s.data)
return result
```

However, `Range()` also copies correctly, so the only victim is a snapshot taken via `Values()` and then a `Remove` is called. Test `TestRemove_DoesNotCorruptPreviousValuesSlice` exercises this.

**Severity**: Medium — violates the contract that `Values()` returns an independent snapshot.

---

## Test Coverage Gaps in Existing Tests

The existing test file (`sorted_set_test.go`) covers only three functions with happy-path scenarios:

| Covered | Not Covered |
|---------|-------------|
| `Insert` — basic insert, duplicate, len | Negative integers, zero, MinInt/MaxInt, order invariant |
| `Contains` — present and absent | Empty set, after-remove, negative values |
| `Range` — mid-range with boundaries in set | Empty set, inverted bounds, single-value range, absent boundaries, all-in-range, no-in-range, negatives, mutation isolation |
| — | `Remove` (entirely untested) |
| — | `Rank` (entirely untested) |
| — | `Min` / `Max` (entirely untested) |
| — | `Len` edge cases |
| — | `Values` isolation |
| — | Sorted invariant after mixed operations |

---

## Edge Cases Identified and Tested

### Insert
| Test | Concern |
|------|---------|
| Negative values | Negative integer handling |
| Zero | Zero as a valid value |
| Out-of-order inserts | Sorted invariant maintained |
| Duplicate after Remove | Re-insertion returns `true` |
| `math.MinInt` / `math.MaxInt` | Boundary values for binary search |
| Both extremes together | Ordering at integer range limits |

### Remove
| Test | Concern |
|------|---------|
| From empty set | No panic, returns `false` |
| Non-existent value | Returns `false`, len unchanged |
| Only element | Leaves empty set |
| First element | Correct splice at head |
| Last element | Correct splice at tail |
| Middle element | Correct splice in middle |
| Snapshot isolation | Values() slice not corrupted by later Remove (the confirmed bug) |

### Contains
| Test | Concern |
|------|---------|
| Empty set | No panic, returns `false` |
| Negative value | Correct search through negatives |
| After Remove | Stale positives not returned |

### Rank
| Test | Concern |
|------|---------|
| Absent value | Returns -1 |
| Empty set | Returns -1, no panic |
| First element | Returns 0 |
| Last element | Returns correct index |
| After Remove shifts rank down | Rank reflects current position |
| Negative value | Rank 0 for minimum negative |

### Range
| Test | Concern |
|------|---------|
| `low > high` | Returns `nil` (not panic) |
| Empty set | Returns `nil` |
| Single-value range, value present | Returns `[v]` |
| Single-value range, value absent | Returns `nil` |
| Boundaries not in set | Returns elements strictly within |
| All elements in range | Returns complete slice |
| No elements in range | Returns `nil` |
| Negative values | Correct binary search with negatives |
| `low == high == min element` | Boundary at min |
| `low == high == max element` | Boundary at max |
| Mutation of result | Returned slice is independent copy |

### Min / Max
| Test | Concern |
|------|---------|
| Empty set | Returns `(0, false)` — not panic |
| Single element | Returns that element |
| Negative values | Min/Max correct across negatives |
| After removing current Min | Updates correctly |
| After removing current Max | Updates correctly |

### Values
| Test | Concern |
|------|---------|
| Empty set | Returns `[]int{}` not `nil` |
| Isolation from internal state | Mutating result does not affect set |

### Len
| Test | Concern |
|------|---------|
| Empty set | Returns 0 |
| After insert + remove | Correct count |
| Duplicate insert | Does not increment |
| Failed remove | Does not decrement |

### Sorted Invariant
| Test | Concern |
|------|---------|
| Mixed inserts and removes | Invariant always holds |

---

## Notes on `Values()` Empty-Set Behavior

`Values()` on an empty set returns `make([]int, 0)`, which is a non-nil empty slice. The test `TestValues_EmptySet` asserts it is non-nil. If the API contract is "return nil for empty", this test documents a discrepancy — but the current code returns a non-nil slice, which is the safer choice.
