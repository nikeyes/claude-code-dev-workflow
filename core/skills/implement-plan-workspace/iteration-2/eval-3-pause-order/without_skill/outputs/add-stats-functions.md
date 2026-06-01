# Add Statistics Functions

Extend stats.py with median and mode calculations.

## Phase 1: Add median function

- [ ] `median(values)` returns the middle value for odd-length lists
- [ ] `median(values)` returns the average of the two middle values for even-length lists
- [ ] Raises `ValueError("Cannot compute median of empty list")` for empty input
- [ ] Does not modify the original list (sorts a copy)
- [ ] Tests pass for median scenarios

## Phase 2: Add mode function

- [ ] `mode(values)` returns the most frequently occurring value
- [ ] When multiple values share the highest frequency, returns any one of them
- [ ] Raises `ValueError("Cannot compute mode of empty list")` for empty input
- [ ] Tests pass for mode scenarios

### Manual Verification

After Phase 2, please pause and let me verify:
- [ ] Running `python -c "from stats import median, mode; print(median([3,1,2]), mode([1,2,2,3]))"` prints `2 2`
- [ ] median does not mutate the input list (verify by inspection)
- [ ] mode handles ties gracefully without raising
