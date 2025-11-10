# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **workflow tooling project for Claude Code itself**, not a traditional software application. It provides slash commands, specialized agents, and bash scripts that implement a structured Research → Plan → Implement → Validate development cycle.

The workflow operates entirely locally without cloud dependencies and uses a `thoughts/` directory system with hardlinks for efficient searching.

## Project Structure

```
.claude/
├── commands/          # 6 slash commands (markdown files)
│   ├── research_codebase.md
│   ├── create_plan.md
│   ├── iterate_plan.md
│   ├── implement_plan.md
│   ├── validate_plan.md
│   └── commit.md
└── agents/            # 5 specialized agents (markdown files)
    ├── codebase-locator.md
    ├── codebase-analyzer.md
    ├── codebase-pattern-finder.md
    ├── thoughts-locator.md
    └── thoughts-analyzer.md

bin/                   # 4 bash scripts for thoughts/ management
├── thoughts-init      # Initialize thoughts/ structure
├── thoughts-sync      # Sync hardlinks to searchable/
├── thoughts-metadata  # Generate git metadata
└── thoughts-version   # Check installed version

install.sh            # Installer script (copies to ~/.claude/)
```

## Installation & Testing Workflow

### Installation
```bash
# Install to global ~/.claude/ directory
./install.sh

# Verify installation
ls ~/.claude/commands/
ls ~/.claude/agents/
which thoughts-init thoughts-sync thoughts-metadata thoughts-version

# Check version
thoughts-version
```

### Testing Changes

This project has **two types of testing**:

#### 1. Automated Smoke Tests (for bash scripts)

Run automated tests for core bash functionality:

```bash
# Quick smoke test (~2-3 seconds)
make test

# Verbose output with debug info
make test-verbose

# Shellcheck on all bash scripts
make check
```

**What's covered:**
- ✅ `bin/thoughts-init` - Directory creation, gitignore, README generation
- ✅ `bin/thoughts-sync` - Hardlink creation, orphan cleanup
- ✅ `bin/thoughts-metadata` - Metadata generation
- ✅ `bin/thoughts-version` - Version checking and comparison
- ✅ `install.sh` - File installation, backup creation, VERSION file generation

**Test files:**
- `test/smoke-test.sh` - Main integration tests (7 test groups, 51 assertions)
- `test/test-helpers.sh` - Assertion functions and utilities
- `Makefile` - Test runner targets

#### 2. Manual Testing (for commands/agents)

Commands and agents require manual validation in Claude Code:

1. **Test slash commands in Claude Code:**
   - Commands are loaded from `~/.claude/commands/`
   - After modifying a command file, restart Claude Code or start a new conversation
   - Test by invoking: `/research_codebase`, `/create_plan`, etc.

2. **Validate agents:**
   - Agents spawn as sub-tasks when commands execute
   - Test by running commands that use them (e.g., `/research_codebase` spawns `codebase-locator`)
   - Check agent behavior in Claude Code's task output

### Iterative Development Cycle

When modifying commands/agents/scripts:

1. **Edit** the file in this repo
2. **Re-run** `./install.sh` (or manually copy to `~/.claude/`)
3. **Test** in a sample project
4. **Iterate** based on results

## Architecture

### Command Structure
Commands are markdown files with:
- Frontmatter: `description`, `model` (opus/sonnet/haiku)
- Instructions for Claude Code on how to behave
- Workflow steps (spawn agents, read files, generate documents)

### Agent Structure
Agents are specialized markdown files with:
- Frontmatter: `name`, `description`, `tools`, `model`, `color`
- Narrowly-scoped instructions (locate, analyze, or find patterns)
- Called via `Task` tool by commands

### Thoughts System
Scripts create a directory structure:
```
thoughts/
├── {username}/        # Personal notes (default: nikey_es)
│   ├── tickets/
│   └── notes/
├── shared/            # Team-shared documents
│   ├── research/      # Research documents
│   ├── plans/         # Implementation plans
│   └── prs/           # PR descriptions
└── searchable/        # Hardlinks for fast grep (auto-generated)
```

**Key concept:** `thoughts-sync` creates hardlinks from source directories to `searchable/` for efficient grep operations without file duplication.

### Workflow Philosophy

1. **Context management:** Never exceed 60% context
2. **Phased work:** Research → Plan → Implement → Validate
3. **Clear between phases:** Use `/clear` to reset context
4. **Parallel research:** Commands spawn multiple agents concurrently
5. **Local persistence:** All documents saved to `thoughts/` for future reference

## Configuration

**Username**: Set `export THOUGHTS_USER=your_name` (default: `nikey_es`)
**PATH**: Add `export PATH="$HOME/.local/bin:$PATH"` to shell config

### Version Tracking

The workflow includes built-in version tracking to help teams stay synchronized:

**How it works:**
- `install.sh` creates `~/.claude/claude-code-dev-workflow-version` with version info (version tag/commit, install date, commit hash)
- `thoughts-version` compares your installed version with the repository version
- Other scripts (`thoughts-init`, `thoughts-sync`, `thoughts-metadata`) automatically check for updates and warn if outdated

**Usage:**
```bash
# Check your installed version
thoughts-version

# Example output (up-to-date):
# Installed Version:
#   Version:   v1.2.0
#   Installed: 2025-11-10 14:30:00 UTC
#   Commit:    abc123def456
#
# Repository Version:
#   Version:   v1.2.0
#   Commit:    abc123def456
# ✓ Up to date!

# Example output (outdated):
# ⚠ Update available!
# To update:
#   cd /path/to/claude-code-dev-workflow
#   git pull
#   ./install.sh
```

**Creating releases with tags:**
```bash
# Tag a new release
git tag v1.2.0
git push origin v1.2.0

# Install from specific tag
git checkout v1.2.0
./install.sh
```

**Version format:**
- With tags: `v1.2.0`, `v1.2.0-dirty` (local changes)
- Between tags: `v1.2.0-5-gabc123` (5 commits after v1.2.0)
- Without tags: `abc123` (commit hash only)

## Development Workflow

1. Edit file (command/agent/script)
2. Run `./install.sh` or `make test`
3. Test changes
4. Iterate

## Attribution

This project is derived from [HumanLayer](https://github.com/humanlayer/humanlayer) and adapted for local-only operation. All `.claude/` components are modified versions licensed under Apache License 2.0.
