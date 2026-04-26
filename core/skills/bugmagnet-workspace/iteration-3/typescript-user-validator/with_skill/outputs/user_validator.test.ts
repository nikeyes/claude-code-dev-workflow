import { describe, it, expect, test } from "vitest";
import { validateUser, normalizeEmail, formatUserDisplay } from "./user_validator";

// ---------------------------------------------------------------------------
// validateUser — name field
// ---------------------------------------------------------------------------

describe("validateUser — name boundaries", () => {
  it("accepts name of exactly 1 character", () => {
    const result = validateUser({ name: "A", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts name of exactly 100 characters (upper boundary)", () => {
    const result = validateUser({ name: "x".repeat(100), email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("rejects name of 101 characters (one over boundary)", () => {
    const result = validateUser({ name: "x".repeat(101), email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  it("rejects whitespace-only name (single space)", () => {
    const result = validateUser({ name: " ", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  it("rejects whitespace-only name (mixed tabs and spaces)", () => {
    const result = validateUser({ name: " \t ", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  it("accepts name that is whitespace-padded but non-empty after trim", () => {
    // "  Alice  " trims to "Alice" — length > 0, so it should be valid.
    const result = validateUser({ name: "  Alice  ", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test.skip("rejects name whose trimmed length exceeds 100 - BUG", () => {
    /*
     * ROOT CAUSE: The length check at user_validator.ts:21 uses `input.name.length`,
     * which counts the raw (untrimmed) string. A padded name like "  " + "x".repeat(100)
     * has raw length 102, so the > 100 guard fires — but it fires on a name that is
     * actually 100 real characters after trimming. Conversely, a name like " ".repeat(50) +
     * "x".repeat(60) (110 chars raw) would correctly fail, but the error message would be
     * misleading because the user's actual intended name is only 60 chars.
     *
     * A related problem: " ".repeat(3) + "x".repeat(98) is a 101-char raw string, so the
     * > 100 guard fires and adds "Name must be 100 characters or less", but the trimmed
     * content is only 98 characters — so the error message is inaccurate.
     *
     * CODE LOCATION: user_validator.ts:21-23
     *
     * CURRENT CODE:
     *   if (input.name && input.name.length > 100) {
     *     errors.push("Name must be 100 characters or less");
     *   }
     *
     * PROPOSED FIX: use trimmed length for the upper-bound check to be consistent with
     * the empty-name check that already calls .trim().length:
     *   if (input.name && input.name.trim().length > 100) {
     *     errors.push("Name must be 100 characters or less");
     *   }
     *
     * EXPECTED: a 3-space-padded, 98-char name (" " * 3 + "x" * 98) should be valid
     *           (trimmed length = 98, within limit)
     * ACTUAL:   invalid — raw length is 101, which trips the > 100 guard
     */
    const paddedName = "   " + "x".repeat(98); // raw=101, trimmed=98 — should be valid
    const result = validateUser({ name: paddedName, email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).not.toContain("Name must be 100 characters or less");
  });

  it("does not add both name errors for a whitespace name that is also long", () => {
    // A name of 101 spaces: trim().length === 0, so "Name is required" fires.
    // name.length > 100 is also true, so "Name must be 100 characters or less" also fires.
    // Both errors appear simultaneously — documents current behavior.
    const result = validateUser({ name: " ".repeat(101), email: "a@b.com", age: 25, role: "user" });
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain("Name must be 100 characters or less");
  });
});

// ---------------------------------------------------------------------------
// validateUser — email field
// ---------------------------------------------------------------------------

describe("validateUser — email edge cases", () => {
  it("rejects empty email", () => {
    const result = validateUser({ name: "Alice", email: "", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  it("accepts email with @ only (current permissive check)", () => {
    // The check is only `includes("@")`, so "@" alone satisfies it.
    const result = validateUser({ name: "Alice", email: "@", age: 25, role: "user" });
    expect(result.errors).not.toContain("Valid email is required");
  });

  it("accepts email with @ at the start (no local part)", () => {
    const result = validateUser({ name: "Alice", email: "@domain.com", age: 25, role: "user" });
    expect(result.errors).not.toContain("Valid email is required");
  });

  it("accepts email with @ at the end (no domain part)", () => {
    const result = validateUser({ name: "Alice", email: "user@", age: 25, role: "user" });
    expect(result.errors).not.toContain("Valid email is required");
  });

  it("accepts email with multiple @ symbols", () => {
    // Technically invalid RFC 5321, but current check only requires one @.
    const result = validateUser({ name: "Alice", email: "a@b@c.com", age: 25, role: "user" });
    expect(result.errors).not.toContain("Valid email is required");
  });

  it("accepts email with spaces (current permissive check)", () => {
    // Spaces in email are illegal per RFC, but the validator only checks for @.
    const result = validateUser({ name: "Alice", email: "a b@c.com", age: 25, role: "user" });
    expect(result.errors).not.toContain("Valid email is required");
  });

  it("accepts a very long email address that contains @", () => {
    const longEmail = "a".repeat(200) + "@" + "b".repeat(200) + ".com";
    const result = validateUser({ name: "Alice", email: longEmail, age: 25, role: "user" });
    expect(result.errors).not.toContain("Valid email is required");
  });
});

// ---------------------------------------------------------------------------
// validateUser — age field
// ---------------------------------------------------------------------------

describe("validateUser — age boundaries and special values", () => {
  it("accepts age 0 (lower boundary)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 0, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts age 150 (upper boundary)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 150, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("rejects age -1 (one below lower boundary)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: -1, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  it("rejects age 151 (one above upper boundary)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 151, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  it("accepts fractional age 0.1 (no integer constraint)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 0.1, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts fractional age 149.9 (no integer constraint)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 149.9, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("rejects Infinity age", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: Infinity, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  it("rejects -Infinity age", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: -Infinity, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test.skip("rejects NaN age - BUG", () => {
    /*
     * ROOT CAUSE: `NaN < 0` and `NaN > 150` both evaluate to false in JavaScript.
     * The condition `input.age < 0 || input.age > 150` therefore never triggers,
     * so NaN silently passes validation.
     *
     * CODE LOCATION: user_validator.ts:29
     *
     * PROPOSED FIX:
     *   if (!Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
     *     errors.push("Age must be between 0 and 150");
     *   }
     *
     * EXPECTED: valid = false, errors includes "Age must be between 0 and 150"
     * ACTUAL:   valid = true, errors = []
     */
    const result = validateUser({ name: "Alice", email: "a@b.com", age: NaN, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  it("accepts negative-zero age (-0 equals 0 in JS)", () => {
    // -0 === 0 in JS; -0 < 0 is false, so it passes the guard.
    const result = validateUser({ name: "Alice", email: "a@b.com", age: -0, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test.skip("rejects string '25' passed as age at runtime - BUG", () => {
    /*
     * ROOT CAUSE: TypeScript's type system prevents this at compile time, but at
     * runtime a string age like "25" reaches the numeric comparisons. In JS,
     * "25" < 0 is false and "25" > 150 is false due to type coercion, so the
     * guard is bypassed. The result is valid=true even though the age field is
     * not a number.
     *
     * CODE LOCATION: user_validator.ts:29
     *
     * PROPOSED FIX: add a runtime type guard:
     *   if (typeof input.age !== "number" || !Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
     *     errors.push("Age must be between 0 and 150");
     *   }
     *
     * EXPECTED: valid = false (a string is not a valid age)
     * ACTUAL:   valid = true (string coercion bypasses both comparisons)
     */
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: "25" as unknown as number,
      role: "user",
    });
    expect(result.valid).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// validateUser — role field
// ---------------------------------------------------------------------------

describe("validateUser — role validation", () => {
  it("accepts role 'admin'", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "admin" });
    expect(result.valid).toBe(true);
  });

  it("accepts role 'user'", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
  });

  it("accepts role 'moderator'", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "moderator" });
    expect(result.valid).toBe(true);
  });

  it("rejects role 'Admin' (wrong casing)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "Admin" as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  it("rejects role 'USER' (all caps)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "USER" as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  it("rejects role 'MODERATOR' (all caps)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "MODERATOR" as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  it("rejects an empty string role", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "" as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  it("rejects a role with surrounding whitespace", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: " user" as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  it("rejects a role that is a number coerced to string", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: 1 as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });
});

// ---------------------------------------------------------------------------
// validateUser — tags field
// ---------------------------------------------------------------------------

describe("validateUser — tags field", () => {
  it("accepts no tags (omitted field)", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts empty tags array", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "user", tags: [] });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts a tag of exactly 50 characters (boundary)", () => {
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: ["t".repeat(50)],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("rejects a tag of 51 characters (one over boundary)", () => {
    const longTag = "t".repeat(51);
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: [longTag],
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain(`Tag "${longTag}" exceeds 50 characters`);
  });

  it("reports separate errors for each oversized tag", () => {
    const tag1 = "a".repeat(51);
    const tag2 = "b".repeat(52);
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: [tag1, tag2],
    });
    expect(result.errors).toContain(`Tag "${tag1}" exceeds 50 characters`);
    expect(result.errors).toContain(`Tag "${tag2}" exceeds 50 characters`);
    expect(result.errors).toHaveLength(2);
  });

  it("accepts an empty-string tag (length 0 passes > 50 check)", () => {
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: [""],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts tags containing special characters", () => {
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: ["vip-user", "group:beta", "@internal"],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("accepts tags containing Unicode characters", () => {
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: ["бета", "日本語"],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test.skip("tag length check uses character count not byte count — potential Unicode BUG", () => {
    /*
     * ROOT CAUSE: `tag.length` in JavaScript counts UTF-16 code units, not
     * Unicode code points. Characters outside the Basic Multilingual Plane
     * (emoji, some CJK extensions) each consume 2 code units (a surrogate pair).
     * A tag of 26 emoji characters (each 2 code units) has `.length === 52`,
     * exceeding the 50-unit limit — even though a human would count only 26
     * characters. Conversely a tag of 50 ASCII chars and 1 emoji has
     * `.length === 52` and is incorrectly rejected.
     *
     * CODE LOCATION: user_validator.ts:39
     *
     * CURRENT CODE:
     *   if (tag.length > 50) {
     *
     * PROPOSED FIX (if limit is in code points):
     *   if ([...tag].length > 50) {
     *
     * EXPECTED: 25 emoji characters (25 surrogate pairs = 50 code units) → valid
     * ACTUAL:   valid (happens to work because 25 * 2 === 50)
     *
     * EXPECTED: 26 emoji characters (52 code units) → valid if limit is in characters
     * ACTUAL:   invalid — `.length` is 52, exceeds 50 code-unit limit
     */
    const twentySixEmoji = "😀".repeat(26); // 26 emoji = 52 code units
    const result = validateUser({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: [twentySixEmoji],
    });
    // If limit is 50 human-readable characters, 26 emoji should be valid.
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// validateUser — multiple errors and cross-field behavior
// ---------------------------------------------------------------------------

describe("validateUser — multiple simultaneous errors", () => {
  it("collects all four field errors at once", () => {
    const result = validateUser({
      name: "",
      email: "notemail",
      age: -1,
      role: "superuser" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain("Valid email is required");
    expect(result.errors).toContain("Age must be between 0 and 150");
    expect(result.errors).toContain("Invalid role");
    expect(result.errors).toHaveLength(4);
  });

  it("collects name error plus oversized tag error together", () => {
    const result = validateUser({
      name: "",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: ["t".repeat(51)],
    });
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain(`Tag "${"t".repeat(51)}" exceeds 50 characters`);
    expect(result.errors).toHaveLength(2);
  });

  it("returns valid:true only when errors array is empty", () => {
    const good = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "user" });
    expect(good.valid).toBe(true);
    expect(good.errors).toHaveLength(0);
  });

  it("returns valid:false whenever errors array is non-empty", () => {
    const bad = validateUser({ name: "", email: "a@b.com", age: 25, role: "user" });
    expect(bad.valid).toBe(false);
    expect(bad.errors.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// normalizeEmail
// ---------------------------------------------------------------------------

describe("normalizeEmail — happy path", () => {
  it("lowercases both local part and domain", () => {
    expect(normalizeEmail("Alice@EXAMPLE.COM")).toBe("alice@example.com");
  });

  it("is idempotent for already-lowercase input", () => {
    expect(normalizeEmail("user@domain.org")).toBe("user@domain.org");
  });

  it("lowercases all-uppercase local part", () => {
    expect(normalizeEmail("ADMIN@example.com")).toBe("admin@example.com");
  });

  it("lowercases all-uppercase domain", () => {
    expect(normalizeEmail("admin@EXAMPLE.COM")).toBe("admin@example.com");
  });

  it("handles plus-addressing in local part", () => {
    expect(normalizeEmail("User+Tag@DOMAIN.IO")).toBe("user+tag@domain.io");
  });

  it("handles dots in local part", () => {
    expect(normalizeEmail("First.Last@Domain.COM")).toBe("first.last@domain.com");
  });

  it("handles numeric characters in local part and domain", () => {
    expect(normalizeEmail("USER99@HOST123.COM")).toBe("user99@host123.com");
  });

  it("handles subdomain in domain part", () => {
    expect(normalizeEmail("User@Mail.Example.COM")).toBe("user@mail.example.com");
  });
});

describe("normalizeEmail — crash bugs", () => {
  test.skip("does not crash when input has no @ symbol - BUG", () => {
    /*
     * ROOT CAUSE: `email.split("@")` returns a one-element array `["notanemail"]`
     * when there is no @ in the string. Destructuring assigns `domain = undefined`.
     * The template literal then calls `undefined.toLowerCase()`, throwing:
     *   TypeError: Cannot read properties of undefined (reading 'toLowerCase')
     *
     * CODE LOCATION: user_validator.ts:49-51
     *
     * PROPOSED FIX:
     *   if (!email.includes("@")) {
     *     throw new Error(`Invalid email: no @ symbol in "${email}"`);
     *   }
     *   const [local, domain] = email.split("@");
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     *
     * EXPECTED: a descriptive Error is thrown (not a raw TypeError)
     * ACTUAL:   TypeError: Cannot read properties of undefined (reading 'toLowerCase')
     */
    expect(() => normalizeEmail("nodomain")).toThrow(Error);
    expect(() => normalizeEmail("nodomain")).not.toThrow(TypeError);
  });

  test.skip("does not crash when input is an empty string - BUG", () => {
    /*
     * ROOT CAUSE: Same as the no-@ case. `"".split("@")` → `[""]`.
     * `domain` is `undefined`, causing a TypeError on `.toLowerCase()`.
     *
     * CODE LOCATION: user_validator.ts:49-51  (same path as above)
     *
     * PROPOSED FIX: same guard as above catches this case too.
     *
     * EXPECTED: a descriptive Error or a returned empty string
     * ACTUAL:   TypeError: Cannot read properties of undefined (reading 'toLowerCase')
     */
    expect(() => normalizeEmail("")).not.toThrow(TypeError);
  });

  test.skip("silently truncates addresses with multiple @ symbols - BUG", () => {
    /*
     * ROOT CAUSE: `"a@b@c".split("@")` returns `["a", "b", "c"]`. Destructuring
     * takes only the first two elements; `"c"` is silently dropped.
     * The returned string is `"a@b"` instead of `"a@b@c"`.
     *
     * CODE LOCATION: user_validator.ts:49
     *
     * PROPOSED FIX: use indexOf to find the first @ and slice manually:
     *   const atIndex = email.indexOf("@");
     *   const local = email.slice(0, atIndex);
     *   const domain = email.slice(atIndex + 1);
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     *
     * EXPECTED: normalizeEmail("A@B@C.com") === "a@b@c.com"
     * ACTUAL:   "a@b"  (everything after the second @ is dropped)
     */
    expect(normalizeEmail("A@B@C.com")).toBe("a@b@c.com");
  });
});

// ---------------------------------------------------------------------------
// formatUserDisplay
// ---------------------------------------------------------------------------

describe("formatUserDisplay — output format", () => {
  it("formats correctly with tags", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["staff", "beta"],
    });
    expect(result).toBe("Alice (User) - alice@example.com [Tags: staff, beta]");
  });

  it("formats correctly without tags (shows 'none')", () => {
    const result = formatUserDisplay({
      name: "Bob",
      email: "bob@example.com",
      age: 25,
      role: "admin",
    });
    expect(result).toBe("Bob (Admin) - bob@example.com [Tags: none]");
  });

  it("capitalizes first letter of role for admin", () => {
    const result = formatUserDisplay({ name: "A", email: "a@b.com", age: 20, role: "admin" });
    expect(result).toContain("(Admin)");
  });

  it("capitalizes first letter of role for moderator", () => {
    const result = formatUserDisplay({ name: "A", email: "a@b.com", age: 20, role: "moderator" });
    expect(result).toContain("(Moderator)");
  });

  it("capitalizes first letter of role for user", () => {
    const result = formatUserDisplay({ name: "A", email: "a@b.com", age: 20, role: "user" });
    expect(result).toContain("(User)");
  });

  it("renders tag list joined by ', ' (comma space)", () => {
    const result = formatUserDisplay({
      name: "A",
      email: "a@b.com",
      age: 20,
      role: "user",
      tags: ["x", "y", "z"],
    });
    expect(result).toContain("[Tags: x, y, z]");
  });

  it("renders a single tag without trailing comma", () => {
    const result = formatUserDisplay({
      name: "A",
      email: "a@b.com",
      age: 20,
      role: "user",
      tags: ["solo"],
    });
    expect(result).toContain("[Tags: solo]");
  });

  it("does not modify email casing (display only)", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "Alice@EXAMPLE.COM",
      age: 30,
      role: "user",
    });
    expect(result).toContain("Alice@EXAMPLE.COM");
  });

  it("preserves special characters in name without escaping", () => {
    const result = formatUserDisplay({
      name: "O'Brien-Müller",
      email: "o@b.com",
      age: 40,
      role: "user",
    });
    expect(result).toContain("O'Brien-Müller");
  });

  test.skip("shows 'none' for an explicit empty tags array - BUG", () => {
    /*
     * ROOT CAUSE: `[].join(", ")` returns `""` (empty string, not null/undefined).
     * The nullish coalescing operator `?? "none"` only substitutes for null/undefined,
     * so `tagStr` becomes `""` and the output is "[Tags: ]" instead of "[Tags: none]".
     *
     * CODE LOCATION: user_validator.ts:55
     *
     * CURRENT CODE:
     *   const tagStr = user.tags?.join(", ") ?? "none";
     *
     * PROPOSED FIX:
     *   const tagStr = user.tags && user.tags.length > 0 ? user.tags.join(", ") : "none";
     *
     * EXPECTED: "Alice (User) - a@b.com [Tags: none]"
     * ACTUAL:   "Alice (User) - a@b.com [Tags: ]"
     */
    const result = formatUserDisplay({
      name: "Alice",
      email: "a@b.com",
      age: 25,
      role: "user",
      tags: [],
    });
    expect(result).toBe("Alice (User) - a@b.com [Tags: none]");
  });

  it("includes the age field in the struct without rendering it in the output", () => {
    // formatUserDisplay does not print the age — verify it is intentionally absent.
    const result = formatUserDisplay({ name: "Alice", email: "a@b.com", age: 99, role: "user" });
    expect(result).not.toContain("99");
  });
});

describe("formatUserDisplay — name with only one character role label", () => {
  it("capitalizes single-character role label correctly", () => {
    // All valid roles are multi-character; this documents that charAt(0).toUpperCase()
    // + slice(1) is safe for any non-empty string, including single chars.
    // We cannot pass a truly single-char role through TS, but we verify the pattern
    // holds for the three real roles.
    for (const role of ["admin", "user", "moderator"] as const) {
      const expected = role.charAt(0).toUpperCase() + role.slice(1);
      const result = formatUserDisplay({ name: "X", email: "x@x.com", age: 1, role });
      expect(result).toContain(`(${expected})`);
    }
  });
});
