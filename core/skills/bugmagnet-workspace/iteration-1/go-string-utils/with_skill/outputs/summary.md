# BugMagnet Session Summary — string_utils.go

**Date:** 2026-04-25
**File analyzed:** `string_utils.go` (package `stringutils`)
**Language:** Go
**Testing framework:** Go standard `testing` package

> **Note:** Go is not installed on this machine. Tests were written following Go
> testing conventions but **were not executed**. All test expectations are based
> on static code analysis of the implementation.

---

## Test Coverage Summary

**Tests Added: 65 total**

| Category | Tests |
|---|---|
| Truncate — happy path & boundary conditions | 9 |
| Truncate — bug reproduction (skipped) | 2 |
| SlugifyText — happy path & boundary conditions | 17 |
| CountWords — happy path & boundary conditions | 10 |
| ExtractInitials — happy path & boundary conditions | 8 |
| ExtractInitials — bug reproduction (skipped) | 2 |
| WrapText — happy path & boundary conditions | 14 |
| Bugmagnet session advanced edge cases | 13 |

**Final Count (estimated):**
- ~59 passing tests (based on static analysis)
- 4 skipped tests (bugs documented)
- 2 additional tests documenting surprising-but-correct behaviours
- **Total: 65 tests**

---

## Bugs Discovered

### Bug 1 — `Truncate`: byte-length indexing instead of rune count

**Severity:** High  
**File:** `string_utils.go:10,13`  
**Skipped tests:**
- `TestTruncate_returnsCorrectResultForMultibyteUnicodeCharacters_BUG`
- `TestTruncate_returnsOriginalForMultibyteStringWithinLimit_BUG`

**Root cause:** The function uses `len(s)` (byte count) for the length check and
`s[:maxLen]` (byte slice) for the truncation cut. For ASCII strings this is
harmless, but for any string containing multibyte UTF-8 codepoints (accented
characters, emoji, CJK, etc.) it produces two distinct problems:

1. **Wrong length comparison** — a 5-rune string like `"héllo"` has 6 bytes,
   so `Truncate("héllo", 5)` truncates when it should not, because the check
   `6 <= 5` is false.
2. **Mid-rune split** — `s[:3]` on `"héllo"` cuts through the 2-byte `é`
   encoding, producing invalid UTF-8 bytes in the output.

**Proposed fix:**

```go
func Truncate(s string, maxLen int) string {
    runes := []rune(s)
    if len(runes) <= maxLen {
        return s
    }
    return string(runes[:maxLen]) + "..."
}
```

---

### Bug 2 — `ExtractInitials`: byte access instead of rune for first character

**Severity:** High  
**File:** `string_utils.go:44`  
**Skipped tests:**
- `TestExtractInitials_returnsCorrectInitialsForAccentedFirstCharacters_BUG`
- `TestExtractInitials_returnsCorrectInitialsForChineseCharacters_BUG`

**Root cause:** The expression `rune(p[0])` takes the first **byte** of the
string `p` and casts it to `rune`. For any name part that begins with a
multibyte UTF-8 character (e.g. `Å` = `0xC3 0x85`, `李` = `0xE6 0x9D 0x8E`)
this returns the raw first byte value (`0xC3`, `0xE6`) rather than the actual
Unicode codepoint. `strings.ToUpper` then operates on this garbage byte value,
yielding incorrect output.

**Proposed fix:**

```go
for _, p := range parts {
    runes := []rune(p)
    initials = append(initials, runes[0])
}
```

---

### Bug 3 — `Truncate`: negative `maxLen` causes a panic

**Severity:** Medium  
**File:** `string_utils.go:10-13`  
**Test:** `TestTruncate_handlesNegativeMaxLen`

**Root cause:** There is no guard for `maxLen < 0`. When `maxLen` is negative,
`len(s) <= maxLen` is always false for any non-empty string (since `len` is
always >= 0). The function then executes `s[:maxLen]` which is a negative slice
index, causing a runtime panic: `runtime error: slice bounds out of range`.

**Proposed fix:** Add an early return or guard:

```go
func Truncate(s string, maxLen int) string {
    if maxLen < 0 {
        maxLen = 0
    }
    runes := []rune(s)
    if len(runes) <= maxLen {
        return s
    }
    return string(runes[:maxLen]) + "..."
}
```

---

## Key Findings About Behaviour

### `Truncate`
- The result length when truncation occurs is `maxLen + 3` (not `maxLen`) because `"..."` is appended after the prefix. This is expected by the docstring but callers should be aware.
- `maxLen = 0` on a non-empty string returns `"..."` (3 chars).

### `SlugifyText`
- Tabs, newlines, underscores, and all non-letter/digit/space/hyphen characters are **silently dropped**, not converted to separators. `"hello_world"` → `"helloworld"` (words merged). This may surprise users who expect `_` to act as a separator.
- Unicode letters (e.g. accented characters like `café`) are preserved via `unicode.IsLetter`, which returns true for all Unicode letter categories.
- The double-hyphen collapse loop handles arbitrary depths of repetition correctly.

### `CountWords`
- Delegates entirely to `strings.Fields`, which handles all whitespace variants (space, tab, newline, `\r\n`) correctly. No bugs found.
- Punctuation attached to words (e.g. `"hello,"`) is counted as part of the word, not as a separator. This is consistent with `strings.Fields` semantics.

### `ExtractInitials`
- Returns an empty string for empty or whitespace-only input (correct: the loop never runs).
- Hyphenated names like `"Mary-Jane"` are treated as a single token by `strings.Fields`, so only the first letter `M` is extracted as the initial.
- **See Bug 2 above for the multibyte issue.**

### `WrapText`
- Long words that exceed the wrap width are placed on their own line without being broken. This is consistent with standard word-wrap algorithms.
- Leading/trailing whitespace and extra internal spaces in the input are normalized away via `strings.Fields`.
- `width = 0` causes every word after the first to go on its own line (no panic).
- Newlines in the input are treated as word separators (via `strings.Fields`), so the original line structure is not preserved.

---

## Coverage Before This Session

The existing test file (`string_utils_test.go`) contained 3 tests:
- `TestTruncate` — one basic truncation case
- `TestSlugifyText` — one basic slug case
- `TestCountWords` — one basic word count case

`ExtractInitials` and `WrapText` had **zero test coverage**.

---

## Files

| File | Description |
|---|---|
| `string_utils.go` | Implementation (unchanged copy) |
| `string_utils_test.go` | Comprehensive test suite (65 tests, 4 skipped for bugs) |
| `summary.md` | This document |
