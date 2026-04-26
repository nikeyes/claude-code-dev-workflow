# BugMagnet Session Summary — user_validator.ts

**Date:** 2026-04-26
**File analyzed:** `user_validator.ts`
**Language / Framework:** TypeScript / Vitest

---

## Test Coverage Summary

**Tests added: 69 total**

| Category | Tests |
|---|---|
| validateUser — happy path | 4 |
| validateUser — name validation | 8 |
| validateUser — email validation | 5 |
| validateUser — age validation | 8 |
| validateUser — role validation | 3 |
| validateUser — tags validation | 6 |
| validateUser — multiple errors | 1 |
| normalizeEmail | 8 |
| formatUserDisplay | 9 |
| bugmagnet session (advanced edge cases) | 17 |

**Final count:**

- 64 passing tests
- 5 skipped tests (bugs documented)
- **Total: 69 tests**

---

## Bugs Discovered

### Bug 1 — NaN bypasses age range check

**Severity:** High
**File:** `user_validator.ts:29`
**Function:** `validateUser`

**Description:** Passing `NaN` as the `age` field produces `valid: true` instead of a validation error. Any numeric comparison with `NaN` evaluates to `false` in JavaScript, so both sides of `input.age < 0 || input.age > 150` return `false`, and the guard is never triggered.

**Current code:**
```typescript
if (input.age < 0 || input.age > 150) {
  errors.push("Age must be between 0 and 150");
}
```

**Proposed fix:**
```typescript
if (!Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
  errors.push("Age must be between 0 and 150");
}
```

**Expected:** `valid = false`, `errors = ["Age must be between 0 and 150"]`
**Actual:** `valid = true`, `errors = []`

**Test:** `validateUser — returns error for NaN age - BUG`

---

### Bug 2 — normalizeEmail crashes when input has no @ symbol

**Severity:** High
**File:** `user_validator.ts:49-51`
**Function:** `normalizeEmail`

**Description:** `email.split("@")` on a string with no `@` returns a single-element array. Destructuring assigns `domain = undefined`. Calling `undefined.toLowerCase()` throws `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`.

This affects any caller that does not pre-validate the email, including situations where `validateUser` rejects the email but `normalizeEmail` is still called on the same value.

**Current code:**
```typescript
const [local, domain] = email.split("@");
return `${local.toLowerCase()}@${domain.toLowerCase()}`;
```

**Proposed fix:**
```typescript
if (!email.includes("@")) {
  throw new Error(`Invalid email address: "${email}" contains no @ symbol`);
}
const [local, domain] = email.split("@");
return `${local.toLowerCase()}@${domain.toLowerCase()}`;
```

**Expected:** Meaningful `Error` thrown, not a raw `TypeError` about `undefined`
**Actual:** `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`

**Tests:** `normalizeEmail — does not crash when email has no @ symbol - BUG`, `normalizeEmail — does not crash when email is empty string - BUG`

---

### Bug 3 — normalizeEmail silently drops segments when email contains multiple @

**Severity:** Medium
**File:** `user_validator.ts:49`
**Function:** `normalizeEmail`

**Description:** `email.split("@")` on `"a@b@c"` returns `["a", "b", "c"]`. Destructuring captures only the first two elements (`local = "a"`, `domain = "b"`); the third segment `"c"` is silently discarded. The result is `"a@b"` instead of `"a@b@c"`.

While multiple-@ addresses are technically invalid per RFC 5321, the function contract is to normalize casing, not to reject invalid addresses. Silent truncation is unexpected and could allow spoofed addresses to pass downstream checks.

**Current code:**
```typescript
const [local, domain] = email.split("@");
```

**Proposed fix:**
```typescript
const atIndex = email.indexOf("@");
const local = email.slice(0, atIndex);
const domain = email.slice(atIndex + 1);
return `${local.toLowerCase()}@${domain.toLowerCase()}`;
```

**Expected:** `"a@b@c"` (full string lowercased)
**Actual:** `"a@b"` (third segment dropped)

**Test:** `normalizeEmail — preserves the full address when email contains multiple @ symbols - BUG`

---

### Bug 4 — formatUserDisplay shows "[Tags: ]" for an empty tags array

**Severity:** Low–Medium
**File:** `user_validator.ts:55`
**Function:** `formatUserDisplay`

**Description:** When `tags` is provided as an empty array `[]`, the display renders `"[Tags: ]"` (blank inside the brackets) instead of the expected `"[Tags: none]"`. This happens because `[].join(", ")` returns `""` (empty string), and the nullish coalescing operator `?? "none"` only replaces `null` or `undefined`, not an empty string.

**Current code:**
```typescript
const tagStr = user.tags?.join(", ") ?? "none";
```

**Proposed fix:**
```typescript
const tagStr =
  user.tags && user.tags.length > 0 ? user.tags.join(", ") : "none";
```

**Expected:** `"Alice (User) - alice@example.com [Tags: none]"`
**Actual:** `"Alice (User) - alice@example.com [Tags: ]"`

**Test:** `formatUserDisplay — shows 'none' for empty tags array instead of blank bracket - BUG`

---

## Key Behavioral Findings

- `validateUser` email check (`includes("@")`) is intentionally permissive: `"@"`, `"@domain"`, and `"user@"` all pass.
- `validateUser` has no integer constraint on `age`; fractional values like `30.5` are accepted.
- `validateUser` correctly catches `Infinity` and `-Infinity` for age (those ARE caught by `< 0 || > 150`), but NOT `NaN`.
- `formatUserDisplay` does not normalize or sanitize any field — it is a pure display formatter.
- Role validation is case-sensitive; `"Admin"` and `"USER"` are rejected.
- The `tags` field `undefined` (omitted) and `null` produce `"[Tags: none]"` correctly via `?.` and `??`; only the empty-array case is broken.
- All three bugs (`NaN` age, `normalizeEmail` crash, empty-tags display) are independent and do not interact with each other.
