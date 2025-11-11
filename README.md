# Claude Code Workflow - Local Setup

[![Plugin Available](https://img.shields.io/badge/Claude_Code-Plugin_Available-blue)](https://github.com/nikey-es/claude-code-dev-workflow)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)](test/)

A complete workflow system for Claude Code inspired by [Ashley Ha's workflow](https://medium.com/@ashleybcha/i-mastered-the-claude-code-workflow-d7ea726b38fd), adapted to work 100% locally without HumanLayer Cloud dependencies.

## 🎯 What This Is

This workflow implements the **Research → Plan → Implement → Validate** cycle with:

- **6 Slash Commands** for structured development
- **5 Specialized Agents** for parallel research
- **4 Bash Scripts** for local thoughts/ management
- **Built-in version tracking** for team synchronization
- **Local-only operation** - no cloud dependencies

### Philosophy

- Never exceed 60% context.  
- Split work into phases. 
- Clear context between each phase. 
- Save everything to a local `thoughts/` directory with hardlinks for efficient searching.

## 📦 What's Included

### Slash Commands

| Command | Description |
|---------|-------------|
| `/research_codebase` | Research and document codebase comprehensively |
| `/create_plan` | Create detailed implementation plans iteratively |
| `/iterate_plan` | Update existing implementation plans |
| `/implement_plan` | Execute plans phase by phase with validation |
| `/validate_plan` | Validate implementation against plan |
| `/commit` | Create git commits (no Claude attribution) |

### Specialized Agents

| Agent | Purpose |
|-------|---------|
| `codebase-locator` | Find WHERE code lives in the codebase |
| `codebase-analyzer` | Understand HOW code works |
| `codebase-pattern-finder` | Find similar patterns to model after |
| `thoughts-locator` | Discover documents in thoughts/ |
| `thoughts-analyzer` | Extract insights from thoughts docs |

### Thoughts Scripts (`~/.local/bin/`)

| Script | Purpose |
|--------|---------|
| `thoughts-init` | Initialize thoughts/ structure in a project |
| `thoughts-sync` | Sync hardlinks in searchable/ directory |
| `thoughts-metadata` | Generate git metadata for documents |

## 🚀 Installation

### Step 1: Install Plugin

```bash
# Add marketplace from GitHub
/plugin marketplace add nikey-es/claude-code-dev-workflow

# Install plugin
/plugin install stepwise-dev@stepwise-dev-marketplace
```

Restart Claude Code after installation.

### Step 2: Install Helper Scripts

The plugin installs commands and agents automatically. You also need to install helper scripts to your PATH:

```bash
git clone https://github.com/nikey-es/claude-code-dev-workflow.git
cd claude-code-dev-workflow
./install-scripts.sh
```

**Why two steps?** Plugin installs commands/agents automatically. Scripts need manual install to your PATH.

### Verify Installation

```bash
# Check scripts are in PATH
which thoughts-init thoughts-sync thoughts-metadata
```

If not found, add to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 📁 Directory Structure

After running `thoughts-init` in a project:

```
<your-project>/
├── thoughts/
│   ├── nikey_es/          # Your personal notes (you write)
│   │   ├── tickets/       # Ticket documentation
│   │   └── notes/         # Personal notes
│   ├── shared/            # Team-shared documents (Claude writes)
│   │   ├── research/      # Research documents
│   │   ├── plans/         # Implementation plans
│   │   └── prs/           # PR descriptions
│   └── searchable/        # Hardlinks for grep (auto-generated)
│       ├── nikey_es/      # -> hardlinks to nikey_es/
│       └── shared/        # -> hardlinks to shared/
├── .gitignore            # (add thoughts/searchable/ to this)
└── ...
```

**Key distinction:**
- **`nikey_es/`**: Personal tickets/notes you create manually
- **`shared/`**: Formal docs Claude generates from commands
- **Example**: `/create_plan thoughts/nikey_es/tickets/eng_1234.md` reads your ticket → writes `shared/plans/2025-11-09-ENG-1234-*.md`

### Why Hardlinks?

- **Fast searching**: Grep one directory instead of many
- **No duplication**: Same file, same inode, no extra disk space
- **Auto-sync**: Changes in source are immediately visible
- **Efficient**: Better than symlinks for grep operations

## Thoughts Directory

This directory contains research documents, implementation plans, and notes for this project.

### Structure

- `nikey_es/` - Personal notes and tickets
  - `tickets/` - Ticket documentation and tracking
  - `notes/` - Personal notes and observations
- `shared/` - Team-shared documents
  - `research/` - Research documents from /research_codebase
  - `plans/` - Implementation plans from /create_plan
  - `prs/` - PR descriptions and documentation
- `searchable/` - Hardlinks for efficient grep searching (auto-generated)

### Usage

Use Claude Code slash commands:
- `/research_codebase [topic]` - Research and document codebase
- `/create_plan [description]` - Create implementation plan
- `/implement_plan [plan-file]` - Execute a plan
- `/validate_plan [plan-file]` - Validate implementation

Run `thoughts-sync` after adding/modifying files to update searchable/ hardlinks.


## 🔄 The Four-Phase Workflow

### Phase 1: Research

**Goal**: Understand what exists before changing anything.

```bash
# In Claude Code
/research_codebase How does authentication work in this app?
```

This will:
1. Spawn parallel agents to search the codebase
2. Search thoughts/ for historical context
3. Generate a comprehensive research document
4. Save to `thoughts/shared/research/YYYY-MM-DD-topic.md`
5. Run `thoughts-sync` to update searchable/

**Output**: Research document with code references, architecture insights, and file:line numbers.

### Phase 2: Plan

**Goal**: Create a detailed, iterative implementation plan.

```bash
# In Claude Code
/create_plan Add rate limiting to the API
# Or reference a research doc:
/create_plan @thoughts/shared/research/2025-11-09-auth-system.md
```

This will:
1. Ask clarifying questions
2. Research existing patterns in the codebase
3. Iterate with you 5+ times on the plan
4. Create phases with specific changes
5. Define automated AND manual success criteria
6. Save to `thoughts/shared/plans/YYYY-MM-DD-topic.md`

**Output**: Detailed plan with phases, file paths, code snippets, and verification steps.

### Phase 3: Implement

**Goal**: Execute one phase at a time with confidence.

```bash
# In Claude Code
/implement_plan @thoughts/shared/plans/2025-11-09-rate-limiting.md
```

This will:
1. Read the complete plan
2. Implement Phase 1
3. Run automated verification (tests, linting)
4. **Pause for manual verification**
5. Wait for your confirmation
6. Proceed to Phase 2 (or stop)

**Key Rule**: One phase at a time. Validate before proceeding.

### Phase 4: Validate

**Goal**: Systematically verify the entire implementation.

```bash
# In Claude Code
/validate_plan @thoughts/shared/plans/2025-11-09-rate-limiting.md
```

This will:
1. Check all phases are complete
2. Run all automated verification
3. Review code against plan
4. Identify deviations or issues
5. Generate validation report

**Output**: Report showing what passed, what needs fixing, and manual test checklist.

## 💡 Usage Examples

### Example 1: Feature Development

```bash
# 1. Research
/research_codebase Where is user registration handled?
# → Saves to thoughts/shared/research/2025-11-09-user-registration.md
# → /context shows 45%
# → /clear

# 2. Plan
/create_plan Add OAuth login support
# → Iterates 5 times
# → Saves to thoughts/shared/plans/2025-11-09-oauth-login.md
# → /context shows 58%
# → /clear

# 3. Implement (Phase 1 only)
/implement_plan @thoughts/shared/plans/2025-11-09-oauth-login.md
# → Completes Phase 1
# → Runs tests
# → Pauses for manual testing
# → You verify it works
# → "Continue to Phase 2"
# → /context shows 62%
# → /clear

# 4. Validate
/validate_plan @thoughts/shared/plans/2025-11-09-oauth-login.md
# → Comprehensive verification
# → /context shows 41%

# 5. Commit
/commit
# → Creates atomic commits
```

### Example 2: Bug Investigation

```bash
# Research the bug
/research_codebase Why are webhooks timing out after 30 seconds?

# Create a fix plan
/create_plan Fix webhook timeout issue based on @thoughts/shared/research/...md

# Implement the fix
/implement_plan @thoughts/shared/plans/...md

# Commit
/commit
```

### Example 3: Iterating on a Plan

```bash
# You've created a plan but need to adjust it
/iterate_plan @thoughts/shared/plans/2025-11-09-feature.md

# Claude asks: What changes would you like to make?
# You: "Add error handling phase before deployment"

# Claude updates the plan in place
```

## 🛠️ Thoughts Scripts

### thoughts-init

Initialize thoughts/ in current project:

```bash
cd ~/projects/my-app
thoughts-init
```

Creates structure, README, .gitignore, and runs initial sync.

### thoughts-sync

Sync hardlinks in searchable/:

```bash
thoughts-sync
```

Run this:
- After adding new .md files
- After modifying file structure
- If searchable/ seems out of sync

The scripts automatically run this after `/research_codebase` and `/create_plan`.

### thoughts-metadata

Generate metadata for the current repo:

```bash
thoughts-metadata
```

Returns:
```
Current Date/Time (TZ): 2025-11-09 15:30:00 PST
ISO DateTime: 2025-11-09T23:30:00+0000
Date Short: 2025-11-09
Current Git Commit Hash: abc123...
Current Branch Name: main
Repository Name: my-app
Git User: nikey_es
```

Used internally by commands to populate frontmatter.

## 🏷️ Version Management

### Checking Plugin Version

```bash
# List installed plugins
/plugin list

# Show detailed plugin info
/plugin show stepwise-dev@stepwise-dev-marketplace
```

### Updating

```bash
# Update plugin
/plugin update stepwise-dev@stepwise-dev-marketplace

# Update scripts
cd /path/to/claude-code-dev-workflow
git pull
./install-scripts.sh
```

## 📝 Context Management

**Golden Rule**: Never exceed 60% context capacity.

Check context frequently:
```bash
/context
```

Clear between phases:
```bash
/clear
```

### The 60% Rule

| Phase | Typical Context | Action |
|-------|----------------|--------|
| Research | 50-70% | Clear after |
| Plan | 50-65% | Clear after |
| Implement | 60-75% | Clear between phases |
| Validate | 40-50% | Usually safe to continue |

## 🎓 Best Practices

1. **Always Research First** - Even if you "know" the code, patterns and edge cases emerge
2. **Iterate Plans 5+ Times** - First draft is never complete
3. **One Phase at a Time** - Don't skip phases; bugs cascade
4. **Separate Automated vs Manual** - Split verification criteria clearly
5. **Sync Regularly** - Run `thoughts-sync` to make docs searchable

## 🔧 Customization

**Change Username**: Set `export THOUGHTS_USER=your_name` or edit `bin/thoughts-init:8`

**Add Commands**: Create `.md` files in `~/.claude/commands/` with frontmatter. Claude auto-detects on restart.

## 🧪 Testing

```bash
make test    # Run smoke tests
make check   # Run shellcheck on all bash scripts
```

Tests validate all bash scripts (thoughts-init, thoughts-sync, thoughts-metadata, install.sh). No dependencies needed, runs in isolated temp directories.

## 🐛 Troubleshooting

### Plugin Issues

**Commands not showing after installation**:
- Restart Claude Code completely
- Check plugin is enabled: `/plugin list`
- Try reinstalling: `/plugin uninstall stepwise-dev@stepwise-dev-marketplace` then `/plugin install stepwise-dev@stepwise-dev-marketplace`

**Scripts not found in PATH**:
- Check installation: `which thoughts-init`
- Add to shell config: `export PATH="$HOME/.local/bin:$PATH"`
- Source your shell config: `source ~/.zshrc` (or `~/.bashrc`)
- Run `./install-scripts.sh` again if needed

**Plugin installation fails**:
- Verify marketplace added: `/plugin marketplace list`
- Check network connection (for GitHub marketplaces)
- Try local marketplace for testing: `/plugin marketplace add ./test-marketplace`

### Workflow Issues

**Hardlinks failing**: Script auto-falls back to symlinks (slower but works)

**No files synced**: Run `THOUGHTS_DEBUG=1 thoughts-sync` to debug

**Plugin version mismatch**: Update plugin with `/plugin update stepwise-dev@stepwise-dev-marketplace`, update scripts with `cd /path/to/repo && git pull && ./install-scripts.sh`

## 📚 Learn More

- **Original Article**: [I mastered the Claude Code workflow](https://medium.com/@ashleybcha/i-mastered-the-claude-code-workflow-d7ea726b38fd) by Ashley Ha
- **HumanLayer**: Original inspiration from [HumanLayer's .claude directory](https://github.com/humanlayer/humanlayer)

## 🤝 Contributing

This is extracted from HumanLayer and adapted for local use. If you have improvements:

1. Test them in your workflow
2. Document what changed and why
3. Share with the community

## 📄 License

Apache License 2.0 - See LICENSE file for details.

## 🔖 Attribution

This project contains code derived from [HumanLayer](https://github.com/humanlayer/humanlayer)
Copyright (c) 2024, humanlayer Authors
Licensed under the Apache License, Version 2.0

All slash commands and specialized agents are modified versions of the original HumanLayer implementations, adapted for local-only operation without cloud dependencies.

## 🙏 Credits

- **Ashley Ha** - For documenting and popularizing this workflow
- **HumanLayer Team** (Dex Horthy et al.) - For creating the original commands and agents
- **Anthropic** - For Claude Code

---

**Happy Coding! 🚀**

Questions? Issues? Check the planning doc or open a discussion.
