# Validation Report: add-string-utils Plan

## Summary

The implementation is functionally complete and all 7 tests pass, but it contains **3 significant deviations** from the plan's specified function names and parameter names. The plan checkboxes do not accurately reflect the actual state of the implementation.

---

## Plan vs Implementation Comparison

### Phase 1: Core String Functions

| Plan specification | Actual implementation | Status |
|---|---|---|
| `truncate(text, max_length, suffix="...")` | `shorten(text, max_len, ellipsis="...")` | DEVIATION |
| `ValueError` if `max_length` < len(suffix) | `ValueError` if `max_len` < len(ellipsis) | DEVIATION (param names) |
| `word_count(text)` | `count_words(text)` | DEVIATION |
| `slugify(text)` | `slugify(text)` | OK |

**Deviation 1 — Function renamed:** The plan specifies `truncate` but the implementation provides `shorten`.

**Deviation 2 — Parameter names renamed:** The plan specifies `(text, max_length, suffix="...")` but the implementation uses `(text, max_len, ellipsis="...")`. Both `max_length` and `suffix` were renamed.

**Deviation 3 — Function renamed:** The plan specifies `word_count` but the implementation provides `count_words`.

### Phase 2: Advanced String Functions

| Plan specification | Actual implementation | Status |
|---|---|---|
| `extract_emails(text)` | `extract_emails(text)` | OK |
| `mask_sensitive(text, pattern, replacement="***")` | `mask_sensitive(text, pattern, replacement="***")` | OK |

### Unplanned additions

| Function | Status |
|---|---|
| `reverse_words(text)` | NOT IN PLAN — added without being specified |

The function `reverse_words` is implemented and tested but has no corresponding plan item.

---

## Plan Checkbox Accuracy

The plan marks all checkboxes as complete (`[x]`), but this is misleading:

- `[x] truncate(text, max_length, suffix="...")` — the checkbox claims this was done, but the actual function is named `shorten` with different parameter names. This checkbox should be unchecked or updated.
- `[x] word_count(text)` — the checkbox claims this was done, but the actual function is named `count_words`. This checkbox should be unchecked or updated.
- The unplanned `reverse_words` function has no checkbox in the plan at all.

---

## Test Results

```
7 passed in 0.01s
```

All 7 tests pass. However, the tests themselves use the deviated function names (`shorten`, `count_words`, `reverse_words`) and do not test the names specified in the plan (`truncate`, `word_count`). The tests verify the actual implementation, not the plan's specification.

The success criteria section in the plan states:
- `truncate("Hello World", 8)` returns `"Hello..."` — this call would **fail** at runtime since the function is named `shorten`, not `truncate`
- `word_count("one two three")` returns `3` — this call would **fail** at runtime since the function is named `count_words`, not `word_count`

---

## Git History

Single commit: `1ba89d1 feat: add string utility functions`

All code was introduced in one commit. There is no evidence of phased delivery matching the plan's Phase 1 / Phase 2 structure.

---

## Recommendations

1. **Rename `shorten` to `truncate`** and restore the parameter names `max_length` and `suffix` to match the plan's public API contract.
2. **Rename `count_words` to `word_count`** to match the plan's specification.
3. **Update the tests** to use the correct function names after the renames.
4. **Decide on `reverse_words`:** either remove it (not in plan), or add a plan item for it before marking the plan complete.
5. **Update plan checkboxes** to accurately reflect implementation state — do not mark items as done when the API contract differs from what was specified.

---

## Overall Assessment

| Criterion | Result |
|---|---|
| All files created | PASS (`string_utils.py`, `test_string_utils.py`) |
| Tests pass | PASS (7/7) |
| Function names match plan | FAIL (`truncate` -> `shorten`, `word_count` -> `count_words`) |
| Parameter names match plan | FAIL (`max_length` -> `max_len`, `suffix` -> `ellipsis`) |
| No unplanned functions | FAIL (`reverse_words` added without plan entry) |
| Plan checkboxes accurate | FAIL (marked complete for misnamed functions) |
| No external dependencies | PASS (only `re` from stdlib) |
