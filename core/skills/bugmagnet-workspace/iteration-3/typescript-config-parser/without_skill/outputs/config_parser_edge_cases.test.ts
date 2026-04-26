import { describe, it, expect } from "vitest";
import {
  parseConfig,
  serializeConfig,
  getValue,
  getTypedValue,
} from "../../../../../../evals/files/config_parser";

// ---------------------------------------------------------------------------
// getTypedValue — unit-level edge cases
// ---------------------------------------------------------------------------

describe("getTypedValue", () => {
  it("returns boolean true for the string 'true'", () => {
    expect(getTypedValue("true")).toBe(true);
  });

  it("returns boolean false for the string 'false'", () => {
    expect(getTypedValue("false")).toBe(false);
  });

  it("parses integer strings as numbers", () => {
    expect(getTypedValue("42")).toBe(42);
  });

  it("parses float strings as numbers", () => {
    expect(getTypedValue("3.14")).toBe(3.14);
  });

  it("returns the string unchanged for non-numeric, non-boolean input", () => {
    expect(getTypedValue("hello")).toBe("hello");
  });

  it("returns empty string for an empty input", () => {
    // Number("") === 0, but raw.trim() === "" so it should NOT become 0
    expect(getTypedValue("")).toBe("");
  });

  // BUG: whitespace-only string — Number("  ") === 0 but "  ".trim() === ""
  // so the condition `raw.trim() !== ""` protects against this.
  // Verify that whitespace-only strings are NOT converted to 0.
  it("does not convert a whitespace-only string to the number 0", () => {
    const result = getTypedValue("   ");
    expect(typeof result).toBe("string");
    expect(result).not.toBe(0);
  });

  // BUG candidate: "Infinity" and "-Infinity" pass !isNaN and produce Infinity
  it("does not convert the string 'Infinity' to the number Infinity", () => {
    const result = getTypedValue("Infinity");
    // Expected: string "Infinity" (not converted to the special JS Infinity value)
    expect(typeof result).toBe("string");
  });

  it("does not convert the string '-Infinity' to the number -Infinity", () => {
    const result = getTypedValue("-Infinity");
    expect(typeof result).toBe("string");
  });

  it("does not convert the string 'NaN' to the number NaN", () => {
    const result = getTypedValue("NaN");
    // isNaN(Number("NaN")) === true, so this should stay a string — verify it does
    expect(typeof result).toBe("string");
  });

  it("parses negative numbers correctly", () => {
    expect(getTypedValue("-5")).toBe(-5);
  });

  it("parses zero correctly", () => {
    expect(getTypedValue("0")).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// parseConfig — basic structure
// ---------------------------------------------------------------------------

describe("parseConfig — basic structure", () => {
  it("always returns a 'default' section even for empty input", () => {
    const config = parseConfig("");
    expect(config["default"]).toBeDefined();
    expect(Object.keys(config["default"])).toHaveLength(0);
  });

  it("returns typed value for boolean true", () => {
    const config = parseConfig("flag = true");
    expect(config["default"]["flag"].typed).toBe(true);
  });

  it("returns typed value for boolean false", () => {
    const config = parseConfig("enabled = false");
    expect(config["default"]["enabled"].typed).toBe(false);
  });

  it("returns typed number for integer value", () => {
    const config = parseConfig("port = 8080");
    expect(config["default"]["port"].typed).toBe(8080);
  });

  it("stores raw value without surrounding quotes (double quotes)", () => {
    const config = parseConfig('name = "Alice"');
    expect(config["default"]["name"].raw).toBe("Alice");
  });

  it("stores raw value without surrounding quotes (single quotes)", () => {
    const config = parseConfig("name = 'Bob'");
    expect(config["default"]["name"].raw).toBe("Bob");
  });

  it("typed value for a quoted string is the unquoted string", () => {
    const config = parseConfig('greeting = "hello world"');
    expect(config["default"]["greeting"].typed).toBe("hello world");
  });
});

// ---------------------------------------------------------------------------
// parseConfig — comment handling
// ---------------------------------------------------------------------------

describe("parseConfig — comment handling", () => {
  it("ignores lines that start with #", () => {
    const config = parseConfig("# full line comment\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("ignores lines that start with ;", () => {
    const config = parseConfig("; semicolon comment\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("strips trailing # inline comment from a value", () => {
    const config = parseConfig("host = localhost # dev only");
    expect(config["default"]["host"].raw).toBe("localhost");
  });

  // BUG: inline ';' comment is NOT stripped — only '#' is handled inline.
  it("strips trailing ; inline comment from a value", () => {
    const config = parseConfig("host = localhost ; dev only");
    // Expected: raw should be "localhost", not "localhost ; dev only"
    expect(config["default"]["host"].raw).toBe("localhost");
  });

  it("ignores blank lines", () => {
    const config = parseConfig("\n\nkey = value\n\n");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("ignores lines with only whitespace", () => {
    const config = parseConfig("   \n   \nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });
});

// ---------------------------------------------------------------------------
// parseConfig — values containing '='
// ---------------------------------------------------------------------------

describe("parseConfig — values containing equals sign", () => {
  // BUG: `parts.split("=")` then only reads parts[1], so everything after the
  // second '=' is silently dropped.
  it("preserves a value that contains an equals sign", () => {
    const config = parseConfig("url = http://host/path?a=1&b=2");
    // Expected full value: "http://host/path?a=1&b=2"
    expect(config["default"]["url"].raw).toBe("http://host/path?a=1&b=2");
  });

  it("preserves a base64-encoded value (which contains '=')", () => {
    const config = parseConfig("token = aGVsbG8=");
    expect(config["default"]["token"].raw).toBe("aGVsbG8=");
  });

  it("preserves a value with multiple equals signs", () => {
    const config = parseConfig("expr = a=b=c");
    expect(config["default"]["expr"].raw).toBe("a=b=c");
  });
});

// ---------------------------------------------------------------------------
// parseConfig — quoted values with special characters
// ---------------------------------------------------------------------------

describe("parseConfig — quoted values with special characters", () => {
  // BUG: '#' inside a quoted value is treated as an inline comment marker
  // BEFORE quote stripping happens. This truncates the quoted value.
  it("preserves a # character inside double-quoted value", () => {
    const config = parseConfig('color = "#ff0000"');
    expect(config["default"]["color"].raw).toBe("#ff0000");
  });

  it("preserves a # character inside single-quoted value", () => {
    const config = parseConfig("color = '#ff0000'");
    expect(config["default"]["color"].raw).toBe("#ff0000");
  });

  it("preserves a semicolon inside a quoted value", () => {
    const config = parseConfig('message = "hello; world"');
    expect(config["default"]["message"].raw).toBe("hello; world");
  });

  it("preserves an equals sign inside a quoted value", () => {
    const config = parseConfig('formula = "x=y+z"');
    expect(config["default"]["formula"].raw).toBe("x=y+z");
  });

  it("preserves spaces inside a quoted value", () => {
    const config = parseConfig('path = "C:\\Program Files\\app"');
    expect(config["default"]["path"].raw).toBe("C:\\Program Files\\app");
  });
});

// ---------------------------------------------------------------------------
// parseConfig — section handling
// ---------------------------------------------------------------------------

describe("parseConfig — section handling", () => {
  it("creates a new section for each header encountered", () => {
    const config = parseConfig("[server]\nhost = 127.0.0.1\n[db]\nport = 5432");
    expect(config["server"]).toBeDefined();
    expect(config["db"]).toBeDefined();
  });

  it("does not include section header key in entries", () => {
    const config = parseConfig("[server]\nhost = example.com");
    expect(config["server"]["host"]).toBeDefined();
    expect(Object.keys(config["server"])).not.toContain("[server]");
  });

  it("keys before any section header land in 'default'", () => {
    const config = parseConfig("global = yes\n[app]\nname = test");
    expect(config["default"]["global"].raw).toBe("yes");
    expect(config["app"]["name"].raw).toBe("test");
  });

  it("section name with surrounding whitespace is trimmed", () => {
    const config = parseConfig("[  db  ]\nport = 5432");
    expect(config["db"]).toBeDefined();
    expect(config["db"]["port"].typed).toBe(5432);
  });

  // BUG candidate: empty section name '[]' produces an entry with key ""
  it("handles an empty section name '[]' without crashing", () => {
    expect(() => parseConfig("[]\nkey = value")).not.toThrow();
  });

  it("duplicate section headers merge their keys", () => {
    const input = "[db]\nhost = localhost\n[db]\nport = 5432";
    const config = parseConfig(input);
    expect(config["db"]["host"].raw).toBe("localhost");
    expect(config["db"]["port"].typed).toBe(5432);
  });

  it("later section definitions do not wipe earlier keys", () => {
    const input = "[db]\nhost = localhost\n[app]\nname = myapp\n[db]\nport = 5432";
    const config = parseConfig(input);
    // 'host' set in first [db] block must still be present after re-entering [db]
    expect(config["db"]["host"].raw).toBe("localhost");
    expect(config["db"]["port"].typed).toBe(5432);
  });
});

// ---------------------------------------------------------------------------
// parseConfig — duplicate keys
// ---------------------------------------------------------------------------

describe("parseConfig — duplicate keys", () => {
  it("last duplicate key wins within the same section", () => {
    const config = parseConfig("key = first\nkey = second");
    expect(config["default"]["key"].raw).toBe("second");
  });
});

// ---------------------------------------------------------------------------
// parseConfig — key edge cases
// ---------------------------------------------------------------------------

describe("parseConfig — key edge cases", () => {
  it("skips a line with no '=' separator", () => {
    const config = parseConfig("notakeyvalue\nvalid = yes");
    expect(config["default"]["notakeyvalue"]).toBeUndefined();
    expect(config["default"]["valid"].raw).toBe("yes");
  });

  it("skips a line where the key is empty (starts with =)", () => {
    const config = parseConfig("= value\nvalid = yes");
    expect(config["default"]["valid"].raw).toBe("yes");
    // empty key must NOT be stored
    expect(config["default"][""]).toBeUndefined();
  });

  it("trims whitespace from keys", () => {
    const config = parseConfig("  port  = 3000");
    expect(config["default"]["port"]).toBeDefined();
    expect(config["default"]["port"].typed).toBe(3000);
  });

  it("handles a key with no space around '='", () => {
    const config = parseConfig("port=3000");
    expect(config["default"]["port"].typed).toBe(3000);
  });
});

// ---------------------------------------------------------------------------
// parseConfig — line ending variants
// ---------------------------------------------------------------------------

describe("parseConfig — line endings", () => {
  it("parses Unix line endings (LF)", () => {
    const config = parseConfig("a = 1\nb = 2");
    expect(config["default"]["a"].typed).toBe(1);
    expect(config["default"]["b"].typed).toBe(2);
  });

  it("parses Windows line endings (CRLF)", () => {
    const config = parseConfig("a = 1\r\nb = 2\r\n");
    expect(config["default"]["a"].typed).toBe(1);
    expect(config["default"]["b"].typed).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// serializeConfig — round-trip fidelity
// ---------------------------------------------------------------------------

describe("serializeConfig — round-trip fidelity", () => {
  it("serializes a default section without a section header", () => {
    const config = parseConfig("host = localhost");
    const output = serializeConfig(config);
    expect(output).not.toContain("[default]");
    expect(output).toContain("host = localhost");
  });

  it("includes section headers for non-default sections", () => {
    const config = parseConfig("[db]\nport = 5432");
    const output = serializeConfig(config);
    expect(output).toContain("[db]");
    expect(output).toContain("port = 5432");
  });

  it("round-trips simple key-value pairs", () => {
    const original = "host = localhost";
    const config = parseConfig(original);
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    expect(reparsed["default"]["host"].raw).toBe(
      config["default"]["host"].raw
    );
  });

  it("round-trips a numeric value", () => {
    const config = parseConfig("[app]\nport = 9000");
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    expect(reparsed["app"]["port"].typed).toBe(9000);
  });

  it("round-trips a boolean value", () => {
    const config = parseConfig("debug = true");
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    expect(reparsed["default"]["debug"].typed).toBe(true);
  });

  // BUG: values that contained quotes originally have those quotes stripped from
  // 'raw', so serializeConfig does NOT re-add quotes. A value with spaces will
  // round-trip correctly only if the parser does not need quotes to identify it,
  // but values that relied on quoting to contain '#' or ';' will NOT survive.
  it("serialized output re-parses to the same typed value for a string with spaces", () => {
    const config = parseConfig('greeting = "hello world"');
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    // "hello world" without quotes: typed should still be the string "hello world"
    expect(reparsed["default"]["greeting"].typed).toBe("hello world");
  });

  it("does not produce trailing whitespace on value lines", () => {
    const config = parseConfig("key = value");
    const output = serializeConfig(config);
    for (const line of output.split("\n")) {
      expect(line).toBe(line.trimEnd());
    }
  });
});

// ---------------------------------------------------------------------------
// getValue — edge cases
// ---------------------------------------------------------------------------

describe("getValue — edge cases", () => {
  it("returns undefined when section is missing and no default given", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key")).toBeUndefined();
  });

  it("returns defaultValue when section is missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", 42)).toBe(42);
  });

  it("returns defaultValue when key is missing in existing section", () => {
    const config = parseConfig("[db]\nhost = localhost");
    expect(getValue(config, "db", "port", 5432)).toBe(5432);
  });

  it("returns the actual typed value when section and key exist", () => {
    const config = parseConfig("[db]\nport = 3306");
    expect(getValue(config, "db", "port")).toBe(3306);
  });

  it("returns the actual value even when defaultValue is provided", () => {
    const config = parseConfig("[app]\ndebug = false");
    expect(getValue(config, "app", "debug", true)).toBe(false);
  });

  it("retrieves a value from the default section", () => {
    const config = parseConfig("global = yes");
    expect(getValue(config, "default", "global")).toBe("yes");
  });

  it("returns undefined when both section and key are missing and no default", () => {
    const config = parseConfig("");
    expect(getValue(config, "nope", "nope")).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// parseConfig — large / stress inputs
// ---------------------------------------------------------------------------

describe("parseConfig — stress inputs", () => {
  it("handles a config with many sections and keys without error", () => {
    const lines: string[] = [];
    for (let s = 0; s < 10; s++) {
      lines.push(`[section${s}]`);
      for (let k = 0; k < 10; k++) {
        lines.push(`key${k} = value${k}`);
      }
    }
    const config = parseConfig(lines.join("\n"));
    expect(config["section0"]["key0"].raw).toBe("value0");
    expect(config["section9"]["key9"].raw).toBe("value9");
  });

  it("parses a completely empty string without throwing", () => {
    expect(() => parseConfig("")).not.toThrow();
  });

  it("parses a string of only comments without throwing", () => {
    expect(() => parseConfig("# comment\n; another\n# yet another")).not.toThrow();
  });
});
