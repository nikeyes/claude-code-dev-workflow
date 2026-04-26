import { describe, it, expect } from "vitest";
import { parseConfig, serializeConfig, getValue, getTypedValue } from "./config_parser";

// =============================================================================
// Original tests (preserved)
// =============================================================================

describe("parseConfig - original tests", () => {
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

describe("getValue - original tests", () => {
  it("returns default when section missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", "fallback")).toBe("fallback");
  });
});

// =============================================================================
// parseConfig — empty and minimal inputs
// =============================================================================

describe("parseConfig - empty and minimal inputs", () => {
  it("returns only default section for empty string", () => {
    const config = parseConfig("");
    expect(Object.keys(config)).toEqual(["default"]);
    expect(config["default"]).toEqual({});
  });

  it("returns empty default section for whitespace-only input", () => {
    const config = parseConfig("   \n\t\n   ");
    expect(config["default"]).toEqual({});
  });

  it("returns empty default section for input with only comment lines", () => {
    const config = parseConfig("# only comments\n; also a comment");
    expect(config["default"]).toEqual({});
    expect(Object.keys(config)).toEqual(["default"]);
  });

  it("returns empty default section for single blank line", () => {
    const config = parseConfig("\n");
    expect(config["default"]).toEqual({});
  });

  it("parses single key-value pair with no sections", () => {
    const config = parseConfig("key = value");
    expect(config["default"]["key"].raw).toBe("value");
    expect(config["default"]["key"].typed).toBe("value");
  });
});

// =============================================================================
// parseConfig — comment handling
// =============================================================================

describe("parseConfig - comment handling", () => {
  it("ignores lines starting with semicolon", () => {
    const config = parseConfig("; this is a comment\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("strips inline hash comment from value", () => {
    const config = parseConfig("key = value # inline comment");
    expect(config["default"]["key"].raw).toBe("value");
  });

  it("strips trailing hash comment with multiple spaces", () => {
    const config = parseConfig("timeout = 30  # seconds");
    expect(config["default"]["timeout"].raw).toBe("30");
    expect(config["default"]["timeout"].typed).toBe(30);
  });

  it.skip("preserves hash character at start of value - BUG", () => {
    /*
     * ROOT CAUSE: config_parser.ts:56-58 uses trimmed.indexOf("#") to find comment
     * start. When the value itself begins with "#" (e.g., HTML color codes), the
     * entire value is treated as a comment and stripped. The effective string becomes
     * "key =" and rawValue becomes "".
     *
     * CODE LOCATION: config_parser.ts:56-58
     *   const commentIdx = trimmed.indexOf("#");
     *   const effective = commentIdx >= 0 ? trimmed.slice(0, commentIdx).trimEnd() : trimmed;
     *
     * PROPOSED FIX: Only treat "#" as a comment when it is preceded by whitespace.
     *   const commentMatch = /\s#/.exec(trimmed);
     *   const effective = commentMatch ? trimmed.slice(0, commentMatch.index).trimEnd() : trimmed;
     *
     * EXPECTED: config["default"]["color"].raw === "#ff0000"
     * ACTUAL:   config["default"]["color"].raw === "" (entire value stripped)
     */
    const config = parseConfig("color = #ff0000");
    expect(config["default"]["color"].raw).toBe("#ff0000");
  });

  it.skip("preserves hash character anywhere inside a value - BUG", () => {
    /*
     * ROOT CAUSE: Same as above — trimmed.indexOf("#") finds the first "#" regardless
     * of whether it is part of the value or a comment delimiter.
     *
     * CODE LOCATION: config_parser.ts:56-58
     * PROPOSED FIX: Only treat "#" as comment when preceded by whitespace.
     *
     * EXPECTED: config["default"]["ref"].raw === "abc#123"
     * ACTUAL:   config["default"]["ref"].raw === "abc" (truncated at "#")
     */
    const config = parseConfig("ref = abc#123");
    expect(config["default"]["ref"].raw).toBe("abc#123");
  });

  it.skip("preserves hash in key name - BUG", () => {
    /*
     * ROOT CAUSE: config_parser.ts:56-58 — comment stripping occurs on the full
     * trimmed line before key/value splitting. A key containing "#" causes the
     * effective line to be truncated before the "=" sign, so parts.length < 2 and
     * the entry is silently skipped.
     *
     * CODE LOCATION: config_parser.ts:56-58
     * PROPOSED FIX: Only apply comment stripping after the first "=" (i.e., restrict
     * comment search to the value portion of the line).
     *
     * EXPECTED: config["default"]["my#key"] exists with raw === "value"
     * ACTUAL:   entry is silently dropped (parts.length < 2 after truncation)
     */
    const config = parseConfig("my#key = value");
    expect(config["default"]["my#key"]).toBeDefined();
    expect(config["default"]["my#key"].raw).toBe("value");
  });
});

// =============================================================================
// parseConfig — section handling
// =============================================================================

describe("parseConfig - section handling", () => {
  it("places keys before first section into the default section", () => {
    const config = parseConfig("early = a\n[section]\nlate = b");
    expect(config["default"]["early"].raw).toBe("a");
    expect(config["section"]["late"].raw).toBe("b");
  });

  it("parses multiple distinct sections", () => {
    const config = parseConfig("[db]\nhost = db-host\n[cache]\nport = 6379");
    expect(config["db"]["host"].raw).toBe("db-host");
    expect(config["cache"]["port"].typed).toBe(6379);
  });

  it("merges keys when same section name appears more than once", () => {
    const config = parseConfig("[db]\nhost = localhost\n[db]\nport = 5432");
    expect(config["db"]["host"].raw).toBe("localhost");
    expect(config["db"]["port"].typed).toBe(5432);
  });

  it("overwrites earlier value when the same key repeats in a section", () => {
    const config = parseConfig("[s]\nkey = first\nkey = second");
    expect(config["s"]["key"].raw).toBe("second");
  });

  it("trims whitespace from section names", () => {
    const config = parseConfig("[ my section ]\nkey = value");
    expect(config["my section"]["key"].raw).toBe("value");
  });

  it("handles section name that consists entirely of whitespace", () => {
    // slice(1,-1).trim() produces "" — an empty-string section key
    const config = parseConfig("[   ]\nkey = value");
    expect(config[""]).toBeDefined();
    expect(config[""]["key"].raw).toBe("value");
  });

  it("creates default section even when input has no default keys", () => {
    const config = parseConfig("[only]\nk = v");
    expect(config["default"]).toBeDefined();
    expect(config["default"]).toEqual({});
  });

  it("section header line with only a name and no trailing space is parsed", () => {
    const config = parseConfig("[section]\nkey = val");
    expect(config["section"]["key"].raw).toBe("val");
  });

  it("preserves section name casing", () => {
    const config = parseConfig("[Database]\nhost = h");
    expect(config["Database"]).toBeDefined();
    expect(config["database"]).toBeUndefined();
  });
});

// =============================================================================
// parseConfig — value types (getTypedValue integration)
// =============================================================================

describe("parseConfig - typed value coercion", () => {
  it("coerces 'true' string to boolean true", () => {
    const config = parseConfig("enabled = true");
    expect(config["default"]["enabled"].typed).toBe(true);
    expect(config["default"]["enabled"].raw).toBe("true");
  });

  it("coerces 'false' string to boolean false", () => {
    const config = parseConfig("enabled = false");
    expect(config["default"]["enabled"].typed).toBe(false);
  });

  it("coerces integer string to number", () => {
    const config = parseConfig("port = 8080");
    expect(config["default"]["port"].typed).toBe(8080);
  });

  it("coerces float string to number", () => {
    const config = parseConfig("threshold = 0.95");
    expect(config["default"]["threshold"].typed).toBe(0.95);
  });

  it("coerces zero string to number zero", () => {
    const config = parseConfig("count = 0");
    expect(config["default"]["count"].typed).toBe(0);
  });

  it("coerces negative number string to number", () => {
    const config = parseConfig("offset = -100");
    expect(config["default"]["offset"].typed).toBe(-100);
  });

  it("keeps plain string as string type", () => {
    const config = parseConfig("name = hello");
    expect(config["default"]["name"].typed).toBe("hello");
  });

  it("does not coerce 'True' (capital T) to boolean", () => {
    const config = parseConfig("flag = True");
    expect(config["default"]["flag"].typed).toBe("True");
  });

  it("does not coerce 'FALSE' (uppercase) to boolean", () => {
    const config = parseConfig("flag = FALSE");
    expect(config["default"]["flag"].typed).toBe("FALSE");
  });

  it("does not coerce 'NaN' string to a number", () => {
    const config = parseConfig("val = NaN");
    expect(config["default"]["val"].typed).toBe("NaN");
  });

  it("stores empty raw value when value portion is only whitespace", () => {
    const config = parseConfig("key =   ");
    expect(config["default"]["key"].raw).toBe("");
  });
});

// =============================================================================
// parseConfig — quoted values
// =============================================================================

describe("parseConfig - quoted values", () => {
  it("strips double quotes surrounding a value", () => {
    const config = parseConfig('greeting = "hello world"');
    expect(config["default"]["greeting"].raw).toBe("hello world");
  });

  it("strips single quotes surrounding a value", () => {
    const config = parseConfig("greeting = 'hello world'");
    expect(config["default"]["greeting"].raw).toBe("hello world");
  });

  it("leaves mismatched quotes intact (double open, single close)", () => {
    const config = parseConfig("val = \"oops'");
    expect(config["default"]["val"].raw).toBe("\"oops'");
  });

  it("leaves mismatched quotes intact (single open, double close)", () => {
    const config = parseConfig('val = \'oops"');
    expect(config["default"]["val"].raw).toBe("'oops\"");
  });

  it("leaves single trailing quote intact", () => {
    const config = parseConfig("val = hello'");
    expect(config["default"]["val"].raw).toBe("hello'");
  });

  it("leaves single leading quote intact", () => {
    const config = parseConfig("val = 'hello");
    expect(config["default"]["val"].raw).toBe("'hello");
  });

  it("strips double quotes from a numeric-looking value", () => {
    const config = parseConfig('port = "8080"');
    // After unquoting raw becomes "8080"; getTypedValue("8080") === 8080
    expect(config["default"]["port"].raw).toBe("8080");
    expect(config["default"]["port"].typed).toBe(8080);
  });

  it("strips double quotes from 'true' and still coerces to boolean", () => {
    const config = parseConfig('flag = "true"');
    expect(config["default"]["flag"].raw).toBe("true");
    expect(config["default"]["flag"].typed).toBe(true);
  });
});

// =============================================================================
// parseConfig — values with special characters
// =============================================================================

describe("parseConfig - special character values", () => {
  it.skip("preserves full value when it contains an equals sign - BUG", () => {
    /*
     * ROOT CAUSE: config_parser.ts:60-64 splits the effective line on ALL "="
     * characters and takes only parts[1]. Everything from the second "=" onward
     * is discarded. For "url = http://host?a=b", parts[1] is "http://host?a"
     * and "b" is lost.
     *
     * CODE LOCATION: config_parser.ts:60-64
     *   const parts = effective.split("=");
     *   if (parts.length < 2) continue;
     *   const key = parts[0].trim();
     *   const rawValue = parts[1].trim();
     *
     * PROPOSED FIX: Split only on the first "=":
     *   const eqIdx = effective.indexOf("=");
     *   if (eqIdx === -1) continue;
     *   const key = effective.slice(0, eqIdx).trim();
     *   const rawValue = effective.slice(eqIdx + 1).trim();
     *
     * EXPECTED: config["default"]["url"].raw === "http://host?a=b"
     * ACTUAL:   config["default"]["url"].raw === "http://host?a"
     */
    const config = parseConfig("url = http://host?a=b");
    expect(config["default"]["url"].raw).toBe("http://host?a=b");
  });

  it.skip("preserves base64 value with equals-sign padding - BUG", () => {
    /*
     * ROOT CAUSE: Same split("=") issue as the URL bug above.
     * "token = dXNlcjpwYXNzd29yZA==" splits into three parts; only parts[1]
     * ("dXNlcjpwYXNzd29yZA") is kept and the "==" padding is dropped.
     *
     * CODE LOCATION: config_parser.ts:60-64
     * PROPOSED FIX: Use indexOf("=") and slice (see URL bug above).
     *
     * EXPECTED: config["default"]["token"].raw === "dXNlcjpwYXNzd29yZA=="
     * ACTUAL:   config["default"]["token"].raw === "dXNlcjpwYXNzd29yZA"
     */
    const config = parseConfig("token = dXNlcjpwYXNzd29yZA==");
    expect(config["default"]["token"].raw).toBe("dXNlcjpwYXNzd29yZA==");
  });

  it.skip("preserves URL with multiple query parameters - BUG", () => {
    /*
     * ROOT CAUSE: Same split("=") issue. "url = http://host?a=1&b=2" produces
     * parts = ["url ", " http://host?a", "1&b", "2"]; only parts[1] is kept.
     *
     * CODE LOCATION: config_parser.ts:60-64
     * PROPOSED FIX: Use indexOf("=") and slice.
     *
     * EXPECTED: config["default"]["url"].raw === "http://host?a=1&b=2"
     * ACTUAL:   config["default"]["url"].raw === "http://host?a"
     */
    const config = parseConfig("url = http://host?a=1&b=2");
    expect(config["default"]["url"].raw).toBe("http://host?a=1&b=2");
  });

  it("skips lines that have no equals sign", () => {
    const config = parseConfig("this_has_no_equals\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("skips lines where the key is empty after trimming", () => {
    const config = parseConfig("= orphaned-value\nkey = ok");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("parses key containing underscore and hyphen", () => {
    const config = parseConfig("my_key-name = value");
    expect(config["default"]["my_key-name"].raw).toBe("value");
  });

  it("parses CRLF line endings correctly", () => {
    const config = parseConfig("key = val\r\n[s]\r\nother = x\r\n");
    expect(config["default"]["key"].raw).toBe("val");
    expect(config["s"]["other"].raw).toBe("x");
  });

  it("parses unicode characters in values", () => {
    const config = parseConfig("greeting = こんにちは");
    expect(config["default"]["greeting"].raw).toBe("こんにちは");
  });

  it("parses unicode characters in keys", () => {
    const config = parseConfig("名前 = taro");
    expect(config["default"]["名前"].raw).toBe("taro");
  });

  it("parses SQL injection pattern as plain string", () => {
    const config = parseConfig("input = Robert'); DROP TABLE students;--");
    expect(config["default"]["input"].raw).toBe("Robert'); DROP TABLE students;--");
  });

  it("parses XSS payload as plain string", () => {
    const config = parseConfig("val = <script>alert(1)</script>");
    expect(config["default"]["val"].raw).toBe("<script>alert(1)</script>");
  });

  it("parses value with only special ASCII punctuation", () => {
    const config = parseConfig("sym = !@$%^&*()");
    expect(config["default"]["sym"].raw).toBe("!@$%^&*()");
  });

  it("parses very long value (10 000 chars)", () => {
    const longVal = "a".repeat(10_000);
    const config = parseConfig(`key = ${longVal}`);
    expect(config["default"]["key"].raw).toBe(longVal);
  });
});

// =============================================================================
// parseConfig — scale and independence
// =============================================================================

describe("parseConfig - scale and independence", () => {
  it("parses 100 key-value pairs in the default section", () => {
    const lines = Array.from({ length: 100 }, (_, i) => `key${i} = val${i}`).join("\n");
    const config = parseConfig(lines);
    expect(Object.keys(config["default"]).length).toBe(100);
    expect(config["default"]["key0"].raw).toBe("val0");
    expect(config["default"]["key99"].raw).toBe("val99");
  });

  it("parses 20 distinct named sections", () => {
    const lines = Array.from({ length: 20 }, (_, i) => `[s${i}]\nk = v${i}`).join("\n");
    const config = parseConfig(lines);
    // 20 named sections + the implicit "default"
    expect(Object.keys(config).length).toBe(21);
    expect(config["s0"]["k"].raw).toBe("v0");
    expect(config["s19"]["k"].raw).toBe("v19");
  });

  it("returns independent configs when parseConfig is called twice", () => {
    const c1 = parseConfig("[s]\nkey = a");
    const c2 = parseConfig("[s]\nkey = b");
    expect(c1["s"]["key"].raw).toBe("a");
    expect(c2["s"]["key"].raw).toBe("b");
  });

  it("mutating the returned config does not affect a subsequent parse", () => {
    const c1 = parseConfig("key = a");
    c1["default"]["key"].raw = "MUTATED";
    const c2 = parseConfig("key = a");
    expect(c2["default"]["key"].raw).toBe("a");
  });
});

// =============================================================================
// getTypedValue — standalone unit tests
// =============================================================================

describe("getTypedValue", () => {
  it("returns true for 'true'", () => {
    expect(getTypedValue("true")).toBe(true);
  });

  it("returns false for 'false'", () => {
    expect(getTypedValue("false")).toBe(false);
  });

  it("returns number for integer string", () => {
    expect(getTypedValue("42")).toBe(42);
  });

  it("returns number for float string", () => {
    expect(getTypedValue("3.14")).toBe(3.14);
  });

  it("returns number for zero string", () => {
    expect(getTypedValue("0")).toBe(0);
  });

  it("returns number for negative integer string", () => {
    expect(getTypedValue("-7")).toBe(-7);
  });

  it("returns number for negative float string", () => {
    expect(getTypedValue("-1.5")).toBe(-1.5);
  });

  it("returns string for 'NaN'", () => {
    expect(getTypedValue("NaN")).toBe("NaN");
  });

  it("returns string for empty string (not coerced to 0)", () => {
    expect(getTypedValue("")).toBe("");
  });

  it("returns string for whitespace-only string (not coerced to 0)", () => {
    expect(getTypedValue("   ")).toBe("   ");
  });

  it("returns string for 'True' (mixed case)", () => {
    expect(getTypedValue("True")).toBe("True");
  });

  it("returns string for 'FALSE' (uppercase)", () => {
    expect(getTypedValue("FALSE")).toBe("FALSE");
  });

  it("returns number for scientific notation '1e2'", () => {
    // Number("1e2") === 100 — documented current behavior
    expect(getTypedValue("1e2")).toBe(100);
  });

  it("returns number for padded number string '  42  '", () => {
    // Number("  42  ") === 42 and "  42  ".trim() !== "" so number conversion fires
    expect(getTypedValue("  42  ")).toBe(42);
  });

  it.skip("returns string for 'Infinity' - BUG", () => {
    /*
     * ROOT CAUSE: config_parser.ts:28-29
     *   const num = Number(raw);
     *   if (!isNaN(num) && raw.trim() !== "") return num;
     * Number("Infinity") === Infinity and !isNaN(Infinity) is true, so the guard
     * passes and the JavaScript special value Infinity is returned. Config files
     * should treat "Infinity" as a plain string.
     *
     * CODE LOCATION: config_parser.ts:28-29
     * PROPOSED FIX: add isFinite check:
     *   if (!isNaN(num) && isFinite(num) && raw.trim() !== "") return num;
     *
     * EXPECTED: getTypedValue("Infinity") === "Infinity"
     * ACTUAL:   getTypedValue("Infinity") === Infinity (JavaScript number)
     */
    expect(getTypedValue("Infinity")).toBe("Infinity");
  });

  it.skip("returns string for '-Infinity' - BUG", () => {
    /*
     * ROOT CAUSE: Same as Infinity bug above. Number("-Infinity") === -Infinity
     * and !isNaN(-Infinity) is true.
     *
     * CODE LOCATION: config_parser.ts:28-29
     * PROPOSED FIX: add isFinite check (see Infinity bug above).
     *
     * EXPECTED: getTypedValue("-Infinity") === "-Infinity"
     * ACTUAL:   getTypedValue("-Infinity") === -Infinity
     */
    expect(getTypedValue("-Infinity")).toBe("-Infinity");
  });

  it("returns number for MAX_SAFE_INTEGER string", () => {
    expect(getTypedValue("9007199254740991")).toBe(9007199254740991);
  });

  it("returns number for string '0.0'", () => {
    expect(getTypedValue("0.0")).toBe(0);
  });
});

// =============================================================================
// serializeConfig
// =============================================================================

describe("serializeConfig", () => {
  it("serializes default section without a [default] header", () => {
    const config = parseConfig("key = value");
    const result = serializeConfig(config);
    expect(result).toContain("key = value");
    expect(result).not.toContain("[default]");
  });

  it("serializes named section with a section header", () => {
    const config = parseConfig("[db]\nhost = localhost");
    const result = serializeConfig(config);
    expect(result).toContain("[db]");
    expect(result).toContain("host = localhost");
  });

  it("serializes multiple named sections each with a header", () => {
    const config = parseConfig("[db]\nhost = h\n[cache]\nport = 6379");
    const result = serializeConfig(config);
    expect(result).toContain("[db]");
    expect(result).toContain("host = h");
    expect(result).toContain("[cache]");
    expect(result).toContain("port = 6379");
  });

  it("returns empty string for a config with no keys", () => {
    const config = parseConfig("");
    expect(serializeConfig(config)).toBe("");
  });

  it("serializes boolean values using their raw string form", () => {
    const config = parseConfig("debug = true");
    expect(serializeConfig(config)).toContain("debug = true");
  });

  it("round-trips a simple config through serialize and re-parse", () => {
    const input = "[section]\nkey = value\nport = 3000";
    const config = parseConfig(input);
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    expect(reparsed["section"]["key"].raw).toBe("value");
    expect(reparsed["section"]["port"].typed).toBe(3000);
  });

  it("round-trips a multi-section config correctly", () => {
    const input = "[a]\nx = 1\n[b]\ny = hello";
    const reparsed = parseConfig(serializeConfig(parseConfig(input)));
    expect(reparsed["a"]["x"].typed).toBe(1);
    expect(reparsed["b"]["y"].raw).toBe("hello");
  });

  it.skip("emits [default] header when input explicitly declared [default] section - BUG", () => {
    /*
     * ROOT CAUSE: config_parser.ts:83-85
     *   if (section !== "default") { lines.push(`[${section}]`); }
     * The serializer unconditionally omits the header for the "default" section,
     * even when the input contained an explicit [default] section header. The
     * round-trip silently drops the [default] header.
     *
     * CODE LOCATION: config_parser.ts:83-85
     * PROPOSED FIX: Track which sections were explicitly declared (e.g., a Set) and
     * emit the header for any section that was declared explicitly, including "default".
     *
     * EXPECTED: serialized output contains "[default]"
     * ACTUAL:   serialized output never contains "[default]"
     */
    const input = "[default]\nkey = val\n[other]\nfoo = bar";
    const config = parseConfig(input);
    const serialized = serializeConfig(config);
    expect(serialized).toContain("[default]");
  });

  it("does not include raw key with value that was originally quoted", () => {
    // raw stores the unquoted value; serialize should write it back unquoted
    const config = parseConfig('name = "Alice"');
    const result = serializeConfig(config);
    expect(result).toContain("name = Alice");
    expect(result).not.toContain('"Alice"');
  });
});

// =============================================================================
// getValue
// =============================================================================

describe("getValue", () => {
  it("returns the default when section is missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", "fallback")).toBe("fallback");
  });

  it("returns undefined when section is missing and no default supplied", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key")).toBeUndefined();
  });

  it("returns the default when key is missing in an existing section", () => {
    const config = parseConfig("[db]\nhost = localhost");
    expect(getValue(config, "db", "missing_key", 9999)).toBe(9999);
  });

  it("returns undefined when key is missing and no default supplied", () => {
    const config = parseConfig("[db]\nhost = localhost");
    expect(getValue(config, "db", "missing_key")).toBeUndefined();
  });

  it("returns typed string value", () => {
    const config = parseConfig("[app]\nname = myapp");
    expect(getValue(config, "app", "name")).toBe("myapp");
  });

  it("returns typed number value", () => {
    const config = parseConfig("[app]\nport = 3000");
    expect(getValue(config, "app", "port")).toBe(3000);
  });

  it("returns typed boolean true value", () => {
    const config = parseConfig("[app]\ndebug = true");
    expect(getValue(config, "app", "debug")).toBe(true);
  });

  it("returns typed boolean false value", () => {
    const config = parseConfig("[app]\ndebug = false");
    expect(getValue(config, "app", "debug")).toBe(false);
  });

  it("returns value from the default section", () => {
    const config = parseConfig("host = localhost");
    expect(getValue(config, "default", "host")).toBe("localhost");
  });

  it("returns actual value even when a default is provided", () => {
    const config = parseConfig("[db]\nhost = prod");
    expect(getValue(config, "db", "host", "localhost")).toBe("prod");
  });

  it("returns numeric zero as default without ambiguity", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", 0)).toBe(0);
  });

  it("returns boolean false as default without ambiguity", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", false)).toBe(false);
  });

  it("returns empty string as default without ambiguity", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", "")).toBe("");
  });
});
