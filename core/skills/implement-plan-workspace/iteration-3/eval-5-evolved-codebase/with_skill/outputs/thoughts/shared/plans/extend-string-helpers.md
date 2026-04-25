# Extend String Helpers

Add search and padding utilities to the existing string helper module.

## Phase 1: Review existing code

<!-- Naming/structural mismatch adapted: string_helpers.py does not exist. The codebase has been split into text_utils.py (slugify, word_count) and text_transforms.py (truncate, title_case). Tests are the source of truth for function placement. -->

- [x] Read `string_helpers.py` and understand the existing functions
- [x] Verify `truncate()` and `slugify()` exist in `string_helpers.py`
- [x] Confirm existing tests pass

## Phase 2: Add search functions to string_helpers.py

<!-- Adapted: added to text_utils.py instead of string_helpers.py (module was split/renamed) -->

Add text search utilities to `string_helpers.py`.

- [x] `contains_any(text, keywords)` returns True if text contains any keyword
- [x] `extract_emails(text)` returns list of email addresses found in text
- [x] Returns empty list when no emails found
- [x] Tests pass for search functions

## Phase 3: Add padding and repeat functions to string_helpers.py

<!-- Adapted: added to text_transforms.py instead of string_helpers.py (module was split/renamed) -->

Add text padding utilities to `string_helpers.py`.

- [x] `pad_right(text, width)` pads text with spaces to given width
- [x] `pad_center(text, width)` centers text within given width
- [x] `repeat_text(text, count)` repeats text N times
- [x] If text is already longer than width, return unchanged
- [x] All tests pass with `make test`
