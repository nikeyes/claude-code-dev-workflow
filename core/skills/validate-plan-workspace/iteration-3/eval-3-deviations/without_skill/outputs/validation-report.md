# Validation Report: Add String Utility Functions

## Plan Reference
`thoughts/shared/plans/add-string-utils.md`

## Test Results

`make test` was run from the project directory.

**Result: ALL 7 TESTS PASS**

```
test_string_utils.py::test_shorten          PASSED
test_string_utils.py::test_shorten_invalid  PASSED
test_string_utils.py::test_slugify          PASSED
test_string_utils.py::test_count_words      PASSED
test_string_utils.py::test_extract_emails   PASSED
test_string_utils.py::test_mask_sensitive   PASSED
test_string_utils.py::test_reverse_words    PASSED

7 passed in 0.01s
```

---

## Plan vs Implementation Comparison

### Phase 1: Core String Functions

| Plan requirement | Status | Notes |
|---|---|---|
| `truncate(text, max_length, suffix="...")` | DEVIATED | Implemented as `shorten(text, max_len, ellipsis="...")` — function name and parameter names differ |
| `slugify(text)` | IMPLEMENTED | Correct name and behavior |
| `word_count(text)` | DEVIATED | Implemented as `count_words(text)` — function name is reversed |
| Raise `ValueError` if `max_length < len(suffix)` in `truncate` | IMPLEMENTED | Logic is present but under the wrong function name (`shorten`) |

### Phase 2: Advanced String Functions

| Plan requirement | Status | Notes |
|---|---|---|
| `extract_emails(text)` | IMPLEMENTED | Correct name and behavior |
| `mask_sensitive(text, pattern, replacement="***")` | IMPLEMENTED | Correct name and behavior |

### Success Criteria Verification

| Criterion | Status | Notes |
|---|---|---|
| `truncate("Hello World", 8)` returns `"Hello..."` | DEVIATED | Function is named `shorten`, not `truncate`; behavior is correct under that name |
| `slugify("Hello World!")` returns `"hello-world"` | PASS | |
| `word_count("one two three")` returns `3` | DEVIATED | Function is named `count_words`, not `word_count`; behavior is correct under that name |
| `extract_emails("contact foo@bar.com")` returns `["foo@bar.com"]` | PASS | |
| `mask_sensitive("card 1234-5678", "1234-5678")` returns `"card ***"` | PASS | |

---

## Deviations from Plan

### Deviation 1 — Wrong function name: `truncate` implemented as `shorten`

- **Plan**: `truncate(text, max_length, suffix="...")`
- **Actual**: `shorten(text, max_len, ellipsis="...")`
- **Impact**: Any caller using the planned API (`truncate(...)`) will get a `NameError`. The parameter names also differ (`max_length` vs `max_len`, `suffix` vs `ellipsis`), breaking keyword-argument calls.
- **Severity**: High — public API contract not honoured.

### Deviation 2 — Wrong function name: `word_count` implemented as `count_words`

- **Plan**: `word_count(text)`
- **Actual**: `count_words(text)`
- **Impact**: Any caller using `word_count(...)` will get a `NameError`.
- **Severity**: High — public API contract not honoured.

### Deviation 3 — Unplanned function added: `reverse_words`

- **Plan**: No mention of this function.
- **Actual**: `reverse_words(text)` added to `string_utils.py` with a corresponding test.
- **Impact**: Low — this is additive and does not break anything, but it was not requested and adds scope beyond the plan.
- **Severity**: Low.

---

## Manual Verification Checklist (from plan)

| Item | Status | Notes |
|---|---|---|
| Functions follow consistent naming convention | FAIL | `shorten`/`count_words` break the verb-noun or noun-verb consistency; `word_count` and `extract_emails` follow noun-verb, while `shorten` is verb-only |
| Error messages are descriptive | PARTIAL | `shorten` raises `ValueError("max_len must be >= length of ellipsis")` — message references internal param name (`max_len`) rather than the public API name (`max_length`) |
| No external dependencies added | PASS | Only `re` from the standard library is used |

---

## Summary

| Category | Result |
|---|---|
| Tests pass | YES (7/7) |
| Plan fully implemented | NO |
| Deviations found | 3 |

The implementation **passes all tests**, but the tests themselves are written against the deviated implementation rather than the plan's specified API. The two core functions (`truncate` and `word_count`) were renamed, meaning any external code relying on the planned public API would break. One unplanned function (`reverse_words`) was added. The plan should be considered **partially implemented with naming deviations** that require correction or explicit approval before the plan can be marked complete.
