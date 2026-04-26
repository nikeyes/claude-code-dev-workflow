# Bug Discovery Summary — TypeScript INI-style Config Parser

## Files Analysed

- Implementation: `evals/files/config_parser.ts`
- Existing tests: `evals/files/config_parser.test.ts`

---

## Existing Test Coverage Assessment

The original test suite has only **4 tests** covering:

| Area | Covered |
|------|---------|
| Simple key-value parsing | Yes (1 case) |
| Section headers | Yes (1 case) |
| `#` comment lines | Yes (1 case) |
| `getValue` missing section | Yes (1 case) |

Entirely untested: inline comments, values with `=`, quoted values with special characters, `serializeConfig`, `getTypedValue` directly, Windows line endings, duplicate keys/sections, boundary inputs, and all error paths.

---

## Confirmed Bugs

### Bug 1 — Values containing `=` are silently truncated

**Location**: `parseConfig`, line 60–64

```ts
const parts = effective.split("=");
if (parts.length < 2) continue;
const key = parts[0].trim();
const rawValue = parts[1].trim();   // <-- only reads index 1
```

`split("=")` produces more than two parts for any value containing `=`, but only `parts[1]` is read. Everything after the second `=` is dropped.

**Impact**: Base64 values (`aGVsbG8=`), URLs (`http://host?a=1&b=2`), and any key-value assignment expressions stored as config values are silently corrupted.

**Fix**: Use `parts.slice(1).join("=")` instead of `parts[1]`.

---

### Bug 2 — Inline `;` comments are not stripped

**Location**: `parseConfig`, line 56–58

```ts
const commentIdx = trimmed.indexOf("#");
const effective =
  commentIdx >= 0 ? trimmed.slice(0, commentIdx).trimEnd() : trimmed;
```

Only `#` is treated as an inline comment marker. The INI format also uses `;` as a comment character (and the parser already strips full lines starting with `;`), but inline `;` characters are left in the value.

**Impact**: `host = localhost ; dev only` produces `raw = "localhost ; dev only"` instead of `"localhost"`.

**Fix**: Also find the index of `;` and use the earlier of the two positions.

---

### Bug 3 — `#` inside a quoted value is treated as an inline comment

**Location**: `parseConfig`, lines 56–68 (comment stripping runs before quote stripping)

The inline-comment strip (`indexOf("#")`) is applied to the raw line text before `stripQuotes` is called. A value like `'#ff0000'` has the `#` stripped first, producing an empty effective value; then `stripQuotes` sees only the remaining fragment.

**Impact**: Any quoted value that contains a `#` character (e.g. hex colours, comments-in-strings, hash-style passwords) is corrupted.

**Fix**: Parse quote boundaries first, then only strip comments that fall outside quoted regions.

---

### Bug 4 — `getTypedValue` converts `"Infinity"` / `"-Infinity"` to JS `Infinity`

**Location**: `getTypedValue`, lines 28–29

```ts
const num = Number(raw);
if (!isNaN(num) && raw.trim() !== "") return num;
```

`Number("Infinity")` returns the JavaScript special value `Infinity`, which is not `NaN`, so the guard passes and the string `"Infinity"` is typed as the number `Infinity`. The same applies to `"-Infinity"`.

**Impact**: Config values literally set to `Infinity` or `-Infinity` are silently coerced to JS numeric infinity instead of remaining strings, which may break downstream consumers that do type-checks or serialization.

**Fix**: Add an explicit `isFinite(num)` check, or reject strings that are not purely decimal/floating-point via regex before attempting `Number()`.

---

### Bug 5 — `serializeConfig` does not re-quote values, breaking round-trips for values with special characters

**Location**: `serializeConfig`, line 87

```ts
lines.push(`${key} = ${value.raw}`);
```

`raw` is the already-stripped value (quotes removed by `stripQuotes`). When the original value contained characters that require quoting (spaces that resemble comments, `#` characters, `;` characters), the serialized form lacks quotes and will be misinterpreted when re-parsed.

**Impact**: `parseConfig(serializeConfig(config))` does not always reproduce the original config.

**Fix**: Re-quote values in `serializeConfig` when `raw` contains characters that the parser would otherwise misinterpret (`#`, `;`, or leading/trailing whitespace).

---

## Additional Edge Cases (Not Bugs, But Untested)

| Edge Case | Behaviour | Verified by Test |
|-----------|-----------|-----------------|
| Empty input | Returns `{ default: {} }` | Yes (new test) |
| Windows CRLF line endings | `trim()` strips `\r`, so parsing works | Yes (new test) |
| Duplicate key in same section | Last value wins (silent overwrite) | Yes (new test) |
| Re-entering same section `[db]…[app]…[db]` | Merges; earlier keys preserved | Yes (new test) |
| Empty section name `[]` | Creates `config[""]`, no crash | Yes (new test) |
| Key starting with `=` | Empty key is skipped correctly | Yes (new test) |
| Line with no `=` | Skipped correctly | Yes (new test) |
| Section name with whitespace `[  db  ]` | Trimmed correctly | Yes (new test) |
| `getTypedValue("")` | Returns `""` (not `0`) — `raw.trim() !== ""` guard works | Yes (new test) |
| `getTypedValue("   ")` | Should return string, not `0` | Yes (new test — potential bug) |
| `getTypedValue("NaN")` | `isNaN(Number("NaN"))` is `true` → stays string | Yes (new test) |
| `getValue` with no defaultValue | Returns `undefined` | Yes (new test) |

---

## Coverage Summary

| Function | Original Tests | New Tests Added |
|----------|---------------|-----------------|
| `getTypedValue` | 0 | 11 |
| `parseConfig` | 3 | 30+ |
| `serializeConfig` | 0 | 7 |
| `getValue` | 1 | 6 |

**Total new tests**: ~55 (across all describe blocks in `config_parser_edge_cases.test.ts`)
