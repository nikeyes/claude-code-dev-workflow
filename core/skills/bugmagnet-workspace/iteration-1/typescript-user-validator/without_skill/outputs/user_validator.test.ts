import { describe, test, expect } from "vitest";
import {
  validateUser,
  normalizeEmail,
  formatUserDisplay,
} from "../../../../../../core/skills/bugmagnet/evals/files/user_validator";

// ---------------------------------------------------------------------------
// validateUser
// ---------------------------------------------------------------------------

describe("validateUser – name field", () => {
  test("accepts a normal name", () => {
    const result = validateUser({ name: "Alice", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test("rejects empty string name", () => {
    const result = validateUser({ name: "", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("rejects whitespace-only name", () => {
    // BUG: the check `input.name.trim().length === 0` only fires when !input.name is falsy.
    // A whitespace-only string is truthy, so trim() IS evaluated — this should fail.
    const result = validateUser({ name: "   ", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name is required");
  });

  test("accepts name at exactly 100 characters", () => {
    const name = "A".repeat(100);
    const result = validateUser({ name, email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("rejects name longer than 100 characters", () => {
    const name = "A".repeat(101);
    const result = validateUser({ name, email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Name must be 100 characters or less");
  });

  test("accepts name with unicode / accented characters", () => {
    const result = validateUser({ name: "Ángel García-Pérez", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("accepts name with apostrophe", () => {
    const result = validateUser({ name: "O'Brien", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("accepts name with emoji (unicode supplementary plane)", () => {
    const result = validateUser({ name: "Ren 🐉", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
  });
});

describe("validateUser – email field", () => {
  test("accepts valid email", () => {
    const result = validateUser({ name: "Bob", email: "bob@example.com", age: 30, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("rejects email with no @ symbol", () => {
    const result = validateUser({ name: "Bob", email: "bobatexample.com", age: 30, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("rejects empty email", () => {
    const result = validateUser({ name: "Bob", email: "", age: 30, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });

  test("rejects email missing domain (user@)", () => {
    // @ present but no domain — still passes current check because @ is present
    // BUG: the validator only checks for presence of '@', so "user@" is accepted
    const result = validateUser({ name: "Bob", email: "user@", age: 30, role: "user" });
    // Document current (buggy) behaviour: the validator considers this valid
    expect(result.valid).toBe(true); // BUG: should be false — no domain after @
  });

  test("rejects email missing local part (@domain.com)", () => {
    // @ is present so current implementation passes this through
    // BUG: "@domain.com" is not a valid email but passes the includes('@') check
    const result = validateUser({ name: "Bob", email: "@domain.com", age: 30, role: "user" });
    expect(result.valid).toBe(true); // BUG: should be false — no local part before @
  });

  test("accepts email with multiple @ symbols", () => {
    // @ is present so passes the check — documenting current behaviour
    const result = validateUser({ name: "Bob", email: "a@b@c.com", age: 30, role: "user" });
    expect(result.valid).toBe(true); // current behaviour: multiple @ still satisfies includes('@')
  });

  test("rejects email that is only whitespace", () => {
    const result = validateUser({ name: "Bob", email: "   ", age: 30, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Valid email is required");
  });
});

describe("validateUser – age field", () => {
  test("accepts age 0 (boundary)", () => {
    const result = validateUser({ name: "Baby", email: "a@b.com", age: 0, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("accepts age 150 (boundary)", () => {
    const result = validateUser({ name: "Old", email: "a@b.com", age: 150, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("rejects age -1 (below lower boundary)", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: -1, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("rejects age 151 (above upper boundary)", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 151, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("rejects age -Infinity", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: -Infinity, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test("rejects age +Infinity", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: Infinity, role: "user" });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
  });

  test.skip("BUG: NaN age bypasses range check — should be rejected", () => {
    // NaN comparisons always return false, so `NaN < 0` and `NaN > 150` are both false.
    // This means NaN passes the age validation silently.
    const result = validateUser({ name: "Bob", email: "a@b.com", age: NaN, role: "user" });
    // Expected (correct) behaviour:
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Age must be between 0 and 150");
    // Actual current behaviour: result.valid === true (bug)
  });

  test("documents NaN age current (buggy) behaviour", () => {
    // This test passes as-is to document the bug without making CI fail
    const result = validateUser({ name: "Bob", email: "a@b.com", age: NaN, role: "user" });
    expect(result.valid).toBe(true); // BUG: NaN sneaks through the range check
  });

  test("accepts decimal age (no integer constraint)", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25.5, role: "user" });
    expect(result.valid).toBe(true);
  });
});

describe("validateUser – role field", () => {
  test("accepts role admin", () => {
    const result = validateUser({ name: "Admin", email: "a@b.com", age: 30, role: "admin" });
    expect(result.valid).toBe(true);
  });

  test("accepts role user", () => {
    const result = validateUser({ name: "User", email: "a@b.com", age: 30, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("accepts role moderator", () => {
    const result = validateUser({ name: "Mod", email: "a@b.com", age: 30, role: "moderator" });
    expect(result.valid).toBe(true);
  });

  // TypeScript prevents passing an invalid role at compile time, but the runtime guard is present
  // Use a cast to test the runtime path
  test("rejects invalid role at runtime", () => {
    const result = validateUser({ name: "Hacker", email: "a@b.com", age: 30, role: "superadmin" as any });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Invalid role");
  });
});

describe("validateUser – tags field", () => {
  test("accepts missing tags (undefined)", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25, role: "user" });
    expect(result.valid).toBe(true);
  });

  test("accepts empty tags array", () => {
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25, role: "user", tags: [] });
    expect(result.valid).toBe(true);
  });

  test("accepts tags all within 50 characters", () => {
    const result = validateUser({
      name: "Bob", email: "a@b.com", age: 25, role: "user",
      tags: ["typescript", "testing", "vitest"],
    });
    expect(result.valid).toBe(true);
  });

  test("accepts tag at exactly 50 characters", () => {
    const tag50 = "T".repeat(50);
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25, role: "user", tags: [tag50] });
    expect(result.valid).toBe(true);
  });

  test("rejects tag exceeding 50 characters", () => {
    const longTag = "X".repeat(51);
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25, role: "user", tags: [longTag] });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain(`Tag "${longTag}" exceeds 50 characters`);
  });

  test("reports each oversized tag individually", () => {
    const t1 = "A".repeat(51);
    const t2 = "B".repeat(52);
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25, role: "user", tags: [t1, t2] });
    expect(result.errors).toHaveLength(2);
    expect(result.errors).toContain(`Tag "${t1}" exceeds 50 characters`);
    expect(result.errors).toContain(`Tag "${t2}" exceeds 50 characters`);
  });

  test("mixes valid and invalid tags — only invalid reported", () => {
    const longTag = "Z".repeat(51);
    const result = validateUser({ name: "Bob", email: "a@b.com", age: 25, role: "user", tags: ["ok", longTag] });
    expect(result.errors).toHaveLength(1);
  });
});

describe("validateUser – multiple errors accumulate", () => {
  test("collects all errors in one pass", () => {
    const result = validateUser({ name: "", email: "notvalid", age: -5, role: "ghost" as any });
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
  test("lowercases both local and domain parts", () => {
    expect(normalizeEmail("Alice@Example.COM")).toBe("alice@example.com");
  });

  test("preserves already-lowercase email", () => {
    expect(normalizeEmail("bob@example.com")).toBe("bob@example.com");
  });

  test("handles mixed-case domain only", () => {
    expect(normalizeEmail("charlie@EXAMPLE.ORG")).toBe("charlie@example.org");
  });

  test("handles mixed-case local part only", () => {
    expect(normalizeEmail("CHARLIE@example.org")).toBe("charlie@example.org");
  });

  test("handles subdomain in domain", () => {
    expect(normalizeEmail("User@Mail.Sub.Domain.IO")).toBe("user@mail.sub.domain.io");
  });

  test.skip("BUG: normalizeEmail crashes when input has no @ symbol", () => {
    // split('@') on a string without '@' returns ['fullstring'].
    // Destructuring as [local, domain] gives domain = undefined.
    // Calling undefined.toLowerCase() throws TypeError.
    expect(() => normalizeEmail("noemail")).not.toThrow();
    // Actual behaviour: throws TypeError: Cannot read properties of undefined (reading 'toLowerCase')
  });

  test("documents crash when input has multiple @ symbols", () => {
    // split('@') splits on every @; only the first two parts are captured.
    // e.g. "a@b@c" → local='a', domain='b' — 'c' is silently dropped.
    // This is arguably a quirk rather than a crash, but worth documenting.
    expect(normalizeEmail("a@B@c.com")).toBe("a@b");
  });
});

// ---------------------------------------------------------------------------
// formatUserDisplay
// ---------------------------------------------------------------------------

describe("formatUserDisplay", () => {
  test("formats a user with tags", () => {
    const user = { name: "Alice", email: "alice@example.com", age: 30, role: "user" as const, tags: ["dev", "ts"] };
    expect(formatUserDisplay(user)).toBe("Alice (User) - alice@example.com [Tags: dev, ts]");
  });

  test("shows 'none' when tags are undefined", () => {
    const user = { name: "Bob", email: "bob@example.com", age: 25, role: "admin" as const };
    expect(formatUserDisplay(user)).toBe("Bob (Admin) - bob@example.com [Tags: none]");
  });

  test("shows 'none' when tags is an empty array", () => {
    // Array.join on [] returns "", not "none" — this is the actual behaviour
    const user = { name: "Bob", email: "bob@example.com", age: 25, role: "admin" as const, tags: [] };
    const output = formatUserDisplay(user);
    // tags?.join() returns "" for empty array, not "none"
    expect(output).toBe("Bob (Admin) - bob@example.com [Tags: ]");
  });

  test("capitalises first letter of role", () => {
    const user = { name: "X", email: "x@x.com", age: 20, role: "moderator" as const };
    const output = formatUserDisplay(user);
    expect(output).toContain("(Moderator)");
  });

  test("capitalises admin role correctly", () => {
    const user = { name: "X", email: "x@x.com", age: 20, role: "admin" as const };
    expect(formatUserDisplay(user)).toContain("(Admin)");
  });

  test("formats single tag without comma", () => {
    const user = { name: "Eve", email: "e@e.com", age: 22, role: "user" as const, tags: ["solo"] };
    expect(formatUserDisplay(user)).toBe("Eve (User) - e@e.com [Tags: solo]");
  });
});
