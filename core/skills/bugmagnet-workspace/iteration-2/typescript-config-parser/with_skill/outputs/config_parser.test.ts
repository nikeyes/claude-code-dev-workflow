import { describe, it, expect } from "vitest";
import { parseConfig, serializeConfig, getValue, getTypedValue } from "./config_parser";

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

  // --- Empty / minimal inputs ---
  it("returns empty default section when input is empty string", () => {
    const config = parseConfig("");
    expect(config["default"]).toEqual({});
  });

  it("returns empty default section when input is only whitespace lines", () => {
    const config = parseConfig("   \n   \n   ");
    expect(config["default"]).toEqual({});
  });

  it("returns only default section when input has only comments", () => {
    const config = parseConfig("# comment\n; another comment");
    expect(config["default"]).toEqual({});
    expect(Object.keys(config)).toEqual(["default"]);
  });

  // --- Comment handling ---
  it("ignores semicolon comment lines", () => {
    const config = parseConfig("; comment\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("strips inline hash comments from values", () => {
    const config = parseConfig("key = value # inline comment");
    expect(config["default"]["key"].raw).toBe("value");
  });

  it.skip("returns color value containing hash character - BUG", () => {
    /*
     * BUG: Inline comment stripping removes value content when value contains '#'
     *
     * ROOT CAUSE: config_parser.ts:56 uses trimmed.indexOf("#") to find comments.
     * This incorrectly strips value content when the value itself contains '#',
     * such as HTML color codes like "#ff0000". When value starts with "#",
     * effective becomes "key = " (everything before #), so rawValue becomes "".
     *
     * CODE LOCATION: config_parser.ts:56-58
     * CURRENT CODE:
     *   const commentIdx = trimmed.indexOf("#");
     *   const effective = commentIdx >= 0 ? trimmed.slice(0, commentIdx).trimEnd() : trimmed;
     * PROPOSED FIX:
     *   Only treat '#' as a comment start when preceded by whitespace.
     *   Use regex: /\s#/ or find first '#' not immediately following '=' value.
     *
     * EXPECTED: config["default"]["color"].raw === "#ff0000"
     * ACTUAL:   config["default"]["color"].raw === "" (empty, stripped)
     */
    const config = parseConfig("color = #ff0000");
    expect(config["default"]["color"].raw).toBe("#ff0000");
  });

  // --- Section handling ---
  it("places keys before any section header into default section", () => {
    const config = parseConfig("key1 = a\n[section]\nkey2 = b");
    expect(config["default"]["key1"].raw).toBe("a");
    expect(config["section"]["key2"].raw).toBe("b");
  });

  it("parses multiple sections independently", () => {
    const input = "[db]\nhost = localhost\n[cache]\nhost = redis";
    const config = parseConfig(input);
    expect(config["db"]["host"].raw).toBe("localhost");
    expect(config["cache"]["host"].raw).toBe("redis");
  });

  it("merges keys when same section appears multiple times", () => {
    const input = "[db]\nhost = localhost\n[db]\nport = 5432";
    const config = parseConfig(input);
    expect(config["db"]["host"].raw).toBe("localhost");
    expect(config["db"]["port"].raw).toBe("5432");
  });

  it("overwrites earlier key when same key appears twice in a section", () => {
    const config = parseConfig("[s]\nkey = first\nkey = second");
    expect(config["s"]["key"].raw).toBe("second");
  });

  it("trims whitespace from section names", () => {
    const config = parseConfig("[ section with spaces ]\nkey = value");
    expect(config["section with spaces"]["key"].raw).toBe("value");
  });

  // --- Value types ---
  it("parses boolean true value", () => {
    const config = parseConfig("enabled = true");
    expect(config["default"]["enabled"].typed).toBe(true);
    expect(config["default"]["enabled"].raw).toBe("true");
  });

  it("parses boolean false value", () => {
    const config = parseConfig("enabled = false");
    expect(config["default"]["enabled"].typed).toBe(false);
  });

  it("parses integer value as number", () => {
    const config = parseConfig("port = 8080");
    expect(config["default"]["port"].typed).toBe(8080);
  });

  it("parses float value as number", () => {
    const config = parseConfig("threshold = 0.95");
    expect(config["default"]["threshold"].typed).toBe(0.95);
  });

  it("parses zero as number", () => {
    const config = parseConfig("count = 0");
    expect(config["default"]["count"].typed).toBe(0);
  });

  it("parses string value as string", () => {
    const config = parseConfig("name = hello");
    expect(config["default"]["name"].typed).toBe("hello");
  });

  // --- Quoted values ---
  it("strips double quotes from value", () => {
    const config = parseConfig('name = "hello world"');
    expect(config["default"]["name"].raw).toBe("hello world");
  });

  it("strips single quotes from value", () => {
    const config = parseConfig("name = 'hello world'");
    expect(config["default"]["name"].raw).toBe("hello world");
  });

  it("returns value unchanged when quotes are mismatched", () => {
    const config = parseConfig("name = \"hello'");
    expect(config["default"]["name"].raw).toBe("\"hello'");
  });

  it("returns value unchanged when only one quote present", () => {
    const config = parseConfig("name = hello'");
    expect(config["default"]["name"].raw).toBe("hello'");
  });

  // --- Values with special characters ---
  it.skip("parses value containing equals sign - BUG", () => {
    /*
     * BUG: Values containing '=' are truncated after the first '=' in the value.
     *
     * ROOT CAUSE: config_parser.ts:60-64
     *   const parts = effective.split("=");
     *   const rawValue = parts[1].trim();
     * This splits on ALL '=' characters and takes only parts[1],
     * discarding everything from the second '=' onward.
     * For example, "url = http://x?a=b&c=d" yields rawValue = "http://x?a".
     *
     * CODE LOCATION: config_parser.ts:60-64
     * CURRENT CODE:
     *   const parts = effective.split("=");
     *   if (parts.length < 2) continue;
     *   const key = parts[0].trim();
     *   const rawValue = parts[1].trim();
     * PROPOSED FIX:
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

  it("skips lines without an equals sign", () => {
    const config = parseConfig("no_equals_here\nkey = value");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("skips lines where key is empty after trim", () => {
    const config = parseConfig("= value\nkey = ok");
    expect(Object.keys(config["default"])).toEqual(["key"]);
  });

  it("parses key with underscore and hyphen", () => {
    const config = parseConfig("my_key-name = value");
    expect(config["default"]["my_key-name"].raw).toBe("value");
  });

  it("parses Windows CRLF line endings correctly", () => {
    // split("\n") leaves "\r" in each line, but trim() strips it
    const config = parseConfig("key = value\r\n[section]\r\nother = val\r\n");
    expect(config["default"]["key"].raw).toBe("value");
    expect(config["section"]["other"].raw).toBe("val");
  });
});

describe("getTypedValue", () => {
  it("returns true boolean for string 'true'", () => {
    expect(getTypedValue("true")).toBe(true);
  });

  it("returns false boolean for string 'false'", () => {
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

  it("returns number for negative number string", () => {
    expect(getTypedValue("-5")).toBe(-5);
  });

  it("returns string for empty string", () => {
    // Number("") is 0, but "".trim() === "" so guard prevents number conversion
    expect(getTypedValue("")).toBe("");
  });

  it("returns string for whitespace-only string", () => {
    // Number("   ") is 0, but "   ".trim() === "" so guard prevents number conversion
    expect(getTypedValue("   ")).toBe("   ");
  });

  it("returns string for non-numeric string", () => {
    expect(getTypedValue("hello")).toBe("hello");
  });

  it("returns string for 'NaN'", () => {
    // Number("NaN") is NaN, isNaN check prevents number conversion
    expect(getTypedValue("NaN")).toBe("NaN");
  });

  it.skip("returns string for 'Infinity' - BUG", () => {
    /*
     * BUG: The string "Infinity" is converted to the number Infinity
     *
     * ROOT CAUSE: config_parser.ts:28-29
     *   const num = Number(raw);
     *   if (!isNaN(num) && raw.trim() !== "") return num;
     * Number("Infinity") === Infinity, and !isNaN(Infinity) is true,
     * so "Infinity" is returned as the number Infinity.
     * This is almost certainly not intended behavior for config files.
     *
     * CODE LOCATION: config_parser.ts:28-29
     * PROPOSED FIX:
     *   if (!isNaN(num) && isFinite(num) && raw.trim() !== "") return num;
     *
     * EXPECTED: getTypedValue("Infinity") === "Infinity" (string)
     * ACTUAL:   getTypedValue("Infinity") === Infinity (number)
     */
    expect(getTypedValue("Infinity")).toBe("Infinity");
  });

  it.skip("returns string for '-Infinity' - BUG", () => {
    /*
     * BUG: "-Infinity" is converted to the number -Infinity (same root cause as Infinity bug)
     *
     * CODE LOCATION: config_parser.ts:28-29
     * PROPOSED FIX: add isFinite(num) check (see 'Infinity' bug above)
     *
     * EXPECTED: getTypedValue("-Infinity") === "-Infinity" (string)
     * ACTUAL:   getTypedValue("-Infinity") === -Infinity (number)
     */
    expect(getTypedValue("-Infinity")).toBe("-Infinity");
  });

  it("returns number for scientific notation string", () => {
    // Number("1e2") === 100, this is current documented behavior
    expect(getTypedValue("1e2")).toBe(100);
  });

  it("returns number for string with leading/trailing spaces", () => {
    // Number("  42  ") === 42, and "  42  ".trim() !== "" so returns number
    expect(getTypedValue("  42  ")).toBe(42);
  });

  it("returns string for 'True' with capital T", () => {
    // Only exact lowercase "true" triggers boolean conversion
    expect(getTypedValue("True")).toBe("True");
  });

  it("returns string for 'FALSE' in uppercase", () => {
    expect(getTypedValue("FALSE")).toBe("FALSE");
  });
});

describe("serializeConfig", () => {
  it("serializes default section without a section header", () => {
    const config = parseConfig("key = value");
    const result = serializeConfig(config);
    // default section has no header; result contains the key-value pair
    expect(result).toContain("key = value");
    expect(result).not.toContain("[default]");
  });

  it("serializes non-default section with a section header", () => {
    const config = parseConfig("[db]\nhost = localhost");
    const result = serializeConfig(config);
    // parseConfig always creates empty default section first, producing a leading newline
    // before the named section
    expect(result).toContain("[db]");
    expect(result).toContain("host = localhost");
  });

  it("serializes multiple sections with section headers", () => {
    const config = parseConfig("[db]\nhost = localhost\n[cache]\nport = 6379");
    const result = serializeConfig(config);
    expect(result).toContain("[db]");
    expect(result).toContain("host = localhost");
    expect(result).toContain("[cache]");
    expect(result).toContain("port = 6379");
  });

  it("returns empty string for empty config", () => {
    const config = parseConfig("");
    const result = serializeConfig(config);
    expect(result).toBe("");
  });

  it("round-trips a config through parse and serialize", () => {
    const input = "[section]\nkey = value\nport = 5432";
    const config = parseConfig(input);
    const serialized = serializeConfig(config);
    const reparsed = parseConfig(serialized);
    expect(reparsed["section"]["key"].raw).toBe("value");
    expect(reparsed["section"]["port"].typed).toBe(5432);
  });

  it("serializes boolean values as their raw string form", () => {
    const config = parseConfig("enabled = true");
    const result = serializeConfig(config);
    expect(result).toContain("enabled = true");
  });

  it.skip("omits [default] header for explicitly declared default section - BUG", () => {
    /*
     * BUG: When input explicitly declares a [default] section,
     * serializeConfig omits the [default] header in the output.
     * While the round-trip still works (keys go back into default), the
     * serialized output does not match the original format.
     *
     * CODE LOCATION: config_parser.ts:83-85
     * CURRENT CODE:
     *   if (section !== "default") { lines.push(`[${section}]`); }
     * PROPOSED FIX: Track whether the section was explicitly declared.
     * This is a design/documentation issue — the behavior should be documented
     * or the explicit [default] header should be preserved.
     *
     * EXPECTED: serialized output includes "[default]"
     * ACTUAL:   "[default]" header is always omitted
     */
    const input = "[default]\nkey = val\n[other]\nfoo = bar";
    const config = parseConfig(input);
    const serialized = serializeConfig(config);
    expect(serialized).toContain("[default]");
  });
});

describe("getValue", () => {
  it("returns default when section missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", "fallback")).toBe("fallback");
  });

  it("returns undefined when section missing and no default provided", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key")).toBeUndefined();
  });

  it("returns default value when key missing in existing section", () => {
    const config = parseConfig("[db]\nhost = localhost");
    expect(getValue(config, "db", "port", 5432)).toBe(5432);
  });

  it("returns undefined when key missing and no default provided", () => {
    const config = parseConfig("[db]\nhost = localhost");
    expect(getValue(config, "db", "port")).toBeUndefined();
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

  it("returns typed value from default section", () => {
    const config = parseConfig("host = localhost");
    expect(getValue(config, "default", "host")).toBe("localhost");
  });

  it("returns actual value not default when key exists", () => {
    const config = parseConfig("[db]\nhost = prod-server");
    expect(getValue(config, "db", "host", "localhost")).toBe("prod-server");
  });
});

// =============================================================================
// Phase 4: Advanced Coverage — bugmagnet session 2026-04-26
// =============================================================================

describe("bugmagnet session 2026-04-26", () => {
  // --- Numeric edge cases in values ---
  it("parses very large integer as number type", () => {
    const config = parseConfig("big = 9007199254740991");
    expect(config["default"]["big"].typed).toBe(9007199254740991);
  });

  it("parses negative number as number", () => {
    const config = parseConfig("val = -42");
    expect(config["default"]["val"].typed).toBe(-42);
  });

  it("parses whitespace-surrounded 'true' as boolean after key/value trim", () => {
    const config = parseConfig("  enabled  =  true  ");
    expect(config["default"]["enabled"].typed).toBe(true);
  });

  // --- String edge cases ---
  it("parses value that is only whitespace as empty string", () => {
    // "key =   " — parts[1].trim() === "" — stored as empty raw
    const config = parseConfig("key =   ");
    expect(config["default"]["key"].raw).toBe("");
  });

  it("parses very long value string of 10000 characters", () => {
    const longValue = "x".repeat(10000);
    const config = parseConfig(`key = ${longValue}`);
    expect(config["default"]["key"].raw.length).toBe(10000);
    expect(config["default"]["key"].raw).toBe(longValue);
  });

  it("parses unicode characters in values", () => {
    const config = parseConfig("greeting = こんにちは");
    expect(config["default"]["greeting"].raw).toBe("こんにちは");
  });

  it("parses unicode characters in keys", () => {
    const config = parseConfig("名前 = test");
    expect(config["default"]["名前"].raw).toBe("test");
  });

  // --- Security edge cases ---
  it("parses SQL injection pattern as plain string value", () => {
    const config = parseConfig("input = Robert'); DROP TABLE students;--");
    expect(config["default"]["input"].raw).toBe("Robert'); DROP TABLE students;--");
  });

  it("parses XSS pattern in value as plain string", () => {
    const config = parseConfig("value = <script>alert(1)</script>");
    expect(config["default"]["value"].raw).toBe("<script>alert(1)</script>");
  });

  // --- Collection / scale edge cases ---
  it("parses config with 100 key-value pairs", () => {
    const lines = Array.from({ length: 100 }, (_, i) => `key${i} = value${i}`).join("\n");
    const config = parseConfig(lines);
    expect(Object.keys(config["default"]).length).toBe(100);
    expect(config["default"]["key0"].raw).toBe("value0");
    expect(config["default"]["key99"].raw).toBe("value99");
  });

  it("parses config with 20 different sections", () => {
    const lines = Array.from({ length: 20 }, (_, i) => `[section${i}]\nkey = val${i}`).join("\n");
    const config = parseConfig(lines);
    expect(Object.keys(config).length).toBe(21); // 20 named + default
    expect(config["section0"]["key"].raw).toBe("val0");
    expect(config["section19"]["key"].raw).toBe("val19");
  });

  // --- Stateful / independence ---
  it("returns independent configs when parseConfig is called twice", () => {
    const config1 = parseConfig("[s]\nkey = a");
    const config2 = parseConfig("[s]\nkey = b");
    expect(config1["s"]["key"].raw).toBe("a");
    expect(config2["s"]["key"].raw).toBe("b");
  });

  // --- Domain constraint violations ---
  it("handles section name that is only whitespace resulting in empty string key", () => {
    // "[   ]" — trimmed.slice(1,-1).trim() === "" — section name becomes ""
    const config = parseConfig("[   ]\nkey = value");
    expect(config[""]).toBeDefined();
    expect(config[""]["key"].raw).toBe("value");
  });

  it("returns numeric zero default value when section missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", 0)).toBe(0);
  });

  it("returns boolean false default value when section missing", () => {
    const config = parseConfig("");
    expect(getValue(config, "missing", "key", false)).toBe(false);
  });

  // --- Bug cluster: values with equals signs ---
  it.skip("preserves full URL value containing equals sign in query param - BUG", () => {
    /*
     * BUG: URL values with query parameters containing '=' are silently truncated.
     * This is a cluster of the primary '=' split bug documented above.
     *
     * MINIMAL REPRODUCTION:
     *   parseConfig("url = http://host?a=1&b=2")
     *   → config["default"]["url"].raw === "http://host?a" (truncated at 2nd =)
     *
     * ROOT CAUSE: config_parser.ts:60-64 — split("=") then takes only parts[1]
     * PROPOSED FIX: Use indexOf("=") and slice to split only on first '='
     *
     * EXPECTED: "http://host?a=1&b=2"
     * ACTUAL:   "http://host?a"
     */
    const config = parseConfig("url = http://host?a=1&b=2");
    expect(config["default"]["url"].raw).toBe("http://host?a=1&b=2");
  });

  it.skip("preserves base64 value with equals-sign padding - BUG", () => {
    /*
     * BUG: Base64 values with '=' padding characters are truncated.
     * Same root cause as the URL equals-sign bug.
     *
     * MINIMAL REPRODUCTION:
     *   parseConfig("token = dXNlcjpwYXNzd29yZA==")
     *   → config["default"]["token"].raw === "dXNlcjpwYXNzd29yZA" (padding stripped)
     *
     * ROOT CAUSE: config_parser.ts:60-64 — split("=") loses content after 2nd '='
     * PROPOSED FIX: Use indexOf("=") and slice to split only on first '='
     *
     * EXPECTED: raw === "dXNlcjpwYXNzd29yZA=="
     * ACTUAL:   raw === "dXNlcjpwYXNzd29yZA"
     */
    const config = parseConfig("token = dXNlcjpwYXNzd29yZA==");
    expect(config["default"]["token"].raw).toBe("dXNlcjpwYXNzd29yZA==");
  });

  it.skip("parses HTML color code starting with hash as value - BUG", () => {
    /*
     * BUG: Values starting with '#' are treated as inline comments, stripping the value.
     * This is a cluster of the inline comment stripping bug documented above.
     *
     * MINIMAL REPRODUCTION:
     *   parseConfig("bg = #ff0000")
     *   → config["default"]["bg"].raw === "" (empty, entire value stripped)
     *
     * ROOT CAUSE: config_parser.ts:56-58
     *   const commentIdx = trimmed.indexOf("#");
     *   effective = trimmed.slice(0, commentIdx).trimEnd()  // = "bg ="
     * Then split("=") → parts[1].trim() === "" so raw is stored as "".
     *
     * PROPOSED FIX: Only treat '#' as comment when preceded by at least one space.
     * Use: /\s+#/.exec(trimmed) to find comment start position.
     *
     * EXPECTED: config["default"]["bg"].raw === "#ff0000"
     * ACTUAL:   config["default"]["bg"].raw === "" (empty string)
     */
    const config = parseConfig("bg = #ff0000");
    expect(config["default"]["bg"].raw).toBe("#ff0000");
  });
});
