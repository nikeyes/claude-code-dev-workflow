# User Validator - Test Coverage Analysis Summary

## Total Tests Added

- **Original tests:** 3
- **New tests added:** 37
- **Total tests:** 40

---

## Bugs Discovered

### Bug 1: `normalizeEmail` crashes when email has no `@` sign

- **Severity:** High (runtime crash)
- **File:** `user_validator.ts`, line 49–51
- **Root cause:** `email.split("@")` on a string with no `@` returns `["entirestring"]`. Destructuring assigns `local = "entirestring"` and `domain = undefined`. Calling `undefined.toLowerCase()` throws a `TypeError`.
- **Reproducer:** `normalizeEmail("noemail")` → `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`
- **Proposed fix:** Guard against missing `@` before splitting, or validate the email format first:
  ```ts
  export function normalizeEmail(email: string): string {
    if (!email.includes("@")) {
      throw new Error(`Invalid email: missing "@" in "${email}"`);
    }
    const atIndex = email.lastIndexOf("@");
    const local = email.slice(0, atIndex).toLowerCase();
    const domain = email.slice(atIndex + 1).toLowerCase();
    return `${local}@${domain}`;
  }
  ```

---

### Bug 2: `normalizeEmail` silently drops everything after the second `@`

- **Severity:** Medium (silent data corruption)
- **File:** `user_validator.ts`, line 49
- **Root cause:** `email.split("@")` on `"a@b@c.com"` returns `["a", "b", "c.com"]`. Array destructuring `const [local, domain]` binds only the first two elements, silently discarding `"c.com"`. The result is `"a@b"` instead of `"a@b@c.com"`.
- **Proposed fix:** Use `lastIndexOf("@")` to split correctly, keeping the full domain (see fix in Bug 1 above). This also handles edge cases where the local part contains quoted `@` characters.

---

### Bug 3: `formatUserDisplay` shows `[Tags: ]` (empty) instead of `[Tags: none]` for an empty tags array

- **Severity:** Medium (incorrect display)
- **File:** `user_validator.ts`, line 55
- **Root cause:** `[].join(", ")` returns `""` (empty string). The nullish coalescing operator `?? "none"` only substitutes when the left-hand side is `null` or `undefined`. An empty string is neither, so `"" ?? "none"` evaluates to `""`, and the output is `[Tags: ]` instead of `[Tags: none]`.
- **Proposed fix:** Use `||` (logical OR) instead of `??`, or explicitly check for empty string:
  ```ts
  const tagStr = user.tags && user.tags.length > 0 ? user.tags.join(", ") : "none";
  ```

---

### Bug 4: `validateUser` accepts `NaN` as a valid age

- **Severity:** Medium (silent invalid data)
- **File:** `user_validator.ts`, line 29
- **Root cause:** The condition `if (age < 0 || age > 150)` uses JavaScript relational operators. All comparisons with `NaN` return `false` (`NaN < 0` is `false`, `NaN > 150` is `false`), so a `NaN` age bypasses validation entirely and the user is returned as valid.
- **Proposed fix:** Add an explicit `isNaN` or `Number.isFinite` check:
  ```ts
  if (!Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
    errors.push("Age must be between 0 and 150");
  }
  ```

---

### Bug 5 (design concern): `validateUser` accepts fractional ages

- **Severity:** Low (depends on business requirements)
- **File:** `user_validator.ts`, line 29
- **Root cause:** No integer check exists. Ages like `25.7` or `0.5` pass validation without error.
- **Proposed fix:** Add an integer check if the business domain requires whole-number ages:
  ```ts
  if (!Number.isInteger(input.age) || input.age < 0 || input.age > 150) {
    errors.push("Age must be between 0 and 150");
  }
  ```

---

### Bug 6 (design concern): `validateUser` email validation is too permissive

- **Severity:** Low–Medium (depends on downstream use)
- **File:** `user_validator.ts`, line 25
- **Root cause:** Validation only checks for presence of `@` using `String.includes("@")`. The following invalid values all pass:
  - `"@"` — just an at-sign, no local part or domain
  - `"@domain.com"` — missing local part
  - `"user@"` — missing domain
- **Proposed fix:** Check that both local and domain parts are non-empty:
  ```ts
  const atIndex = input.email.indexOf("@");
  if (atIndex <= 0 || atIndex === input.email.length - 1) {
    errors.push("Valid email is required");
  }
  ```
  (A stricter regex is also acceptable, though overkill for most use cases.)

---

## Coverage Assessment

### Before (3 tests)

| Area | Coverage |
|---|---|
| `validateUser` – name empty | Covered |
| `validateUser` – happy path | Covered |
| `normalizeEmail` – basic lowercasing | Covered |
| All other paths | **Not covered** |

### After (40 tests)

| Area | Tests Added | Key Gaps Addressed |
|---|---|---|
| `validateUser` – name boundaries (whitespace, 100-char limit) | 4 | Whitespace-only, exact boundary at 100 |
| `validateUser` – email structural validation | 4 | `@` alone, no local part, no domain |
| `validateUser` – age boundaries (0, 150, NaN, fractional) | 5 | NaN bug, fractional bug, boundary values |
| `validateUser` – role validation (all roles + runtime invalid) | 3 | Runtime invalid role |
| `validateUser` – tags (valid, too long, empty array, multiple errors) | 6 | Exact 50-char boundary, multi-error accumulation |
| `validateUser` – multiple simultaneous errors | 1 | Error accumulation |
| `normalizeEmail` – case normalization variants | 4 | Mixed cases per part |
| `normalizeEmail` – crash on missing `@` (Bug 1) | 1 | Runtime crash |
| `normalizeEmail` – data loss on multiple `@` (Bug 2) | 1 | Silent truncation |
| `formatUserDisplay` – role capitalization | 3 | All three roles |
| `formatUserDisplay` – tags display variants | 4 | Empty array bug, single tag, undefined |

All three exported functions now have meaningful edge case coverage. The six bugs documented above represent real defects that the expanded test suite exposes.
