# Stepwise Dev - Multi-Plugin Suite

[![Plugin Available](https://img.shields.io/badge/Claude_Code-Plugin_Available-blue)](https://github.com/nikeyes/stepwise-dev)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)](test/)

A modular development workflow suite for Claude Code inspired by [Ashley Ha's workflow](https://medium.com/@ashleyha/i-mastered-the-claude-code-workflow-145d25e502cf), adapted to work 100% locally with thoughts.

**📖 Read more**: [Tu CLAUDE.md no funciona sin Context Engineering](https://nikeyes.github.io/tu-claude-md-no-funciona-sin-context-engineering-es/) (Spanish article about Stepwise-dev)

## 🎯 What This Is

Solves the context management problem: LLMs lose attention after 60% context usage.

Implements **Research → Plan → Implement → Validate** with frequent `/clear` and persistent `thoughts/` storage.

### Philosophy

- Keep context < 60% (attention threshold)
- Split work into phases
- Clear between phases, save to `thoughts/`
- Never lose research or decisions

## 📦 Available Plugins

This repository contains **4 independent plugins** that can be installed separately based on your needs:

### 1. **stepwise-core** (Core Workflow)
The foundation plugin with the complete Research → Plan → Implement → Validate cycle.

**Includes:**
- 11 skills (`research-codebase`, `create-plan`, `iterate-plan`, `implement-plan`, `validate-plan`, `thoughts-management`, `bugmagnet`, `hamburger-method`, `small-safe-steps`, `story-splitting`, `test-desiderata`)
- 5 specialized agents (codebase exploration and thoughts management)

[→ Read more](./core/README.md)

### 2. **stepwise-git** (Git Operations)
Clean git commit workflow without Claude attribution.

**Includes:**
- 1 skill (`commit`)
- Smart staging and commit message generation

[→ Read more](./git/README.md)

### 3. **stepwise-web** (Web Research)
Web search and research capabilities for external context.

**Includes:**
- 1 specialized agent (`web-search-researcher`)
- Deep web research with source citations

[→ Read more](./web/README.md)

### 4. **stepwise-research** (Multi-Agent Deep Research)
Advanced multi-agent research system with parallel web searches and synthesis.

**Includes:**
- 1 skill (`deep-research`, includes `generate-report` script for structured reports)
- 3 specialized agents (research-lead, research-worker, citation-analyst)
- Comprehensive research reports with citations and metadata

[→ Read more](./research/README.md)

## 🚀 Installation

### Option 1: Install All Plugins (Recommended for first-time users)

```bash
claude plugin marketplace add https://github.com/nikeyes/stepwise-dev.git

# Install all plugins
claude plugin install stepwise-core@stepwise-dev
claude plugin install stepwise-git@stepwise-dev
claude plugin install stepwise-web@stepwise-dev
claude plugin install stepwise-research@stepwise-dev
```

### Option 2: Install Only What You Need

```bash
# Add marketplace (SSH or HTTPS)
claude plugin marketplace add https://github.com/nikeyes/stepwise-dev.git

# Install only the core workflow
claude plugin install stepwise-core@stepwise-dev

# Optionally add git operations
claude plugin install stepwise-git@stepwise-dev

# Optionally add web research
claude plugin install stepwise-web@stepwise-dev

# Optionally add multi-agent deep research
claude plugin install stepwise-research@stepwise-dev
```

**Restart Claude Code after installation.**

### Local Development (Testing Without Installing)

Use `--bare` with `--plugin-dir` to load only your local plugin directories, skipping all installed/marketplace plugins:

```bash
claude --bare \
    --plugin-dir /path/to/stepwise-dev/core \
    --plugin-dir /path/to/stepwise-dev/git \
    --plugin-dir /path/to/stepwise-dev/web \
    --plugin-dir /path/to/stepwise-dev/research
```

`--bare` disables plugin sync (so installed plugins are ignored) but still loads the directories you pass via `--plugin-dir`. This means your local changes are tested in isolation without needing to reinstall anything.

## 🧪 Try It Out

Don't have a project to test with? Use [stepwise-todo-api-test](https://github.com/nikeyes/stepwise-todo-api-test) — a sample repository designed for testing these plugins.

## 📁 Directory Structure

After running `thoughts-init` (from stepwise-core) in a project:

```
<your-project>/
├── thoughts/
│   ├── nikey_es/          # Your personal notes (you write)
│   │   ├── tickets/       # Ticket documentation
│   │   └── notes/         # Personal notes
│   └── shared/            # Team-shared documents (Claude writes)
│       ├── research/      # Research documents
│       ├── plans/         # Implementation plans
│       └── prs/           # PR descriptions
└── ...
```

**Key distinction:**
- **`nikey_es/`**: Personal tickets/notes you create manually
- **`shared/`**: Formal docs Claude generates from commands

Use `grep -r thoughts/` to search across all documents.

## 🔄 The Four-Phase Workflow

### Phase 1: Research (stepwise-core)

```bash
/stepwise-core:research-codebase How does authentication work?
```

Spawns parallel agents, searches codebase and thoughts/, generates comprehensive research document.

### Phase 2: Plan (stepwise-core)

```bash
/stepwise-core:create-plan Add rate limiting to the API
```

Iterates with you 5+ times, creates detailed phases with verification steps.

### Phase 3: Implement (stepwise-core)

```bash
/stepwise-core:implement-plan @thoughts/shared/plans/2025-11-09-rate-limiting.md
```

Executes one phase at a time, validates before proceeding.

### Phase 4: Validate (stepwise-core)

```bash
/stepwise-core:validate-plan @thoughts/shared/plans/2025-11-09-rate-limiting.md
```

Systematically verifies the entire implementation.

### Commit (stepwise-git)

```bash
/stepwise-git:commit
```

Creates clean commits without Claude attribution.

## 💡 Usage Examples

### Example 1: Complete Feature Development

```bash
# Research (core)
/stepwise-core:research-codebase Where is user registration handled?
# /clear

# Plan (core)
/stepwise-core:create-plan Add OAuth login support
# /clear

# Implement (core)
/stepwise-core:implement-plan @thoughts/shared/plans/...md
# /clear

# Validate (core)
/stepwise-core:validate-plan @thoughts/shared/plans/...md

# Commit (git)
/stepwise-git:commit
```

### Example 2: Using Web Research

```bash
# Research external best practices (web)
"What are the best practices for implementing rate limiting in REST APIs?"
# The web-search-researcher agent will be invoked automatically

# Research your codebase (core)
/stepwise-core:research-codebase Where do we handle API rate limiting?

# Continue with plan and implementation...
```

## 🏷️ Version Management

```bash
# Check versions
claude plugin list

# Update marketplace and all plugins
claude plugin marketplace update stepwise-dev

claude plugin update stepwise-core@stepwise-dev
claude plugin update stepwise-git@stepwise-dev
claude plugin update stepwise-web@stepwise-dev
claude plugin update stepwise-research@stepwise-dev
```

## 📝 Context Management

**Golden Rule**: Never exceed 60% context capacity.

```bash
/context  # Check current usage
/clear    # Clear between phases
```

## 🔧 Customization

**Change Username**: Set `export THOUGHTS_USER=your_name` or edit the thoughts-init script.

## 🧪 Testing

```bash
make test          # Run all automated tests
make test-verbose  # Run tests with debug output
make check         # Run shellcheck on bash scripts
make ci            # Run full CI validation
```

### Skill Evaluation

Skills have benchmarks in `<skill-name>-workspace/` directories. Each contains test fixtures, grading results, and timing data for with-skill vs. baseline comparison.

To re-run an evaluation (e.g., against a different model):

```bash
/skill-creator:skill-creator Re-run evals from <skill-name>-workspace/evals/evals.json
```

## 🐛 Troubleshooting

### Plugin Issues

**Commands not showing**:
- Restart Claude Code
- Check plugins enabled: `/plugin list`
- Reinstall if needed

**Plugin installation fails**:
- Verify marketplace: `/plugin marketplace list`
- Check network connection

### Workflow Issues

## 📚 Learn More

- **Original Article**: [I mastered the Claude Code workflow](https://medium.com/@ashleyha/i-mastered-the-claude-code-workflow-145d25e502cf) by Ashley Ha
- **HumanLayer**: Original inspiration from [HumanLayer's .claude directory](https://github.com/humanlayer/humanlayer)

## 🤝 Contributing

Test improvements in your workflow, document changes, and share with the community.

## 📄 License

Apache License 2.0 - See LICENSE file for details.

## 🔖 Attribution

Derived from [HumanLayer's Claude Code workflow](https://github.com/humanlayer/humanlayer/tree/main/.claude) under Apache License 2.0.

See [NOTICE](NOTICE) for detailed attribution.

**Major enhancements**:
- Multi-plugin architecture for modular installation
- Specialized agent system
- Local-only thoughts/ management with Agent Skill
- Automated testing infrastructure
- Enhanced TDD-focused success criteria

## 🙏 Credits

- **[Ashley Ha](https://medium.com/@ashleyha)** - Workflow documentation
- **HumanLayer Team** ([Dex Horthy](https://x.com/dexhorthy) et al.) - Original commands and agents
- **Anthropic** - [Claude Code](https://claude.com/product/claude-code)

---

**Happy Coding! 🚀**

Questions? [Open an issue](https://github.com/nikeyes/stepwise-dev/issues) on GitHub.
