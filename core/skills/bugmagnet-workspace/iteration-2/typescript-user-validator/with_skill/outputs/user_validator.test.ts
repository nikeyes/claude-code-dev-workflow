import { describe, test, expect } from "vitest";
import { validateUser, normalizeEmail, formatUserDisplay } from "./user_validator";

// ---------------------------------------------------------------------------
// validateUser
// ---------------------------------------------------------------------------

describe("validateUser", () => {
  // --- Happy path ---

  test("returns valid for a complete correct input", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid when tags are provided", () => {
    const result = validateUser({
      name: "Bob",
      email: "bob@example.com",
      age: 25,
      role: "admin",
      tags: ["staff", "beta"],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid when tags are omitted", () => {
    const result = validateUser({
      name: "Carol",
      email: "carol@example.com",
      age: 25,
      role: "moderator",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for all three valid roles", () => {
    for (const role of ["admin", "user", "moderator"] as const) {
      const result = validateUser({
        name: "Dan",
        email: "dan@example.com",
        age: 40,
        role,
      });
      expect(result.valid).toBe(true);
      expect(result.errors).toEqual([]);
    }
  });

  // --- Name validation ---

  test("returns error when name is empty string", () => {
    const result = validateUser({
      name: "",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("returns error when name is whitespace only", () => {
    const result = validateUser({
      name: "   ",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("returns error when name is tab and newline whitespace only", () => {
    const result = validateUser({
      name: "\t\n",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("returns valid for name at exactly 100 characters", () => {
    const name = "a".repeat(100);
    const result = validateUser({
      name,
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns error for name at 101 characters", () => {
    const name = "a".repeat(101);
    const result = validateUser({
      name,
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  test("returns valid for single character name", () => {
    const result = validateUser({
      name: "X",
      email: "x@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for name with apostrophe and hyphen", () => {
    const result = validateUser({
      name: "O'Brien-Smith",
      email: "obrien@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for name with accented characters", () => {
    const result = validateUser({
      name: "Ångström",
      email: "a@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- Email validation ---

  test("returns error when email is empty string", () => {
    const result = validateUser({
      name: "Alice",
      email: "",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("returns error when email has no @ symbol", () => {
    const result = validateUser({
      name: "Alice",
      email: "notanemail",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("returns valid for email with subdomain", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@mail.example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for email with plus addressing", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice+filter@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("passes validation for email with only @ present (weak check allows it)", () => {
    // The implementation only checks for presence of "@"; "@" alone passes.
    // This test documents the current permissive behavior.
    const result = validateUser({
      name: "Alice",
      email: "@",
      age: 30,
      role: "user",
    });
    // email.includes("@") is true, so no error is raised
    expect(result.errors).not.toContain("Valid email is required");
  });

  // --- Age validation ---

  test("returns valid for age at lower boundary 0", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 0,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for age at upper boundary 150", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 150,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for age 1 (just above lower boundary)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 1,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for age 149 (just below upper boundary)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 149,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns error for negative age", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: -1,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns error for age exceeding 150", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 151,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test.skip("returns error for NaN age - BUG", () => {
    /*
     * BUG: NaN bypasses the age range check and is accepted as a valid age.
     *
     * ROOT CAUSE: The condition `input.age < 0 || input.age > 150` evaluates
     * to false when input.age is NaN, because any numeric comparison involving
     * NaN returns false in JavaScript/TypeScript. As a result NaN silently
     * passes the range guard and is treated as a valid age value.
     *
     * CODE LOCATION: user_validator.ts:29
     *
     * CURRENT CODE:
     *   if (input.age < 0 || input.age > 150) {
     *     errors.push("Age must be between 0 and 150");
     *   }
     *
     * PROPOSED FIX:
     *   if (!Number.isFinite(input.age) || input.age < 0 || input.age > 150) {
     *     errors.push("Age must be between 0 and 150");
     *   }
     *
     * EXPECTED: valid = false, errors = ["Age must be between 0 and 150"]
     * ACTUAL:   valid = true, errors = [] (NaN passes the guard)
     */
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: NaN,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns error for Infinity age", () => {
    // Infinity > 150 is true, so Infinity IS correctly caught by the guard.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: Infinity,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns error for -Infinity age", () => {
    // -Infinity < 0 is true, so -Infinity IS correctly caught by the guard.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: -Infinity,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns valid for fractional age (no integer check in implementation)", () => {
    // The implementation has no integer check; 30.5 passes the range check.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30.5,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- Role validation ---

  test("returns error for an unrecognized role", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "superadmin" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  test("returns error for role with different casing", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "Admin" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  test("returns error for empty string role", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  // --- Tags validation ---

  test("returns valid for a tag at exactly 50 characters", () => {
    const tag = "a".repeat(50);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [tag],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns error for a tag with 51 characters", () => {
    const longTag = "a".repeat(51);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [longTag],
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain(`Tag "${longTag}" exceeds 50 characters`);
  });

  test("returns an error for each oversized tag individually", () => {
    const tag1 = "b".repeat(51);
    const tag2 = "c".repeat(52);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [tag1, tag2],
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain(`Tag "${tag1}" exceeds 50 characters`);
    expect(result.errors).toContain(`Tag "${tag2}" exceeds 50 characters`);
    expect(result.errors).toHaveLength(2);
  });

  test("returns valid for empty tags array", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for tag that is an empty string", () => {
    // An empty-string tag has length 0, passing the > 50 guard.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [""],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for 100 tags all under 50 characters", () => {
    const tags = Array.from({ length: 100 }, (_, i) => `tag${i}`);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags,
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- Multiple errors ---

  test("returns all errors when multiple fields are invalid", () => {
    const result = validateUser({
      name: "",
      email: "notanemail",
      age: -5,
      role: "god" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain("Valid email is required");
    expect(result.errors).toContain("Age must be between 0 and 150");
    expect(result.errors).toContain("Invalid role");
    expect(result.errors).toHaveLength(4);
  });
});

// ---------------------------------------------------------------------------
// normalizeEmail
// ---------------------------------------------------------------------------

describe("normalizeEmail", () => {
  test("lowercases local part and domain", () => {
    expect(normalizeEmail("Alice@Example.COM")).toBe("alice@example.com");
  });

  test("preserves already lowercase email unchanged", () => {
    expect(normalizeEmail("bob@example.com")).toBe("bob@example.com");
  });

  test("lowercases uppercase-only local part", () => {
    expect(normalizeEmail("CAROL@example.com")).toBe("carol@example.com");
  });

  test("lowercases uppercase-only domain", () => {
    expect(normalizeEmail("dave@EXAMPLE.COM")).toBe("dave@example.com");
  });

  test("handles email with subdomain in domain part", () => {
    expect(normalizeEmail("Eve@Mail.EXAMPLE.COM")).toBe("eve@mail.example.com");
  });

  test("handles email with plus addressing in local part", () => {
    expect(normalizeEmail("Frank+Filter@Example.com")).toBe(
      "frank+filter@example.com"
    );
  });

  test("handles email with dots in local part", () => {
    expect(normalizeEmail("First.Last@Example.COM")).toBe(
      "first.last@example.com"
    );
  });

  test("handles email with numbers and mixed case", () => {
    expect(normalizeEmail("User.Name123@Sub.Domain.IO")).toBe(
      "user.name123@sub.domain.io"
    );
  });

  test.skip("does not crash when email has no @ symbol - BUG", () => {
    /*
     * BUG: normalizeEmail throws a TypeError when the input contains no "@".
     *
     * ROOT CAUSE: `email.split("@")` returns a single-element array when
     * there is no "@" character. Destructuring assigns `domain = undefined`.
     * Calling `undefined.toLowerCase()` then throws:
     *   TypeError: Cannot read properties of undefined (reading 'toLowerCase')
     *
     * CODE LOCATION: user_validator.ts:49-51
     *
     * CURRENT CODE:
     *   const [local, domain] = email.split("@");
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     *
     * PROPOSED FIX (throw a descriptive error):
     *   if (!email.includes("@")) {
     *     throw new Error(`Invalid email address: "${email}" contains no @ symbol`);
     *   }
     *   const [local, domain] = email.split("@");
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     *
     * MINIMAL REPRODUCTION: normalizeEmail("notanemail")
     *
     * EXPECTED: throws a meaningful Error (not a raw TypeError about undefined)
     * ACTUAL:   TypeError: Cannot read properties of undefined (reading 'toLowerCase')
     */
    expect(() => normalizeEmail("notanemail")).not.toThrow(TypeError);
  });

  test.skip("does not crash when email is empty string - BUG", () => {
    /*
     * BUG: normalizeEmail throws a TypeError when called with an empty string.
     *
     * ROOT CAUSE: Same as the no-@ bug above. `"".split("@")` returns `[""]`,
     * so `domain` is `undefined` and `domain.toLowerCase()` throws a TypeError.
     *
     * CODE LOCATION: user_validator.ts:49-51  (same as no-@ bug)
     *
     * MINIMAL REPRODUCTION: normalizeEmail("")
     *
     * EXPECTED: throws a meaningful Error or returns ""
     * ACTUAL:   TypeError: Cannot read properties of undefined (reading 'toLowerCase')
     */
    expect(() => normalizeEmail("")).not.toThrow(TypeError);
  });

  test.skip("preserves the full address when email contains multiple @ symbols - BUG", () => {
    /*
     * BUG: When the email contains multiple "@" characters (e.g. "a@b@c"),
     * `email.split("@")` returns ["a", "b", "c"]. Destructuring captures
     * only the first two elements: local = "a", domain = "b". The third
     * segment "c" is silently discarded, producing "a@b" instead of a
     * correctly normalized "a@b@c".
     *
     * ROOT CAUSE: `split("@")` with multiple delimiters returns more than
     * two segments; the two-element destructure silently drops the rest.
     *
     * CODE LOCATION: user_validator.ts:49
     *
     * CURRENT CODE:
     *   const [local, domain] = email.split("@");
     *
     * PROPOSED FIX:
     *   const atIndex = email.indexOf("@");
     *   const local = email.slice(0, atIndex);
     *   const domain = email.slice(atIndex + 1);
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     *
     * MINIMAL REPRODUCTION: normalizeEmail("A@B@C")
     *
     * EXPECTED: "a@b@c"
     * ACTUAL:   "a@b"  (third segment dropped)
     */
    expect(normalizeEmail("A@B@C")).toBe("a@b@c");
  });
});

// ---------------------------------------------------------------------------
// formatUserDisplay
// ---------------------------------------------------------------------------

describe("formatUserDisplay", () => {
  test("formats user with tags correctly", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["staff", "beta"],
    });
    expect(result).toBe("Alice (User) - alice@example.com [Tags: staff, beta]");
  });

  test("formats user without tags field showing 'none'", () => {
    const result = formatUserDisplay({
      name: "Bob",
      email: "bob@example.com",
      age: 25,
      role: "admin",
    });
    expect(result).toBe("Bob (Admin) - bob@example.com [Tags: none]");
  });

  test("capitalizes role label for admin", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "admin",
    });
    expect(result).toBe("Alice (Admin) - alice@example.com [Tags: none]");
  });

  test("capitalizes role label for moderator", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "moderator",
    });
    expect(result).toBe("Alice (Moderator) - alice@example.com [Tags: none]");
  });

  test("capitalizes role label for user", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result).toBe("Alice (User) - alice@example.com [Tags: none]");
  });

  test("formats user with a single tag", () => {
    const result = formatUserDisplay({
      name: "Carol",
      email: "carol@example.com",
      age: 28,
      role: "moderator",
      tags: ["vip"],
    });
    expect(result).toBe("Carol (Moderator) - carol@example.com [Tags: vip]");
  });

  test("formats user with multiple tags joined by comma and space", () => {
    const result = formatUserDisplay({
      name: "Dave",
      email: "dave@example.com",
      age: 40,
      role: "admin",
      tags: ["alpha", "beta", "gamma"],
    });
    expect(result).toBe(
      "Dave (Admin) - dave@example.com [Tags: alpha, beta, gamma]"
    );
  });

  test("formats user name with spaces correctly", () => {
    const result = formatUserDisplay({
      name: "Jane Doe",
      email: "jane@example.com",
      age: 35,
      role: "user",
    });
    expect(result).toBe("Jane Doe (User) - jane@example.com [Tags: none]");
  });

  test.skip("shows 'none' for empty tags array instead of blank bracket - BUG", () => {
    /*
     * BUG: When `tags` is an empty array `[]`, formatUserDisplay renders
     * "[Tags: ]" (a blank inside the brackets) instead of "[Tags: none]".
     *
     * ROOT CAUSE: `user.tags?.join(", ")` returns `""` (an empty string, not
     * null or undefined) for an empty array. The nullish coalescing operator
     * `?? "none"` only substitutes null/undefined — it does not treat an
     * empty string as a missing value. So `tagStr` becomes `""` and the
     * output is "[Tags: ]".
     *
     * CODE LOCATION: user_validator.ts:55
     *
     * CURRENT CODE:
     *   const tagStr = user.tags?.join(", ") ?? "none";
     *
     * PROPOSED FIX:
     *   const tagStr =
     *     user.tags && user.tags.length > 0 ? user.tags.join(", ") : "none";
     *
     * MINIMAL REPRODUCTION: formatUserDisplay({ ..., tags: [] })
     *
     * EXPECTED: "Alice (User) - alice@example.com [Tags: none]"
     * ACTUAL:   "Alice (User) - alice@example.com [Tags: ]"
     */
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [],
    });
    expect(result).toBe("Alice (User) - alice@example.com [Tags: none]");
  });

  test("does not normalize email casing (display only)", () => {
    // formatUserDisplay is a display formatter, not a normalizer.
    const result = formatUserDisplay({
      name: "Alice",
      email: "Alice@EXAMPLE.COM",
      age: 30,
      role: "user",
    });
    expect(result).toBe("Alice (User) - Alice@EXAMPLE.COM [Tags: none]");
  });

  test("preserves special characters in name", () => {
    const result = formatUserDisplay({
      name: "O'Brien-Müller",
      email: "o@example.com",
      age: 30,
      role: "user",
    });
    expect(result).toBe("O'Brien-Müller (User) - o@example.com [Tags: none]");
  });
});

// ---------------------------------------------------------------------------
// bugmagnet session 2026-04-26 — advanced edge case exploration
// ---------------------------------------------------------------------------

describe("bugmagnet session 2026-04-26", () => {
  // --- validateUser: numeric edge cases for age ---

  test("returns valid for age -0 (negative zero equals 0 in JS)", () => {
    // -0 === 0 in JS, and -0 < 0 is false, so -0 passes the range check.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: -0,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns error for very large age (Number.MAX_SAFE_INTEGER)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: Number.MAX_SAFE_INTEGER,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  // --- validateUser: security patterns in name ---

  test("returns valid for name containing SQL injection pattern", () => {
    // The validator only checks length/emptiness, not content.
    const result = validateUser({
      name: "Robert'); DROP TABLE users;--",
      email: "bobby@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for name containing XSS pattern", () => {
    const result = validateUser({
      name: "<script>alert(1)</script>",
      email: "xss@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- validateUser: reserved / unusual names ---

  test("returns valid for name 'Null'", () => {
    const result = validateUser({
      name: "Null",
      email: "null@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for name 'undefined'", () => {
    const result = validateUser({
      name: "undefined",
      email: "u@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- validateUser: unicode / international names ---

  test("returns valid for Chinese characters in name", () => {
    const result = validateUser({
      name: "王芳",
      email: "wangfang@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns valid for Arabic script in name", () => {
    const result = validateUser({
      name: "محمد",
      email: "m@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- validateUser: name length off-by-one cluster ---

  test("returns valid for name with 99 characters", () => {
    const name = "a".repeat(99);
    const result = validateUser({
      name,
      email: "a@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test("returns error for name with 102 characters", () => {
    const name = "a".repeat(102);
    const result = validateUser({
      name,
      email: "a@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  // --- validateUser: duplicate / related parameter values ---

  test("returns valid when name and email local-part are identical strings", () => {
    const result = validateUser({
      name: "alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  // --- normalizeEmail: edge cases ---

  test("normalizeEmail handles local part with numbers", () => {
    expect(normalizeEmail("User42@Example.com")).toBe("user42@example.com");
  });

  test("normalizeEmail handles already-lowercase input without mutation", () => {
    const input = "test@domain.org";
    expect(normalizeEmail(input)).toBe("test@domain.org");
  });

  // --- formatUserDisplay: tag edge cases ---

  test("formatUserDisplay renders tag containing special characters", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["beta-tester", "group:A"],
    });
    expect(result).toBe(
      "Alice (User) - alice@example.com [Tags: beta-tester, group:A]"
    );
  });

  test("formatUserDisplay renders tag that is a single character", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["x"],
    });
    expect(result).toBe("Alice (User) - alice@example.com [Tags: x]");
  });

  // --- validateUser: runtime type coercion edge case ---

  test("validateUser treats string-coerced age '30' as passing range check", () => {
    // TypeScript prevents this at compile time. At runtime, "30" < 0 and
    // "30" > 150 are both false (string-to-number coercion in comparison),
    // so a string age silently passes. Documents current permissive behavior.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: "30" as unknown as number,
      role: "user",
    });
    expect(result.valid).toBe(true);
  });
});
