# Refactor thoughts-management to Support Config File for Directory Structures

## Overview

The `thoughts-management` skill currently uses a partially-hardcoded directory layout: the top-level root (`thoughts/`) and the shared subdirectory names (`shared/research`, `shared/plans`, `shared/prs`) are baked into the `thoughts-init` script, and the personal username defaults to `nikey_es` overridable only via the `THOUGHTS_USER` environment variable. There is no way to rename `shared/` to something else, add extra subdirectories, remove unwanted ones, point the root to a different path, or describe the structure in a portable, self-documenting way that travels with the project.

This plan adds a `thoughts.config.json` file (created during `thoughts-init` and read by all scripts) so that teams can fully customise the directory layout without touching plugin source code.

---

## Current State Analysis

### Hardcoded locations

| File | Hardcoded value | Role |
|------|----------------|------|
| `core/skills/thoughts-management/scripts/thoughts-init:8` | `THOUGHTS_DIR="thoughts"` | Root directory name |
| `thoughts-init:37-41` | `shared/research`, `shared/plans`, `shared/prs`, `$USERNAME/tickets`, `$USERNAME/notes` | All subdirectories |
| `thoughts-init:7` | `USERNAME="${THOUGHTS_USER:-nikey_es}"` | Personal folder name |
| `SKILL.md:88-94` | The directory tree in documentation | Matches the hardcoded structure |
| `core/agents/thoughts-locator.md:18-20,41-48` | `thoughts/shared/`, `thoughts/{username}/`, `thoughts/global/` | Agent search paths |
| All consumer skills (`create-plan`, `research-codebase`, `iterate-plan`, `validate-plan`, `implement-plan`) | `thoughts/shared/plans/`, `thoughts/shared/research/` | Output file paths |

### Existing configuration mechanism

`THOUGHTS_USER` environment variable overrides the personal directory name. This is the only customisation point. It is not persisted, is not visible to agents, and covers only one of many configurable values.

### Test coverage

`test/thoughts-structure-test.sh` asserts the exact default directory names (`thoughts/nikey_es/tickets`, etc.). These tests must be updated or extended to cover config-driven layouts.

---

## Desired End State

After this refactoring:

1. Running `thoughts-init` in a project produces a `thoughts/thoughts.config.json` file alongside the directory tree.
2. The config file is human-readable JSON that documents and controls the layout:
   ```json
   {
     "version": "1",
     "root": "thoughts",
     "personal_dir": "nikey_es",
     "shared_dir": "shared",
     "personal_subdirs": ["tickets", "notes"],
     "shared_subdirs": ["research", "plans", "prs"]
   }
   ```
3. All scripts (`thoughts-init`, `thoughts-metadata`) read the config when it exists, falling back to defaults when it does not (full backward compatibility).
4. Users can edit `thoughts.config.json` to rename any directory segment or add/remove subdirectories, and subsequent `thoughts-init` runs (re-init mode) will honour the config.
5. The `THOUGHTS_USER` env var still works, but the config file takes precedence over the default; the env var overrides both.
6. Agents (`thoughts-locator`) read the config to know where to look instead of assuming `shared/`.
7. All existing tests continue to pass; new tests cover config-driven behaviour.

### Verification

```bash
make test        # All automated tests green
make check       # shellcheck clean
```

---

## What We Are NOT Doing

- We are not changing the default directory layout (the defaults remain identical to today).
- We are not supporting YAML or TOML config formats — JSON only for this iteration.
- We are not adding hot-reload; changes to `thoughts.config.json` take effect on the next script invocation.
- We are not updating every prose reference of `thoughts/shared/plans/` in SKILL.md documentation strings — those are illustrative examples, not runtime paths.
- We are not adding a `thoughts-config` sub-command or CLI flag parsing beyond what is needed.
- We are not migrating existing `thoughts/` trees to a new layout automatically.

---

## Implementation Approach

Use a small, self-contained shell function `load_thoughts_config` that is sourced by both scripts. The function looks for `thoughts.config.json` in the project root (same directory from which the scripts are run), parses it with `python3 -m json.tool` + `grep`/`sed` (no external dependencies), and exports shell variables. This keeps the solution portable and avoids adding `jq` as a hard dependency.

The config file is written by `thoughts-init` during first-time setup if it does not already exist. Re-running `thoughts-init` on an existing project reads the existing config (so customisations are not overwritten).

---

## Phase 1: Create the Config Reader Library

### Overview

Extract config-reading logic into a shared file that both scripts can source.

### Changes Required

#### 1. New file: `core/skills/thoughts-management/scripts/thoughts-config-lib`

This is a sourceable bash library (not executable directly).

```bash
#!/usr/bin/env bash
# thoughts-config-lib - Shared config reader for thoughts scripts
# Source this file; do not execute it directly.

# Defaults (match current hardcoded behaviour)
THOUGHTS_ROOT="${THOUGHTS_ROOT:-thoughts}"
THOUGHTS_PERSONAL_DIR="${THOUGHTS_USER:-nikey_es}"
THOUGHTS_SHARED_DIR="shared"
THOUGHTS_PERSONAL_SUBDIRS="tickets notes"
THOUGHTS_SHARED_SUBDIRS="research plans prs"

load_thoughts_config() {
  local config_file="${THOUGHTS_ROOT}/thoughts.config.json"
  [ -f "$config_file" ] || return 0   # no config — keep defaults

  # Parse with python3 (available on all modern macOS/Linux)
  local root personal shared p_subdirs s_subdirs
  root=$(python3 -c "import json,sys; d=json.load(open('$config_file')); print(d.get('root','thoughts'))" 2>/dev/null) && THOUGHTS_ROOT="$root"
  personal=$(python3 -c "import json,sys; d=json.load(open('$config_file')); print(d.get('personal_dir','nikey_es'))" 2>/dev/null) && THOUGHTS_PERSONAL_DIR="$personal"
  shared=$(python3 -c "import json,sys; d=json.load(open('$config_file')); print(d.get('shared_dir','shared'))" 2>/dev/null) && THOUGHTS_SHARED_DIR="$shared"
  p_subdirs=$(python3 -c "import json,sys; d=json.load(open('$config_file')); print(' '.join(d.get('personal_subdirs',['tickets','notes'])))" 2>/dev/null) && THOUGHTS_PERSONAL_SUBDIRS="$p_subdirs"
  s_subdirs=$(python3 -c "import json,sys; d=json.load(open('$config_file')); print(' '.join(d.get('shared_subdirs',['research','plans','prs'])))" 2>/dev/null) && THOUGHTS_SHARED_SUBDIRS="$s_subdirs"

  # THOUGHTS_USER env var overrides config personal_dir
  [ -n "${THOUGHTS_USER:-}" ] && THOUGHTS_PERSONAL_DIR="$THOUGHTS_USER"
}
```

### Success Criteria

- [ ] File exists at `core/skills/thoughts-management/scripts/thoughts-config-lib`
- [ ] `shellcheck` passes on the new file: `shellcheck core/skills/thoughts-management/scripts/thoughts-config-lib`

---

## Phase 2: Update `thoughts-init` to Write and Read Config

### Overview

Make `thoughts-init` generate `thoughts.config.json` on first run and honour an existing one on re-runs.

### Changes Required

#### 1. `core/skills/thoughts-management/scripts/thoughts-init`

Replace the current hardcoded variable block with:

```bash
# Source config library (same directory as this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=thoughts-config-lib
source "$SCRIPT_DIR/thoughts-config-lib"
load_thoughts_config

# After loading config, THOUGHTS_ROOT / THOUGHTS_PERSONAL_DIR / etc. are set.
# Rename local vars for clarity
THOUGHTS_DIR="$THOUGHTS_ROOT"
USERNAME="$THOUGHTS_PERSONAL_DIR"
SHARED_DIR="$THOUGHTS_SHARED_DIR"
```

Replace the hardcoded `mkdir -p` block with a loop:

```bash
for subdir in $THOUGHTS_PERSONAL_SUBDIRS; do
  mkdir -p "$THOUGHTS_DIR/$USERNAME/$subdir"
done
for subdir in $THOUGHTS_SHARED_SUBDIRS; do
  mkdir -p "$THOUGHTS_DIR/$SHARED_DIR/$subdir"
done
```

Add config file generation after the directory creation (only if config does not yet exist):

```bash
write_config() {
  local config_file="$THOUGHTS_DIR/thoughts.config.json"
  [ -f "$config_file" ] && { info "thoughts.config.json already exists — keeping existing config."; return; }

  info "Creating thoughts.config.json..."
  # Convert space-separated lists to JSON arrays
  local p_array s_array
  p_array=$(echo "$THOUGHTS_PERSONAL_SUBDIRS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().split()))")
  s_array=$(echo "$THOUGHTS_SHARED_SUBDIRS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().split()))")

  cat > "$config_file" <<CONFIGEOF
{
  "version": "1",
  "root": "$THOUGHTS_DIR",
  "personal_dir": "$USERNAME",
  "shared_dir": "$SHARED_DIR",
  "personal_subdirs": $p_array,
  "shared_subdirs": $s_array
}
CONFIGEOF
}
write_config
```

### Success Criteria

- [ ] `make test` passes (default layout unchanged, `nikey_es` still the default personal dir)
- [ ] Running `thoughts-init` in a temp dir creates `thoughts/thoughts.config.json` with correct JSON
- [ ] Running `thoughts-init` a second time does not overwrite an edited `thoughts.config.json`
- [ ] A custom config (e.g. `personal_dir: "acme_team"`) causes `thoughts-init` to create `thoughts/acme_team/` instead of `thoughts/nikey_es/`
- [ ] `shellcheck` passes: `shellcheck core/skills/thoughts-management/scripts/thoughts-init`

---

## Phase 3: Update `thoughts-metadata` to Expose Config Values

### Overview

`thoughts-metadata` currently only outputs git/date metadata. Add config-derived values to its output so that consuming skills can discover the correct paths without hardcoding them.

### Changes Required

#### 1. `core/skills/thoughts-management/scripts/thoughts-metadata`

Source the config library and append path metadata to the output:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=thoughts-config-lib
source "$SCRIPT_DIR/thoughts-config-lib"
load_thoughts_config
```

Add to the printed output section:

```bash
echo "Thoughts Root: $THOUGHTS_ROOT"
echo "Thoughts Personal Dir: $THOUGHTS_PERSONAL_DIR"
echo "Thoughts Shared Dir: $THOUGHTS_SHARED_DIR"
echo "Thoughts Personal Subdirs: $THOUGHTS_PERSONAL_SUBDIRS"
echo "Thoughts Shared Subdirs: $THOUGHTS_SHARED_SUBDIRS"
```

### Success Criteria

- [ ] `thoughts-metadata` output contains `Thoughts Root: thoughts` in the default case
- [ ] `thoughts-metadata` output contains `Thoughts Personal Dir: nikey_es` in the default case
- [ ] With a custom config (`personal_dir: "jorge"`), output shows `Thoughts Personal Dir: jorge`
- [ ] `make test` passes (existing metadata assertions still satisfied)
- [ ] `shellcheck` passes: `shellcheck core/skills/thoughts-management/scripts/thoughts-metadata`

---

## Phase 4: Update `thoughts-management` SKILL.md

### Overview

Update the Skill documentation so it reflects the new config mechanism and how to use it.

### Changes Required

#### 1. `core/skills/thoughts-management/SKILL.md`

- Add a new **Configuration** section explaining `thoughts.config.json` format and all supported keys.
- Update the `## Configuration` section to note that `thoughts.config.json` takes precedence over defaults but `THOUGHTS_USER` env var still overrides `personal_dir`.
- Update the directory structure diagram to show `thoughts.config.json` at the root.
- Update the `thoughts-metadata` output sample to include the new `Thoughts Root:` etc. lines.

### Success Criteria

- [ ] `SKILL.md` documents all six `thoughts.config.json` keys (`version`, `root`, `personal_dir`, `shared_dir`, `personal_subdirs`, `shared_subdirs`)
- [ ] The config file format example is correct JSON that matches what `thoughts-init` writes

---

## Phase 5: Update `thoughts-locator` Agent

### Overview

The `thoughts-locator` agent currently has `thoughts/shared/` and `thoughts/{username}/` baked into its instructions. Once the config file exists, the agent should read it first to discover the actual paths.

### Changes Required

#### 1. `core/agents/thoughts-locator.md`

Replace the hardcoded directory tree example in the **Directory Structure** section with guidance to:

1. Check for `thoughts/thoughts.config.json` first.
2. If the file exists, parse it to learn the actual `root`, `personal_dir`, `shared_dir`, and subdirectory names.
3. Fall back to the default layout (`thoughts/shared/`, `thoughts/{username}/`) when no config exists.

Add a note at the top of the **Search Strategy** section:

```
Before searching, check if thoughts/thoughts.config.json exists.
If it does, read it to determine the correct directory paths.
Example: root may be "docs/thoughts" instead of "thoughts", and the personal
directory may be "jorge" instead of "nikey_es".
```

### Success Criteria

- [ ] The agent instructions no longer contain `nikey_es` as a literal username
- [ ] The instructions explicitly direct the agent to read `thoughts.config.json` when present

---

## Phase 6: Update Tests

### Overview

Update `test/thoughts-structure-test.sh` to cover config-driven behaviour in addition to the existing default-layout tests.

### Changes Required

#### 1. `test/thoughts-structure-test.sh`

Add a new test section after Test 1:

```bash
# Test 2b: custom config is honoured
section "Test 2b: thoughts-init honours custom config"

CUSTOM_DIR=$(mktemp -d)
mkdir -p "$CUSTOM_DIR/thoughts"
cat > "$CUSTOM_DIR/thoughts/thoughts.config.json" <<'CFGEOF'
{
  "version": "1",
  "root": "thoughts",
  "personal_dir": "custom_user",
  "shared_dir": "team",
  "personal_subdirs": ["tasks"],
  "shared_subdirs": ["docs", "specs"]
}
CFGEOF

cd "$CUSTOM_DIR"
setup_git_repo "$CUSTOM_DIR"
thoughts-init

assert_dir_exists "thoughts/custom_user/tasks"   "custom personal dir created"
assert_dir_exists "thoughts/team/docs"           "custom shared subdir created"
assert_dir_exists "thoughts/team/specs"          "custom shared subdir created"
assert_dir_not_exists "thoughts/nikey_es"        "default personal dir NOT created"
assert_dir_not_exists "thoughts/shared"          "default shared dir NOT created"

rm -rf "$CUSTOM_DIR"
```

Add assertions in Test 2 (metadata test) for the new config output lines:

```bash
assert_output_contains "$output" "Thoughts Root:" "metadata contains thoughts root"
assert_output_contains "$output" "Thoughts Personal Dir:" "metadata contains personal dir"
```

### Success Criteria

- [ ] `make test` passes with all new and existing assertions green

---

## Testing Strategy

### Automated (all runnable via `make test`)

- Default layout: existing tests in `test/thoughts-structure-test.sh` — no regressions
- Config-driven layout: new Test 2b covers custom `personal_dir`, `shared_dir`, custom subdirs
- Config not overwritten: assert `thoughts.config.json` content unchanged after second `thoughts-init` call
- Metadata output: new assertions for `Thoughts Root:` etc. in metadata output
- `shellcheck`: `make check` covers all bash scripts including the new lib

### Manual

None required — all observable behaviour is script output or directory existence, both testable with shell assertions.

---

## Migration Notes

- **No breaking changes.** Projects without `thoughts.config.json` behave exactly as before.
- **Opt-in customisation.** Teams edit `thoughts.config.json` after the first `thoughts-init`. Existing `thoughts/` trees are not touched.
- **Commit the config.** `thoughts.config.json` should be committed to the project repository so all team members share the same layout.

---

## References

- `core/skills/thoughts-management/SKILL.md` — Skill entry point
- `core/skills/thoughts-management/scripts/thoughts-init` — Directory initializer (main target)
- `core/skills/thoughts-management/scripts/thoughts-metadata` — Metadata generator
- `core/agents/thoughts-locator.md` — Agent that searches the thoughts tree
- `test/thoughts-structure-test.sh` — Automated test suite
