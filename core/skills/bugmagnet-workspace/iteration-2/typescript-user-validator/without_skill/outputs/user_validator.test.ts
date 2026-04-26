import { describe, test, expect } from "vitest";
import { validateUser, normalizeEmail, formatUserDisplay } from "./user_validator";

describe("validateUser", () => {
  test("returns valid for correct input", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test("returns error when name is empty", () => {
    const result = validateUser({
      name: "",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  // --- Name validation ---

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

  test("returns error when name exceeds 100 characters", () => {
    const result = validateUser({
      name: "A".repeat(101),
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  test("accepts name of exactly 100 characters", () => {
    const result = validateUser({
      name: "A".repeat(100),
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.errors).not.toContain("Name must be 100 characters or less");
  });

  test("accepts name of 1 character", () => {
    const result = validateUser({
      name: "A",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.errors).not.toContain("Name is required");
  });

  // --- Email validation ---

  test("returns error when email has no @ sign", () => {
    const result = validateUser({
      name: "Alice",
      email: "aliceexample.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

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

  // BUG: email "@" alone passes validation (has @ but no local part or domain)
  test("returns error when email is just @ with no local part or domain", () => {
    const result = validateUser({
      name: "Alice",
      email: "@",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  // BUG: email "@domain.com" passes validation (has @ but no local part)
  test("returns error when email has no local part before @", () => {
    const result = validateUser({
      name: "Alice",
      email: "@domain.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  // BUG: email "user@" passes validation (has @ but no domain)
  test("returns error when email has no domain after @", () => {
    const result = validateUser({
      name: "Alice",
      email: "user@",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  // --- Age validation ---

  test("returns error when age is negative", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: -1,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("returns error when age exceeds 150", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 151,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("accepts age of exactly 0", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 0,
      role: "user",
    });
    expect(result.errors).not.toContain("Age must be between 0 and 150");
  });

  test("accepts age of exactly 150", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 150,
      role: "user",
    });
    expect(result.errors).not.toContain("Age must be between 0 and 150");
  });

  // BUG: NaN passes age validation silently (NaN < 0 and NaN > 150 are both false)
  test("returns error when age is NaN", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: NaN,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  // BUG: fractional ages like 25.7 pass validation (no integer enforcement)
  test("returns error when age is a non-integer (fractional)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 25.7,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  // --- Role validation ---

  test("accepts role admin", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "admin",
    });
    expect(result.errors).not.toContain("Invalid role");
  });

  test("accepts role moderator", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "moderator",
    });
    expect(result.errors).not.toContain("Invalid role");
  });

  // TypeScript's type system prevents invalid roles at compile time, but
  // at runtime (e.g. from API input) an invalid role string could arrive.
  test("returns error when role is invalid at runtime", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "superuser" as "admin",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  // --- Tags validation ---

  test("accepts valid tags within 50 characters", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["typescript", "frontend"],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test("accepts tag of exactly 50 characters", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["A".repeat(50)],
    });
    expect(result.errors).not.toContain(
      `Tag "${"A".repeat(50)}" exceeds 50 characters`
    );
  });

  test("returns error when a tag exceeds 50 characters", () => {
    const longTag = "A".repeat(51);
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

  test("returns errors for each tag that exceeds 50 characters", () => {
    const longTag1 = "A".repeat(51);
    const longTag2 = "B".repeat(60);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [longTag1, "ok-tag", longTag2],
    });
    expect(result.errors).toContain(`Tag "${longTag1}" exceeds 50 characters`);
    expect(result.errors).toContain(`Tag "${longTag2}" exceeds 50 characters`);
  });

  test("accepts no tags (undefined)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
  });

  test("accepts empty tags array", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [],
    });
    expect(result.valid).toBe(true);
  });

  // --- Multiple errors ---

  test("accumulates multiple errors in a single call", () => {
    const result = validateUser({
      name: "",
      email: "not-an-email",
      age: -5,
      role: "hacker" as "admin",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain("Valid email is required");
    expect(result.errors).toContain("Age must be between 0 and 150");
    expect(result.errors).toContain("Invalid role");
  });
});

describe("normalizeEmail", () => {
  test("lowercases email", () => {
    expect(normalizeEmail("Alice@Example.COM")).toBe("alice@example.com");
  });

  test("lowercases local part only (already lowercase domain)", () => {
    expect(normalizeEmail("ALICE@example.com")).toBe("alice@example.com");
  });

  test("lowercases domain only (already lowercase local part)", () => {
    expect(normalizeEmail("alice@EXAMPLE.COM")).toBe("alice@example.com");
  });

  test("leaves already lowercase email unchanged", () => {
    expect(normalizeEmail("alice@example.com")).toBe("alice@example.com");
  });

  // BUG: normalizeEmail throws TypeError when email has no @ sign
  // domain = undefined, and undefined.toLowerCase() throws
  test("throws when email has no @ sign", () => {
    expect(() => normalizeEmail("noemail")).toThrow();
  });

  // BUG: normalizeEmail silently loses everything after the second @
  // "a@b@c.com".split("@") => ["a", "b", "c.com"], destructuring gives local="a", domain="b"
  // result is "a@b" — the ".com" part of the domain is dropped
  test("handles email with multiple @ signs correctly", () => {
    // Currently produces "a@b" — losing "c.com" — this is a bug
    const result = normalizeEmail("a@b@c.com");
    expect(result).toBe("a@b@c.com"); // expected full preservation or error
  });
});

describe("formatUserDisplay", () => {
  test("formats user with role capitalized", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result).toBe("Alice (User) - alice@example.com [Tags: none]");
  });

  test("formats admin role with capital A", () => {
    const result = formatUserDisplay({
      name: "Bob",
      email: "bob@example.com",
      age: 25,
      role: "admin",
    });
    expect(result).toBe("Bob (Admin) - bob@example.com [Tags: none]");
  });

  test("formats moderator role with capital M", () => {
    const result = formatUserDisplay({
      name: "Carol",
      email: "carol@example.com",
      age: 40,
      role: "moderator",
    });
    expect(result).toBe("Carol (Moderator) - carol@example.com [Tags: none]");
  });

  test("formats user with tags joined by comma and space", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["typescript", "frontend"],
    });
    expect(result).toBe(
      "Alice (User) - alice@example.com [Tags: typescript, frontend]"
    );
  });

  test("shows 'none' when tags is undefined", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: undefined,
    });
    expect(result).toContain("[Tags: none]");
  });

  // BUG: empty tags array produces [Tags: ] instead of [Tags: none]
  // user.tags?.join(", ") returns "" for [], and "" ?? "none" is "" (not "none")
  // because ?? only replaces null/undefined, not empty string
  test("shows 'none' when tags is an empty array", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [],
    });
    expect(result).toContain("[Tags: none]");
  });

  test("formats single tag without trailing comma", () => {
    const result = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["solo"],
    });
    expect(result).toContain("[Tags: solo]");
  });
});
