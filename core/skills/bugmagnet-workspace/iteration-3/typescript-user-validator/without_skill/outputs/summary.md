# Bug Discovery Summary: user_validator.ts

## Overview

A manual analysis of `user_validator.ts` and its existing test suite (`user_validator.test.ts`) was performed. Three confirmed bugs and several coverage gaps were found. The existing test suite covers only 2 of the 3 exported functions, and only happy-path / obvious-error scenarios.

---

## Confirmed Bugs

### Bug 1 — `normalizeEmail`: throws `TypeError` when email has no `@`

**Location**: `normalizeEmail`, line 49-51  
**Severity**: High

```ts
const [local, domain] = email.split("@");
return `${local.toLowerCase()}@${domain.toLowerCase()}`;
```

`"not-an-email".split("@")` returns `["not-an-email"]`. The destructuring assigns `domain = undefined`. Calling `undefined.toLowerCase()` throws a `TypeError` at runtime.

The function has no guard, and callers that pass unvalidated strings (before calling `validateUser`) will crash.

---

### Bug 2 — `normalizeEmail`: silently truncates emails with multiple `@` signs

**Location**: `normalizeEmail`, line 49-51  
**Severity**: Medium

`"a@b@c".split("@")` returns `["a", "b", "c"]`. Destructuring only picks the first two elements, so `local = "a"` and `domain = "b"`. The trailing `"@c"` segment is silently dropped, and the function returns `"a@b"` instead of throwing or producing a deterministic error.

---

### Bug 3 — `formatUserDisplay`: empty `tags` array renders as blank instead of `"none"`

**Location**: `formatUserDisplay`, line 55  
**Severity**: Low–Medium

```ts
const tagStr = user.tags?.join(", ") ?? "none";
```

The `??` (nullish coalescing) operator only triggers for `null` or `undefined`. When `tags` is `[]` (an empty array), `[].join(", ")` evaluates to `""` (an empty string), which is not nullish. The output becomes `"[Tags: ]"` rather than the expected `"[Tags: none]"`.

Fix: use `user.tags?.length ? user.tags.join(", ") : "none"` or check for falsy/empty.

---

## Coverage Gaps (no confirmed bug, but untested behaviour)

### Gap 1 — `validateUser` name: whitespace-only name triggers two errors simultaneously

A name consisting entirely of spaces (e.g. 101 spaces) is both "empty after trim" and "longer than 100 characters". Both error messages are added. Whether this is intentional is unclear, but it is untested.

### Gap 2 — `validateUser` age: `NaN` passes validation silently

`NaN < 0` and `NaN > 150` both evaluate to `false` in JavaScript. An `age` of `NaN` therefore produces no error and `valid: true`. This is almost certainly a bug, though whether it is reachable from the TypeScript type system depends on how the function is called at runtime (e.g., from JSON input).

### Gap 3 — `validateUser` age: fractional values are accepted

An age of `25.7` passes all guards. Whether integers are required is not stated in the implementation; this gap needs a business-rules clarification.

### Gap 4 — `validateUser` age boundaries not tested

Neither `0` (lower bound), `150` (upper bound), `-1`, nor `151` are tested.

### Gap 5 — `validateUser` email: minimal `@`-only strings pass

The email check is `email.includes("@")`, so `"@"`, `"@domain"`, and `"local@"` all pass. The existing test only verifies that a fully missing `@` fails.

### Gap 6 — `validateUser` tags: boundary at 50 / 51 characters not tested

The limit uses `> 50` (strictly greater than), so a tag of exactly 50 characters is valid and one of exactly 51 is not. Neither boundary is covered.

### Gap 7 — `validateUser` role: case-sensitivity not tested

`"Admin"` and `"USER"` are rejected because the check is case-sensitive. This is correct but untested.

### Gap 8 — `validateUser` multiple simultaneous errors not tested

No test verifies that all errors are collected when several fields are invalid at the same time.

### Gap 9 — `formatUserDisplay` not tested at all

The existing test suite has zero tests for `formatUserDisplay`. Role capitalisation, tag joining, and the `undefined`-vs-empty-array fallback are all completely uncovered.

### Gap 10 — `normalizeEmail` with subdomains, plus-addressing, and dots not tested

Edge cases like `User+Tag@Sub.Domain.COM` are not covered.

---

## Summary Table

| ID | Function | Type | Description | Severity |
|----|----------|------|-------------|----------|
| B1 | `normalizeEmail` | Bug | Crashes on input with no `@` | High |
| B2 | `normalizeEmail` | Bug | Silently truncates multi-`@` emails | Medium |
| B3 | `formatUserDisplay` | Bug | Empty tags array shows blank, not "none" | Low–Medium |
| G1 | `validateUser` | Gap | Whitespace-only long name emits two errors | Low |
| G2 | `validateUser` | Bug (likely) | NaN age passes silently | Medium |
| G3 | `validateUser` | Gap | Fractional age not validated | Low |
| G4 | `validateUser` | Gap | Age boundary values (0, 150, -1, 151) untested | Low |
| G5 | `validateUser` | Gap | Minimal-but-technically-valid emails (e.g. "@") | Medium |
| G6 | `validateUser` | Gap | Tag length boundary (50 / 51 chars) untested | Low |
| G7 | `validateUser` | Gap | Role case-sensitivity untested | Low |
| G8 | `validateUser` | Gap | Multiple simultaneous errors untested | Low |
| G9 | `formatUserDisplay` | Gap | Function has zero test coverage | Medium |
| G10 | `normalizeEmail` | Gap | Subdomains, plus-addressing, dots untested | Low |
