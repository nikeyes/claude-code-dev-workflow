# Extend String Helpers

Add search and padding utilities to the existing string helper module.

## Phase 1: Review existing code

- [ ] Read `string_helpers.py` and understand the existing functions
- [ ] Verify `truncate()` and `slugify()` exist in `string_helpers.py`
- [ ] Confirm existing tests pass

## Phase 2: Add search functions to string_helpers.py

Add text search utilities to `string_helpers.py`.

- [ ] `contains_any(text, keywords)` returns True if text contains any keyword
- [ ] `extract_emails(text)` returns list of email addresses found in text
- [ ] Returns empty list when no emails found
- [ ] Tests pass for search functions

## Phase 3: Add padding and repeat functions to string_helpers.py

Add text padding utilities to `string_helpers.py`.

- [ ] `pad_right(text, width)` pads text with spaces to given width
- [ ] `pad_center(text, width)` centers text within given width
- [ ] `repeat_text(text, count)` repeats text N times
- [ ] If text is already longer than width, return unchanged
- [ ] All tests pass with `make test`
