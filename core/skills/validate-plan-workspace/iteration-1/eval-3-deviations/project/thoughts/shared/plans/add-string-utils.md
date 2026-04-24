# Plan: Add String Utility Functions

## Overview
Add a set of string manipulation utilities following consistent patterns.

## Phase 1: Core String Functions
- [x] Add `string_utils.py` with the following functions:
  - [x] `truncate(text, max_length, suffix="...")` — truncate text to max_length, appending suffix if truncated
  - [x] `slugify(text)` — convert text to URL-friendly slug (lowercase, hyphens, no special chars)
  - [x] `word_count(text)` — return number of words in text
- [x] Raise `ValueError` if `max_length` < len(suffix) in `truncate`
- [x] Add comprehensive tests in `test_string_utils.py`

## Phase 2: Advanced String Functions
- [x] Add `extract_emails(text)` — return list of email addresses found in text using regex
- [x] Add `mask_sensitive(text, pattern, replacement="***")` — replace occurrences of pattern with replacement
- [x] Add tests for advanced functions

## Success Criteria

### Automated Verification
```bash
make test
```
- All tests pass
- `truncate("Hello World", 8)` returns `"Hello..."`
- `slugify("Hello World!")` returns `"hello-world"`
- `word_count("one two three")` returns `3`
- `extract_emails("contact foo@bar.com")` returns `["foo@bar.com"]`
- `mask_sensitive("card 1234-5678", "1234-5678")` returns `"card ***"`

### Manual Verification
- [ ] Functions follow consistent naming convention
- [ ] Error messages are descriptive
- [ ] No external dependencies added
