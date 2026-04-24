# create-plan skill execution — Refactor thoughts-management for config-driven directory structures

**Skill**: `/stepwise-core:create-plan`
**Arguments**: "Refactor the thoughts-management skill to support custom directory structures via a config file instead of hardcoded paths"

---

## Step 1: Context Gathering & Initial Analysis

I read all relevant files before spawning any sub-tasks. Here is what I found:

**I've found that:**
- `core/skills/thoughts-management/scripts/thoughts-init:7-8` — Two config knobs exist today: `USERNAME="${THOUGHTS_USER:-nikey_es}"` and `THOUGHTS_DIR="thoughts"`, but all subdirectory names (`tickets`, `notes`, `research`, `plans`, `prs`) are hardcoded literals
- `core/skills/thoughts-management/scripts/thoughts-init:37-41` — Five `mkdir -p` calls with fully hardcoded paths; no looping, no variables for subdirectory names
- `core/skills/thoughts-management/SKILL.md:88-95` — Documents the hardcoded tree structure; mentions `nikey_es` as default username
- `core/skills/create-plan/SKILL.md:186` — References `thoughts/shared/plans/` directly (hardcoded in LLM instructions)
- `core/skills/research-codebase/SKILL.md:102` — References `thoughts/shared/research/` directly (hardcoded in LLM instructions)
- `test/thoughts-structure-test.sh:41-42` — Asserts `thoughts/nikey_es/tickets` and `thoughts/nikey_es/notes` by literal name (will need updating)
- `Makefile:42` — `jq` is already referenced in CI for JSON validation, making it a safe choice for config parsing

**Questions that my research couldn't answer** (I would normally ask the user these, then proceed on best judgment):

1. **Config file format**: JSON, YAML, or bash-sourced `.env`? I'll choose JSON (`.thoughts.json`) since `jq` is already used in the Makefile and is the most structured.
2. **Config file location**: Project root (`.thoughts.json`) — consistent with other dotfiles like `.gitignore`.
3. **What should be configurable**: Base directory name, username, personal subdirectory names, shared subdirectory names. I'll make all four configurable.
4. **Should other skills (create-plan, research-codebase) be updated**: Those are markdown instruction files for the LLM, not executable scripts — they cannot dynamically read a config file. They will continue documenting the default paths and users should be aware custom paths may diverge. Out of scope.
5. **Backwards compatibility requirement**: Fully backwards-compatible — no config file = current behaviour unchanged.

*Proceeding with best judgment as instructed.*

---

## Step 2: Design Options Considered

**Option A: Environment variable per directory**
- Pros: No new file format, simple
- Cons: Requires setting 5+ env vars, no persistence without `.bashrc` changes, hard to share with team

**Option B: Bash-sourced config file (`.thoughts.rc`)**
- Pros: Pure bash, no `jq` dependency
- Cons: Security risk (arbitrary bash execution), fragile syntax

**Option C: JSON config file with `jq` (`.thoughts.json`)**
- Pros: Structured, safe, `jq` already used in Makefile, easy to parse arrays for subdirectory lists, portable
- Cons: Requires `jq` — gracefully degrades to defaults when absent

**Selected: Option C** — JSON config with graceful fallback to defaults when `jq` is absent.

---

## Step 3: Plan Structure

Here is the phasing I settled on:

1. **Phase 1**: Update `thoughts-init` to read `.thoughts.json` config and loop over configurable subdirectory arrays
2. **Phase 2**: Update `thoughts-metadata` to output resolved path configuration
3. **Phase 3**: Update tests to cover config-driven initialization
4. **Phase 4**: Update `SKILL.md` documentation

---

## Step 4: Implementation Plan

The full plan has been written to:

`thoughts/shared/plans/2026-04-24-refactor-thoughts-management-config.md`

(For this evaluation, the plan is saved alongside this response as `plan.md`.)

---

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

#### 1. Config File Schema (new example file)
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
- `username` overrides the default `nikey_es`; `THOUGHTS_USER` env var takes precedence over this field
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

  # Override THOUGHTS_DIR if set in config
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
- [ ] Script creates custom directories when `.thoughts.json` is present (manual test — Phase 3 adds automated coverage)

---

## Phase 2: Update `thoughts-metadata` to Output Configured Paths

### Overview
Extend `thoughts-metadata` to output the resolved directory paths from config, so consuming skills don't need to re-implement config-reading logic.

### Changes Required:

#### 1. `thoughts-metadata` Script
**File**: `core/skills/thoughts-management/scripts/thoughts-metadata`
**Changes**: Add config-reading block (same logic as thoughts-init, without directory creation) and print resolved paths at the end of output

```bash
# Resolve configured paths (read-only — no mkdir)
CONFIG_FILE=".thoughts.json"
THOUGHTS_DIR_OUT="thoughts"
USERNAME_OUT="${THOUGHTS_USER:-nikey_es}"
PERSONAL_SUBDIRS_OUT=("tickets" "notes")
SHARED_SUBDIRS_OUT=("research" "plans" "prs")

if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  CONFIG_DIR=$(jq -r '.thoughts_dir // empty' "$CONFIG_FILE")
  [ -n "$CONFIG_DIR" ] && THOUGHTS_DIR_OUT="$CONFIG_DIR"

  if [ -z "${THOUGHTS_USER:-}" ]; then
    CONFIG_USER=$(jq -r '.username // empty' "$CONFIG_FILE")
    [ -n "$CONFIG_USER" ] && USERNAME_OUT="$CONFIG_USER"
  fi

  mapfile -t CONFIG_PERSONAL < <(jq -r '.personal_subdirs[]? // empty' "$CONFIG_FILE" 2>/dev/null)
  [ "${#CONFIG_PERSONAL[@]}" -gt 0 ] && PERSONAL_SUBDIRS_OUT=("${CONFIG_PERSONAL[@]}")

  mapfile -t CONFIG_SHARED < <(jq -r '.shared_subdirs[]? // empty' "$CONFIG_FILE" 2>/dev/null)
  [ "${#CONFIG_SHARED[@]}" -gt 0 ] && SHARED_SUBDIRS_OUT=("${CONFIG_SHARED[@]}")
fi

echo "Thoughts Dir: $THOUGHTS_DIR_OUT"
echo "Personal Dir: $THOUGHTS_DIR_OUT/$USERNAME_OUT"
echo "Shared Dir: $THOUGHTS_DIR_OUT/shared"
echo "Personal Subdirs: ${PERSONAL_SUBDIRS_OUT[*]}"
echo "Shared Subdirs: ${SHARED_SUBDIRS_OUT[*]}"
```

**Note:** The config-loading logic is duplicated between the two scripts intentionally. Each script is independently invocable. If the duplication grows, extracting to a shared sourced helper would be worth considering in a future iteration.

### Success Criteria:
- [ ] `thoughts-metadata` passes shellcheck: `make check`
- [ ] Output includes new `Thoughts Dir`, `Personal Dir`, `Shared Dir`, `Personal Subdirs`, `Shared Subdirs` lines
- [ ] All existing metadata fields (date, git, etc.) are still present: `make test`

---

## Phase 3: Update Tests for Config-Driven Layout

### Overview
Extend `test/thoughts-structure-test.sh` to add a test case that uses a `.thoughts.json` with a custom layout and verifies those directories are created.

### Changes Required:

#### 1. `thoughts-structure-test.sh` — Update Test 1 to use variable for username
**File**: `test/thoughts-structure-test.sh`
**Changes**: Replace literal `nikey_es` with `${THOUGHTS_USER:-nikey_es}` in existing assertions

```bash
EXPECTED_USER="${THOUGHTS_USER:-nikey_es}"
assert_dir_exists "thoughts/$EXPECTED_USER/tickets" "thoughts/{user}/tickets/ created"
assert_dir_exists "thoughts/$EXPECTED_USER/notes"   "thoughts/{user}/notes/ created"
```

#### 2. `thoughts-structure-test.sh` — Add Test 3 for config-driven initialization
**File**: `test/thoughts-structure-test.sh`
**Changes**: Add new test section after Test 2

```bash
# ============================================================================
# Test 3: thoughts-init respects .thoughts.json config
# ============================================================================
section "Test 3: thoughts-init respects .thoughts.json config"

CONFIG_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$CONFIG_TEST_DIR"' EXIT

cd "$CONFIG_TEST_DIR"
setup_git_repo "$CONFIG_TEST_DIR"

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
  echo -e "${YELLOW}⚠${NC} jq not available — skipping config-driven layout test"
fi
```

### Success Criteria:
- [ ] `make test` passes with no `.thoughts.json` (default layout preserved)
- [ ] `make test` passes with a custom `.thoughts.json` when `jq` is available
- [ ] Test gracefully skips (no failure) when `jq` is not installed

---

## Phase 4: Update SKILL.md Documentation

### Overview
Update `core/skills/thoughts-management/SKILL.md` to document the new config file capability.

### Changes Required:

#### 1. `SKILL.md` — Add Config File section
**File**: `core/skills/thoughts-management/SKILL.md`
**Changes**: Add a "Config File" section below the existing "Configuration" section, and note that the "Directory structure" section shows the default layout

```markdown
## Config File

For persistent configuration, create `.thoughts.json` in the project root:

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
| `personal_subdirs` | `["tickets", "notes"]` | Subdirs under `{thoughts_dir}/{username}/` |
| `shared_subdirs` | `["research", "plans", "prs"]` | Subdirs under `{thoughts_dir}/shared/` |

**Priority order for username**: `THOUGHTS_USER` env var > `username` in `.thoughts.json` > default `nikey_es`

**Requires**: `jq` must be installed for config file support. Without `jq`, defaults are used silently.
```

### Success Criteria:
- [ ] SKILL.md documents the `.thoughts.json` schema with all keys
- [ ] SKILL.md documents priority order for username resolution
- [ ] SKILL.md notes `jq` dependency for config file support

---

## Testing Strategy

### Unit Tests (Automated):
- Default layout creation (existing): `make test`
- Custom layout from `.thoughts.json` (new): `make test`
- shellcheck on all scripts: `make check`

### Integration Tests:
- `thoughts-metadata` outputs new path fields: verified by Test 2 extension in `thoughts-structure-test.sh`

### Manual Testing Steps:
1. Create a `.thoughts.json` in a test project with custom `thoughts_dir`, `personal_subdirs`, and `shared_subdirs`
2. Run `bash core/skills/thoughts-management/scripts/thoughts-init` and verify custom directories appear
3. Run `bash core/skills/thoughts-management/scripts/thoughts-metadata` and verify output shows custom paths
4. Delete `.thoughts.json` and re-run both scripts — verify default layout is restored unchanged

## Performance Considerations

No meaningful performance implications. Config file is read once per script execution. `jq` processes small JSON files in milliseconds.

## Migration Notes

Fully backwards-compatible. Existing projects with no `.thoughts.json` will behave exactly as before. No migration of existing `thoughts/` directories is required.

## References

- Script under refactoring: `core/skills/thoughts-management/scripts/thoughts-init`
- Metadata script: `core/skills/thoughts-management/scripts/thoughts-metadata`
- Skill documentation: `core/skills/thoughts-management/SKILL.md`
- Test file: `test/thoughts-structure-test.sh`
- Makefile test targets: `Makefile`

---

## Step 5: Plan Complete

I've created the implementation plan.

```
Implementation plan complete: thoughts/shared/plans/2026-04-24-refactor-thoughts-management-config.md
```

(Saved to `create-plan-workspace/iteration-1/eval-3-refactoring/with_skill/outputs/plan.md` for this evaluation.)

Next steps in the workflow:
- Review and approve the plan
- Use `/stepwise-core:implement-plan thoughts/shared/plans/2026-04-24-refactor-thoughts-management-config.md` to execute it
- Or use `/stepwise-core:iterate-plan thoughts/shared/plans/2026-04-24-refactor-thoughts-management-config.md [changes]` to refine further

Tip: Use `/clear` to free up context before starting implementation
