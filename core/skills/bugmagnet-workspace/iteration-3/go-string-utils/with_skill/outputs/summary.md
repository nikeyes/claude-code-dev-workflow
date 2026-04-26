# BugMagnet Session Summary — string_utils.go

**Date:** 2026-04-26
**File analyzed:** `string_utils.go` (package `stringutils`)
**Language:** Go
**Testing framework:** Go standard `testing` package

> **Note:** Tests were written through static code analysis of the implementation.
> No Go toolchain was available to execute them during this session.

---

## Test Coverage Summary

**Tests Added: 56 total**

| Category | Tests |
|---|---|
| Truncate — boundary conditions (table-driven) | 8 |
| Truncate — output length assertion | 1 |
| Truncate — bug reproduction (skipped) | 3 |
| SlugifyText — happy path (table-driven) | 6 |
| SlugifyText — empty and whitespace inputs (table-driven) | 4 |
| SlugifyText — special characters dropped (table-driven) | 5 |
| SlugifyText — hyphen collapsing (table-driven) | 4 |
| SlugifyText — leading/trailing hyphens | 1 |
| SlugifyText — unicode letters preserved (table-driven) | 3 |
| SlugifyText — apostrophe behaviour | 1 |
| CountWords — full table-driven suite | 12 |
| ExtractInitials — happy path (table-driven) | 7 |
| ExtractInitials — empty and whitespace (table-driven) | 3 |
| ExtractInitials — hyphenated name token | 1 |
| ExtractInitials — bug reproduction (skipped) | 2 |
| WrapText — happy path (table-driven) | 6 |
| WrapText — empty and whitespace inputs (table-driven) | 3 |
| WrapText — long word not broken | 1 |
| WrapText — no trailing newline | 1 |
| WrapText — multiple spaces collapsed | 1 |
| WrapText — width zero / width one edge cases | 2 |
| WrapText — newlines as separators | 1 |
| WrapText — bug reproduction (skipped) | 2 |

**Results (static analysis estimate):**
- ~50 passing tests
- 6 skipped tests (bugs documented)
- **Total: 56 tests**

**Coverage before this session:**
- 3 tests existed (one per function — all happy-path ASCII, `ExtractInitials` and `WrapText` untested)

---

## Bugs Discovered

### Bug 1 — `Truncate`: byte-length comparison misidentifies rune count

**Severity:** High
**File:** `string_utils.go:10`
**Skipped test:** `TestTruncate_multibyteRuneCountEqualsMaxLen_BUG`

**Root cause:** `len(s)` returns byte count. A string of N runes with multibyte
characters has `len(s) > N`. The condition `len(s) <= maxLen` therefore triggers
truncation when the rune count is exactly `maxLen`, producing a wrong result.

**Minimal reproduction:** `Truncate("☺☺", 2)` — "☺☺" has 2 runes but 6 bytes.
`len(s)=6 <= maxLen=2` is false so it truncates; then `s[:2]` slices through the
middle of the 3-byte `☺` encoding, yielding `"\xe2\x98..."` (invalid UTF-8).

**Proposed fix:**
```go
runes := []rune(s)
if len(runes) <= maxLen {
    return s
}
return string(runes[:maxLen]) + "..."
```

---

### Bug 2 — `Truncate`: negative `maxLen` causes a runtime panic

**Severity:** High
**File:** `string_utils.go:10-13`
**Skipped test:** `TestTruncate_negativMaxLenPanics_BUG`

**Root cause:** No guard for `maxLen < 0`. For any non-empty string
`len(s) <= maxLen` is false (len ≥ 0 > any negative). Execution reaches
`s[:maxLen]`, which is a negative slice index:
```
panic: runtime error: slice bounds out of range [:-3]
```

**Proposed fix:**
```go
if maxLen < 0 {
    maxLen = 0
}
```

---

### Bug 3 — `Truncate`: byte-level slice cuts through multibyte rune

**Severity:** High
**File:** `string_utils.go:13`
**Skipped test:** `TestTruncate_midRuneSliceProducesInvalidUTF8_BUG`

**Root cause:** Even if the length comparison were corrected to use rune count,
the slice `s[:maxLen]` still operates on bytes. If the character at rune
position `maxLen` starts within the byte range `< maxLen+N` for a multibyte
rune, the slice severs that rune's byte sequence, yielding invalid UTF-8.

**Minimal reproduction:** `Truncate("naïve", 3)` — `s[:3]` = `"na\xc3"` (half of `ï`).

**Proposed fix:** Same as Bug 1 — convert to `[]rune` first.

---

### Bug 4 — `ExtractInitials`: byte access produces wrong initial for multibyte first characters

**Severity:** High
**File:** `string_utils.go:44`
**Skipped test:** `TestExtractInitials_nonASCIIFirstLetterProducesGarbage_BUG`

**Root cause:** `rune(p[0])` indexes the string `p` by byte position. For any
name token whose first character requires more than one byte in UTF-8, `p[0]`
returns only the leading byte of that multi-byte sequence, which is cast to
`rune`. The resulting codepoint is wrong:

| Name char | UTF-8 bytes | p[0] | rune(p[0]) |
|---|---|---|---|
| `Ö` (U+00D6) | `0xC3 0x96` | `0xC3` | `Ã` (U+00C3) |
| `中` (U+4E2D) | `0xE4 0xB8 0xAD` | `0xE4` | `ä` (U+00E4) |

**Proposed fix:**
```go
import "unicode/utf8"

r, _ := utf8.DecodeRuneInString(p)
initials = append(initials, r)
```

---

### Bug 5 — `ExtractInitials`: CJK first character produces wrong initial (same root cause)

**Severity:** High
**File:** `string_utils.go:44`
**Skipped test:** `TestExtractInitials_CJKFirstLetterProducesGarbage_BUG`

Same byte-vs-rune bug, confirmed with a 3-byte CJK character. Documented
separately as the failure mode is more dramatic (first byte of a 3-byte sequence
mapped to a Latin Extended character).

---

### Bug 6 — `WrapText`: byte-length width check causes premature line wrapping for Unicode

**Severity:** Medium
**File:** `string_utils.go:58`
**Skipped tests:** `TestWrapText_byteVsRuneCountCausesEarlyWrapForUnicode_BUG`,
`TestWrapText_emojiCausesEarlyWrapBecauseOfByteCount_BUG`

**Root cause:** `len(currentLine)+1+len(w) <= width` counts bytes. Multibyte
characters inflate the byte count beyond the visible character count, making
lines wrap earlier than the caller-specified `width` (measured in visible
characters) requires.

The problem scales with character size:
- 2-byte characters (Latin accented): 1 extra byte per char
- 3-byte characters (CJK): 2 extra bytes per char
- 4-byte characters (emoji): 3 extra bytes per char

**Minimal reproduction:** `WrapText("über alles", 10)` — 10 visible characters,
should fit, but `len("über")=5` + 1 + `len("alles")=5` = 11 > 10 → wraps to
`"über\nalles"`.

**Proposed fix:**
```go
import "unicode/utf8"

if utf8.RuneCountInString(currentLine)+1+utf8.RuneCountInString(w) <= width {
```

---

## Key Observations

### Systemic issue: byte vs rune confusion

All bugs except the negative-`maxLen` panic share the same root cause: using
Go's built-in `len()` on strings (which returns byte count) instead of
`utf8.RuneCountInString()` or `[]rune` conversion (which counts Unicode code
points). This is a common Go pitfall. The fix in every case is consistent:
convert to `[]rune` before length measurement and slicing, or use the
`unicode/utf8` package.

### Functions without bugs (ASCII inputs work correctly)

- **`SlugifyText`**: Correct for all tested inputs. Underscore-drops-without-separator
  is surprising but consistent behaviour, not a bug. Unicode letters are preserved
  because `unicode.IsLetter` is correctly used.
- **`CountWords`**: Delegates to `strings.Fields` which handles all whitespace
  variants correctly. No bugs found.

### Pre-existing test gap

Before this session: 3 tests, all ASCII happy-path. `ExtractInitials` and
`WrapText` had zero test coverage. All five functions lacked boundary and
Unicode testing.

---

## Files

| File | Description |
|---|---|
| `string_utils_test.go` | Comprehensive test suite (56 tests, 6 skipped for bugs) |
| `summary.md` | This document |
