# BugMagnet Session Summary — user_validator.ts

**Date:** 2026-04-26
**File analyzed:** `user_validator.ts`
**Language / Framework:** TypeScript / Vitest
**Iteration:** 3

---

## Test Coverage Summary

**Tests Added:** 71 total

| Category | Tests |
|---|---|
| validateUser — name boundaries | 8 (incl. 1 skipped bug) |
| validateUser — email edge cases | 7 |
| validateUser — age boundaries and special values | 10 (incl. 2 skipped bugs) |
| validateUser — role validation | 9 |
| validateUser — tags field | 9 (incl. 1 skipped potential bug) |
| validateUser — multiple errors and cross-field behavior | 4 |
| normalizeEmail — happy path | 8 |
| normalizeEmail — crash bugs | 3 (all skipped bugs) |
| formatUserDisplay — output format | 10 (incl. 1 skipped bug) |
| formatUserDisplay — role label | 1 |

**Results:** 63 passing, 8 skipped (bugs)

---

## Bugs Discovered

### Bug 1 — NaN age silently passes validation
**File:** `user_validator.ts:29`
**Function:** `validateUser`

- **Root cause:** `NaN < 0` and `NaN > 150` both evaluate to `false` in JavaScript, so the guard `input.age < 0 || input.age > 150` never fires for `NaN`.
- **Proposed fix:** Prefix with `!Number.isFinite(input.age) ||` so that `NaN`, `Infinity`, and `-Infinity` are all caught by a single guard. (Note: `Infinity` and `-Infinity` are already caught by the existing numeric comparisons, but `NaN` is not.)

```typescript
// Current
if (input.age < 0 || input.age > 150) {

// Fixed
if (!Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
```

**Expected:** `valid = false`, errors includes `"Age must be between 0 and 150"`
**Actual:** `valid = true`, `errors = []`

---

### Bug 2 — normalizeEmail crashes with TypeError when input has no `@`
**File:** `user_validator.ts:49–51`
**Function:** `normalizeEmail`

- **Root cause:** `"nodomain".split("@")` → `["nodomain"]`. Destructuring assigns `domain = undefined`. The template literal calls `undefined.toLowerCase()`, throwing `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`.
- **Proposed fix:** Guard at the top of the function before the split:

```typescript
if (!email.includes("@")) {
  throw new Error(`Invalid email: no @ symbol in "${email}"`);
}
```

**Expected:** a descriptive `Error` is thrown (or a graceful fallback)
**Actual:** `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`

---

### Bug 3 — normalizeEmail crashes with TypeError for empty-string input
**File:** `user_validator.ts:49–51`
**Function:** `normalizeEmail`

- **Root cause:** Same path as Bug 2. `"".split("@")` → `[""]`, `domain = undefined`, `.toLowerCase()` throws.
- **Proposed fix:** Same guard as Bug 2 covers this case.

**Expected:** graceful handling (error or passthrough)
**Actual:** `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`

---

### Bug 4 — normalizeEmail silently truncates addresses containing multiple `@` symbols
**File:** `user_validator.ts:49`
**Function:** `normalizeEmail`

- **Root cause:** `"a@b@c".split("@")` → `["a", "b", "c"]`. Two-element destructuring captures `local = "a"` and `domain = "b"`; the third segment `"c"` is silently dropped, returning `"a@b"` instead of `"a@b@c"`.
- **Proposed fix:** Use `indexOf` to find the first `@` and slice manually, preserving everything after it as the domain:

```typescript
const atIndex = email.indexOf("@");
const local = email.slice(0, atIndex);
const domain = email.slice(atIndex + 1);
return `${local.toLowerCase()}@${domain.toLowerCase()}`;
```

**Expected:** `normalizeEmail("A@B@C.com")` → `"a@b@c.com"`
**Actual:** `"a@b"` (everything from the second `@` onward is discarded)

---

### Bug 5 — formatUserDisplay renders `[Tags: ]` for an empty tags array instead of `[Tags: none]`
**File:** `user_validator.ts:55`
**Function:** `formatUserDisplay`

- **Root cause:** `[].join(", ")` returns `""` (empty string). The nullish coalescing operator `?? "none"` only substitutes for `null` or `undefined`, not for an empty string. So `tagStr` becomes `""` and the output is `"[Tags: ]"`.
- **Proposed fix:**

```typescript
// Current
const tagStr = user.tags?.join(", ") ?? "none";

// Fixed
const tagStr = user.tags && user.tags.length > 0 ? user.tags.join(", ") : "none";
```

**Expected:** `"… [Tags: none]"`
**Actual:** `"… [Tags: ]"`

---

### Bug 6 — Name length checked on raw string instead of trimmed string
**File:** `user_validator.ts:21–23`
**Function:** `validateUser`

- **Root cause:** The empty-name check uses `input.name.trim().length === 0` (consistent), but the upper-length check uses the raw `input.name.length`. A name like `"   " + "x".repeat(98)` has raw length 101 and is rejected with "Name must be 100 characters or less", even though its meaningful content (after trimming) is only 98 characters and should be valid.
- **Proposed fix:** Apply `.trim()` before the length comparison to be consistent with the empty check:

```typescript
// Current
if (input.name && input.name.length > 100) {

// Fixed
if (input.name && input.name.trim().length > 100) {
```

**Expected:** a name with 3 leading spaces and 98 real characters → `valid = true`
**Actual:** `valid = false` — raw length 101 trips the guard

---

### Bug 7 — String age bypasses range check at runtime
**File:** `user_validator.ts:29`
**Function:** `validateUser`

- **Root cause:** TypeScript prevents passing a string as `age` at compile time. At runtime, JavaScript's type coercion means `"25" < 0` and `"25" > 150` are both `false` (string coerced to number), so the guard is silently bypassed and the input is accepted as valid.
- **Proposed fix:**

```typescript
if (typeof input.age !== "number" || !Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
  errors.push("Age must be between 0 and 150");
}
```

**Expected:** `valid = false` (a string is not a valid age)
**Actual:** `valid = true` (passes all range checks via coercion)

---

### Bug 8 (potential) — Tag length uses UTF-16 code units, not Unicode code points
**File:** `user_validator.ts:39`
**Function:** `validateUser`

- **Root cause:** `tag.length` counts UTF-16 code units. Characters outside the Basic Multilingual Plane (emoji, some extended CJK) are encoded as surrogate pairs, each consuming 2 code units. A tag of 26 emoji has `.length === 52` and is rejected even though it contains only 26 human-readable characters.
- **Proposed fix (if limit is in code points):** Use spread to count real characters: `[...tag].length > 50`

**Expected:** 26 emoji characters → valid (26 ≤ 50 code points)
**Actual:** invalid — `.length === 52` exceeds the 50 code-unit limit

---

## Key Behavioral Findings

- `validateUser` email validation is intentionally permissive: only checks for presence of `@`, so `"@"`, `"user@"`, `"@domain"`, and multi-@ addresses all pass.
- `validateUser` has no integer constraint on `age`; fractional values like `0.1` and `149.9` are accepted.
- `validateUser` correctly rejects `Infinity` and `-Infinity` for age (those satisfy `< 0` or `> 150`), but not `NaN`.
- The whitespace-only name detection uses `.trim().length === 0`, but the max-length guard uses raw `.length` — an inconsistency that can cause false positives on padded names.
- `formatUserDisplay` is a pure display formatter: it does not normalize casing, sanitize content, or validate fields.
- An empty `tags: []` and an omitted `tags` field behave differently in `formatUserDisplay`: omitted produces `"none"` correctly; empty array produces `""` (a blank).
- `normalizeEmail` has no defensive guards; it is fully unsafe for any input without an `@`.
- The three `normalizeEmail` bugs (no-@, empty string, multiple-@) all stem from the same unchecked `split("@")` pattern and can be fixed together.
