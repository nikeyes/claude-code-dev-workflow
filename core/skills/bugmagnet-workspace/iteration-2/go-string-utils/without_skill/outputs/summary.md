# Bug Magnet Analysis: string_utils.go

## Overview

Analyzed `string_utils.go` for edge cases, boundary conditions, and bugs. Extended the existing test suite from 3 tests to 42 tests.

---

## Total Tests Added

- **Before**: 3 tests (one per function, all happy-path only)
- **After**: 42 tests total (**39 new tests added**)

### Distribution by function

| Function          | Original | Added | Total |
|-------------------|----------|-------|-------|
| `Truncate`        | 1        | 7     | 8     |
| `SlugifyText`     | 1        | 13    | 14    |
| `CountWords`      | 1        | 7     | 8     |
| `ExtractInitials` | 0        | 8     | 8     |
| `WrapText`        | 0        | 10    | 10    |

---

## Bugs Discovered

### Bug 1: `Truncate` — byte-level slicing corrupts multi-byte UTF-8 strings

**File**: `string_utils.go`, line 10 and 13  
**Severity**: High  
**Root cause**: `len(s)` returns the **byte** length, not the rune (character) count. `s[:maxLen]` slices at byte position `maxLen`, which can land in the middle of a multi-byte UTF-8 rune (any character outside ASCII takes 2–4 bytes). This produces invalid UTF-8 output. For example, `"héllo"` has byte-length 6 but rune-length 5. `Truncate("héllo", 3)` cuts the `é` rune (2 bytes: 0xC3 0xA9) in half at byte index 3, producing a garbled string.

**Reproducing test**: `TestTruncate_MultiByteBoundary_BugReport`

**Proposed fix**:
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

### Bug 2: `ExtractInitials` — byte indexing `p[0]` corrupts multi-byte first characters

**File**: `string_utils.go`, line 45  
**Severity**: High  
**Root cause**: `p[0]` indexes a Go string by **byte**, not rune. For any name whose first character is a multi-byte UTF-8 codepoint (e.g. `Ü`, `Ä`, `É`, CJK characters), `p[0]` returns only the first byte of that character's UTF-8 encoding, which is meaningless on its own (typically 0xC3 for Latin extended characters). The result is garbled output rather than the correct initial letter.

**Example**: `ExtractInitials("Ünde Arna")` should return `"ÜA"`, but instead returns a string starting with the byte `0xC3` cast to a rune (the character `Ã`), uppercased.

**Reproducing test**: `TestExtractInitials_MultiByteFirstRune_BugReport`

**Proposed fix**:
```go
func ExtractInitials(name string) string {
    parts := strings.Fields(name)
    var initials []rune
    for _, p := range parts {
        runes := []rune(p)
        if len(runes) > 0 {
            initials = append(initials, runes[0])
        }
    }
    return strings.ToUpper(string(initials))
}
```

---

## Additional Boundary Conditions Documented (not bugs, but noteworthy)

### `Truncate` with `maxLen=0`
When `maxLen` is 0 and the string is non-empty, the function returns `"..."`. This may be surprising — callers should be aware that the suffix alone is returned when truncating to zero characters.

### `WrapText` — words longer than `width` are not split
A single word that exceeds `width` is placed on its own line without splitting. This is a documented limitation of the greedy word-wrap algorithm (consistent with most wrapping implementations), but callers expecting hard-wrapping at `width` characters would be surprised.
Test: `TestWrapText_WordLongerThanWidth`.

### `SlugifyText` — non-ASCII letters pass through unchanged
Characters like `é`, `ö`, `ü` satisfy `unicode.IsLetter` and are included in slugs (lowercased). This may produce slugs that are not purely ASCII. Whether this is a bug depends on requirements; it is documented and tested in `TestSlugifyText_NonASCIILettersPassThrough`.

---

## Coverage Assessment

### Before new tests
- `Truncate`: single happy-path (truncation case only)
- `SlugifyText`: single happy-path (two words, basic)
- `CountWords`: single happy-path (three words, no whitespace variations)
- `ExtractInitials`: **zero tests**
- `WrapText`: **zero tests**

### After new tests
- **`Truncate`**: happy-path, exact boundary, shorter-than-max, empty string, zero maxLen, single-char truncation, multi-byte boundary (bug confirmation), multi-byte safe case.
- **`SlugifyText`**: empty, already-lowercase, uppercase, multiple spaces, leading/trailing spaces, leading/trailing hyphens, special characters removed, numbers preserved, only specials, mixed hyphens+spaces, only spaces, only hyphens, single word, numbers only, non-ASCII passthrough.
- **`CountWords`**: empty, only spaces, single word, leading/trailing spaces, multiple spaces, tabs+newlines, single-char words.
- **`ExtractInitials`**: two parts, three parts, single name, all uppercase, all lowercase, empty string, only spaces, extra spaces, multi-byte first rune (bug report).
- **`WrapText`**: basic wrap, empty, single word, all fits, exact fit, each word on own line, only spaces, width=1, word longer than width, multiple spaces normalised, word content preserved, no line exceeds width.

Remaining blind spots (acceptable risk):
- Negative `maxLen` in `Truncate` (would panic — input validation is caller responsibility)
- Very large strings (performance characteristics, not functional bugs)
- Right-to-left / bidirectional text
