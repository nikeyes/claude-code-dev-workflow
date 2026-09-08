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

### Why This Workflow With AI

**More generated code = more risk if you don't have a solid feedback loop.**

The faster AI generates code, the more these practices matter:

- **Story Splitting** — AI can produce a lot in little time. If scope isn't cut, chaos scales just as fast.
- **Hamburger Method** — Deliver value end-to-end continuously by slicing features into thin vertical layers.
- **Small Safe Steps** — Each step must be reversible. Speed of generation is not speed to production.
- **Advanced testing** — Mutation, acceptance, and architectural testing. The feedback loop must be solid. No more excuses.

## 📦 Available Plugins

This repository contains **5 independent plugins** that can be installed separately based on your needs:

### 1. **stepwise-core** (Core Workflow)
The foundation plugin with the complete Research → Plan → Implement → Validate cycle.

**Includes:**
- 13 skills (`research-codebase`, `create-plan`, `iterate-plan`, `implement-plan`, `validate-plan`, `thoughts-management`, `bugmagnet`, `hamburger-method`, `small-safe-steps`, `story-splitting`, `test-desiderata`, `tdd`, `grill-me`)
- 5 specialized agents (codebase exploration and thoughts management)

[→ Read more](./core/README.md)

### 2. **stepwise-git** (Git & GitHub Operations)
Clean git commit workflow without Claude attribution, plus rigorous PR comment review.

**Includes:**
- 2 skills (`commit`, `review-pr-comments`)
- Smart staging and commit message generation
- PR comment negotiation with individual inline replies

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

### 5. **stepwise-slides** (HTML Slide Decks)
Generate beautiful HTML presentations from a coding agent. **Vendored** from [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) (MIT, author Zara Zhang).

**Includes:**
- 1 skill (`frontend-slides`) with a large template pack

## 🚀 Installation

### Option 1: Install All Plugins (Recommended for first-time users)

```bash
claude plugin marketplace add https://github.com/nikeyes/stepwise-dev.git

# Install all plugins
claude plugin install stepwise-core@stepwise-dev
claude plugin install stepwise-git@stepwise-dev
claude plugin install stepwise-web@stepwise-dev
claude plugin install stepwise-research@stepwise-dev
claude plugin install stepwise-slides@stepwise-dev
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

# Optionally add HTML slide generation (vendored)
claude plugin install stepwise-slides@stepwise-dev
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

## 🤖 Using It with Codex

The same skills also run under OpenAI Codex.

- **From a clone of this repo:**
  ```bash
  make install-codex
  ```
- **Already installed via the Claude Code marketplace?** The full repo (including `Makefile` and `codex/`) lives in `~/.claude/plugins/marketplaces/stepwise-dev/`, so:
  ```bash
  cd ~/.claude/plugins/marketplaces/stepwise-dev && make install-codex
  ```

This installs:

- **17 skills** symlinked into `~/.agents/skills/` (13 from core, 2 from git, 1 from research, 1 from vendored slides) — Codex follows symlinks when scanning that directory, so edits in the repo take effect immediately
- **9 agents** copied into `~/.codex/agents/` as TOML, generated from the agent markdown by `codex/transpile-agents.sh`

Regenerate the agents after editing any `*/agents/*.md` with `make transpile-codex`; `make check-codex` fails if they're out of sync.

### Known limitations under Codex

- `research-codebase`, `create-plan` and `iterate-plan` use `$ARGUMENTS`, which Codex does not expand. You'll see the literal string — pass your input in the message itself instead.
- Codex only delegates to subagents on an explicit instruction, so the skills spell out the parallel spawns. If a skill investigates in its main context instead of spawning agents, say so explicitly in your prompt.
- Skills that are user-invoked only carry an `agents/openai.yaml` opting out of implicit invocation. This is documented for the ChatGPT desktop app; whether the Codex CLI honors it is unverified.

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

**Use `/clear` between phases.** Knowledge lives in `thoughts/`, not in the context window.

### Quick reference

| Phase | Main command | Helpers (skills / agents) |
|---|---|---|
| Across all phases | `/clear` between phases | `thoughts-management`, `thoughts-locator`, `thoughts-analyzer` |
| **Before** (product side) | `/story-splitting` | Applied to the PRD / ticket / use case — **not** the code |
| 🔍 Research | `/research-codebase`, `/deep-research` | `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, `web-search-researcher`, `citation-analyst` |
| 🗺️ Plan | `/create-plan`, `/iterate-plan` | `/hamburger-method`, `/small-safe-steps`, `/grill-me` (stress-test the plan) |
| 🛠️ Implement | `/implement-plan`, `/commit` | `/tdd` (test-first development), `/test-desiderata` (test quality), `/bugmagnet <file>` (edge-case & bug hunt) |
| ✅ Validate | `/validate-plan` | — |
| 🌐 Any web lookup | _"search the web for..."_ | `web-search-researcher` fires automatically |

### Phase 1: Research (stepwise-core)

```bash
/stepwise-core:research-codebase How does authentication work?
```

Spawns parallel agents, searches codebase and thoughts/, generates comprehensive research document.

### Phase 2: Plan (stepwise-core)

```bash
/stepwise-core:create-plan Add rate limiting to the API
```

Iterates with you 5+ times, creates detailed phases with verification steps. Use `/grill-me` to stress-test the plan before moving on — it interviews you on every assumption until the design is solid.

### Phase 3: Implement (stepwise-core)

```bash
/stepwise-core:implement-plan @thoughts/shared/plans/2025-11-09-rate-limiting.md
```

Executes one phase at a time, validates before proceeding. Use `/tdd` to drive the implementation test-first (red→green→refactor). While implementing, lean on `/test-desiderata` to keep test quality high and `/bugmagnet <file>` to surface edge cases on a specific module.

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
claude plugin update stepwise-slides@stepwise-dev
```

## 📝 Golden Rules

1. **Keep context under 60%** — past that, accuracy drops.
2. **`/clear` between phases** — knowledge lives in `thoughts/`, not in the context window.
3. **Read a 200-line plan before Claude writes 2,000 lines of code.**
4. **Implement one phase at a time** — with its own tests and its own commit.
5. **Delegate noisy work** (web research, large codebase scans) to **sub-agents** so the parent context stays clean.

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

Each skill has an eval suite in its `<skill-name>-workspace/evals/` directory:

```
core/skills/bugmagnet-workspace/evals/
├── evals.json              # Eval definitions (prompts, assertions, grading guide)
├── files/                  # Test fixtures (source files the skill analyzes)
├── iteration-1/            # Benchmark run results
│   ├── benchmark.json      # Machine-readable: per-eval pass rates, timing, tokens
│   ├── benchmark.md        # Human-readable summary table
│   └── eval-1-name/        # Per-eval evidence
│       └── eval_metadata.json
├── iteration-2/
└── ...
```

**Running evals:**

```bash
/skill-creator:skill-creator Run evals from <skill-name>-workspace/evals/evals.json
```

This runs each eval with-skill and without-skill, grades assertions, and writes results to a new `iteration-N/` directory.

**Reading benchmark results:**

Open `iteration-N/benchmark.md` for a quick summary table, or `benchmark.json` for detailed per-assertion evidence. Key metrics:

- **pass_rate**: percentage of assertions passed (with_skill vs without_skill)
- **delta**: the skill's added value over baseline — higher is better
- **time_seconds / tokens**: cost of using the skill

Compare across iterations to track skill improvements over time.

**Viewing detailed eval reports:**

```bash
make eval-list                                # List skills with eval iterations
make eval-view SKILL=test-desiderata          # View latest iteration
make eval-view SKILL=test-desiderata ITER=1   # View specific iteration
make eval-view SKILL=test-desiderata PREV=1   # Compare latest vs iteration-1
```

The viewer opens two tabs: **Outputs** (per-eval outputs, grading, and feedback) and **Benchmark** (aggregate pass rates, delta, timing, and token usage).

## 📚 Learn More

- **Original Article**: [I mastered the Claude Code workflow](https://medium.com/@ashleyha/i-mastered-the-claude-code-workflow-145d25e502cf) by Ashley Ha
- **HumanLayer**: Original inspiration from [HumanLayer's .claude directory](https://github.com/humanlayer/humanlayer)

## 🤝 Contributing

Test improvements in your workflow, document changes, and share with the community.

## 📄 License

Apache License 2.0 - See LICENSE file for details.

## 🔖 Attribution

Derived from [HumanLayer's Claude Code workflow](https://github.com/humanlayer/humanlayer/tree/main/.claude) under Apache License 2.0.

`stepwise-slides` is vendored verbatim from [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) (MIT, author Zara Zhang) under the `slides/` prefix, imported via `git subtree`. Do **not** edit files under `slides/` — every future sync must apply cleanly. To pull upstream changes:

```bash
git subtree pull \
  --prefix=slides \
  https://github.com/zarazhangrui/frontend-slides.git \
  main --squash
```

If the pull brings meaningful changes, patch-bump `stepwise-slides` in `.claude-plugin/marketplace.json` and the top-level marketplace `version` per `.claude/rules/versioning.md`. See `AGENTS.md` for full guidance.

Several skills are derived from [Matt Pocock's skills](https://github.com/mattpocock/skills) (grill-me, tdd), [eferro's skill-factory](https://github.com/eferro/skill-factory) (hamburger-method, small-safe-steps, story-splitting, test-desiderata, and tdd/zombies reference) and [Gojko Adzic's BugMagnet](https://github.com/gojko/bugmagnet-ai-assistant). See [NOTICE](NOTICE) for detailed attribution.

**Major enhancements**:
- Multi-plugin architecture for modular installation
- Specialized agent system
- Local-only thoughts/ management with Agent Skill
- Automated testing infrastructure
- Enhanced TDD-focused success criteria

---

**Happy Coding! 🚀**

Questions? [Open an issue](https://github.com/nikeyes/stepwise-dev/issues) on GitHub.
