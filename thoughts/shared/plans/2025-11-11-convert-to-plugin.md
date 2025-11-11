# Convert Claude Code Dev Workflow to Plugin

## Overview

Convert the existing local workflow system into a Claude Code plugin for easier distribution and installation via plugin marketplaces. The plugin will package commands, agents, and thoughts/ management scripts into a single installable unit.

## Current State Analysis

### What Exists Now

**Current Structure (for manual installation):**
```
.claude/                          # WILL BE REMOVED - confusing for plugin
├── commands/                     # Currently here, WILL MOVE to root
│   ├── research_codebase.md
│   ├── create_plan.md
│   ├── iterate_plan.md
│   ├── implement_plan.md
│   ├── validate_plan.md
│   └── commit.md
└── agents/                       # Currently here, WILL MOVE to root
    ├── codebase-locator.md
    ├── codebase-analyzer.md
    ├── codebase-pattern-finder.md
    ├── thoughts-locator.md
    └── thoughts-analyzer.md

bin/                             # 4 bash scripts for thoughts/ management
├── thoughts-init                # Initialize thoughts/ structure
├── thoughts-sync                # Sync hardlinks to searchable/
├── thoughts-metadata            # Generate git metadata
└── thoughts-version             # Check installed version

install.sh                       # Manual installer script (will be updated)
test/                            # Automated bash tests
```

**Target Plugin Structure:**
```
claude-code-dev-workflow/        # Plugin root
├── .claude-plugin/              # Metadata directory (NEW)
│   └── plugin.json             # Plugin manifest (NEW)
├── commands/                    # MOVED from .claude/commands/
│   ├── research_codebase.md
│   ├── create_plan.md
│   ├── iterate_plan.md
│   ├── implement_plan.md
│   ├── validate_plan.md
│   └── commit.md
├── agents/                      # MOVED from .claude/agents/
│   ├── codebase-locator.md
│   ├── codebase-analyzer.md
│   ├── codebase-pattern-finder.md
│   ├── thoughts-locator.md
│   └── thoughts-analyzer.md
├── bin/                         # Scripts (unchanged)
├── test/                        # Tests (unchanged)
└── install.sh                   # Updated for new structure
```

**Installation Method:**
- Current: `./install.sh` → copies from `.claude/` to `~/.claude/` and `~/.local/bin/`
- After conversion: Plugin installs from root `commands/` and `agents/` to `~/.claude/`
- Scripts: Still installed via `install-scripts.sh` to `~/.local/bin/`

**Testing Strategy:**
- ✅ Automated bash tests for `bin/` scripts (`make test`)
- ✅ Manual testing for commands/agents (requires Claude Code execution)
- ✅ Shellcheck linting (`make check`)

### Key Discoveries

1. **Structure Needs Reorganization**: Commands/agents must be at plugin root, not in `.claude/` directory (plugin convention)
2. **Why Remove `.claude/`**: Having `.claude/` in the repo would confuse users - it looks like Claude Code's actual installation location
3. **Testing is Appropriate**: Current strategy is correct - markdown prompts cannot be unit tested
4. **Scripts Cannot Be Replaced by Hooks**: After analyzing plugin hooks, all 4 `bin/` scripts must be kept:
   - **thoughts-init**: No hook for one-time project setup (SessionStart runs every session)
   - **thoughts-sync**: Commands call it explicitly; PostToolUse hook would trigger on ALL file writes (too broad)
   - **thoughts-metadata**: Commands need synchronous metadata; hooks are async and can't return data
   - **thoughts-version**: Useful for both plugin and install.sh users; plugin versioning doesn't replace it
5. **install.sh Impact**: Must be updated to copy from new locations (`commands/` instead of `.claude/commands/`)

## Desired End State

A Claude Code plugin that:
1. Installs via `/plugin install workflow@marketplace-name`
2. Provides all 6 commands and 5 agents automatically
3. Includes helper scripts for thoughts/ management
4. Maintains existing testing strategy
5. Works across terminal and VS Code
6. Can be distributed via GitHub marketplace

### Success Criteria

#### Automated Verification:
- [ ] Plugin structure validates: `claude plugin validate .`
- [ ] All bash tests pass: `make test`
- [ ] Shellcheck passes: `make check`
- [ ] Plugin installs successfully from local marketplace
- [ ] Commands appear in `/help` after installation
- [ ] Agents are available for spawning

#### Manual Verification:
- [ ] `/research_codebase` command works end-to-end
- [ ] `/create_plan` command works with file references
- [ ] `thoughts-init` creates directory structure correctly
- [ ] `thoughts-sync` creates hardlinks as expected
- [ ] Version tracking shows correct plugin version
- [ ] Plugin can be enabled/disabled via `/plugin`

## What We're NOT Doing

- NOT creating hooks (analyzed and determined unnecessary - see bin/ Scripts Analysis below)
- NOT creating MCP servers (not needed for this workflow)
- NOT creating Agent Skills (commands/agents are sufficient)
- NOT converting bin/ scripts to hooks (hooks don't match use cases - scripts must remain)
- NOT changing the testing approach (current strategy is correct)
- NOT modifying the core workflow behavior (only packaging changes)
- NOT removing `install.sh` (remains as fallback for non-plugin users)
- NOT publishing to public marketplace initially (team testing first)

## bin/ Scripts Analysis

After thorough analysis of plugin hooks documentation and the 4 bin/ scripts, **all scripts must be kept**:

### thoughts-init
**Purpose**: One-time project setup - creates `thoughts/` directory structure
**Why keep**:
- ❌ No plugin hook for one-time initialization
- ❌ SessionStart hook runs every session (wrong frequency)
- ✅ User must explicitly initialize each project
**Verdict**: KEEP - no plugin alternative exists

### thoughts-sync
**Purpose**: Creates hardlinks from thoughts/ to thoughts/searchable/
**Why keep**:
- ✅ Commands (`/research_codebase`, `/create_plan`) call it explicitly after writing files
- ✅ User can run manually after adding files
- ❌ PostToolUse hook would trigger on ALL file writes (too broad, wasteful)
- ❌ No way to filter "only thoughts/ directory" in hooks
**Verdict**: KEEP - commands depend on it; hooks are wrong tool

### thoughts-metadata
**Purpose**: Generate git metadata (commit hash, branch, date) for document frontmatter
**Why keep**:
- ✅ Commands call it inline and capture output synchronously
- ❌ Hooks are asynchronous and can't "return data" to commands
- ✅ Commands need metadata immediately when generating documents
**Verdict**: KEEP - essential for command functionality; hooks can't provide synchronous data

### thoughts-version
**Purpose**: Check installed version vs repo version, warn if update available
**Why keep**:
- ✅ User convenience for checking updates
- ✅ Other scripts use it to show update warnings
- ⚠️ Less critical for plugin users (marketplace handles versioning) but still useful
- ✅ Very useful for install.sh users (no automatic updates)
**Verdict**: KEEP - benefits both installation methods

### Summary
**All 4 scripts remain in bin/ and require separate installation** because:
1. Plugin hooks don't match the use cases (one-time setup, on-demand execution, synchronous data return)
2. Commands have explicit dependencies on these scripts
3. Users need manual control over when operations happen
4. Scripts work for both plugin and install.sh installation methods

## Implementation Approach

Convert the project structure to a plugin by:
1. **Moving files**: Relocate `.claude/commands/` and `.claude/agents/` to plugin root
2. **Creating plugin manifest**: Add `.claude-plugin/plugin.json`
3. **Keeping bin/ scripts unchanged**: They cannot be replaced by hooks (see analysis above)
4. **Updating install.sh**: Change paths from `.claude/` to root directories
5. **Updating tests**: Update paths in test suite
6. **Creating local marketplace**: For testing the plugin
7. **Adding plugin validation**: To test suite

## Phase 0: Reorganize Directory Structure

### Overview
Move commands and agents from `.claude/` to plugin root to match Claude Code plugin conventions. This prevents confusion between the plugin's source structure and Claude Code's installation directory.

### Changes Required

#### 1. Move Commands to Root
**Current**: `.claude/commands/*.md`
**Target**: `commands/*.md`
**Changes**: Move directory

```bash
# Create new location
mkdir -p commands

# Move files
mv .claude/commands/*.md commands/

# Remove old directory
rmdir .claude/commands
```

**Why**: Plugin convention requires commands at root, not in `.claude/` subdirectory.

#### 2. Move Agents to Root
**Current**: `.claude/agents/*.md`
**Target**: `agents/*.md`
**Changes**: Move directory

```bash
# Create new location
mkdir -p agents

# Move files
mv .claude/agents/*.md agents/

# Remove old directory
rmdir .claude/agents

# Remove .claude/ if empty
rmdir .claude 2>/dev/null || true
```

**Why**: Plugin convention requires agents at root, not in `.claude/` subdirectory.

#### 3. Update install.sh Paths
**File**: `install.sh`
**Changes**: Update source directory paths

```bash
# Change line 48-49:
# FROM:
SRC_COMMANDS="$SCRIPT_DIR/.claude/commands"
SRC_AGENTS="$SCRIPT_DIR/.claude/agents"

# TO:
SRC_COMMANDS="$SCRIPT_DIR/commands"
SRC_AGENTS="$SCRIPT_DIR/agents"
```

**Why**: install.sh must copy from new locations.

#### 4. Update Test Paths
**File**: `test/smoke-test.sh`
**Changes**: Update file existence checks

```bash
# Update line 134-146 (install.sh validation):
# Commands installed checks use same paths (no change needed - they check target ~/.claude/)
# BUT update source validation if added later

# No immediate changes needed - tests check installed location, not source
```

**Why**: Tests validate installed files, which don't change location.

#### 5. Update CLAUDE.md Documentation
**File**: `CLAUDE.md`
**Changes**: Update structure documentation (lines 13-27)

```markdown
# FROM:
```
.claude/
├── commands/          # 6 slash commands (markdown files)
│   ├── research_codebase.md
...
└── agents/            # 5 specialized agents (markdown files)
```

# TO:
```
commands/              # 6 slash commands (markdown files)
│   ├── research_codebase.md
...
agents/                # 5 specialized agents (markdown files)
```
```

**Why**: Documentation must reflect new structure.

#### 6. Update README.md Structure Section
**File**: `README.md`
**Changes**: Update project structure diagram

Similar update to CLAUDE.md - change directory layout to show commands/agents at root.

**Why**: Users need accurate structure information.

### Success Criteria

#### Automated Verification:
- [x] No `.claude/` directory exists in repo: `test ! -d .claude`
- [x] Commands exist at root: `test -d commands && test -f commands/research_codebase.md`
- [x] Agents exist at root: `test -d agents && test -f agents/codebase-locator.md`
- [x] install.sh has updated paths: `grep -q 'SRC_COMMANDS="\$SCRIPT_DIR/commands"' install.sh`
- [x] All tests still pass: `make test`

#### Manual Verification:
- [ ] Can still install via `./install.sh`
- [ ] Commands appear in `/help` after installation
- [ ] Agents work correctly
- [ ] No confusion about directory structure in documentation

**Important Note**: This phase must be completed before Phase 1, as the plugin manifest will reference the new structure.

## Phase 1: Create Plugin Manifest

### Overview
Establish the plugin metadata by creating the required manifest file. Commands and agents are now at the plugin root (moved in Phase 0).

### Changes Required

#### 1. Create Plugin Manifest
**File**: `.claude-plugin/plugin.json`
**Changes**: Create new file

```json
{
  "name": "workflow-dev",
  "version": "1.0.0",
  "description": "Research → Plan → Implement → Validate workflow for Claude Code with local thoughts/ management",
  "author": {
    "name": "Jorge Castro",
    "email": "nikey_es@yahoo.es"
  },
  "homepage": "https://github.com/nikey-es/claude-code-dev-workflow",
  "repository": "https://github.com/nikey-es/claude-code-dev-workflow",
  "license": "Apache-2.0",
  "keywords": [
    "workflow",
    "development",
    "planning",
    "research",
    "tdd"
  ]
}
```

**Why**: Plugin manifest is required for Claude Code to recognize the plugin.

#### 2. Create Plugin README
**File**: `PLUGIN.md`
**Changes**: Create documentation specific to plugin usage

Content should explain:
- How to install via `/plugin` command
- Script installation requirements (manual `bin/` setup)
- Post-installation steps (`thoughts-init`)
- Differences from `install.sh` method

**Why**: Plugin users need different installation instructions than manual installers.

#### 3. Update Main README
**File**: `README.md`
**Changes**: Add plugin installation section at the top

Add before "Quick Install":
```markdown
## 🚀 Installation

### Method 1: Via Plugin (Recommended)

```bash
# Add marketplace from GitHub
/plugin marketplace add nikey-es/claude-code-dev-workflow

# Install plugin
/plugin install workflow-dev@workflow-dev-marketplace

# Then install helper scripts (one-time setup)
git clone https://github.com/nikey-es/claude-code-dev-workflow.git
cd claude-code-dev-workflow
./install-scripts.sh
```

### Method 2: Manual Installation

```bash
git clone https://github.com/nikey-es/claude-code-dev-workflow.git
cd claude-code-dev-workflow
./install.sh
```
```

**Why**: Users need to know both installation methods exist, with complete instructions.

#### 4. Create Script-Only Installer
**File**: `install-scripts.sh`
**Changes**: Create new installer that only installs `bin/` scripts

```bash
#!/usr/bin/env bash
# install-scripts.sh - Install thoughts/ helper scripts only
# Use this after installing the plugin to add PATH scripts

# ... (similar to install.sh but only bin/ directory)
```

**Why**: Plugin handles commands/agents, but scripts need manual PATH installation.

### Success Criteria

#### Automated Verification:
- [x] Plugin manifest validates: `claude plugin validate .`
- [x] JSON syntax is valid: `jq . .claude-plugin/plugin.json`
- [x] All required manifest fields present
- [x] install-scripts.sh is executable: `test -x install-scripts.sh`

## Phase 2: Create Test Marketplace

### Overview
Set up a local marketplace structure for testing the plugin installation and lifecycle before distribution.

### Changes Required

#### 1. Create Marketplace Directory
**File**: `test-marketplace/.claude-plugin/marketplace.json`
**Changes**: Create new marketplace manifest

```json
{
  "name": "workflow-dev-test",
  "owner": {
    "name": "Jorge Castro",
    "email": "nikey_es@yahoo.es"
  },
  "plugins": [
    {
      "name": "workflow-dev",
      "source": "../",
      "description": "Local development version of workflow-dev plugin",
      "strict": true
    }
  ]
}
```

**Why**: Allows testing plugin installation without pushing to GitHub.

#### 2. Add Marketplace Testing Documentation
**File**: `test-marketplace/README.md`
**Changes**: Create testing instructions

Content:
```markdown
# Test Marketplace for Plugin Development

Test the plugin locally before distribution:

\`\`\`bash
# From project root
cd /path/to/claude-code-dev-workflow

# In Claude Code
/plugin marketplace add ./test-marketplace
/plugin install workflow-dev@workflow-dev-test
/plugin list  # Verify it's installed
\`\`\`

Restart Claude Code, then test:
- `/help` should show all 6 commands
- `/research_codebase` should execute
\`\`\`
```

**Why**: Developers need clear testing workflow.

#### 3. Add .gitignore Entry
**File**: `.gitignore`
**Changes**: Add test marketplace to gitignore if needed

```
test-marketplace/
```

**Why**: Test marketplace is for local development only.

### Success Criteria

#### Automated Verification:
- [ ] Marketplace JSON validates: `jq . test-marketplace/.claude-plugin/marketplace.json`
- [ ] Marketplace directory structure is correct

#### Manual Verification:
- [ ] Can add test marketplace via `/plugin marketplace add ./test-marketplace`
- [ ] Marketplace appears in `/plugin marketplace list`
- [ ] Can install plugin from test marketplace
- [ ] Commands appear in `/help` after installation
- [ ] `/research_codebase` executes successfully

## Phase 3: Update Testing Infrastructure

### Overview
Extend the test suite to validate plugin functionality without changing the core testing approach.

### Changes Required

#### 1. Add Plugin Validation Test
**File**: `test/smoke-test.sh`
**Changes**: Add new test group after Test 7

```bash
# ============================================================================
# Test 8: Plugin manifest validates correctly
# ============================================================================
section "Test 8: Plugin manifest validation"

cd "$PROJECT_ROOT"

# Check .claude-plugin directory exists
assert_dir_exists ".claude-plugin" ".claude-plugin/ directory exists"

# Check plugin.json exists
assert_file_exists ".claude-plugin/plugin.json" "plugin.json exists"

# Validate JSON syntax (if jq available)
if command -v jq >/dev/null 2>&1; then
  if jq empty .claude-plugin/plugin.json 2>/dev/null; then
    echo -e "${GREEN}✓${NC} plugin.json has valid JSON syntax"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}✗${NC} plugin.json has invalid JSON syntax"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  TESTS_RUN=$((TESTS_RUN + 1))
fi

# Check required fields
plugin_content=$(cat .claude-plugin/plugin.json)
assert_output_contains "$plugin_content" '"name"' "manifest contains name field"
assert_output_contains "$plugin_content" '"version"' "manifest contains version field"
assert_output_contains "$plugin_content" '"description"' "manifest contains description field"
```

**Why**: Ensures plugin manifest remains valid as project evolves.

#### 2. Create Plugin Test Instructions
**File**: `test/PLUGIN_TESTING.md`
**Changes**: Create manual testing guide

Content:
```markdown
# Plugin Testing Guide

## Automated Tests

Run automated tests that validate bash scripts and plugin structure:

\`\`\`bash
make test          # Smoke tests (~3 seconds)
make check         # Shellcheck linting
\`\`\`

## Manual Plugin Tests

These require Claude Code and cannot be automated:

### 1. Test Local Installation
\`\`\`bash
/plugin marketplace add ./test-marketplace
/plugin install workflow-dev@workflow-dev-test
\`\`\`
Restart Claude Code.

### 2. Verify Commands Available
\`\`\`bash
/help
\`\`\`
Should show: research_codebase, create_plan, iterate_plan, implement_plan, validate_plan, commit

### 3. Test Full Workflow
\`\`\`bash
cd ~/test-project
thoughts-init
/research_codebase test topic
\`\`\`
Verify: thoughts/shared/research/ contains document

### 4. Test Plugin Lifecycle
\`\`\`bash
/plugin disable workflow-dev@workflow-dev-test
/help  # Commands should be gone
/plugin enable workflow-dev@workflow-dev-test
/help  # Commands should return
\`\`\`

## What Cannot Be Tested

- Actual command execution (requires Claude interpretation)
- Agent spawning behavior (requires Claude's Task tool)
- Interaction quality (subjective, requires human evaluation)

These are tested through real-world usage and iteration.
\`\`\`
```

**Why**: Documents the boundary between automated and manual testing clearly.

#### 3. Update Makefile Help
**File**: `Makefile`
**Changes**: Add plugin testing targets

```makefile
# After line 18, add:
	@echo "Plugin validation:"
	@echo "  make validate-plugin    - Validate plugin manifest"
	@echo "  make test-plugin        - Run automated plugin tests"
	@echo ""

# Add new targets:
validate-plugin:
	@echo "Validating plugin manifest..."
	@if command -v jq >/dev/null 2>&1; then \
		jq empty .claude-plugin/plugin.json && echo "✓ Plugin manifest valid"; \
	else \
		echo "⚠ jq not installed, skipping validation"; \
	fi
	@if command -v claude >/dev/null 2>&1; then \
		claude plugin validate . && echo "✓ Claude plugin validation passed"; \
	else \
		echo "⚠ claude CLI not available, skipping claude validation"; \
	fi

test-plugin: test validate-plugin
	@echo "✓ All plugin tests passed"
```

**Why**: Provides convenient shortcuts for plugin validation.

### Success Criteria

#### Automated Verification:
- [ ] New plugin validation tests pass: `make test`
- [ ] Plugin manifest validates: `make validate-plugin`
- [ ] Existing tests still pass (no regressions)
- [ ] Shellcheck passes: `make check`

## Phase 4: Update Documentation

### Overview
Comprehensive documentation updates to reflect plugin installation method and clarify script requirements.

### Changes Required

#### 1. Update CLAUDE.md
**File**: `CLAUDE.md`
**Changes**: Add plugin information after line 10

Add section:
```markdown
## Plugin Structure

This project is distributed as a Claude Code plugin:

**Plugin Name**: `workflow-dev`
**Components**:
- 6 slash commands in `commands/` (at plugin root)
- 5 specialized agents in `agents/` (at plugin root)
- 4 bash scripts in `bin/` (require separate installation)

**Installation**:
- Plugin: Via `/plugin install workflow-dev@workflow-dev-marketplace`
- Scripts: Via `./install-scripts.sh` (one-time, adds to `~/.local/bin/`)

**Note**: Commands and agents are at the plugin root, NOT in a `.claude/` subdirectory.
This follows Claude Code plugin conventions and prevents confusion with the actual
`~/.claude/` installation directory.

See README.md for detailed installation instructions.
```

**Why**: Developers working on the plugin need to understand the structure and why `.claude/` was removed.

#### 2. Update README Installation Section
**File**: `README.md`
**Changes**: Expand installation section with plugin method

See Phase 1, Change 3 for content.

#### 3. Create CHANGELOG.md
**File**: `CHANGELOG.md`
**Changes**: Create changelog to track plugin versions

```markdown
# Changelog

All notable changes to the Claude Code Workflow plugin.

## [1.0.0] - 2025-11-11

### Added
- Plugin manifest for Claude Code marketplace distribution
- Test marketplace for local development testing
- install-scripts.sh for standalone script installation
- Plugin validation in test suite
- PLUGIN.md documentation

### Changed
- README reorganized with plugin installation as primary method
- CLAUDE.md updated with plugin structure information
- install.sh remains available for non-plugin installation

### Deprecated
- Nothing (install.sh still supported)

## [0.9.0] - Previous Releases

Pre-plugin versions. See git history for details.
```

**Why**: Users need to understand version changes and migration path.

#### 4. Update .gitignore
**File**: `.gitignore`
**Changes**: Ensure plugin-related files are properly handled

```
# Test marketplace (local development only)
test-marketplace/

# Backup files from installer
.claude-workflow-backup-*/

# Thoughts directory is project-specific
thoughts/searchable/
```

**Why**: Prevent committing local test artifacts.

### Success Criteria

#### Automated Verification:
- [ ] All documentation files exist and have content
- [ ] Markdown syntax validates (if linter available)
- [ ] Links in README are not broken

#### Manual Verification:
- [ ] README installation instructions are clear
- [ ] CLAUDE.md accurately describes plugin structure
- [ ] CHANGELOG matches actual changes
- [ ] PLUGIN.md installation steps work end-to-end

## Phase 5: Create GitHub Marketplace

### Overview
Prepare the plugin for distribution via GitHub marketplace for team and community use.

### Changes Required

#### 1. Create Marketplace Manifest
**File**: `.claude-plugin/marketplace.json`
**Changes**: Create production marketplace manifest

```json
{
  "name": "workflow-dev-marketplace",
  "owner": {
    "name": "Jorge Castro",
    "email": "nikey_es@yahoo.es"
  },
  "metadata": {
    "description": "Structured development workflow for Claude Code",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "workflow-dev",
      "source": "./",
      "description": "Research → Plan → Implement → Validate workflow with local thoughts/ management",
      "version": "1.0.0",
      "category": "productivity",
      "keywords": ["workflow", "planning", "tdd", "documentation"],
      "strict": true
    }
  ]
}
```

**Why**: Allows distribution via GitHub repository.

#### 2. Update README with Marketplace Instructions
**File**: `README.md`
**Changes**: Update plugin installation to use GitHub

```markdown
### Method 1: Via Plugin (Recommended)

```bash
# Add marketplace from GitHub
/plugin marketplace add nikey-es/claude-code-dev-workflow

# Install plugin
/plugin install workflow-dev@workflow-dev-marketplace

# Install helper scripts (one-time)
git clone https://github.com/nikey-es/claude-code-dev-workflow.git
cd claude-code-dev-workflow
./install-scripts.sh
```
```

**Why**: Users need actual installation commands, not placeholder ones.

#### 3. Add Marketplace Documentation
**File**: `MARKETPLACE.md`
**Changes**: Create marketplace-specific documentation

```markdown
# Workflow-Dev Plugin Marketplace

This repository hosts the `workflow-dev` plugin for Claude Code.

## Installation

Add the marketplace to your Claude Code:

\`\`\`bash
/plugin marketplace add nikey-es/claude-code-dev-workflow
\`\`\`

Then install the plugin:

\`\`\`bash
/plugin install workflow-dev@workflow-dev-marketplace
\`\`\`

### Helper Scripts

The plugin includes 4 helper scripts for thoughts/ management. Install them separately:

\`\`\`bash
git clone https://github.com/nikey-es/claude-code-dev-workflow.git
cd claude-code-dev-workflow
./install-scripts.sh
\`\`\`

This adds to your PATH:
- `thoughts-init` - Initialize thoughts/ in projects
- `thoughts-sync` - Sync searchable/ hardlinks
- `thoughts-metadata` - Generate git metadata
- `thoughts-version` - Check for updates

## What's Included

### Commands (6)
- `/research_codebase` - Comprehensive codebase research
- `/create_plan` - Interactive implementation planning
- `/iterate_plan` - Update existing plans
- `/implement_plan` - Execute plans phase-by-phase
- `/validate_plan` - Verify implementation completeness
- `/commit` - Create commits (no Claude attribution)

### Agents (5)
- `codebase-locator` - Find code locations
- `codebase-analyzer` - Understand implementations
- `codebase-pattern-finder` - Discover similar patterns
- `thoughts-locator` - Search thoughts/ documents
- `thoughts-analyzer` - Extract insights from thoughts

## Testing

The plugin includes automated tests for helper scripts:

\`\`\`bash
make test    # Smoke tests (~3 seconds)
make check   # Shellcheck linting
\`\`\`

See [test/PLUGIN_TESTING.md](test/PLUGIN_TESTING.md) for manual testing procedures.

## Support

- Issues: https://github.com/nikey-es/claude-code-dev-workflow/issues
- Documentation: https://github.com/nikey-es/claude-code-dev-workflow/blob/main/README.md
\`\`\`
```

**Why**: Marketplace-specific landing page for plugin users.

#### 4. Create Release Workflow
**File**: `.github/workflows/release.yml`
**Changes**: Optional GitHub Actions workflow for releases

```yaml
name: Release Plugin

on:
  push:
    tags:
      - 'v*'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate plugin manifest
        run: |
          sudo apt-get install jq
          jq empty .claude-plugin/plugin.json
          jq empty .claude-plugin/marketplace.json
      - name: Run tests
        run: make test
      - name: Run shellcheck
        run: |
          sudo apt-get install shellcheck
          make check
```

**Why**: Automates validation on version tags (optional but recommended).

### Success Criteria

#### Automated Verification:
- [ ] Marketplace manifest validates: `jq . .claude-plugin/marketplace.json`
- [ ] All documentation files created
- [ ] GitHub Actions workflow syntax valid (if created)

#### Manual Verification:
- [ ] Can add marketplace from GitHub: `/plugin marketplace add nikey-es/claude-code-dev-workflow`
- [ ] Marketplace appears in listing
- [ ] Can install plugin from GitHub marketplace
- [ ] Plugin README displays correctly on GitHub
- [ ] All links in MARKETPLACE.md work

## Phase 6: Final Testing & Documentation

### Overview
Comprehensive end-to-end testing and final documentation polish before distribution.

### Changes Required

#### 1. End-to-End Test Checklist
**File**: `test/E2E_CHECKLIST.md`
**Changes**: Create comprehensive manual test checklist

```markdown
# End-to-End Plugin Testing Checklist

Test the complete plugin lifecycle before release.

## Fresh Installation Test

### Prerequisites
- [ ] Fresh machine or test user account
- [ ] Claude Code installed
- [ ] Git available

### Installation Steps
1. [ ] Add marketplace: `/plugin marketplace add nikey-es/claude-code-dev-workflow`
2. [ ] Verify marketplace appears: `/plugin marketplace list`
3. [ ] Install plugin: `/plugin install workflow-dev@workflow-dev-marketplace`
4. [ ] Restart Claude Code
5. [ ] Verify commands appear: `/help`
6. [ ] Clone repo and install scripts: `./install-scripts.sh`
7. [ ] Verify scripts in PATH: `which thoughts-init`

### Functionality Tests
1. [ ] Create test project directory
2. [ ] Run `thoughts-init`
3. [ ] Verify directory structure created
4. [ ] Execute `/research_codebase test topic`
5. [ ] Verify research document created
6. [ ] Execute `/create_plan test feature`
7. [ ] Verify plan created
8. [ ] Execute `thoughts-sync`
9. [ ] Verify hardlinks created
10. [ ] Test all other commands

### Plugin Lifecycle
1. [ ] Disable plugin: `/plugin disable workflow-dev@workflow-dev-marketplace`
2. [ ] Verify commands gone: `/help`
3. [ ] Enable plugin: `/plugin enable workflow-dev@workflow-dev-marketplace`
4. [ ] Verify commands return: `/help`
5. [ ] Uninstall plugin: `/plugin uninstall workflow-dev@workflow-dev-marketplace`
6. [ ] Verify complete removal

## Update Test

Test upgrading from previous version:

1. [ ] Install v0.9.0 (if exists)
2. [ ] Upgrade to v1.0.0
3. [ ] Verify no data loss
4. [ ] Verify scripts still work
5. [ ] Verify version tracking updates
```

**Why**: Systematic validation catches edge cases before release.

#### 2. Update Main README with Troubleshooting
**File**: `README.md`
**Changes**: Add plugin-specific troubleshooting section

Add before "Learn More" section:
```markdown
## 🐛 Troubleshooting

### Plugin Issues

**Commands not showing after installation**:
- Restart Claude Code completely
- Check plugin is enabled: `/plugin list`
- Try reinstalling: `/plugin uninstall workflow-dev@...` then `/plugin install ...`

**Scripts not found in PATH**:
- Check installation: `which thoughts-init`
- Add to shell config: `export PATH="$HOME/.local/bin:$PATH"`
- Run `./install-scripts.sh` again

**Plugin installation fails**:
- Verify marketplace added: `/plugin marketplace list`
- Check network connection (for GitHub marketplaces)
- Try local marketplace: `/plugin marketplace add ./test-marketplace`

### Workflow Issues

(Keep existing troubleshooting items...)
```

**Why**: Plugin users need plugin-specific help.

#### 3. Create Migration Guide
**File**: `MIGRATION.md`
**Changes**: Guide for existing install.sh users

```markdown
# Migration Guide: install.sh → Plugin

If you previously installed via `./install.sh`, here's how to migrate to the plugin.

## Why Migrate?

Plugin installation provides:
- Automatic updates via marketplace
- Easy enable/disable toggle
- No manual file copying
- Simpler uninstallation

## Migration Steps

### 1. Backup Current Setup (Optional)
```bash
cp -r ~/.claude/commands ~/.claude/commands.backup
cp -r ~/.claude/agents ~/.claude/agents.backup
```

### 2. Uninstall Manual Installation
```bash
# Remove old files
rm ~/.claude/commands/research_codebase.md
rm ~/.claude/commands/create_plan.md
rm ~/.claude/commands/iterate_plan.md
rm ~/.claude/commands/implement_plan.md
rm ~/.claude/commands/validate_plan.md
rm ~/.claude/commands/commit.md
rm ~/.claude/agents/codebase-*.md
rm ~/.claude/agents/thoughts-*.md

# Scripts can stay (same location)
# ~/.local/bin/thoughts-* doesn't conflict
```

### 3. Install Plugin
```bash
/plugin marketplace add nikey-es/claude-code-dev-workflow
/plugin install workflow-dev@workflow-dev-marketplace
```

Restart Claude Code.

### 4. Verify
```bash
/help  # Should show all 6 commands
thoughts-version  # Should show version
```

## Notes

- Your `thoughts/` directories are unaffected
- Scripts remain in `~/.local/bin/` (no reinstall needed)
- Backups can be deleted after verification
- You can still use `./install.sh` if you prefer manual control
```

**Why**: Helps existing users transition smoothly.

#### 4. Add Plugin Badge to README
**File**: `README.md`
**Changes**: Add badge at top showing plugin availability

```markdown
# Claude Code Workflow - Local Setup

[![Plugin Available](https://img.shields.io/badge/Claude_Code-Plugin_Available-blue)](https://github.com/nikey-es/claude-code-dev-workflow)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)](test/)

A complete workflow system...
```

**Why**: Visual indicator of plugin availability and project health.

### Success Criteria

#### Automated Verification:
- [ ] All documentation files exist
- [ ] All links in documentation work
- [ ] Badges render correctly
- [ ] Test suite passes: `make test && make check`

#### Manual Verification:
- [ ] Complete E2E checklist passes 100%
- [ ] Fresh installation works first time
- [ ] Migration from install.sh works
- [ ] All troubleshooting steps are accurate
- [ ] Documentation is clear and comprehensive

## Testing Strategy

### Automated Tests
Run these before every commit:
```bash
make test          # Bash script smoke tests
make check         # Shellcheck linting
make validate-plugin  # Plugin manifest validation
```

**What's covered:**
- ✅ `bin/thoughts-*` script functionality
- ✅ `install.sh` installation logic
- ✅ Plugin manifest JSON validity
- ✅ Required manifest fields present

### Manual Tests
Required for commands/agents (cannot be automated):

1. **Plugin Installation**
   - Add marketplace
   - Install plugin
   - Verify commands in `/help`

2. **Command Execution**
   - `/research_codebase` generates document
   - `/create_plan` creates plan
   - `/implement_plan` executes phases
   - All agents spawn correctly

3. **Script Functionality**
   - `thoughts-init` creates structure
   - `thoughts-sync` creates hardlinks
   - `thoughts-metadata` generates data
   - `thoughts-version` checks updates

See `test/PLUGIN_TESTING.md` for detailed procedures.

### Why This Approach?

**Automated Testing is for:**
- Deterministic bash script behavior
- JSON validation
- File system operations
- Installation mechanics

**Manual Testing is for:**
- Markdown prompt interpretation (Claude-specific)
- Agent spawning behavior (requires Claude context)
- Subjective workflow quality
- User experience evaluation

This boundary is clearly documented and tested.

## Performance Considerations

**Plugin Size**: ~50KB (6 commands + 5 agents + manifest)
**Installation Time**: < 5 seconds
**Script Installation**: < 10 seconds
**No Runtime Overhead**: Commands/agents are loaded on-demand

**Optimization Notes**:
- Plugin is text-only (markdown + JSON)
- No binary dependencies
- Bash scripts are small and fast
- Hardlinks use zero extra disk space

## Migration Notes

### For Existing Users

If you currently use `./install.sh`:
1. Plugin installation is optional (install.sh still works)
2. **Scripts remain unchanged** (same `~/.local/bin/` location, same functionality)
3. Scripts cannot be replaced by hooks (see bin/ Scripts Analysis section for details)
4. thoughts/ directories are unaffected
5. See `MIGRATION.md` for detailed transition guide

### For New Users

Plugin installation is recommended:
- Easier updates via marketplace
- Simple enable/disable toggle
- No manual file management (for commands/agents)
- **Scripts still require manual installation** via `install-scripts.sh`
- Better for team distribution

**Note**: Even with plugin installation, the 4 helper scripts (`thoughts-init`, `thoughts-sync`, `thoughts-metadata`, `thoughts-version`) must be installed separately to `~/.local/bin/`. This is by design - plugin hooks cannot replace their functionality (see bin/ Scripts Analysis).

### Backward Compatibility

All existing functionality preserved:
- ✅ install.sh works as before
- ✅ Scripts work identically
- ✅ thoughts/ structure unchanged
- ✅ Test suite unchanged
- ✅ Documentation accessible both ways

## References

- Plugin documentation: `thoughts/nikey_es/notes/plugins-claude-code.md` (lines 716-1917)
  - Plugin hooks documentation: lines 807-852
  - Plugin directory structure: lines 999-1029
- Original README: `README.md`
- Project structure: `CLAUDE.md`
- Testing strategy: `test/smoke-test.sh`, `test/test-helpers.sh`
- Installation: `install.sh`
- bin/ scripts analysis:
  - `bin/thoughts-init` - Project initialization
  - `bin/thoughts-sync` - Hardlink synchronization
  - `bin/thoughts-metadata` - Git metadata generation
  - `bin/thoughts-version` - Version tracking

## Implementation Timeline

**Estimated Duration**: 5-7 hours

- Phase 0 (Directory Reorganization): 45-60 minutes ⚠️ **MUST BE DONE FIRST**
- Phase 1 (Plugin Manifest): 30-45 minutes
- Phase 2 (Test Marketplace): 30-45 minutes
- Phase 3 (Testing): 45-60 minutes
- Phase 4 (Documentation): 60-90 minutes
- Phase 5 (GitHub Marketplace): 45-60 minutes
- Phase 6 (Final Testing): 60-90 minutes

**Important**: Phase 0 is a prerequisite for all other phases. Once completed, other phases can be done in order or independently tested.
