# Validation Report: Add String Utility Functions

**Plan**: `thoughts/shared/plans/add-string-utils.md`
**Date**: 2026-04-25
**Result**: PARTIAL — Tests pass but implementation deviates from the plan

---

## Test Results

```
make test
```

**Outcome: 7/7 tests PASSED**

All tests pass. No test failures.

---

## Plan vs Implementation Comparison

### Deviations Found

#### 1. `truncate` was renamed to `shorten` (DEVIATION)

- **Plan required**: `truncate(text, max_length, suffix="...")`
- **Implemented as**: `shorten(text, max_len, ellipsis="...")`
- **Impact**: The public API does not match the plan. Parameter names also differ (`max_length` → `max_len`, `suffix` → `ellipsis`). Code importing `truncate` from this module would break.

#### 2. `word_count` was renamed to `count_words` (DEVIATION)

- **Plan required**: `word_count(text)`
- **Implemented as**: `count_words(text)`
- **Impact**: The public API does not match the plan. Code importing `word_count` from this module would break.

#### 3. `reverse_words` function added (DEVIATION — unplanned addition)

- **Plan required**: No such function
- **Implemented**: `reverse_words(text)` — reverses word order in a string
- **Impact**: Scope creep. The function was not requested in the plan. It is harmless but was not part of the agreed specification.

#### 4. `ValueError` message is non-descriptive (MINOR DEVIATION)

- **Plan required**: "Error messages are descriptive" (Manual Verification criterion)
- **Implemented**: `raise ValueError("max_len must be >= length of ellipsis")`
- **Assessment**: The message references the internal parameter name `max_len` instead of the plan's public parameter name `max_length`. Minor issue given the rename deviation above.

---

### What Was Correctly Implemented

| Plan Item | Status |
|---|---|
| `string_utils.py` file created | DONE |
| `test_string_utils.py` file created | DONE |
| Truncate logic (truncates to max_length, appends suffix) | DONE (under wrong name) |
| `slugify(text)` — lowercase, hyphens, no special chars | DONE |
| `word_count(text)` — count words | DONE (under wrong name) |
| `ValueError` raised when `max_length < len(suffix)` | DONE |
| `extract_emails(text)` — regex-based email extraction | DONE |
| `mask_sensitive(text, pattern, replacement="***")` | DONE |
| No external dependencies added | DONE |
| Tests for all functions | DONE |
| `make test` passes | DONE |

---

## Success Criteria Verification

From the plan's Automated Verification section:

| Criterion | Result |
|---|---|
| All tests pass | PASS (7/7) |
| `truncate("Hello World", 8)` returns `"Hello..."` | FAIL — function is named `shorten`, not `truncate` |
| `slugify("Hello World!")` returns `"hello-world"` | PASS |
| `word_count("one two three")` returns `3` | FAIL — function is named `count_words`, not `word_count` |
| `extract_emails("contact foo@bar.com")` returns `["foo@bar.com"]` | PASS |
| `mask_sensitive("card 1234-5678", "1234-5678")` returns `"card ***"` | PASS |

---

## Summary

The implementation is functionally correct — all business logic works and tests pass. However, there are **two naming deviations** that break the public API contract defined in the plan: `truncate` was renamed to `shorten` and `word_count` was renamed to `count_words`. One unplanned function (`reverse_words`) was also added.

**Actions required to bring implementation in line with the plan:**

1. Rename `shorten` → `truncate` and parameter `max_len` → `max_length`, `ellipsis` → `suffix`
2. Rename `count_words` → `word_count`
3. Remove `reverse_words` (or get explicit plan approval to add it)
4. Update `test_string_utils.py` imports and test function names accordingly
