export interface ConfigValue {
  raw: string;
  typed: string | number | boolean;
}

export interface ConfigSection {
  [key: string]: ConfigValue;
}

export interface Config {
  [section: string]: ConfigSection;
}

function stripQuotes(value: string): string {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

export function getTypedValue(raw: string): string | number | boolean {
  if (raw === "true") return true;
  if (raw === "false") return false;

  const num = Number(raw);
  if (!isNaN(num) && raw.trim() !== "") return num;

  return raw;
}

export function parseConfig(input: string): Config {
  const config: Config = {};
  let currentSection = "default";
  config[currentSection] = {};

  const lines = input.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("#") || trimmed.startsWith(";")) {
      continue;
    }

    if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
      currentSection = trimmed.slice(1, -1).trim();
      if (!config[currentSection]) {
        config[currentSection] = {};
      }
      continue;
    }

    const commentIdx = trimmed.indexOf("#");
    const effective =
      commentIdx >= 0 ? trimmed.slice(0, commentIdx).trimEnd() : trimmed;

    const parts = effective.split("=");
    if (parts.length < 2) continue;

    const key = parts[0].trim();
    const rawValue = parts[1].trim();

    if (!key) continue;

    const cleanValue = stripQuotes(rawValue);

    config[currentSection][key] = {
      raw: cleanValue,
      typed: getTypedValue(cleanValue),
    };
  }

  return config;
}

export function serializeConfig(config: Config): string {
  const lines: string[] = [];

  for (const [section, entries] of Object.entries(config)) {
    if (section !== "default") {
      lines.push(`[${section}]`);
    }
    for (const [key, value] of Object.entries(entries)) {
      lines.push(`${key} = ${value.raw}`);
    }
    lines.push("");
  }

  return lines.join("\n").trimEnd();
}

export function getValue(
  config: Config,
  section: string,
  key: string,
  defaultValue?: string | number | boolean
): string | number | boolean | undefined {
  const sec = config[section];
  if (!sec) return defaultValue;
  const entry = sec[key];
  if (!entry) return defaultValue;
  return entry.typed;
}
