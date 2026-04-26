# BugMagnet Session Summary — string_utils.go

**Date:** 2026-04-26
**File analyzed:** `string_utils.go` (package `stringutils`)
**Language:** Go
**Testing framework:** Go standard `testing` package

> **Note:** Go is not installed / Bash is not available on this machine. Tests were
> written following Go testing conventions but **were not executed**. All test
> expectations are based on static code analysis of the implementation.

---

## Test Coverage Summary

**Tests Added: 65 total**

| Category | Tests |
|---|---|
| Truncate — happy path & boundary conditions | 8 |
| Truncate — bug reproduction (skipped) | 2 |
| SlugifyText — happy path & boundary conditions | 12 |
| CountWords — happy path & boundary conditions | 7 |
| ExtractInitials — happy path & boundary conditions | 7 |
| ExtractInitials — bug reproduction (skipped) | 1 |
| WrapText — happy path & boundary conditions | 9 |
| Bugmagnet session 2026-04-26 (advanced edge cases) | 19 |

**Final Count (estimated):**
- ~61 passing tests (based on static analysis)
- 4 skipped tests (bugs documented)
- **Total: 65 tests**

**Coverage before this session:**
- 3 tests existed (all happy-path, all ASCII)
- `ExtractInitials` and `WrapText` had **zero test coverage**

---

## Bugs Discovered

### Bug 1 — `Truncate`: byte-length comparison instead of rune count

**Severity:** High
**File:** `string_utils.go:10,13`
**Skipped test:** `TestTruncate_returnsOriginalWhenRuneCountEqualsMaxLenButByteCountExceeds_BUG`

**Root cause:** The function uses `len(s)` (byte count in UTF-8) for the threshold
comparison and `s[:maxLen]` (byte slice) for the truncation cut. For any string
containing multibyte UTF-8 codepoints (accented characters, emoji, CJK, etc.),
this produces two distinct failure modes:

1. **Wrong truncation trigger** — `"café"` has 4 runes but 6 bytes. `Truncate("café", 4)`
   truncates when it should not, because the byte-level check `6 <= 4` is false.
2. **Mid-rune split** — `s[:4]` on `"café"` cuts through the 2-byte `é` encoding
   at byte offset 3/4, producing `"caf\xc3"` — invalid UTF-8 — followed by `"..."`.

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

**Minimal reproduction:** `Truncate("café", 4)` — expected `"café"`, actual `"caf\xc3..."`

---

### Bug 2 — `Truncate`: negative `maxLen` causes a runtime panic

**Severity:** Medium
**File:** `string_utils.go:10-13`
**Skipped test:** `TestBugmagnet_Truncate_appendsEllipsisNotTruncatesWhenMaxLenNegative_BUG`

**Root cause:** There is no guard for `maxLen < 0`. When `maxLen` is negative,
`len(s) <= maxLen` is always false for any non-empty string (since `len` returns
a non-negative value). The code proceeds to `s[:maxLen]`, which is a negative
slice index, causing a runtime panic:

```
panic: runtime error: slice bounds out of range [:-1]
```

**Proposed fix:** Add a negative guard at the start:

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

**Minimal reproduction:** `Truncate("Hello", -1)` — panics at runtime

---

### Bug 3 — `ExtractInitials`: byte access instead of rune for first character

**Severity:** High
**File:** `string_utils.go:44`
**Skipped test:** `TestExtractInitials_returnsCorrectInitialForNameWithAccentedFirstLetter_BUG`

**Root cause:** The expression `rune(p[0])` takes the first **byte** of the string
`p` and casts it to `rune`. For any name part that begins with a multibyte UTF-8
codepoint:

- `'Å'` (U+00C5) encodes as `0xC3 0x85` in UTF-8
- `p[0]` returns `0xC3`, so `rune(p[0])` = `'Ã'` (U+00C3), not `'Å'`
- `strings.ToUpper("Ã")` = `"Ã"` — still wrong

For 3-byte CJK characters (e.g. `'李'` = `0xE6 0x9D 0x8E`), `p[0]` = `0xE6`,
producing completely incorrect output.

**Proposed fix:**

```go
import "unicode/utf8"

for _, p := range parts {
    r, _ := utf8.DecodeRuneInString(p)
    initials = append(initials, r)
}
```

**Minimal reproduction:** `ExtractInitials("Ångström Doe")` — expected `"ÅD"`, actual garbled first byte

---

### Bug 4 — `WrapText`: byte-length comparison instead of rune count

**Severity:** Medium
**File:** `string_utils.go:58`
**Skipped test:** `TestBugmagnet_WrapText_wrapsAtCorrectWidthWithUnicodeWords_BUG`

**Root cause:** The line-width check `len(currentLine)+1+len(w) <= width` uses
`len()` which counts bytes, not Unicode runes. For strings with multibyte
characters, the byte count exceeds the visible character count, causing premature
line wrapping.

For example, `"héllo wörld"` has 11 runes (visible characters) but 14 bytes:
- `"héllo"` = 5 runes / 7 bytes (`é` is 2 bytes)
- `"wörld"` = 5 runes / 6 bytes (`ö` is 2 bytes)

With `width=11` (intended as 11 visible characters), the byte check computes
`7 + 1 + 6 = 14 > 11` and wraps, even though only 11 visible characters are
needed.

**Proposed fix:**

```go
import "unicode/utf8"

if utf8.RuneCountInString(currentLine)+1+utf8.RuneCountInString(w) <= width {
```

**Minimal reproduction:** `WrapText("héllo wörld", 11)` — expected `"héllo wörld"`, actual `"héllo\nwörld"`

---

## Key Findings About Behaviour

### `Truncate`
- Appending `"..."` means the output length when truncated is `maxLen + 3`, not `maxLen`.
- `maxLen = 0` on a non-empty string returns `"..."` (3 chars).
- Empty string input always returns `""` regardless of `maxLen`.
- All bugs are in the byte-vs-rune distinction — ASCII strings work correctly.

### `SlugifyText`
- Tabs, newlines, underscores, apostrophes, and all non-letter/digit/space/hyphen
  characters are **silently dropped** (not converted to separators). `"hello_world"`
  produces `"helloworld"` — the words are merged with no separator.
- Unicode letters (accented chars like `é`, `ä`) are preserved because
  `unicode.IsLetter` returns true for all Unicode letter categories.
- The double-hyphen collapse loop uses `strings.ReplaceAll` repeatedly until no
  `"--"` remains — handles arbitrary depths of repetition correctly.
- SQL injection and XSS patterns produce safe, empty or sanitized slugs by
  dropping all special characters.

### `CountWords`
- Delegates entirely to `strings.Fields`, which correctly handles all whitespace
  variants (space, tab, newline, carriage return). No bugs found.
- Punctuation attached to words (e.g. `"hello,"`) is counted as part of the word.

### `ExtractInitials`
- Returns `""` for empty or whitespace-only input (correct — loop never runs).
- Hyphenated names like `"Mary-Jane"` are treated as a single token by
  `strings.Fields`, so only `M` is extracted as the initial.
- Correct for all-ASCII names; broken for names with non-ASCII first characters.

### `WrapText`
- Long words that exceed the wrap width are placed on their own line without being
  broken — consistent with standard word-wrap algorithms.
- Leading/trailing whitespace and extra internal spaces are normalized away via
  `strings.Fields`.
- `width = 0` causes every word after the first to go on its own line (no panic).
- Newlines in the input are treated as word separators via `strings.Fields`.

---

## Files

| File | Description |
|---|---|
| `string_utils.go` | Implementation (unchanged copy) |
| `string_utils_test.go` | Comprehensive test suite (65 tests, 4 skipped for bugs) |
| `summary.md` | This document |
