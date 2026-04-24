# Test Coverage Summary — user_validator.ts (without skill)

## Overview

| Metric | Value |
|--------|-------|
| Total tests written | 42 |
| Tests expected to pass | 39 |
| Tests expected to fail (skipped) | 2 |
| Tests documenting bugs (passing but wrong behaviour) | 4 |
| Bugs discovered | 4 |

> Note: The shell permission policy in this session blocked `npm install` and `npx vitest run`.
> A `package.json` is provided alongside the test file so the tests can be run with:
> `npm install && npx vitest run` from the outputs directory.
> All pass/fail expectations below are derived from static analysis of the implementation.

---

## Test Execution

To run the tests manually:

```bash
cd core/skills/bugmagnet-workspace/iteration-1/typescript-user-validator/without_skill/outputs
npm install
npx vitest run
```

---

## Test Groups

| Group | Tests |
|-------|-------|
| validateUser – name field | 8 |
| validateUser – email field | 7 |
| validateUser – age field | 8 |
| validateUser – role field | 4 |
| validateUser – tags field | 7 |
| validateUser – multiple errors accumulate | 1 |
| normalizeEmail | 6 |
| formatUserDisplay | 6 |
| **Total** | **47** |

---

## Bugs Discovered

### BUG 1 — NaN age bypasses range check (CRITICAL)

**Location:** `validateUser`, age validation  
**Code:** `if (input.age < 0 || input.age > 150)`  
**Problem:** In JavaScript, `NaN < 0` and `NaN > 150` both evaluate to `false`. A caller
passing `age: NaN` silently passes validation as if it were a valid age.  
**Documented as:** `test.skip("BUG: NaN age bypasses range check…")` + a companion passing
test that documents the current broken behaviour.  
**Fix:** Add an explicit `isNaN(input.age)` check.

---

### BUG 2 — normalizeEmail crashes on input with no `@` symbol (CRITICAL)

**Location:** `normalizeEmail`  
**Code:** `const [local, domain] = email.split("@");`  
**Problem:** When the input contains no `@`, `split('@')` returns `['fullstring']`.
Destructuring assigns `domain = undefined`. The next line calls `domain.toLowerCase()`,
throwing `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`.  
**Documented as:** `test.skip("BUG: normalizeEmail crashes when input has no @ symbol")`  
**Fix:** Guard against missing domain, e.g. validate before splitting or return early.

---

### BUG 3 — Email validator accepts structurally invalid addresses (LOW)

**Location:** `validateUser`, email validation  
**Code:** `if (!input.email || !input.email.includes("@"))`  
**Problem:** The check only verifies that `@` is present. Both `"user@"` (no domain) and
`"@domain.com"` (no local part) pass validation. Likewise `"a@b@c"` passes.  
**Documented as:** Three passing tests that document current (permissive) behaviour.  
**Fix:** Use a stricter check, e.g. require non-empty local AND domain parts.

---

### BUG 4 — formatUserDisplay shows empty string instead of "none" for empty tags array

**Location:** `formatUserDisplay`  
**Code:** `const tagStr = user.tags?.join(", ") ?? "none";`  
**Problem:** `??` (nullish coalescing) only replaces `null`/`undefined`. An empty array
`[]` is not nullish; `[].join(", ")` returns `""`, which is a defined value. So the output
becomes `[Tags: ]` instead of `[Tags: none]`.  
**Documented as:** A passing test that asserts `[Tags: ]` to reflect actual behaviour,
with a code comment explaining the discrepancy.  
**Fix:** Change to `user.tags && user.tags.length ? user.tags.join(", ") : "none"` (or
similar falsy check on the joined result).

---

## Coverage Analysis vs. Existing Tests

The original test file (`user_validator.test.ts`) had only **3 tests**:

1. Valid user returns `valid: true`
2. Empty name returns "Name is required"
3. `normalizeEmail` lowercases an email

Gaps filled by the new tests:

| Area | Original | New |
|------|----------|-----|
| Name: whitespace-only | ✗ | ✓ |
| Name: 100-char boundary | ✗ | ✓ |
| Name: 101-char over limit | ✗ | ✓ |
| Name: unicode / accents | ✗ | ✓ |
| Email: missing domain | ✗ | ✓ (bug documented) |
| Email: missing local part | ✗ | ✓ (bug documented) |
| Email: multiple @ | ✗ | ✓ |
| Age: boundary values (0, 150) | ✗ | ✓ |
| Age: out-of-range (-1, 151) | ✗ | ✓ |
| Age: NaN bypass | ✗ | ✓ (skipped — bug) |
| Age: Infinity values | ✗ | ✓ |
| Role: all three valid roles | ✗ | ✓ |
| Role: invalid role at runtime | ✗ | ✓ |
| Tags: undefined vs empty array | ✗ | ✓ |
| Tags: length boundary (50 chars) | ✗ | ✓ |
| Tags: multiple oversized tags | ✗ | ✓ |
| Multiple errors at once | ✗ | ✓ |
| normalizeEmail: no @ crash | ✗ | ✓ (skipped — bug) |
| normalizeEmail: multiple @ | ✗ | ✓ |
| formatUserDisplay: with tags | ✗ | ✓ |
| formatUserDisplay: without tags | ✗ | ✓ |
| formatUserDisplay: empty tags | ✗ | ✓ (bug documented) |
| formatUserDisplay: role capitalisation | ✗ | ✓ |
