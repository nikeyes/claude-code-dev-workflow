# Versioning rules

Every change in this repo must bump a version. Claude Code uses the version
field as the **cache key** that decides whether a user receives an update, so
skipping a bump means users stay on the old copy forever.

This repo ships **four independent plugins** through a single marketplace, so
there are two layers of versions and they are bumped **independently**:

1. **Plugin version**: the `version` field in each plugin's `plugin.json`
   (`core/.claude-plugin/plugin.json`, `git/.claude-plugin/plugin.json`,
   `web/.claude-plugin/plugin.json`, `research/.claude-plugin/plugin.json`).
2. **Marketplace version**: the top-level `version` field in
   `.claude-plugin/marketplace.json`.

`plugin.json.version` wins over any `version` set in the marketplace entry
(see [Version management](https://code.claude.com/docs/en/plugins-reference#version-management)),
but this repo also keeps a `version` field on each marketplace entry so the
Claude Code UI can display it. **Keep both in sync**: whenever you bump a
plugin's `plugin.json`, bump the matching entry in `marketplace.json.plugins[]`
to the same value. Never let them drift.

## When to bump a plugin version

Bump the `version` in that plugin's `plugin.json` whenever anything inside its
directory changes (`core/`, `git/`, `web/`, or `research/`). Use semver:

| Change                                                          | Bump          | Example        |
|-----------------------------------------------------------------|---------------|----------------|
| New skill / command / agent / hook / script added               | **minor**     | 1.2.0 to 1.3.0 |
| Existing skill/command/agent/hook/script edited or fixed        | **patch**     | 1.2.0 to 1.2.1 |
| Skill/command/agent/hook removed, renamed, or interface changed | **major**     | 1.2.0 to 2.0.0 |
| README-only or metadata-only edit inside the plugin dir         | **patch**     | 1.2.0 to 1.2.1 |
| Frontmatter tweak (e.g. `model: inherit`) on existing skill/agent | **patch**   | 1.2.0 to 1.2.1 |

If it's unclear which applies, **ask the user before bumping**.

When a change touches **more than one plugin dir**, bump each affected
plugin independently. Example: migrating `model:` frontmatter to `inherit`
across `core/`, `git/`, `web/`, and `research/` is a **patch bump on all
four** — they are independent packages, each with its own cache key.

## When to bump the marketplace version

Bump the top-level `version` in `.claude-plugin/marketplace.json` whenever the
**shape of the catalog itself** changes, meaning anything a user would need
to re-read the manifest to see:

| Change                                                                       | Bump      |
|------------------------------------------------------------------------------|-----------|
| New plugin entry added to `plugins[]`                                        | **minor** |
| Existing plugin entry edited (description, tags, keywords, source, ...)      | **patch** |
| Plugin removed or renamed (`renames` map used, or entry deleted)             | **major** |
| Marketplace metadata edited (`owner`, `metadata`, `pluginRoot`, ...)         | **patch** |
| A plugin's per-entry `version` bumped to mirror its `plugin.json`            | **patch** |

Editing only the **contents** of a plugin (its skills, agents, README, etc.)
without touching its marketplace entry still requires syncing the mirrored
`version` inside `plugins[]` — and that in turn is a **patch** bump of the
top-level marketplace version.

## Rule of thumb

- Changed files inside `core/`, `git/`, `web/`, or `research/`:
  1. Bump that plugin's `plugin.json.version`.
  2. Mirror the new value into the matching entry in `marketplace.json.plugins[]`.
  3. Bump the top-level `marketplace.json.version` (patch).
- Changed `.claude-plugin/marketplace.json` structure or metadata: bump the
  top-level `version` per the table above.
- A PR that adds a new plugin bumps **both**: the new plugin starts at
  `1.0.0`, and the marketplace gets a **minor** bump.

## Worked example

Migrating `model:` frontmatter to `inherit` across every skill/agent in the
four plugins:

- `core/.claude-plugin/plugin.json`: patch bump (e.g. `1.4.0` → `1.4.1`).
- `git/.claude-plugin/plugin.json`: patch bump (e.g. `1.5.0` → `1.5.1`).
- `web/.claude-plugin/plugin.json`: patch bump (e.g. `1.0.0` → `1.0.1`).
- `research/.claude-plugin/plugin.json`: patch bump (e.g. `1.1.0` → `1.1.1`).
- `.claude-plugin/marketplace.json`: mirror each new version into its
  `plugins[]` entry, and patch-bump the top-level `version`.

## Reference

- Plugin manifest & version management: https://code.claude.com/docs/en/plugins-reference#version-management
- Marketplace manifest: https://code.claude.com/docs/en/plugin-marketplaces
