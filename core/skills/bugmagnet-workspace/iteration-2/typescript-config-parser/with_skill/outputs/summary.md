## Test Coverage Summary

**Tests Added: 74 total** (70 new + 4 original)
- parseConfig - empty/minimal inputs (3 tests)
- parseConfig - comment handling (2 tests + 1 skip: hash-in-value bug)
- parseConfig - section handling (5 tests)
- parseConfig - value types (6 tests)
- parseConfig - quoted values (4 tests)
- parseConfig - special characters / edge cases (3 tests + 1 skip: equals-sign bug)
- parseConfig - CRLF line endings (1 test)
- getTypedValue - type coercion (10 tests + 2 skips: Infinity bugs)
- serializeConfig - output format (6 tests + 1 skip: [default] header bug)
- getValue - missing sections/keys/defaults (10 tests)
- bugmagnet session 2026-04-26 - advanced coverage (10 tests + 3 skips: bug clusters)

**Final Count:**
- 67 passing tests
- 7 skipped tests (bugs documented)
- Total: 74 tests

**Bugs Discovered:**

1. Values containing '#' are stripped by inline comment logic - config_parser.ts:56-58
   - Root cause: `trimmed.indexOf("#")` finds any '#' in the line, including '#' that is part of a value (e.g., HTML color codes). The effective line is sliced to everything before '#', so values like `#ff0000` become empty strings.
   - Fix: Only treat '#' as a comment start when preceded by whitespace (e.g., match `/\s+#/` to locate comment position rather than bare `indexOf("#")`).
   - Minimal reproduction: `parseConfig("color = #ff0000")` → `config["default"]["color"].raw === ""` (should be `"#ff0000"`)

2. Values containing '=' are silently truncated - config_parser.ts:60-64
   - Root cause: `effective.split("=")` splits on ALL '=' characters and takes only `parts[1]`. Any content after the second '=' is lost. This affects URLs with query parameters, base64-encoded strings with padding, and any value containing '='.
   - Fix: Use `effective.indexOf("=")` and `effective.slice(eqIdx + 1).trim()` to extract everything after the first '=' as the value.
   - Minimal reproduction: `parseConfig("url = http://host?a=b")` → `raw === "http://host?a"` (should be `"http://host?a=b"`)

3. "Infinity" and "-Infinity" strings are converted to number type - config_parser.ts:28-29
   - Root cause: `Number("Infinity") === Infinity` and `!isNaN(Infinity)` is true, so the guard `!isNaN(num) && raw.trim() !== ""` passes and returns the number `Infinity`. Config files should treat "Infinity" as a string, not a JavaScript special number.
   - Fix: Add `isFinite(num)` to the guard: `if (!isNaN(num) && isFinite(num) && raw.trim() !== "") return num;`
   - Minimal reproduction: `getTypedValue("Infinity") === Infinity` (should be `"Infinity"`)

4. serializeConfig omits [default] header for explicitly declared default sections - config_parser.ts:83-85
   - Root cause: The serializer unconditionally skips the header for the "default" section (`if (section !== "default")`). If the original config had an explicit `[default]` section header, it is lost during serialization.
   - Fix: Track whether a section was explicitly declared (e.g., with a `Set<string>` of explicit section names) and conditionally emit the header.
   - Impact: Parse/serialize round-trips silently remove explicit `[default]` section headers, changing the output format.

**Key Behavioral Notes:**
- Empty string values are stored correctly (whitespace-only value is trimmed to `""`)
- CRLF line endings work correctly because `trim()` removes `\r` from each line
- Whitespace-only strings passed to `getTypedValue` are returned as strings (not coerced to 0)
- Case-sensitive boolean conversion: only exact `"true"`/`"false"` become booleans; `"True"`, `"FALSE"` remain strings
- Section names can be empty strings if `[   ]` is used (whitespace-only section name)
- The '=' equals-sign bug and the '#' hash bug can compound: a value like `bg = #aaa=bbb` would be doubly corrupted
