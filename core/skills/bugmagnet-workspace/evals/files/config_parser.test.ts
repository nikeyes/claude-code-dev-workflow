import { describe, it, expect } from "vitest";
import { parseConfig, serializeConfig, getValue } from "./config_parser";

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
