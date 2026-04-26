export interface UserInput {
  name: string;
  email: string;
  age: number;
  role: "admin" | "user" | "moderator";
  tags?: string[];
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateUser(input: UserInput): ValidationResult {
  const errors: string[] = [];

  if (!input.name || input.name.trim().length === 0) {
    errors.push("Name is required");
  }

  if (input.name && input.name.length > 100) {
    errors.push("Name must be 100 characters or less");
  }

  if (!input.email || !input.email.includes("@")) {
    errors.push("Valid email is required");
  }

  if (input.age < 0 || input.age > 150) {
    errors.push("Age must be between 0 and 150");
  }

  if (!["admin", "user", "moderator"].includes(input.role)) {
    errors.push("Invalid role");
  }

  if (input.tags) {
    for (const tag of input.tags) {
      if (tag.length > 50) {
        errors.push(`Tag "${tag}" exceeds 50 characters`);
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

export function normalizeEmail(email: string): string {
  const [local, domain] = email.split("@");
  return `${local.toLowerCase()}@${domain.toLowerCase()}`;
}

export function formatUserDisplay(user: UserInput): string {
  const roleLabel = user.role.charAt(0).toUpperCase() + user.role.slice(1);
  const tagStr = user.tags?.join(", ") ?? "none";
  return `${user.name} (${roleLabel}) - ${user.email} [Tags: ${tagStr}]`;
}
