# Add Statistics Functions

Extend stats.py with median and mode calculations.

## Phase 1: Add median function

- [x] `median(values)` returns the middle value for odd-length lists
- [x] `median(values)` returns the average of the two middle values for even-length lists
- [x] Raises `ValueError("Cannot compute median of empty list")` for empty input
- [x] Does not modify the original list (sorts a copy)
- [x] Tests pass for median scenarios

## Phase 2: Add mode function

- [x] `mode(values)` returns the most frequently occurring value
- [x] When multiple values share the highest frequency, returns any one of them
- [x] Raises `ValueError("Cannot compute mode of empty list")` for empty input
- [x] Tests pass for mode scenarios

### Manual Verification

After Phase 2, please pause and let me verify:
- [ ] Running `python -c "from stats import median, mode; print(median([3,1,2]), mode([1,2,2,3]))"` prints `2 2`
- [ ] median does not mutate the input list (verify by inspection)
- [ ] mode handles ties gracefully without raising
