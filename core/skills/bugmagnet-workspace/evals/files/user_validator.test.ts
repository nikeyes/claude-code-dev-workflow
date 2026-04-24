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
});

describe("normalizeEmail", () => {
  test("lowercases email", () => {
    expect(normalizeEmail("Alice@Example.COM")).toBe("alice@example.com");
  });
});
