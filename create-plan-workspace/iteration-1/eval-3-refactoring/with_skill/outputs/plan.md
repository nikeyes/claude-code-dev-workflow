# Thoughts-Management Config-Driven Directory Structure Implementation Plan

## Overview

Refactor the `thoughts-management` skill to support custom directory structures via a `.thoughts.json` config file instead of relying solely on hardcoded paths and the `THOUGHTS_USER` environment variable. This enables teams and individuals to define their own `thoughts/` layout without modifying the script itself.

## Current State Analysis

The current implementation hardcodes the entire directory tree inside `thoughts-init`:

```bash
mkdir -p "$THOUGHTS_DIR/$USERNAME/tickets"
mkdir -p "$THOUGHTS_DIR/$USERNAME/notes"
mkdir -p "$THOUGHTS_DIR/shared/research"
mkdir -p "$THOUGHTS_DIR/shared/plans"
mkdir -p "$THOUGHTS_DIR/shared/prs"
```

Key constraints discovered:
- `core/skills/thoughts-management/scripts/thoughts-init:7-8` — `USERNAME` and `THOUGHTS_DIR` are set at the top but subdirectory names (`tickets`, `notes`, `research`, `plans`, `prs`) are completely hardcoded
- `core/skills/thoughts-management/scripts/thoughts-init:37-41` — Five `mkdir -p` calls with literal path segments
- `core/skills/thoughts-management/SKILL.md:88-95` — Documents the hardcoded structure; references `nikey_es` as default
- `core/skills/create-plan/SKILL.md:186` — Saves plans to `thoughts/shared/plans/` (hardcoded)
- `core/skills/research-codebase/SKILL.md:102` — Saves research to `thoughts/shared/research/` (hardcoded)
- `test/thoughts-structure-test.sh:41-42` — Asserts `thoughts/nikey_es/tickets` and `thoughts/nikey_es/notes` by name
- `test/thoughts-structure-test.sh` — No config-file test coverage exists

## Desired End State

After this plan is complete:

1. A `.thoughts.json` config file at the project root can override any directory path segment
2. `thoughts-init` reads `.thoughts.json` when present, falls back to current defaults when absent (fully backwards-compatible)
3. `thoughts-metadata` outputs the configured paths so other skills can consume them
4. `SKILL.md` documents the config schema and usage
5. `test/thoughts-structure-test.sh` covers both default-layout and config-driven-layout scenarios

**Verification:**
```bash
make test   # All tests pass with default layout (no .thoughts.json)
make test   # All tests pass with a custom .thoughts.json
make check  # shellcheck passes on all scripts
```

### Key Discoveries:
- `core/skills/thoughts-management/scripts/thoughts-init:7` — `USERNAME="${THOUGHTS_USER:-nikey_es}"` is the only existing config knob
- `core/skills/thoughts-management/scripts/thoughts-init:8` — `THOUGHTS_DIR="thoughts"` is always "thoughts" (no override)
- `test/thoughts-structure-test.sh:41` — Test asserts `thoughts/nikey_es/tickets` — will need to use `$USERNAME` value or read it dynamically after config support is added
- No existing JSON/YAML parsing library is used anywhere in the scripts; `jq` is used only in the Makefile CI block, making it the safest choice for JSON parsing with a bash fallback

## What We're NOT Doing

- We are NOT changing the default directory layout — existing users with no config file are unaffected
- We are NOT updating `create-plan/SKILL.md` or `research-codebase/SKILL.md` to dynamically read the config (those are markdown instructions for the LLM, not scripts — they will continue to use the documented default paths)
- We are NOT adding network or cloud configuration
- We are NOT migrating existing `thoughts/` directories automatically
- We are NOT adding validation beyond basic directory creation
- We are NOT changing the `THOUGHTS_USER` env var behaviour (it remains supported)

## Implementation Approach

We introduce a simple JSON config file (`.thoughts.json`) at the project root. The schema is flat and minimal. `thoughts-init` tries to load it with `jq` (if available) and falls back to hardcoded defaults if `jq` is absent or the file doesn't exist. This keeps the script dependency-free in the default case.

`thoughts-metadata` is extended to print the resolved paths so that any skill or agent can read them without re-implementing the config-reading logic.

---

## Phase 1: Define Config Schema and Update `thoughts-init`

### Overview
Add config-file reading to `thoughts-init` so every path segment can be overridden. Maintain full backwards compatibility when no config exists.

### Changes Required:

#### 1. Config File Schema (new file at project root — template only, not committed)
**File**: `.thoughts.json.example`
**Changes**: Add example config file that documents all available keys

```json
{
  "thoughts_dir": "thoughts",
  "username": "your_name",
  "personal_subdirs": ["tickets", "notes"],
  "shared_subdirs": ["research", "plans", "prs"]
}
```

**Notes:**
- `thoughts_dir` overrides the base directory name (default: `thoughts`)
- `username` overrides `THOUGHTS_USER` env var (env var takes precedence over config file)
- `personal_subdirs` replaces the hardcoded `tickets` and `notes` list
- `shared_subdirs` replaces the hardcoded `research`, `plans`, `prs` list

#### 2. `thoughts-init` Script
**File**: `core/skills/thoughts-management/scripts/thoughts-init`
**Changes**: Add config-loading block before directory creation; replace hardcoded `mkdir` calls with loops over config-driven arrays

```bash
# Load config from .thoughts.json if present and jq is available
CONFIG_FILE=".thoughts.json"
PERSONAL_SUBDIRS=("tickets" "notes")
SHARED_SUBDIRS=("research" "plans" "prs")

if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  info "Loading config from $CONFIG_FILE..."

  # Override THOUGHTS_DIR if set in config (env var THOUGHTS_USER still wins for username)
  CONFIG_DIR=$(jq -r '.thoughts_dir // empty' "$CONFIG_FILE")
  [ -n "$CONFIG_DIR" ] && THOUGHTS_DIR="$CONFIG_DIR"

  # Config username is only used if THOUGHTS_USER env var is not set
  if [ -z "${THOUGHTS_USER:-}" ]; then
    CONFIG_USER=$(jq -r '.username // empty' "$CONFIG_FILE")
    [ -n "$CONFIG_USER" ] && USERNAME="$CONFIG_USER"
  fi

  # Override personal subdirs if specified
  mapfile -t CONFIG_PERSONAL < <(jq -r '.personal_subdirs[]? // empty' "$CONFIG_FILE" 2>/dev/null)
  [ "${#CONFIG_PERSONAL[@]}" -gt 0 ] && PERSONAL_SUBDIRS=("${CONFIG_PERSONAL[@]}")

  # Override shared subdirs if specified
  mapfile -t CONFIG_SHARED < <(jq -r '.shared_subdirs[]? // empty' "$CONFIG_FILE" 2>/dev/null)
  [ "${#CONFIG_SHARED[@]}" -gt 0 ] && SHARED_SUBDIRS=("${CONFIG_SHARED[@]}")
fi

# Create personal subdirectories
for subdir in "${PERSONAL_SUBDIRS[@]}"; do
  mkdir -p "$THOUGHTS_DIR/$USERNAME/$subdir"
done

# Create shared subdirectories
for subdir in "${SHARED_SUBDIRS[@]}"; do
  mkdir -p "$THOUGHTS_DIR/shared/$subdir"
done
```

The existing display block (the `echo` tree) also needs to be replaced with loops over the arrays to stay accurate.

### Success Criteria:
- [ ] Script passes shellcheck: `make check`
- [ ] Default layout still created when no `.thoughts.json` exists: `make test`
- [ ] Script creates custom directories when `.thoughts.json` is present (manual test, Phase 3 adds automated test)

---

## Phase 2: Update `thoughts-metadata` to Output Configured Paths

### Overview
Extend `thoughts-metadata` to output the resolved directory paths from config, so consuming skills don't need to re-implement config-reading logic.

### Changes Required:

#### 1. `thoughts-metadata` Script
**File**: `core/skills/thoughts-management/scripts/thoughts-metadata`
**Changes**: Add config-reading block (same logic as thoughts-init, without directory creation) and print resolved paths

```bash
# Resolve configured paths (same logic as thoughts-init, read-only)
CONFIG_FILE=".thoughts.json"
THOUGHTS_DIR="thoughts"
USERNAME="${THOUGHTS_USER:-nikey_es}"
PERSONAL_SUBDIRS=("tickets" "notes")
SHARED_SUBDIRS=("research" "plans" "prs")

if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  CONFIG_DIR=$(jq -r '.thoughts_dir // empty' "$CONFIG_FILE")
  [ -n "$CONFIG_DIR" ] && THOUGHTS_DIR="$CONFIG_DIR"

  if [ -z "${THOUGHTS_USER:-}" ]; then
    CONFIG_USER=$(jq -r '.username // empty' "$CONFIG_FILE")
    [ -n "$CONFIG_USER" ] && USERNAME="$CONFIG_USER"
  fi

  mapfile -t CONFIG_PERSONAL < <(jq -r '.personal_subdirs[]? // empty' "$CONFIG_FILE" 2>/dev/null)
  [ "${#CONFIG_PERSONAL[@]}" -gt 0 ] && PERSONAL_SUBDIRS=("${CONFIG_PERSONAL[@]}")

  mapfile -t CONFIG_SHARED < <(jq -r '.shared_subdirs[]? // empty' "$CONFIG_FILE" 2>/dev/null)
  [ "${#CONFIG_SHARED[@]}" -gt 0 ] && SHARED_SUBDIRS=("${CONFIG_SHARED[@]}")
fi

# Print resolved paths after existing git metadata
echo "Thoughts Dir: $THOUGHTS_DIR"
echo "Personal Dir: $THOUGHTS_DIR/$USERNAME"
echo "Shared Dir: $THOUGHTS_DIR/shared"
echo "Personal Subdirs: ${PERSONAL_SUBDIRS[*]}"
echo "Shared Subdirs: ${SHARED_SUBDIRS[*]}"
```

**Note:** The config-loading logic is identical in both scripts. This is intentional: each script is independently invocable and we deliberately keep duplication here for clarity (different contexts: init vs metadata). If it grows further, extracting to a shared sourced file would be worth considering.

### Success Criteria:
- [ ] `thoughts-metadata` passes shellcheck: `make check`
- [ ] Output includes `Thoughts Dir`, `Personal Dir`, `Shared Dir`, `Personal Subdirs`, `Shared Subdirs` lines
- [ ] Existing metadata fields (date, git commit, etc.) are unchanged: `make test`

---

## Phase 3: Update Tests for Config-Driven Layout

### Overview
Extend `test/thoughts-structure-test.sh` to add a test case that uses a `.thoughts.json` with a custom layout and verifies those directories are created.

### Changes Required:

#### 1. `thoughts-structure-test.sh`
**File**: `test/thoughts-structure-test.sh`
**Changes**: Add Test 3 for config-driven initialization

```bash
# ============================================================================
# Test 3: thoughts-init respects .thoughts.json config
# ============================================================================
section "Test 3: thoughts-init respects .thoughts.json config"

# Create a fresh temp dir for this test
CONFIG_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$CONFIG_TEST_DIR"' EXIT

cd "$CONFIG_TEST_DIR"
setup_git_repo "$CONFIG_TEST_DIR"

# Write a custom config
cat > .thoughts.json <<'EOF'
{
  "thoughts_dir": "notes",
  "username": "test_user",
  "personal_subdirs": ["tasks", "diary"],
  "shared_subdirs": ["docs", "decisions"]
}
EOF

if command -v jq >/dev/null 2>&1; then
  thoughts-init

  assert_dir_exists "notes/test_user/tasks"    "config: personal tasks/ created"
  assert_dir_exists "notes/test_user/diary"    "config: personal diary/ created"
  assert_dir_exists "notes/shared/docs"        "config: shared docs/ created"
  assert_dir_exists "notes/shared/decisions"   "config: shared decisions/ created"
  assert_file_exists "notes/README.md"         "config: README.md created in custom dir"
else
  echo -e "${YELLOW}⚠${NC} jq not available — skipping config-driven test"
fi
```

**Also update Test 1** to use the USERNAME variable dynamically instead of `nikey_es`:
```bash
# Read USERNAME that thoughts-init would use (default)
EXPECTED_USER="${THOUGHTS_USER:-nikey_es}"
assert_dir_exists "thoughts/$EXPECTED_USER/tickets" "thoughts/{user}/tickets/ created"
assert_dir_exists "thoughts/$EXPECTED_USER/notes"   "thoughts/{user}/notes/ created"
```

### Success Criteria:
- [ ] `make test` passes with no `.thoughts.json` present (existing behaviour preserved)
- [ ] `make test` passes with a custom `.thoughts.json` (if `jq` available)
- [ ] Test gracefully skips config test when `jq` is not installed

---

## Phase 4: Update SKILL.md Documentation

### Overview
Update `core/skills/thoughts-management/SKILL.md` to document the new config file capability.

### Changes Required:

#### 1. `SKILL.md` — Add Config File section
**File**: `core/skills/thoughts-management/SKILL.md`
**Changes**: Add a "Config File" section below the existing "Configuration" section

```markdown
## Config File

For persistent configuration across sessions and team members, create `.thoughts.json` in the project root:

```json
{
  "thoughts_dir": "thoughts",
  "username": "your_name",
  "personal_subdirs": ["tickets", "notes"],
  "shared_subdirs": ["research", "plans", "prs"]
}
```

All keys are optional. Any omitted key falls back to its default value.

| Key | Default | Description |
|-----|---------|-------------|
| `thoughts_dir` | `thoughts` | Base directory name |
| `username` | `nikey_es` | Personal subdirectory name (overridden by `THOUGHTS_USER` env var) |
| `personal_subdirs` | `["tickets", "notes"]` | Subdirectories under `{thoughts_dir}/{username}/` |
| `shared_subdirs` | `["research", "plans", "prs"]` | Subdirectories under `{thoughts_dir}/shared/` |

**Priority order for username**: `THOUGHTS_USER` env var > `username` in `.thoughts.json` > default `nikey_es`

**Requires**: `jq` must be installed for config file support. Without `jq`, defaults are used silently.
```

Also update the existing "Directory structure" section to note it shows the default structure.

### Success Criteria:
- [ ] SKILL.md documents the `.thoughts.json` schema with all keys
- [ ] SKILL.md documents priority order for username resolution
- [ ] SKILL.md notes `jq` dependency for config file support

---

## Testing Strategy

### Unit Tests (Automated):
- Default layout creation (existing): `make test`
- Custom layout from `.thoughts.json` (new Test 3): `make test`
- shellcheck on all scripts: `make check`

### Integration Tests:
- `thoughts-metadata` output includes new path fields: verified by Test 2 extension
- Config-driven `thoughts-metadata` output reflects custom paths: manual validation

### Manual Testing Steps:
1. Create a `.thoughts.json` in a test project with custom `thoughts_dir`, `personal_subdirs`, and `shared_subdirs`
2. Run `bash core/skills/thoughts-management/scripts/thoughts-init` and verify the custom directories appear
3. Run `bash core/skills/thoughts-management/scripts/thoughts-metadata` and verify the output shows the custom paths
4. Delete `.thoughts.json` and re-run both scripts — verify default layout is restored

## Performance Considerations

No performance implications. Config file is read once per script execution. `jq` is fast for small JSON files.

## Migration Notes

Fully backwards-compatible. Existing projects with no `.thoughts.json` will behave exactly as before. No migration of existing `thoughts/` directories is required or performed automatically.

## References

- Script under refactoring: `core/skills/thoughts-management/scripts/thoughts-init`
- Metadata script: `core/skills/thoughts-management/scripts/thoughts-metadata`
- Skill documentation: `core/skills/thoughts-management/SKILL.md`
- Test file: `test/thoughts-structure-test.sh`
- Makefile test targets: `Makefile`
