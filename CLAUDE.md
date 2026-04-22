# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **workflow tooling project for Claude Code itself**, not a traditional software application. It provides slash commands, specialized agents, and bash scripts that implement a structured Research → Plan → Implement → Validate development cycle.

The workflow operates entirely locally without cloud dependencies and uses a `thoughts/` directory system for persistent storage.

## Multi-Plugin Architecture

This project is distributed as **3 independent Claude Code plugins** in a single marketplace:

### Plugin 1: stepwise-core
**Location**: `core/`
**Components**:
- 5 slash commands (research_codebase, create_plan, iterate_plan, implement_plan, validate_plan)
- 5 specialized agents (codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer)
- 1 Agent Skill (thoughts-management with 2 bash scripts)

### Plugin 2: stepwise-git
**Location**: `git/`
**Components**:
- 1 slash command (commit)

### Plugin 3: stepwise-web
**Location**: `web/`
**Components**:
- 1 specialized agent (web-search-researcher)

**Installation**:
```bash
# Add marketplace
/plugin marketplace add nikeyes/stepwise-dev

# Install all three (or pick individual ones)
/plugin install stepwise-core@stepwise-dev
/plugin install stepwise-git@stepwise-dev
/plugin install stepwise-web@stepwise-dev
```

See README.md for detailed installation instructions.

## Project Structure

```
.claude-plugin/        # Marketplace configuration
└── marketplace.json   # Marketplace listing all 3 plugins

core/                  # stepwise-core plugin
├── .claude-plugin/
│   └── plugin.json
├── commands/          # 5 slash commands (markdown files)
│   ├── research_codebase.md
│   ├── create_plan.md
│   ├── iterate_plan.md
│   ├── implement_plan.md
│   └── validate_plan.md
├── agents/            # 5 specialized agents (markdown files)
│   ├── codebase-locator.md
│   ├── codebase-analyzer.md
│   ├── codebase-pattern-finder.md
│   ├── thoughts-locator.md
│   └── thoughts-analyzer.md
└── skills/            # 1 Agent Skill
    └── thoughts-management/
        ├── SKILL.md
        └── scripts/
            ├── thoughts-init
            └── thoughts-metadata

git/                   # stepwise-git plugin
├── .claude-plugin/
│   └── plugin.json
└── commands/          # 1 slash command
    └── commit.md

web/                   # stepwise-web plugin
├── .claude-plugin/
│   └── plugin.json
└── agents/            # 1 specialized agent
    └── web-search-researcher.md

test/                  # Automated bash tests (for development)
```

## Installation & Testing Workflow

### Installation
```bash
# Install plugins in Claude Code
/plugin marketplace add nikeyes/stepwise-dev
/plugin install stepwise-core@stepwise-dev
/plugin install stepwise-git@stepwise-dev
/plugin install stepwise-web@stepwise-dev
# Restart Claude Code

# That's it! All components are included in the respective plugins
# No additional installation steps required
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
- ✅ `core/skills/thoughts-management/scripts/thoughts-init` - Directory creation, README generation
- ✅ `core/skills/thoughts-management/scripts/thoughts-metadata` - Metadata generation

**Test files:**
- `test/smoke-test.sh` - Main integration tests
- `test/test-helpers.sh` - Assertion functions and utilities
- `Makefile` - Test runner targets

#### 2. Manual Testing (for commands/agents/skills)

Commands, agents, and skills require manual validation in Claude Code:

1. **Test slash commands in Claude Code:**
   - Commands are loaded via the plugins
   - After modifying a command file, restart Claude Code or use `/plugin reload`
   - Test by invoking: `/stepwise-core:research_codebase`, `/stepwise-git:commit`, etc.

2. **Validate agents:**
   - Agents spawn as sub-tasks when commands execute
   - Test by running commands that use them (e.g., `/stepwise-core:research_codebase` spawns `codebase-locator`)
   - Check agent behavior in Claude Code's task output

3. **Test the thoughts-management Skill:**
   - The Skill activates automatically when Claude needs to manage thoughts/
   - Test by creating research documents or plans with stepwise-core
   - Verify Claude calls the Skill to gather metadata

### Iterative Development Cycle

When modifying **commands/agents/skills**:
1. **Edit** the file in `core/commands/`, `core/agents/`, `git/commands/`, `web/agents/`, etc.
2. **Test locally** via plugin development mode or by reinstalling the specific plugin
3. **Validate** in a sample project
4. **Iterate** based on results

When modifying **scripts in the Skill**:
1. **Edit** the file in `core/skills/thoughts-management/scripts/`
2. **Reinstall** stepwise-core plugin or test in development mode
3. **Test** by triggering the Skill (create research docs, plans, etc.)
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

### Thoughts System & Skill
The `thoughts-management` Skill provides directory initialization and metadata generation:
```
thoughts/
├── {username}/        # Personal notes (default: nikey_es)
│   ├── tickets/
│   └── notes/
└── shared/            # Team-shared documents
    ├── research/      # Research documents
    ├── plans/         # Implementation plans
    └── prs/           # PR descriptions
```

Use `grep -r thoughts/` to search across all documents.

### Workflow Philosophy

1. **Context management:** Never exceed 60% context
2. **Phased work:** Research → Plan → Implement → Validate
3. **Clear between phases:** Use `/clear` to reset context
4. **Parallel research:** Commands spawn multiple agents concurrently
5. **Local persistence:** All documents saved to `thoughts/` for future reference

## Configuration

**Username**: Set `export THOUGHTS_USER=your_name` (default: `nikey_es`)

### Version Management

**Plugin versions:**
- Managed by Claude Code plugin system
- Check with `/plugin list`
- Update individual plugins:
  - `/plugin update stepwise-core@stepwise-dev`
  - `/plugin update stepwise-git@stepwise-dev`
  - `/plugin update stepwise-web@stepwise-dev`

**Scripts:**
- Updated automatically when stepwise-core plugin updates
- Part of the stepwise-core plugin package, no separate installation

## Development Workflow

For **scripts**:
1. Edit file in `core/skills/thoughts-management/scripts/`
2. Test using `make test` (runs automated tests)
3. Test manually by triggering the Skill in Claude Code
4. Iterate based on results

For **commands/agents**:
1. Edit file in the specific plugin directory (`core/commands/`, `git/commands/`, `web/agents/`, etc.)
2. Test via plugin reload or development mode
3. Validate in Claude Code
4. Iterate

## Attribution

This project is derived from [HumanLayer](https://github.com/humanlayer/humanlayer) and adapted for local-only operation. All `.claude/` components are modified versions licensed under Apache License 2.0.
