import { describe, test, expect } from "vitest";
import {
  validateUser,
  normalizeEmail,
  formatUserDisplay,
  type UserInput,
} from "./user_validator";

const validUser: UserInput = {
  name: "Alice",
  email: "alice@example.com",
  age: 30,
  role: "user",
};

// =============================================================================
// Phase 3: Core functionality gaps (High Priority)
// =============================================================================

describe("validateUser", () => {
  test("returns valid for correct input", () => {
    const result = validateUser(validUser);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  // --- Name validation ---
  test("returns error when name is empty string", () => {
    const result = validateUser({ ...validUser, name: "" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("returns error when name is whitespace only", () => {
    const result = validateUser({ ...validUser, name: "   " });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("returns valid for single character name", () => {
    const result = validateUser({ ...validUser, name: "A" });
    expect(result.valid).toBe(true);
  });

  test("returns error when name exceeds 100 characters", () => {
    const result = validateUser({ ...validUser, name: "A".repeat(101) });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  test("returns valid for name with exactly 100 characters", () => {
    const result = validateUser({ ...validUser, name: "A".repeat(100) });
    expect(result.valid).toBe(true);
  });

  test("returns valid for name with accents and special characters", () => {
    const result = validateUser({ ...validUser, name: "José García-López" });
    expect(result.valid).toBe(true);
  });

  test("returns valid for name with apostrophe", () => {
    const result = validateUser({ ...validUser, name: "O'Brien" });
    expect(result.valid).toBe(true);
  });

  test("returns valid for name with unicode characters", () => {
    const result = validateUser({ ...validUser, name: "田中太郎" });
    expect(result.valid).toBe(true);
  });

  // --- Email validation ---
  test("returns error when email is empty", () => {
    const result = validateUser({ ...validUser, email: "" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("returns error when email has no @ sign", () => {
    const result = validateUser({ ...validUser, email: "nodomain" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("returns valid for email with only @ and surrounding text", () => {
    // Current implementation only checks for @ presence
    const result = validateUser({ ...validUser, email: "user@" });
    expect(result.valid).toBe(true); // Documents weak validation
  });

  test("returns valid for email with multiple @ signs", () => {
    // Current implementation only checks includes("@")
    const result = validateUser({ ...validUser, email: "a@b@c" });
    expect(result.valid).toBe(true); // Documents weak validation
  });

  test("returns valid for email with subdomain", () => {
    const result = validateUser({
      ...validUser,
      email: "user@mail.example.com",
    });
    expect(result.valid).toBe(true);
  });

  test("returns valid for email with plus addressing", () => {
    const result = validateUser({
      ...validUser,
      email: "user+tag@example.com",
    });
    expect(result.valid).toBe(true);
  });

  // --- Age validation ---
  test("returns error when age is negative", () => {
    const result = validateUser({ ...validUser, age: -1 });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns error when age exceeds 150", () => {
    const result = validateUser({ ...validUser, age: 151 });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns valid for age 0", () => {
    const result = validateUser({ ...validUser, age: 0 });
    expect(result.valid).toBe(true);
  });

  test("returns valid for age 150", () => {
    const result = validateUser({ ...validUser, age: 150 });
    expect(result.valid).toBe(true);
  });

  test.skip("returns error when age is NaN - BUG", () => {
    /*
     * BUG: NaN age bypasses range check
     *
     * ROOT CAUSE: NaN < 0 and NaN > 150 are both false in JavaScript,
     * so the condition `input.age < 0 || input.age > 150` never triggers.
     *
     * CODE LOCATION: user_validator.ts:30
     * CURRENT CODE:
     *   if (input.age < 0 || input.age > 150)
     * PROPOSED FIX:
     *   if (Number.isNaN(input.age) || input.age < 0 || input.age > 150)
     *
     * EXPECTED: { valid: false, errors: ["Age must be between 0 and 150"] }
     * ACTUAL: { valid: true, errors: [] }
     */
    const result = validateUser({ ...validUser, age: NaN });
    expect(result.valid).toBe(false);
  });

  test.skip("returns error when age is Infinity - BUG", () => {
    /*
     * BUG: Infinity age bypasses upper range check
     *
     * ROOT CAUSE: Infinity > 150 is true, so this actually works.
     * But -Infinity < 0 is true too. The real issue is with NaN.
     * Keeping this for completeness — Infinity is not a valid age.
     */
    const result = validateUser({ ...validUser, age: Infinity });
    expect(result.valid).toBe(false);
  });

  // --- Role validation ---
  test("returns valid for admin role", () => {
    const result = validateUser({ ...validUser, role: "admin" });
    expect(result.valid).toBe(true);
  });

  test("returns valid for moderator role", () => {
    const result = validateUser({ ...validUser, role: "moderator" });
    expect(result.valid).toBe(true);
  });

  test("returns error for invalid role", () => {
    const result = validateUser({
      ...validUser,
      role: "superadmin" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  // --- Tags validation ---
  test("returns valid when tags is undefined", () => {
    const { tags, ...noTags } = validUser;
    const result = validateUser(noTags as UserInput);
    expect(result.valid).toBe(true);
  });

  test("returns valid for empty tags array", () => {
    const result = validateUser({ ...validUser, tags: [] });
    expect(result.valid).toBe(true);
  });

  test("returns valid for tags within length limit", () => {
    const result = validateUser({ ...validUser, tags: ["tag1", "tag2"] });
    expect(result.valid).toBe(true);
  });

  test("returns error when tag exceeds 50 characters", () => {
    const longTag = "a".repeat(51);
    const result = validateUser({ ...validUser, tags: [longTag] });
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain("exceeds 50 characters");
  });

  test("returns valid for tag with exactly 50 characters", () => {
    const result = validateUser({ ...validUser, tags: ["a".repeat(50)] });
    expect(result.valid).toBe(true);
  });

  // --- Multiple errors ---
  test("returns multiple errors for multiple invalid fields", () => {
    const result = validateUser({
      name: "",
      email: "invalid",
      age: -1,
      role: "invalid" as any,
    });
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThanOrEqual(3);
  });
});

// =============================================================================
// normalizeEmail
// =============================================================================

describe("normalizeEmail", () => {
  test("returns lowercased email", () => {
    expect(normalizeEmail("Alice@Example.COM")).toBe("alice@example.com");
  });

  test("returns unchanged already-lowercase email", () => {
    expect(normalizeEmail("user@example.com")).toBe("user@example.com");
  });

  test("returns lowercased local and domain parts separately", () => {
    expect(normalizeEmail("USER@DOMAIN.COM")).toBe("user@domain.com");
  });

  test.skip("throws when email has no @ sign - BUG", () => {
    /*
     * BUG: normalizeEmail crashes on input without @
     *
     * ROOT CAUSE: email.split("@") returns ["nodomain"], so domain is
     * undefined. Calling .toLowerCase() on undefined throws TypeError.
     *
     * CODE LOCATION: user_validator.ts:50
     * CURRENT CODE:
     *   const [local, domain] = email.split("@");
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     * PROPOSED FIX:
     *   const atIndex = email.indexOf("@");
     *   if (atIndex === -1) throw new Error("Invalid email: missing @");
     *   const local = email.slice(0, atIndex);
     *   const domain = email.slice(atIndex + 1);
     *   return `${local.toLowerCase()}@${domain.toLowerCase()}`;
     *
     * EXPECTED: Error thrown or handled gracefully
     * ACTUAL: TypeError: Cannot read properties of undefined
     */
    expect(() => normalizeEmail("nodomain")).toThrow();
  });

  test("returns normalized email with plus addressing", () => {
    expect(normalizeEmail("User+Tag@Example.com")).toBe(
      "user+tag@example.com"
    );
  });
});

// =============================================================================
// formatUserDisplay
// =============================================================================

describe("formatUserDisplay", () => {
  test("returns formatted string with role capitalized", () => {
    expect(formatUserDisplay(validUser)).toBe(
      "Alice (User) - alice@example.com [Tags: none]"
    );
  });

  test("returns formatted string with tags joined", () => {
    const user = { ...validUser, tags: ["dev", "lead"] };
    expect(formatUserDisplay(user)).toBe(
      "Alice (User) - alice@example.com [Tags: dev, lead]"
    );
  });

  test("returns 'none' when tags is undefined", () => {
    expect(formatUserDisplay(validUser)).toContain("[Tags: none]");
  });

  test("returns empty tags display when tags is empty array", () => {
    // [].join(", ") returns "" which is not nullish, so ?? "none" doesn't trigger
    const user = { ...validUser, tags: [] };
    const result = formatUserDisplay(user);
    expect(result).toContain("[Tags: ]"); // Documents empty-array edge case
  });

  test("returns formatted string for admin role", () => {
    const user = { ...validUser, role: "admin" as const };
    expect(formatUserDisplay(user)).toContain("(Admin)");
  });

  test("returns formatted string for moderator role", () => {
    const user = { ...validUser, role: "moderator" as const };
    expect(formatUserDisplay(user)).toContain("(Moderator)");
  });
});

// =============================================================================
// Phase 4: Advanced Coverage — bugmagnet session
// =============================================================================

describe("bugmagnet session 2026-04-25", () => {
  test("validates name with reserved word 'Null'", () => {
    const result = validateUser({ ...validUser, name: "Null" });
    expect(result.valid).toBe(true);
  });

  test("validates name with reserved word 'undefined'", () => {
    const result = validateUser({ ...validUser, name: "undefined" });
    expect(result.valid).toBe(true);
  });

  test("validates email with SQL injection pattern", () => {
    const result = validateUser({
      ...validUser,
      email: "user@example.com'; DROP TABLE users;--",
    });
    expect(result.valid).toBe(true); // passes because it contains @
  });

  test("validates email with XSS pattern", () => {
    const result = validateUser({
      ...validUser,
      email: "sc]ript-injection@example.com",
    });
    expect(result.valid).toBe(true); // passes because it contains @
  });

  test("validates tag with empty string", () => {
    const result = validateUser({ ...validUser, tags: [""] });
    expect(result.valid).toBe(true);
  });

  test("validates multiple tags where one exceeds limit", () => {
    const result = validateUser({
      ...validUser,
      tags: ["valid", "a".repeat(51), "also-valid"],
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
  });
});
