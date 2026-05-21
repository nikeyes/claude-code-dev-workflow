# Extend String Helpers

Add search and padding utilities to the existing string helper module.

> **Structural Adaptation Note**: `string_helpers.py` does not exist. The codebase
> has been split into `text_utils.py` (slugify, word_count) and `text_transforms.py`
> (truncate, title_case). Tests confirm the intended module placement for new functions:
> search functions → `text_utils.py`, padding/repeat functions → `text_transforms.py`.

## Phase 1: Review existing code

- [x] Read `string_helpers.py` and understand the existing functions
  > Adapted: read `text_utils.py` and `text_transforms.py` instead (structural mismatch resolved)
- [x] Verify `truncate()` and `slugify()` exist in `string_helpers.py`
  > `slugify()` found in `text_utils.py`; `truncate()` found in `text_transforms.py`
- [x] Confirm existing tests pass
  > 4 existing tests pass (test_slugify, test_word_count, test_truncate, test_title_case)

## Phase 2: Add search functions to string_helpers.py

> Adapted: functions added to `text_utils.py` (confirmed by test imports)

- [x] `contains_any(text, keywords)` returns True if text contains any keyword
- [x] `extract_emails(text)` returns list of email addresses found in text
- [x] Returns empty list when no emails found
- [x] Tests pass for search functions

## Phase 3: Add padding and repeat functions to string_helpers.py

> Adapted: functions added to `text_transforms.py` (confirmed by test imports)

- [x] `pad_right(text, width)` pads text with spaces to given width
- [x] `pad_center(text, width)` centers text within given width
- [x] `repeat_text(text, count)` repeats text N times
- [x] If text is already longer than width, return unchanged
- [x] All tests pass with `make test`
