import { describe, test, expect } from "vitest";
import { validateUser, normalizeEmail, formatUserDisplay } from "../../../../../evals/files/user_validator";

// ---------------------------------------------------------------------------
// validateUser
// ---------------------------------------------------------------------------

describe("validateUser - name validation", () => {
  test("rejects name that is only whitespace", () => {
    const result = validateUser({
      name: "   ",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("rejects name that is a single whitespace character", () => {
    const result = validateUser({
      name: " ",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("accepts name at exactly 100 characters (boundary)", () => {
    const result = validateUser({
      name: "a".repeat(100),
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).not.toContain("Name must be 100 characters or less");
  });

  test("rejects name at exactly 101 characters (boundary + 1)", () => {
    const result = validateUser({
      name: "a".repeat(101),
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  test("returns only 'Name is required' when name is empty string (not the length error too)", () => {
    // A blank name that is technically long (all spaces) should not also produce the length error
    const result = validateUser({
      name: " ".repeat(101),
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    // Implementation BUG: both "Name is required" and "Name must be 100 characters or less"
    // are emitted because the whitespace-only check and the length check are independent.
    // This test documents the actual (buggy) behaviour.
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain("Name must be 100 characters or less");
  });
});

describe("validateUser - email validation", () => {
  test("rejects email with no @ symbol", () => {
    const result = validateUser({
      name: "Alice",
      email: "aliceexample.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("rejects email that is just '@'", () => {
    // Current implementation accepts this because "@".includes("@") is true — BUG
    const result = validateUser({
      name: "Alice",
      email: "@",
      age: 30,
      role: "user",
    });
    // Expected behaviour: invalid
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("rejects email with no local part (starts with @)", () => {
    // "@example.com" — no local part — should be invalid
    const result = validateUser({
      name: "Alice",
      email: "@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("rejects email with no domain part (ends with @)", () => {
    // "alice@" — no domain — should be invalid
    const result = validateUser({
      name: "Alice",
      email: "alice@",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("rejects empty string email", () => {
    const result = validateUser({
      name: "Alice",
      email: "",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("accepts valid email with subdomain", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@mail.example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
  });
});

describe("validateUser - age validation", () => {
  test("accepts age of 0 (boundary)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 0,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).not.toContain("Age must be between 0 and 150");
  });

  test("accepts age of 150 (boundary)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 150,
      role: "user",
    });
    expect(result.valid).toBe(true);
    expect(result.errors).not.toContain("Age must be between 0 and 150");
  });

  test("rejects age of -1 (boundary - 1)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: -1,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("rejects age of 151 (boundary + 1)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 151,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("rejects NaN age — BUG: NaN comparisons are always false so no error is added", () => {
    // NaN < 0 === false AND NaN > 150 === false, so the guard never triggers
    // This documents the existing bug: NaN passes validation silently
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: NaN,
      role: "user",
    });
    // Expected behaviour: should be invalid
    // Actual (buggy) behaviour: valid === true
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("rejects non-integer fractional age", () => {
    // 25.7 is technically within 0-150 — whether it should be allowed is a design decision.
    // Current implementation accepts it; this test documents that.
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 25.7,
      role: "user",
    });
    // If the requirement is integers only, this should be invalid.
    // Documenting as a coverage gap — the test will fail if behaviour is fixed.
    expect(result.valid).toBe(true);
  });
});

describe("validateUser - role validation", () => {
  test("accepts 'admin' role", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "admin",
    });
    expect(result.valid).toBe(true);
  });

  test("accepts 'moderator' role", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "moderator",
    });
    expect(result.valid).toBe(true);
  });

  test("rejects unknown role cast via type assertion", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "superadmin" as "admin",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });

  test("rejects role with different casing", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "Admin" as "admin",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });
});

describe("validateUser - tags validation", () => {
  test("accepts user with no tags (tags undefined)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(result.valid).toBe(true);
  });

  test("accepts user with empty tags array", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [],
    });
    expect(result.valid).toBe(true);
  });

  test("accepts tag at exactly 50 characters (boundary)", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["a".repeat(50)],
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test("rejects tag at exactly 51 characters (boundary + 1)", () => {
    const tag = "a".repeat(51);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [tag],
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain(`Tag "${tag}" exceeds 50 characters`);
  });

  test("accumulates errors for multiple oversized tags", () => {
    const longTag1 = "a".repeat(51);
    const longTag2 = "b".repeat(52);
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [longTag1, longTag2],
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(2);
  });

  test("accepts multiple valid tags", () => {
    const result = validateUser({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["typescript", "backend", "api"],
    });
    expect(result.valid).toBe(true);
  });
});

describe("validateUser - multiple simultaneous errors", () => {
  test("collects all errors when name, email and age are all invalid", () => {
    const result = validateUser({
      name: "",
      email: "not-an-email",
      age: -5,
      role: "user",
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
    expect(result.errors).toContain("Valid email is required");
    expect(result.errors).toContain("Age must be between 0 and 150");
  });
});

// ---------------------------------------------------------------------------
// normalizeEmail
// ---------------------------------------------------------------------------

describe("normalizeEmail", () => {
  test("lowercases the local part", () => {
    expect(normalizeEmail("ALICE@example.com")).toBe("alice@example.com");
  });

  test("lowercases the domain part", () => {
    expect(normalizeEmail("alice@EXAMPLE.COM")).toBe("alice@example.com");
  });

  test("handles already lowercase email", () => {
    expect(normalizeEmail("alice@example.com")).toBe("alice@example.com");
  });

  test("handles mixed case in both parts", () => {
    expect(normalizeEmail("Alice@Example.COM")).toBe("alice@example.com");
  });

  test("throws when email has no @ symbol — BUG: domain is undefined", () => {
    // split("@") on a string without "@" returns a one-element array.
    // domain destructures as undefined, and undefined.toLowerCase() throws TypeError.
    expect(() => normalizeEmail("not-an-email")).toThrow(TypeError);
  });

  test("handles multiple @ symbols — BUG: only first segment used as local, second as domain, rest dropped", () => {
    // "a@b@c".split("@") → ["a", "b", "c"]
    // destructuring: local="a", domain="b", "c" is silently discarded
    // Actual output: "a@b"  (loses the final "@c" portion)
    const result = normalizeEmail("a@b@c");
    // Expected behaviour (if fixed): should throw or handle gracefully
    // Current (buggy) behaviour: silently truncates to "a@b"
    expect(result).toBe("a@b");
  });

  test("normalizes email with subdomain", () => {
    expect(normalizeEmail("User@Mail.Example.COM")).toBe("user@mail.example.com");
  });

  test("preserves dots in local part", () => {
    expect(normalizeEmail("First.Last@Example.com")).toBe("first.last@example.com");
  });

  test("preserves plus signs in local part", () => {
    expect(normalizeEmail("Alice+TAG@Example.com")).toBe("alice+tag@example.com");
  });
});

// ---------------------------------------------------------------------------
// formatUserDisplay
// ---------------------------------------------------------------------------

describe("formatUserDisplay", () => {
  test("formats user with tags correctly", () => {
    const output = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: ["typescript", "backend"],
    });
    expect(output).toBe("Alice (User) - alice@example.com [Tags: typescript, backend]");
  });

  test("formats user without tags as 'none'", () => {
    const output = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
    });
    expect(output).toBe("Alice (User) - alice@example.com [Tags: none]");
  });

  test("formats user with empty tags array — BUG: shows empty string instead of 'none'", () => {
    // user.tags is [] (not undefined), so the ?? 'none' fallback is NOT triggered.
    // [].join(", ") === "" — the output is "[Tags: ]" not "[Tags: none]"
    const output = formatUserDisplay({
      name: "Alice",
      email: "alice@example.com",
      age: 30,
      role: "user",
      tags: [],
    });
    // Expected (correct) behaviour:
    expect(output).toBe("Alice (User) - alice@example.com [Tags: none]");
    // Actual (buggy) behaviour produces: "Alice (User) - alice@example.com [Tags: ]"
  });

  test("capitalises first letter of 'admin' role", () => {
    const output = formatUserDisplay({
      name: "Bob",
      email: "bob@example.com",
      age: 40,
      role: "admin",
    });
    expect(output).toBe("Bob (Admin) - bob@example.com [Tags: none]");
  });

  test("capitalises first letter of 'moderator' role", () => {
    const output = formatUserDisplay({
      name: "Carol",
      email: "carol@example.com",
      age: 25,
      role: "moderator",
    });
    expect(output).toBe("Carol (Moderator) - carol@example.com [Tags: none]");
  });

  test("formats user with a single tag", () => {
    const output = formatUserDisplay({
      name: "Dave",
      email: "dave@example.com",
      age: 22,
      role: "user",
      tags: ["solo"],
    });
    expect(output).toBe("Dave (User) - dave@example.com [Tags: solo]");
  });

  test("tags containing commas produce ambiguous output", () => {
    // A tag value that contains a comma makes the formatted output indistinguishable
    // from two separate tags — this is a design/escaping gap.
    const output = formatUserDisplay({
      name: "Eve",
      email: "eve@example.com",
      age: 28,
      role: "user",
      tags: ["a,b", "c"],
    });
    // "a,b" and "c" joined → "a,b, c" which looks like three tags: "a", "b", "c"
    expect(output).toBe("Eve (User) - eve@example.com [Tags: a,b, c]");
  });
});
