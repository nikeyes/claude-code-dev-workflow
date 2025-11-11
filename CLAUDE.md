# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **workflow tooling project for Claude Code itself**, not a traditional software application. It provides slash commands, specialized agents, and bash scripts that implement a structured Research → Plan → Implement → Validate development cycle.

The workflow operates entirely locally without cloud dependencies and uses a `thoughts/` directory system with hardlinks for efficient searching.

## Plugin Structure

This project is distributed as a Claude Code plugin:

**Plugin Name**: `stepwise-dev`

**Components**:
- 6 slash commands in `commands/` (at plugin root)
- 5 specialized agents in `agents/` (at plugin root)
- 3 bash scripts in `bin/` (require separate installation)

**Installation**:
- Plugin: Via `/plugin install stepwise-dev@stepwise-dev-marketplace`
- Scripts: Via `./install-scripts.sh` (one-time, adds to `~/.local/bin/`)

**Note**: Commands and agents are at the plugin root, NOT in a `.claude/` subdirectory.
This follows Claude Code plugin conventions and prevents confusion with the actual
`~/.claude/` installation directory.

See README.md for detailed installation instructions.

## Project Structure

```
commands/              # 6 slash commands (markdown files)
├── research_codebase.md
├── create_plan.md
├── iterate_plan.md
├── implement_plan.md
├── validate_plan.md
└── commit.md

agents/                # 5 specialized agents (markdown files)
├── codebase-locator.md
├── codebase-analyzer.md
├── codebase-pattern-finder.md
├── thoughts-locator.md
└── thoughts-analyzer.md

bin/                   # 3 bash scripts for thoughts/ management
├── thoughts-init      # Initialize thoughts/ structure
├── thoughts-sync      # Sync hardlinks to searchable/
└── thoughts-metadata  # Generate git metadata

install-scripts.sh    # Script installer (copies to ~/.local/bin/)
test/                 # Automated bash tests
```

## Installation & Testing Workflow

### Installation
```bash
# Install plugin in Claude Code
/plugin marketplace add nikey-es/claude-code-dev-workflow
/plugin install stepwise-dev@stepwise-dev-marketplace
# Restart Claude Code

# Install scripts to PATH
./install-scripts.sh

# Verify installation
which thoughts-init thoughts-sync thoughts-metadata
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
- ✅ `install-scripts.sh` - Script installation to ~/.local/bin/

**Test files:**
- `test/smoke-test.sh` - Main integration tests (7 test groups)
- `test/test-helpers.sh` - Assertion functions and utilities
- `Makefile` - Test runner targets

#### 2. Manual Testing (for commands/agents)

Commands and agents require manual validation in Claude Code:

1. **Test slash commands in Claude Code:**
   - Commands are loaded via the plugin
   - After modifying a command file, restart Claude Code or use `/plugin reload`
   - Test by invoking: `/research_codebase`, `/create_plan`, etc.

2. **Validate agents:**
   - Agents spawn as sub-tasks when commands execute
   - Test by running commands that use them (e.g., `/research_codebase` spawns `codebase-locator`)
   - Check agent behavior in Claude Code's task output

### Iterative Development Cycle

When modifying **commands/agents**:
1. **Edit** the file in `commands/` or `agents/`
2. **Test locally** via plugin development mode or by reinstalling the plugin
3. **Validate** in a sample project
4. **Iterate** based on results

When modifying **scripts**:
1. **Edit** the file in `bin/`
2. **Re-run** `./install-scripts.sh`
3. **Test** with the script directly
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

### Version Management

**Plugin version:**
- Managed by Claude Code plugin system
- Check with `/plugin list` or `/plugin show stepwise-dev@stepwise-dev-marketplace`
- Update with `/plugin update stepwise-dev@stepwise-dev-marketplace`

**Scripts:**
- Updated independently via `./install-scripts.sh`
- No built-in version checking (scripts are simple utilities)

## Development Workflow

For **scripts**:
1. Edit file in `bin/`
2. Run `./install-scripts.sh` or `make test`
3. Test changes
4. Iterate

For **commands/agents**:
1. Edit file in `commands/` or `agents/`
2. Test via plugin reload or development mode
3. Validate in Claude Code
4. Iterate

## Attribution

This project is derived from [HumanLayer](https://github.com/humanlayer/humanlayer) and adapted for local-only operation. All `.claude/` components are modified versions licensed under Apache License 2.0.
