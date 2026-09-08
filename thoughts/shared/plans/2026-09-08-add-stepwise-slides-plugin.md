# Add `stepwise-slides` plugin (vendored from `zarazhangrui/frontend-slides`)

## Overview

Add a fifth plugin — `stepwise-slides` — to the stepwise-dev marketplace by vendoring `zarazhangrui/frontend-slides` (MIT) via `git subtree` at the `slides/` prefix. Keep the upstream layout untouched so future `git subtree pull` runs cleanly, and wrap it in stepwise-dev's marketplace + Codex conventions.

## Current State Analysis

- The repo ships four plugins (`core/`, `git/`, `web/`, `research/`) declared in `.claude-plugin/marketplace.json:11-40`, each with a flat `<plugin>/.claude-plugin/plugin.json` + `<plugin>/skills/` or `<plugin>/agents/` layout.
- `codex/install.sh:15` symlinks every skill dir from `core/skills/*/`, `git/skills/*/`, `research/skills/*/` into `~/.agents/skills/`. `web/` is skipped because it only has agents.
- Versioning rules in `.claude/rules/versioning.md` require plugin-level + marketplace-level bumps on any change; a **new plugin** starts at `1.0.0` and triggers a **minor** bump on the marketplace top-level version.
- Upstream `zarazhangrui/frontend-slides` (MIT) is itself packaged as a Claude Code marketplace with a **nested plugin** at `plugins/frontend-slides/`, plus a duplicate `SKILL.md` and `.claude-plugin/marketplace.json` at its root (inert weight for us).
- Upstream `SKILL.md` has **no `model:` frontmatter** and there are **no agents**, so no transpilation or `inherit` migration is required.

## Desired End State

- `slides/` in the repo contains the upstream tree verbatim (imported via `git subtree add --squash`).
- `.claude-plugin/marketplace.json` gains a fifth entry `stepwise-slides` (v `1.0.0`) whose `source` points to `./slides/plugins/frontend-slides`; top-level marketplace version bumped from `1.0.1` → `1.1.0`.
- `codex/install.sh` symlinks `slides/plugins/frontend-slides/skills/*/` into `~/.agents/skills/` alongside the others.
- `AGENTS.md` and `README.md` document the new plugin, its attribution to Zara Zhang (MIT), and the one-liner for optional future sync.
- Smoke tests validate the new plugin's structural integrity.
- Verification: `make ci` green; `make install-codex` creates the `~/.agents/skills/frontend-slides` symlink; installing the plugin in Claude Code loads the `frontend-slides` skill.

### Key Discoveries:

- Upstream plugin.json: `plugins/frontend-slides/.claude-plugin/plugin.json` (version `2.1.0`, MIT, author `zarazhangrui`). We do NOT touch this file.
- Upstream SKILL.md frontmatter has only `name` + `description` (no `model:`) → no Codex warning, no migration needed.
- `codex/install.sh:15` uses a single `for skill in ...` loop — extending it is a one-line change.
- Nested `source` path in `marketplace.json` is unusual for this repo but supported by Claude Code's plugin resolver.

## What We're NOT Doing

- **Not modifying any file inside `slides/`.** Every future `git subtree pull` must succeed without conflicts.
- **Not migrating the upstream `SKILL.md` frontmatter to `model: inherit`** (there's no `model:` key to migrate anyway).
- **Not transpiling agents to Codex TOML** (upstream has no agents).
- **Not adding a NOTICE or ATTRIBUTION.md file** — MIT is satisfied by preserving `slides/LICENSE`; attribution lives in the marketplace entry + README.
- **Not deleting upstream duplicates** (`slides/SKILL.md`, `slides/.claude-plugin/marketplace.json`) — inert, deleting them breaks subtree pulls.
- **Not automating `git subtree pull`** in CI — documented as a manual one-liner in AGENTS.md, executed on demand.
- **Not writing content tests** for the skill's templates, HTML output, or animations — upstream owns that.

## Implementation Approach

Vendoring via `git subtree add --squash` preserves upstream history as a single squashed commit and lets us pull upstream updates later without submodule friction. The nested `slides/plugins/frontend-slides/` path is a small pattern break paid once in the marketplace entry, in exchange for zero-friction sync.

---

## Phase 1: Import upstream via git subtree

### Overview
Bring `zarazhangrui/frontend-slides@main` into the repo at prefix `slides/` as a single squashed commit.

### Changes Required:

#### 1. Subtree import
Run once from the repo root:

```bash
git subtree add \
  --prefix=slides \
  https://github.com/zarazhangrui/frontend-slides.git \
  main --squash
```

This produces one merge commit and one squashed commit; the resulting tree has:
- `slides/LICENSE` (upstream MIT, preserved for attribution)
- `slides/plugins/frontend-slides/.claude-plugin/plugin.json`
- `slides/plugins/frontend-slides/skills/frontend-slides/SKILL.md`
- `slides/plugins/frontend-slides/skills/frontend-slides/bold-template-pack/…` (~40+ template dirs)
- Inert upstream duplicates: `slides/SKILL.md`, `slides/.claude-plugin/marketplace.json` (do not delete)

### Success Criteria:
- [ ] `slides/LICENSE` exists and is MIT.
- [ ] `slides/plugins/frontend-slides/.claude-plugin/plugin.json` parses as JSON: `jq . slides/plugins/frontend-slides/.claude-plugin/plugin.json`
- [ ] `slides/plugins/frontend-slides/skills/frontend-slides/SKILL.md` exists with frontmatter containing `name: frontend-slides`.
- [ ] `git log --oneline -3` shows the squash+merge from the subtree add.

---

## Phase 2: Wire into the marketplace

### Overview
Add the `stepwise-slides` entry to `.claude-plugin/marketplace.json` and bump the top-level version.

### Changes Required:

#### 1. Marketplace manifest
**File**: `.claude-plugin/marketplace.json`
**Changes**: Add a fifth entry to `plugins[]`; bump top-level `version` from `1.0.1` → `1.1.0` (minor: new plugin added per `.claude/rules/versioning.md`).

```json
{
  "name": "stepwise-slides",
  "source": "./slides/plugins/frontend-slides",
  "version": "1.0.0",
  "description": "Create beautiful HTML slides from a coding agent — vendored from zarazhangrui/frontend-slides (MIT)",
  "author": {
    "name": "Zara Zhang",
    "url": "https://github.com/zarazhangrui/frontend-slides"
  },
  "keywords": ["slides", "presentation", "html", "generative-ui", "vendored"]
}
```

### Success Criteria:
- [ ] `jq '.version' .claude-plugin/marketplace.json` returns `"1.1.0"`.
- [ ] `jq '.plugins[] | select(.name == "stepwise-slides")' .claude-plugin/marketplace.json` returns the new entry.
- [ ] `jq '.plugins[].source' .claude-plugin/marketplace.json` includes `"./slides/plugins/frontend-slides"`.

---

## Phase 3: Codex compatibility

### Overview
Symlink the upstream skill dir into `~/.agents/skills/` when `make install-codex` runs.

### Changes Required:

#### 1. Extend Codex install script
**File**: `codex/install.sh:15`
**Changes**: Append `slides/plugins/frontend-slides/skills/*/` to the skill-iteration glob.

```bash
for skill in "$REPO_ROOT"/core/skills/*/ \
             "$REPO_ROOT"/git/skills/*/ \
             "$REPO_ROOT"/research/skills/*/ \
             "$REPO_ROOT"/slides/plugins/frontend-slides/skills/*/; do
```

**Verification during implementation**: `grep -nE '(\$HOME|/Users/|/tmp)' slides/plugins/frontend-slides/skills/frontend-slides/SKILL.md` — must return nothing. Upstream SKILL.md is self-contained with relative paths; if this check fails, add a wrapper skill instead of symlinking directly. (Expected: passes without change.)

### Success Criteria:
- [ ] `make install-codex` succeeds.
- [ ] `readlink ~/.agents/skills/frontend-slides` resolves to `<repo>/slides/plugins/frontend-slides/skills/frontend-slides`.
- [ ] `make uninstall-codex` removes the symlink cleanly.
- [ ] `make check-codex` passes (no agents to transpile → no diff).

---

## Phase 4: Smoke tests

### Overview
Add four cheap structural checks to `test/smoke-test.sh` covering the new plugin's shape.

### Changes Required:

#### 1. Extend smoke test suite
**File**: `test/smoke-test.sh`
**Changes**: Add a new test group `stepwise_slides_structure` that runs:

1. `slides/LICENSE` exists and starts with `MIT License`.
2. `slides/plugins/frontend-slides/.claude-plugin/plugin.json` is valid JSON with `.name == "frontend-slides"`.
3. `slides/plugins/frontend-slides/skills/frontend-slides/SKILL.md` exists and has YAML frontmatter with `name:` and `description:` keys.
4. `.claude-plugin/marketplace.json` has an entry `.plugins[] | select(.name == "stepwise-slides")` whose `source` equals `./slides/plugins/frontend-slides`.

Use the existing helpers in `test/test-helpers.sh` (assertion patterns like `assert_file_exists`, `assert_json_valid`).

### Success Criteria:
- [ ] `make test` passes (existing + new checks).
- [ ] `make test-verbose` shows the four new assertions running.
- [ ] `make check` (shellcheck) passes on `test/smoke-test.sh`.

---

## Phase 5: Documentation

### Overview
Document the new plugin, its provenance, and the optional sync workflow.

### Changes Required:

#### 1. AGENTS.md
**File**: `AGENTS.md`
**Changes**:
- Update "Multi-Plugin Architecture" from "4 independent Claude Code plugins" → **5**.
- Add a "Plugin 5: stepwise-slides" section mirroring the existing four (Location `slides/plugins/frontend-slides/`, Components: 1 skill).
- Update the `Project Structure` tree with the `slides/` branch.
- Add an install line under "Installation": `claude plugin install stepwise-slides@stepwise-dev`.
- Add a new subsection **"Vendored plugins"** documenting:
  - Origin: `zarazhangrui/frontend-slides`, MIT, author Zara Zhang.
  - Import method: `git subtree add --prefix=slides --squash`.
  - Optional update: `git subtree pull --prefix=slides https://github.com/zarazhangrui/frontend-slides.git main --squash`.
  - Reminder: do not edit files under `slides/`; wrap externally if divergence is needed.
- Update the "Attribution" section at the bottom to mention Zara Zhang / frontend-slides alongside HumanLayer.

#### 2. README.md
**File**: `README.md`
**Changes**: Add the new install command and a one-line description in the plugin list.

### Success Criteria:
- [ ] `AGENTS.md` mentions "5 independent Claude Code plugins" and includes the `slides/` tree.
- [ ] `AGENTS.md` has a "Vendored plugins" section with the exact `git subtree pull` one-liner.
- [ ] `README.md` lists `claude plugin install stepwise-slides@stepwise-dev`.
- [ ] Both files mention Zara Zhang + MIT + upstream URL.

---

## Testing Strategy

### Automated (in this repo):
- `make test` — smoke checks from Phase 4.
- `make check` — shellcheck on scripts.
- `make check-codex` — no-op for slides (no agents), guards accidental regressions.
- `make ci` — umbrella target already wires the above.

### Manual (one-time acceptance):
1. From a scratch dir: `claude plugin marketplace add <local-path-or-git-url>` then `claude plugin install stepwise-slides@stepwise-dev`, restart Claude Code, invoke the `frontend-slides` skill, confirm it loads.
2. `make install-codex` and confirm `~/.agents/skills/frontend-slides` resolves.
3. (Optional) Trigger the skill from a test project and generate a sample deck to confirm no path breakage from the nested layout.

## Migration Notes

None. This is additive: no existing plugin, script, or test is modified in a breaking way. Users on stepwise-dev prior to this change are unaffected until they run `claude plugin install stepwise-slides@stepwise-dev`.

## Future Sync (documented, not automated)

When you want to pull upstream changes:

```bash
git subtree pull \
  --prefix=slides \
  https://github.com/zarazhangrui/frontend-slides.git \
  main --squash
```

If the pull brings meaningful content changes, bump `stepwise-slides` in `marketplace.json` (patch: e.g. `1.0.0` → `1.0.1`) and patch-bump the top-level marketplace version per `.claude/rules/versioning.md`.

## References

- Upstream: https://github.com/zarazhangrui/frontend-slides (MIT, author Zara Zhang)
- Versioning rules: `.claude/rules/versioning.md`
- Marketplace manifest: `.claude-plugin/marketplace.json:1-42`
- Codex install script: `codex/install.sh:15`
- Prior vendored-plugin precedent: none in this repo (this is the first).
