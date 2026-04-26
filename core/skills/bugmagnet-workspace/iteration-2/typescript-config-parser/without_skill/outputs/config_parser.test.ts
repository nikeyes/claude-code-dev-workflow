import { describe, it, expect } from "vitest";
import {
  parseConfig,
  serializeConfig,
  getValue,
  getTypedValue,
} from "./config_parser";

// ─── Original tests (preserved) ──────────────────────────────────────────────

describe("parseConfig", () => {
  it("parses a simple key-value pair", () => {
    const config = parseConfig("host = localhost");
    expect(config["default"]["host"].raw).toBe("localhost");
  });

  it("parses section headers", () => {
    const config = parseConfig("[database]\nport = 5432");
    expect(config["database"]["port"].typed).toBe(5432);
  });

  it("ignores comment lines", () => {
    const config = parseConfig("# comment\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });
});

describe("getValue", () => {
  it("returns default when section missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", "fallback")).toBe("fallback");
  });
});

// ─── getTypedValue ────────────────────────────────────────────────────────────

describe("getTypedValue", () => {
  it("returns boolean true for 'true'", () => {
    expect(getTypedValue("true")).toBe(true);
  });

  it("returns boolean false for 'false'", () => {
    expect(getTypedValue("false")).toBe(false);
  });

  it("returns a number for a plain integer string", () => {
    expect(getTypedValue("42")).toBe(42);
  });

  it("returns a number for a float string", () => {
    expect(getTypedValue("3.14")).toBe(3.14);
  });

  it("returns a number for zero", () => {
    expect(getTypedValue("0")).toBe(0);
  });

  it("returns a number for negative values", () => {
    expect(getTypedValue("-7")).toBe(-7);
  });

  it("returns a string for plain text", () => {
    expect(getTypedValue("hello")).toBe("hello");
  });

  it("returns a string for an empty string", () => {
    // raw.trim() === "" guard prevents empty string becoming 0
    expect(getTypedValue("")).toBe("");
  });

  it("returns a string for a whitespace-only input", () => {
    // " ".trim() === "" so the numeric guard fires and " " is returned as string
    expect(typeof getTypedValue("  ")).toBe("string");
  });

  it("BUG — 'Infinity' is typed as the number Infinity instead of a string", () => {
    // Number("Infinity") === Infinity, isNaN(Infinity) === false
    // So "Infinity" becomes the number Infinity — likely unintended for config
    const result = getTypedValue("Infinity");
    expect(result).toBe(Infinity); // documents actual behaviour
  });

  it("returns scientific notation numbers as numbers", () => {
    expect(getTypedValue("1e3")).toBe(1000);
  });

  it("BUG — hex literals are silently converted to their numeric value", () => {
    // Number("0x10") === 16, so "0x10" becomes 16 instead of staying a string
    const result = getTypedValue("0x10");
    expect(result).toBe(16); // documents actual behaviour
  });

  it("returns the string 'NaN' unchanged (not coerced to number)", () => {
    // isNaN(NaN) === true so the number branch is correctly skipped
    expect(getTypedValue("NaN")).toBe("NaN");
  });
});

// ─── parseConfig — basic key/value handling ───────────────────────────────────

describe("parseConfig — basic key/value handling", () => {
  it("trims whitespace around keys", () => {
    const config = parseConfig("  host  = localhost");
    expect(config["default"]["host"]).toBeDefined();
  });

  it("trims whitespace around values", () => {
    const config = parseConfig("host =   localhost  ");
    expect(config["default"]["host"].raw).toBe("localhost");
  });

  it("creates a default section even for an empty input", () => {
    const config = parseConfig("");
    expect(config["default"]).toBeDefined();
  });

  it("skips lines with no equals sign", () => {
    const config = parseConfig("justakeynovalue");
    expect(Object.keys(config["default"])).toHaveLength(0);
  });

  it("skips lines where key is empty (= value)", () => {
    const config = parseConfig("= value");
    expect(Object.keys(config["default"])).toHaveLength(0);
  });

  it("stores both raw and typed values", () => {
    const config = parseConfig("count = 5");
    expect(config["default"]["count"].raw).toBe("5");
    expect(config["default"]["count"].typed).toBe(5);
  });

  it("handles boolean typed values correctly", () => {
    const config = parseConfig("enabled = true");
    expect(config["default"]["enabled"].typed).toBe(true);
    expect(config["default"]["enabled"].raw).toBe("true");
  });
});

// ─── parseConfig — quoted values ──────────────────────────────────────────────

describe("parseConfig — quoted values", () => {
  it("strips double quotes from value", () => {
    const config = parseConfig('name = "Alice"');
    expect(config["default"]["name"].raw).toBe("Alice");
  });

  it("strips single quotes from value", () => {
    const config = parseConfig("name = 'Alice'");
    expect(config["default"]["name"].raw).toBe("Alice");
  });

  it("does not strip mismatched quotes", () => {
    const config = parseConfig("name = \"Alice'");
    expect(config["default"]["name"].raw).toBe("\"Alice'");
  });

  it("does not strip a lone leading/trailing quote character", () => {
    const config = parseConfig("name = 'Alice");
    expect(config["default"]["name"].raw).toBe("'Alice");
  });

  it("a quoted number is unquoted to a string that is then typed as a number", () => {
    // After stripping quotes rawValue is "42", which getTypedValue converts to 42
    const config = parseConfig('port = "42"');
    expect(config["default"]["port"].raw).toBe("42");
    expect(config["default"]["port"].typed).toBe(42);
  });
});

// ─── parseConfig — comment handling ──────────────────────────────────────────

describe("parseConfig — comment handling", () => {
  it("ignores semicolon comment lines", () => {
    const config = parseConfig("; this is a comment\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("strips inline # comments from a value", () => {
    const config = parseConfig("key = value # inline comment");
    expect(config["default"]["key"].raw).toBe("value");
  });

  it("BUG — hex color values starting with # are treated as inline comments", () => {
    // "color = #ff0000": commentIdx finds '#' at position 8, so effective
    // becomes "color = " and rawValue is "".  The color is silently lost.
    const config = parseConfig("color = #ff0000");
    // Documents actual (buggy) behaviour: value is empty string
    expect(config["default"]["color"].raw).toBe("");
  });

  it("inline semicolon comments are NOT stripped (only # is stripped)", () => {
    // Only '#' is used as an inline comment delimiter; ';' is not
    const config = parseConfig("key = value ; inline comment");
    expect(config["default"]["key"].raw).toBe("value ; inline comment");
  });
});

// ─── parseConfig — values containing '=' ──────────────────────────────────────

describe("parseConfig — values containing '='", () => {
  it("BUG — a value containing '=' is silently truncated at the first '='", () => {
    // "url = http://host?a=1" splits to ["url ", " http://host?a", "1"].
    // Only parts[1] is used, so the value becomes "http://host?a" — the query
    // string parameter is dropped.
    const config = parseConfig("url = http://host?a=1");
    // Documents actual (buggy) behaviour
    expect(config["default"]["url"].raw).toBe("http://host?a");
  });

  it("BUG — a base64-encoded value with padding '=' is truncated", () => {
    const config = parseConfig("token = abc==");
    // Only the segment before the second '=' survives
    expect(config["default"]["token"].raw).toBe("abc");
  });

  it("BUG — compact key=value=extra only captures the first segment", () => {
    const config = parseConfig("a=b=c");
    expect(config["default"]["a"].raw).toBe("b");
  });
});

// ─── parseConfig — sections ───────────────────────────────────────────────────

describe("parseConfig — sections", () => {
  it("creates a section and puts subsequent keys in it", () => {
    const input = "[server]\nhost = 127.0.0.1\nport = 8080";
    const config = parseConfig(input);
    expect(config["server"]["host"].raw).toBe("127.0.0.1");
    expect(config["server"]["port"].typed).toBe(8080);
  });

  it("supports multiple sections", () => {
    const input = "[a]\nx = 1\n[b]\ny = 2";
    const config = parseConfig(input);
    expect(config["a"]["x"].typed).toBe(1);
    expect(config["b"]["y"].typed).toBe(2);
  });

  it("keeps default section keys separate from named-section keys", () => {
    const input = "global = yes\n[section]\nlocal = no";
    const config = parseConfig(input);
    expect(config["default"]["global"].raw).toBe("yes");
    expect(config["section"]["local"].raw).toBe("no");
    expect(config["default"]["local"]).toBeUndefined();
  });

  it("merges duplicate sections instead of overwriting them", () => {
    const input = "[db]\nhost = a\n[db]\nport = 5432";
    const config = parseConfig(input);
    expect(config["db"]["host"].raw).toBe("a");
    expect(config["db"]["port"].typed).toBe(5432);
  });

  it("trims whitespace inside section brackets", () => {
    const config = parseConfig("[ server ]\nkey = val");
    expect(config["server"]).toBeDefined();
    expect(config["server"]["key"].raw).toBe("val");
  });

  it("handles an empty section (no keys follow the header)", () => {
    const config = parseConfig("[empty]");
    expect(config["empty"]).toBeDefined();
    expect(Object.keys(config["empty"])).toHaveLength(0);
  });
});

// ─── parseConfig — whitespace and line-ending edge cases ─────────────────────

describe("parseConfig — whitespace and line endings", () => {
  it("skips blank lines", () => {
    const config = parseConfig("\n\nkey = value\n\n");
    expect(config["default"]["key"].raw).toBe("value");
  });

  it("handles CRLF line endings gracefully (\\r stripped by trim())", () => {
    // Implementation splits on '\n' only; '\r' stays in the trimmed token
    // but trim() removes it, so this should work correctly
    const config = parseConfig("key = value\r\nnext = other");
    expect(config["default"]["key"].raw).toBe("value");
    expect(config["default"]["next"].raw).toBe("other");
  });

  it("skips lines that are only whitespace", () => {
    const config = parseConfig("   \nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });
});

// ─── serializeConfig ──────────────────────────────────────────────────────────

describe("serializeConfig", () => {
  it("serializes default-section keys without emitting a [default] header", () => {
    const config = parseConfig("host = localhost");
    const output = serializeConfig(config);
    expect(output).toContain("host = localhost");
    expect(output).not.toContain("[default]");
  });

  it("serializes named sections with a section header", () => {
    const config = parseConfig("[db]\nport = 5432");
    const output = serializeConfig(config);
    expect(output).toContain("[db]");
    expect(output).toContain("port = 5432");
  });

  it("produces output that round-trips cleanly through parseConfig", () => {
    const original = "[server]\nhost = localhost\nport = 8080";
    const config = parseConfig(original);
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    expect(reparsed["server"]["host"].raw).toBe("localhost");
    expect(reparsed["server"]["port"].typed).toBe(8080);
  });

  it("does not throw for an entirely empty config (only default, no keys)", () => {
    const config = parseConfig("");
    expect(() => serializeConfig(config)).not.toThrow();
  });

  it("preserves boolean raw values in output", () => {
    const config = parseConfig("flag = true");
    const output = serializeConfig(config);
    expect(output).toContain("flag = true");
  });
});

// ─── getValue — extended ──────────────────────────────────────────────────────

describe("getValue — extended", () => {
  it("returns the typed value for an existing key", () => {
    const config = parseConfig("[db]\nport = 5432");
    expect(getValue(config, "db", "port")).toBe(5432);
  });

  it("returns undefined when key is missing and no default is provided", () => {
    const config = parseConfig("[db]\nport = 5432");
    expect(getValue(config, "db", "host")).toBeUndefined();
  });

  it("returns the provided default string when key is missing", () => {
    const config = parseConfig("[db]\nport = 5432");
    expect(getValue(config, "db", "host", "127.0.0.1")).toBe("127.0.0.1");
  });

  it("returns undefined when section is missing and no default is provided", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key")).toBeUndefined();
  });

  it("returns a numeric default value when key is missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", 0)).toBe(0);
  });

  it("returns a boolean typed value for an existing boolean key", () => {
    const config = parseConfig("enabled = true");
    expect(getValue(config, "default", "enabled")).toBe(true);
  });

  it("returns the numeric default when a key exists in a section but a different key is queried", () => {
    const config = parseConfig("host = localhost");
    expect(getValue(config, "default", "port", 80)).toBe(80);
  });
});

// ─── Integration ─────────────────────────────────────────────────────────────

describe("integration", () => {
  it("parses a realistic multi-section config file", () => {
    const input = [
      "# Global settings",
      "debug = false",
      "",
      "[database]",
      "host = db.example.com",
      "port = 5432",
      "name = myapp",
      "",
      "[cache]",
      "ttl = 300",
      "enabled = true",
    ].join("\n");

    const config = parseConfig(input);

    expect(config["default"]["debug"].typed).toBe(false);
    expect(config["database"]["host"].raw).toBe("db.example.com");
    expect(config["database"]["port"].typed).toBe(5432);
    expect(config["cache"]["ttl"].typed).toBe(300);
    expect(config["cache"]["enabled"].typed).toBe(true);
  });

  it("a later key assignment in the same section overwrites the earlier one", () => {
    const config = parseConfig("[s]\nkey = first\nkey = second");
    expect(config["s"]["key"].raw).toBe("second");
  });
});
