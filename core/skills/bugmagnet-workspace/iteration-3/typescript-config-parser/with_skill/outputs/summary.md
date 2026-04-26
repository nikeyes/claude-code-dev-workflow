## Test Coverage Summary

**Tests Added:** 96 total (92 new + 4 original)
- parseConfig — empty / minimal inputs (5 tests)
- parseConfig — comment handling (3 tests + 3 skips: hash-value bugs)
- parseConfig — section handling (8 tests)
- parseConfig — typed value coercion (11 tests)
- parseConfig — quoted values (8 tests)
- parseConfig — special character values (10 tests + 3 skips: equals-sign bugs)
- parseConfig — scale and independence (4 tests)
- getTypedValue — standalone coercion (16 tests + 2 skips: Infinity bugs)
- serializeConfig — output format (8 tests + 1 skip: [default] header bug)
- getValue — missing sections / keys / defaults (13 tests)

**Results:** 87 passing, 9 skipped (bugs)

**Bugs Discovered:**

1. Values starting with `#` are silently stripped — config_parser.ts:56-58
   - Root cause: `trimmed.indexOf("#")` finds the first `#` anywhere in the line,
     including `#` that is part of the value itself (e.g., `color = #ff0000`). The
     effective line is truncated to everything before `#`, so `rawValue` becomes `""`.
   - Proposed fix: Only treat `#` as a comment start when it is preceded by whitespace.
     Replace `trimmed.indexOf("#")` with a regex like `/\s#/.exec(trimmed)`.

2. Values containing `#` anywhere (not only as a prefix) are truncated — config_parser.ts:56-58
   - Root cause: Same `indexOf("#")` logic as bug 1. Any `#` in a value, such as
     `ref = abc#123`, is treated as the start of an inline comment, silently truncating
     the value to `"abc"`.
   - Proposed fix: Same as bug 1 — require whitespace before `#` to treat it as a comment.

3. Keys containing `#` cause the entry to be silently dropped — config_parser.ts:56-58
   - Root cause: Comment stripping applies to the full trimmed line before splitting on
     `=`. A key such as `my#key = value` is truncated to `my`, leaving no `=` in the
     effective string, so `parts.length < 2` and the line is skipped entirely.
   - Proposed fix: Apply comment stripping only to the value portion of the line (i.e.,
     after the first `=`), not to the full line.

4. Values containing `=` are truncated after the first occurrence — config_parser.ts:60-64
   - Root cause: `effective.split("=")` produces multiple parts and only `parts[1]` is
     kept. Everything from the second `=` onward is discarded. This corrupts URLs with
     query parameters (`http://host?a=b` → `http://host?a`) and base64 padding
     (`dXNlcjpwYXNzd29yZA==` → `dXNlcjpwYXNzd29yZA`).
   - Proposed fix: Split only on the first `=` using `indexOf`:
     ```ts
     const eqIdx = effective.indexOf("=");
     if (eqIdx === -1) continue;
     const key = effective.slice(0, eqIdx).trim();
     const rawValue = effective.slice(eqIdx + 1).trim();
     ```

5. `"Infinity"` is coerced to the JavaScript number `Infinity` — config_parser.ts:28-29
   - Root cause: `Number("Infinity") === Infinity` and `!isNaN(Infinity)` is `true`, so
     the guard `!isNaN(num) && raw.trim() !== ""` passes and returns the numeric
     `Infinity`. Config files should treat the string `"Infinity"` as a plain string.
   - Proposed fix: Add an `isFinite` check:
     `if (!isNaN(num) && isFinite(num) && raw.trim() !== "") return num;`

6. `"-Infinity"` is coerced to the JavaScript number `-Infinity` — config_parser.ts:28-29
   - Root cause: Identical to bug 5 (`Number("-Infinity") === -Infinity`,
     `!isNaN(-Infinity)` is `true`).
   - Proposed fix: Same `isFinite` guard as bug 5.

7. `serializeConfig` omits `[default]` header for explicitly declared default sections — config_parser.ts:83-85
   - Root cause: The serializer unconditionally skips the header for the `"default"`
     section (`if (section !== "default")`). An input that explicitly wrote
     `[default]` has that header silently removed during serialization, breaking
     format-preserving round-trips.
   - Proposed fix: Track which sections were explicitly declared in a `Set` and emit
     their headers unconditionally, including for `"default"`.

**Key Behavioral Notes (not bugs — observed and verified):**
- Whitespace-only value strings are trimmed to `""` (stored as empty raw).
- CRLF line endings work correctly because `trim()` strips `\r` from each token.
- Only exact lowercase `"true"` / `"false"` become booleans; `"True"`, `"FALSE"` remain strings.
- `Number("")` would be 0, but the guard `raw.trim() !== ""` prevents empty strings from being coerced to numbers.
- `"NaN"` → `isNaN(Number("NaN"))` is `true` so it correctly stays a string.
- `"1e2"` is correctly coerced to `100` (scientific notation is valid numeric input).
- Section names can be empty strings when `[   ]` (whitespace-only) is used.
- Bugs 3 and 4 can compound: a line like `bg = #aaa=bbb` would be doubly corrupted — the `#` truncation fires first, leaving `bg =`, then splitting on `=` produces an empty value.
