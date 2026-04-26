# Bug Report and Coverage Assessment — config_parser

## Overview

Analysed `config_parser.ts` against its 4 original tests. Added 50 new tests
covering edge cases, boundary conditions, and confirmed bugs.

---

## Bugs Discovered

### Bug 1 — Values containing `=` are silently truncated

**Root cause:** `parseConfig` splits the effective line on every `=` character
(`effective.split("=")`) and then only reads `parts[1]`. Any content after the
second `=` is silently discarded.

**File:** `config_parser.ts`, line 60–64.

**Affected input examples:**
- `url = http://host?a=1` → stored as `http://host?a` (query parameter lost)
- `token = abc==` → stored as `abc` (base64 padding lost)
- `a=b=c` → stored as `b`

**Proposed fix:** Use `indexOf("=")` to find only the first `=` and split there:
```typescript
const eqIdx = effective.indexOf("=");
if (eqIdx < 0) continue;
const key = effective.slice(0, eqIdx).trim();
const rawValue = effective.slice(eqIdx + 1).trim();
```

---

### Bug 2 — Hex color values (and any value starting with `#`) are silently dropped

**Root cause:** `parseConfig` strips inline comments by finding the first `#`
in the *full* effective line (not just in the value portion). A value like
`#ff0000` is treated as the start of an inline comment, making the stored value
an empty string.

**File:** `config_parser.ts`, lines 56–58.

**Affected input example:**
- `color = #ff0000` → stored as `""` (color completely lost)

**Proposed fix:** Search for `#` only in the value portion (after the `=`), or
check that the `#` is preceded by whitespace before treating it as a comment
delimiter:
```typescript
// Find comment only after the first '='
const eqIdx = effective.indexOf("=");
const valueStart = eqIdx + 1;
const commentInValue = effective.indexOf(" #", valueStart);
const valuePart = commentInValue >= 0
  ? effective.slice(valueStart, commentInValue)
  : effective.slice(valueStart);
const rawValue = valuePart.trim();
```

---

### Bug 3 — `"Infinity"` and hex literals are coerced to unexpected numeric types

**Root cause:** `getTypedValue` uses `Number(raw)` and `!isNaN(num)` to decide
whether to return a number. `Number("Infinity") === Infinity` (which passes
`!isNaN`) and `Number("0x10") === 16`, so these strings are converted to
numbers instead of being kept as strings.

**File:** `config_parser.ts`, lines 28–30.

**Affected input examples:**
- `limit = Infinity` → typed as the JavaScript `Infinity` number
- `flags = 0x10` → typed as `16`

**Proposed fix:** Add explicit guards:
```typescript
if (!isFinite(num)) return raw;          // reject Infinity / -Infinity
if (/^0[xX]/.test(raw)) return raw;      // reject hex literals
```

---

## Tests Added

| Group | Tests Added |
|---|---|
| `getTypedValue` | 11 |
| `parseConfig — basic key/value` | 7 |
| `parseConfig — quoted values` | 5 |
| `parseConfig — comment handling` | 4 |
| `parseConfig — values with '='` | 3 |
| `parseConfig — sections` | 6 |
| `parseConfig — whitespace / line endings` | 3 |
| `serializeConfig` | 5 |
| `getValue — extended` | 7 |
| `integration` | 2 |
| **Total new tests** | **53** |

(The 4 original tests are preserved unchanged.)

---

## Coverage Assessment

### What the original tests covered
- Happy-path parsing of a single key-value pair
- Parsing a named section with a numeric value
- Skipping `#` comment lines
- `getValue` returning a fallback for a missing section

### What was missing (now added)

**Untested functions:**
- `getTypedValue` had zero direct tests — now has 11.
- `serializeConfig` had zero tests — now has 5.

**Untested paths in `parseConfig`:**
- Semicolon comment lines (`;`)
- Inline `#` comments (including the bug with `#` values)
- Quoted values (single and double) and their edge cases
- Values/keys with `=` characters (including the truncation bug)
- Empty input, blank lines, whitespace-only lines
- Multiple sections, duplicate sections, empty sections
- Section name trimming
- CRLF line endings
- Empty-key lines (`= value`)
- Key overwrite within the same section

**Untested paths in `getValue`:**
- Missing key within an existing section
- Numeric and boolean default values
- Boolean typed return values

**Untested edge cases in `getTypedValue`:**
- Zero (`"0"`)
- Negative numbers
- Floats
- Scientific notation (`"1e3"`)
- Hex literals (`"0x10"`) — confirmed bug
- `"Infinity"` — confirmed bug
- `"NaN"` — correct behaviour verified
- Empty string and whitespace-only strings
