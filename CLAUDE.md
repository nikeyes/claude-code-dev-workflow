# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **workflow tooling project for Claude Code itself**, not a traditional software application. It provides skills, specialized agents, and bash scripts that implement a structured Research → Plan → Implement → Validate development cycle.

The workflow operates entirely locally without cloud dependencies and uses a `thoughts/` directory system for persistent storage.

## Multi-Plugin Architecture

This project is distributed as **4 independent Claude Code plugins** in a single marketplace:

### Plugin 1: stepwise-core
**Location**: `core/`
**Components**:
- 10 skills (research-codebase, create-plan, iterate-plan, implement-plan, validate-plan, thoughts-management, bugmagnet, hamburger-method, small-safe-steps, story-splitting, test-desiderata)
- 5 specialized agents (codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer)

### Plugin 2: stepwise-git
**Location**: `git/`
**Components**:
- 1 skill (commit)

### Plugin 3: stepwise-web
**Location**: `web/`
**Components**:
- 1 specialized agent (web-search-researcher)

### Plugin 4: stepwise-research
**Location**: `research/`
**Components**:
- 1 skill (deep-research)
- 1 skill (research-reports)
- 3 specialized agents (research-lead, research-worker, citation-analyst)

**Installation**:
```bash
# Add marketplace
claude plugin marketplace add git@github.com:nikeyes/stepwise-dev.git

# Install all (or pick individual ones)
claude plugin install stepwise-core@stepwise-dev
claude plugin install stepwise-git@stepwise-dev
claude plugin install stepwise-web@stepwise-dev
claude plugin install stepwise-research@stepwise-dev
```

See README.md for detailed installation instructions.

## Project Structure

```
.claude-plugin/        # Marketplace configuration
└── marketplace.json   # Marketplace listing all 4 plugins

core/                  # stepwise-core plugin
├── .claude-plugin/
│   └── plugin.json
├── agents/            # 5 specialized agents (markdown files)
│   ├── codebase-locator.md
│   ├── codebase-analyzer.md
│   ├── codebase-pattern-finder.md
│   ├── thoughts-locator.md
│   └── thoughts-analyzer.md
└── skills/            # 11 skills (SKILL.md directories)
    ├── create-plan/SKILL.md
    ├── iterate-plan/SKILL.md
    ├── implement-plan/SKILL.md
    ├── validate-plan/SKILL.md
    ├── research-codebase/SKILL.md
    ├── thoughts-management/
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── thoughts-init
    │       └── thoughts-metadata
    ├── bugmagnet/SKILL.md
    ├── hamburger-method/SKILL.md
    ├── small-safe-steps/SKILL.md
    ├── story-splitting/SKILL.md
    └── test-desiderata/SKILL.md

git/                   # stepwise-git plugin
├── .claude-plugin/
│   └── plugin.json
└── skills/            # 1 skill
    └── commit/SKILL.md

web/                   # stepwise-web plugin
├── .claude-plugin/
│   └── plugin.json
└── agents/            # 1 specialized agent
    └── web-search-researcher.md

research/              # stepwise-research plugin
├── .claude-plugin/
│   └── plugin.json
├── agents/            # 3 specialized agents
│   ├── research-lead.md
│   ├── research-worker.md
│   └── citation-analyst.md
└── skills/            # 2 skills
    ├── deep-research/SKILL.md
    └── research-reports/
        ├── SKILL.md
        └── scripts/
            └── generate-report

test/                  # Automated bash tests (for development)
```

## Installation & Testing Workflow

### Installation
```bash
# Add marketplace and install plugins
claude plugin marketplace add git@github.com:nikeyes/stepwise-dev.git
claude plugin install stepwise-core@stepwise-dev
claude plugin install stepwise-git@stepwise-dev
claude plugin install stepwise-web@stepwise-dev
claude plugin install stepwise-research@stepwise-dev
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
- `core/skills/thoughts-management/scripts/thoughts-init` - Directory creation, README generation
- `core/skills/thoughts-management/scripts/thoughts-metadata` - Metadata generation

**Test files:**
- `test/smoke-test.sh` - Main integration tests
- `test/test-helpers.sh` - Assertion functions and utilities
- `Makefile` - Test runner targets

#### 2. Manual Testing (for skills/agents)

Skills and agents require manual validation in Claude Code:

1. **Test skills in Claude Code:**
   - Skills are loaded via the plugins
   - After modifying a skill file, restart Claude Code or use `/reload-plugins`
   - Test by invoking: `/stepwise-core:research-codebase`, `/stepwise-git:commit`, etc.

2. **Validate agents:**
   - Agents spawn as sub-tasks when skills execute
   - Test by running skills that use them (e.g., `/stepwise-core:research-codebase` spawns `codebase-locator`)
   - Check agent behavior in Claude Code's task output

3. **Test the thoughts-management Skill:**
   - The Skill activates automatically when Claude needs to manage thoughts/
   - Test by creating research documents or plans with stepwise-core
   - Verify Claude calls the Skill to gather metadata

### Iterative Development Cycle

When modifying **skills/agents**:
1. **Edit** the file in `core/skills/`, `core/agents/`, `git/skills/`, `web/agents/`, `research/skills/`, etc.
2. **Test locally** via plugin development mode or by reinstalling the specific plugin
3. **Validate** in a sample project
4. **Iterate** based on results

When modifying **scripts in a Skill**:
1. **Edit** the file in the skill's `scripts/` directory
2. **Reinstall** the plugin or test in development mode
3. **Test** by triggering the Skill
4. **Iterate** based on results

## Architecture

### Skill Structure
Skills are directories with a `SKILL.md` entrypoint:
- Frontmatter: `name`, `description`, `model`, `disable-model-invocation`, `allowed-tools`, `argument-hint`
- Instructions for Claude Code on how to behave
- Workflow steps (spawn agents, read files, generate documents)
- Optional supporting files (scripts, templates, references)

### Agent Structure
Agents are specialized markdown files with:
- Frontmatter: `name`, `description`, `tools`, `model`, `color`
- Narrowly-scoped instructions (locate, analyze, or find patterns)
- Called via `Task` tool by skills

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
4. **Parallel research:** Skills spawn multiple agents concurrently
5. **Local persistence:** All documents saved to `thoughts/` for future reference

## Configuration

**Username**: Set `export THOUGHTS_USER=your_name` (default: `nikey_es`)

### Version Management

**Plugin versions:**
- Managed by Claude Code plugin system
- Check with `claude plugin list`
- Update marketplace and individual plugins:
  - `claude plugin marketplace update stepwise-dev`
  - `claude plugin update stepwise-core@stepwise-dev`
  - `claude plugin update stepwise-git@stepwise-dev`
  - `claude plugin update stepwise-web@stepwise-dev`
  - `claude plugin update stepwise-research@stepwise-dev`

**Scripts:**
- Updated automatically when plugin updates
- Part of the plugin package, no separate installation

## Development Workflow

For **scripts**:
1. Edit file in the skill's `scripts/` directory
2. Test using `make test` (runs automated tests)
3. Test manually by triggering the Skill in Claude Code
4. Iterate based on results

For **skills/agents**:
1. Edit file in the specific plugin directory (`core/skills/`, `git/skills/`, `web/agents/`, `research/skills/`, etc.)
2. Test via plugin reload or development mode
3. Validate in Claude Code
4. Iterate

## Attribution

This project is derived from [HumanLayer](https://github.com/humanlayer/humanlayer) and adapted for local-only operation. All `.claude/` components are modified versions licensed under Apache License 2.0.
