# Bug Discovery Summary — string_utils.go

## Overview

The existing test suite covers only three happy-path cases and leaves large portions of the API untested. Two confirmed bugs were found, and multiple undocumented edge-case behaviours were identified.

---

## Confirmed Bugs

### Bug 1 — `Truncate`: byte slicing breaks multi-byte UTF-8 strings

**Location**: `string_utils.go:10-13`

**Root cause**: The guard uses `len(s)` (byte count) and the slice `s[:maxLen]` indexes bytes. For strings containing multi-byte UTF-8 code points (e.g. accented Latin characters, CJK, emoji) this slices through the middle of a rune, producing an invalid UTF-8 sequence in the output.

**Example**:
```
Truncate("héllo", 3)
// 'h' = 1 byte, 'é' = 2 bytes (0xC3 0xA9)
// s[:3] == "h" + 0xC3 → first byte of 'é' only → invalid UTF-8
// Correct: truncate by rune count → "hél..."
```

**Test**: `TestTruncate_MultiByteUTF8SlicesBytesNotRunes`

---

### Bug 2 — `ExtractInitials`: byte index instead of rune for first character

**Location**: `string_utils.go:44`

**Root cause**: `rune(p[0])` reads the byte at index 0, not the first Unicode code point. For names that start with a multi-byte character (e.g. `'É'` = 0xC3 0x89) this returns `0xC3` (a stray byte) rather than the intended rune `'É'`.

**Example**:
```
ExtractInitials("Émile Durkheim")
// p[0] for "Émile" == 0xC3, not 'É'
// Correct: []rune(p)[0] or utf8.DecodeRuneInString(p)
```

**Test**: `TestExtractInitials_MultiByteFirstCharBug`

---

## Untested Behaviours (not bugs per se, but undocumented)

### `Truncate`

| Case | Behaviour | Test |
|---|---|---|
| Empty string | Returns `""` | `TestTruncate_EmptyString` |
| String length == maxLen | Returns string unchanged (no `"..."`) | `TestTruncate_ExactLength` |
| String shorter than maxLen | Returns unchanged | `TestTruncate_ShorterThanMax` |
| maxLen == 0 | Returns `"..."` for any non-empty input | `TestTruncate_MaxLenZero` |
| maxLen == 1 | Returns first byte + `"..."` | `TestTruncate_MaxLenOne` |

### `SlugifyText`

| Case | Behaviour | Test |
|---|---|---|
| Empty string | Returns `""` | `TestSlugifyText_EmptyString` |
| Only spaces | Returns `""` | `TestSlugifyText_AllSpaces` |
| Leading/trailing spaces | Trimmed via hyphen-trim | `TestSlugifyText_LeadingTrailingSpaces` |
| Multiple consecutive spaces | Collapsed to single hyphen | `TestSlugifyText_MultipleConsecutiveSpaces` |
| Underscores | **Silently dropped** (not converted to `-`) | `TestSlugifyText_UnderscoreIsDropped` |
| Tabs / newlines | Silently dropped (not converted to `-`) | `TestSlugifyText_TabsAndNewlines` |
| All special chars | Returns `""` | `TestSlugifyText_AllSpecialChars` |
| Leading/trailing hyphens | Trimmed | `TestSlugifyText_LeadingHyphen`, `TestSlugifyText_TrailingHyphen` |
| Non-ASCII Unicode letters | Preserved (pass `unicode.IsLetter`) | `TestSlugifyText_UnicodeLettersPreserved` |

Notable undocumented design choice: underscores are dropped rather than converted to hyphens. This is likely surprising to callers expecting `snake_case → kebab-case` conversion.

### `CountWords`

| Case | Behaviour | Test |
|---|---|---|
| Empty string | Returns 0 | `TestCountWords_EmptyString` |
| Only whitespace | Returns 0 | `TestCountWords_OnlySpaces` |
| Leading/trailing spaces | Ignored (correct) | `TestCountWords_LeadingTrailingSpaces` |
| Multiple spaces between words | Collapsed (correct) | `TestCountWords_MultipleSpacesBetweenWords` |
| Tabs / newlines as delimiters | Treated as whitespace | `TestCountWords_TabsAndNewlinesAsDelimiters` |
| Punctuation attached to words | Punctuation is part of the token | `TestCountWords_PunctuationTreatedAsWordChars` |

### `ExtractInitials`

| Case | Behaviour | Test |
|---|---|---|
| Empty string | Returns `""` (no panic) | `TestExtractInitials_EmptyString` |
| Only whitespace | Returns `""` (no panic) | `TestExtractInitials_OnlySpaces` |
| Three-part name | Returns three initials | `TestExtractInitials_ThreePartName` |
| Extra whitespace | Handled by `strings.Fields` | `TestExtractInitials_ExtraWhitespaceBetweenNames` |

### `WrapText`

| Case | Behaviour | Test |
|---|---|---|
| Empty string | Returns `""` | `TestWrapText_EmptyString` |
| Only spaces | Returns `""` | `TestWrapText_OnlySpaces` |
| Single word, fits | Returns word | `TestWrapText_SingleWordFitsInWidth` |
| Single word longer than width | Word is **not split** — placed on its own line | `TestWrapText_SingleWordExceedsWidth` |
| width == 0 | Each word becomes its own line | `TestWrapText_WidthZero` |
| width == 1 | Each word becomes its own line | `TestWrapText_WidthOne` |
| Exact boundary fit | Word that exactly reaches width goes on current line | `TestWrapText_AllWordsExactlyFit`, `TestWrapText_ExactBoundary` |
| Tabs/newlines in input | Normalised to spaces by `strings.Fields` | `TestWrapText_TabsNormalizedToSingleSpace` |

Notable design choice: words longer than `width` are never split — they overflow. This is intentional in many wrapping implementations but is unspecified in the docstring and untested.

---

## Coverage Gap Summary

| Function | Original tests | New edge-case tests added |
|---|---|---|
| `Truncate` | 1 (basic truncation) | 6 |
| `SlugifyText` | 1 (basic slug) | 14 |
| `CountWords` | 1 (basic count) | 7 |
| `ExtractInitials` | 0 | 7 |
| `WrapText` | 0 | 13 |
| **Total** | **3** | **47** |

---

## Recommended Fixes

1. **`Truncate`**: Replace `len(s)` with `utf8.RuneCountInString(s)` and slice using `[]rune(s)[:maxLen]` (or use `norm.String`/`runes` package) to count and slice by code point.

2. **`ExtractInitials`**: Replace `rune(p[0])` with `[]rune(p)[0]` or use `utf8.DecodeRuneInString(p)` to read the first code point correctly.

3. **`SlugifyText`** (design clarification needed): Document whether underscores, tabs and newlines should become hyphens. If yes, add those characters to the second branch of the `if` condition.

4. **`WrapText`** (design clarification needed): Document the behaviour for words longer than `width`. If hard-wrapping is required, add logic to split oversized words.
