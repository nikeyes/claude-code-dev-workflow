---
date: 2026-04-26T00:00:00+0000
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "Investiga los tests"
tags: [research, testing, bash-tests, evals, smoke-tests, plugin-validation, test-helpers]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Investiga los tests

**Date**: 2026-04-26T00:00:00+0000
**Researcher**: Jorge Castro
**Git Commit**: a1cdcbb
**Branch**: main
**Repository**: stepwise-dev

## Research Question

"Investiga los tests" — Investigate the tests in this project.

## Summary

This project has two distinct testing layers: (1) automated bash-based tests for scripts and plugin structure, and (2) a skill evaluation (eval) framework that benchmarks skill quality across iterations. The automated tests live in `test/` and are orchestrated by `Makefile`. The eval framework lives inside each skill's `*-workspace/` directory and uses JSON-defined eval scenarios with assertion sets, executed against a given iteration of the skill.

**Key test components:**
- `test/test-helpers.sh` — shared assertion library (9 functions, colored output)
- `test/thoughts-structure-test.sh` — functional tests for `thoughts-init` and `thoughts-metadata` scripts
- `test/plugin-structure-test.sh` — structural tests for the 4-plugin marketplace layout
- `test/E2E_CHECKLIST.md` — manual testing checklist for Claude Code runtime behavior
- `Makefile` — orchestrates `make test`, `make check`, `make ci` targets
- `core/skills/*-workspace/evals/evals.json` — per-skill eval scenarios with assertions
- `core/skills/*-workspace/iteration-N/` — benchmark results and outputs per skill per iteration

---

## Detailed Findings

### 1. Automated Bash Test Suite (`test/`)

#### Test Helper Library
**Location**: `test/test-helpers.sh`

Provides 9 reusable assertion functions, all tracking shared counters (`TESTS_RUN`, `TESTS_PASSED`, `TESTS_FAILED`) and printing colored output:

| Function | What it tests |
|---|---|
| `assert_file_exists PATH desc` | `[ -f "$file" ]` |
| `assert_dir_exists PATH desc` | `[ -d "$dir" ]` |
| `assert_executable PATH desc` | `[ -x "$file" ]` |
| `assert_contains FILE PATTERN desc` | `grep -q "$pattern" "$file"` |
| `assert_file_not_exists PATH desc` | `[ ! -e "$file" ]` |
| `assert_output_contains OUTPUT PATTERN desc` | `echo "$output" \| grep -q "$pattern"` |
| `assert_not_empty VALUE desc` | `[ -n "$value" ]` |
| `setup_git_repo DIR` | Utility: `git init` + test user config |
| `print_summary` | Prints total / passed / failed counts |

Colors: `GREEN` for pass, `RED` for fail, `YELLOW` for section headers.

#### Functional Tests (thoughts scripts)
**Location**: `test/thoughts-structure-test.sh`

Tests the bash scripts inside the `thoughts-management` Skill. Creates an isolated temporary directory (`mktemp -d`) with `trap 'rm -rf "$TEST_DIR"' EXIT` for cleanup. Adds Skill scripts to `PATH` before running.

**Test 1** — `thoughts-init` creates directory structure:
- Verifies 5 directories: `thoughts/nikey_es/tickets`, `thoughts/nikey_es/notes`, `thoughts/shared/research`, `thoughts/shared/plans`, `thoughts/shared/prs`
- Verifies `thoughts/README.md` exists

**Test 2** — `thoughts-metadata` generates valid metadata:
- Checks output contains: "Current Date/Time", "ISO DateTime", "Git User", "Git Email", "Current Git Commit Hash", "Current Branch Name", "Timestamp For Filename"
- Validates ISO 8601 date format via regex: `[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}`

#### Structural Tests (plugin architecture)
**Location**: `test/plugin-structure-test.sh`

Validates the multi-plugin marketplace structure. Groups of assertions for each of the 4 plugins.

**Test 1** — Marketplace manifest: checks `.claude-plugin/marketplace.json` is valid JSON (`jq empty`), has `name`, `owner.name`, and at least 3 plugins listed.

**Test 2** — `stepwise-core` plugin: checks `core/.claude-plugin/plugin.json`, `core/README.md`, all 5 workflow skill files, all 5 agent files, Skill directory and scripts.

**Test 3** — `stepwise-git` plugin: checks `git/.claude-plugin/plugin.json`, `git/README.md`, `git/skills/commit/SKILL.md`.

**Test 4** — `stepwise-web` plugin: checks `web/.claude-plugin/plugin.json`, `web/README.md`, `web/agents/web-search-researcher.md`.

**Test 5** — Root documentation: checks `README.md`, `CLAUDE.md`, `.gitignore`, and README content references "stepwise-dev".

#### Manual E2E Checklist
**Location**: `test/E2E_CHECKLIST.md`

Covers tests that cannot be automated because they require the Claude Code runtime:
- Plugin installation/uninstallation/re-enabling
- Slash command execution quality (`/stepwise-core:research-codebase`, `/stepwise-core:create-plan`)
- Agent spawning and parallel execution
- LLM response quality and context management

#### Makefile Orchestration
**Location**: `Makefile`

Four targets:
- `make test` — runs functional + structural tests sequentially
- `make test-verbose` — same with `bash -x` debug output
- `make check` — runs `shellcheck` on `core/skills/thoughts-management/scripts/*` and `test/*.sh` (graceful skip if not installed)
- `make ci` — `test` + `check` + JSON manifest validation via `jq`

---

### 2. Skill Evaluation (Eval) Framework

Each skill that has been benchmarked has a `*-workspace/` directory alongside its `SKILL.md`:

```
core/skills/
├── research-codebase/SKILL.md
├── research-codebase-workspace/
│   ├── evals/
│   │   └── evals.json           ← eval definitions with assertions
│   ├── iteration-1/
│   │   ├── benchmark.json        ← iteration results summary
│   │   └── {eval-name}/
│   │       ├── eval_metadata.json
│   │       ├── with_skill/
│   │       │   ├── outputs/      ← skill output artifacts
│   │       │   ├── grading.json
│   │       │   └── timing.json
│   │       └── without_skill/    ← baseline (no skill)
│   └── iteration-2/
│       └── ...
```

Skills with workspace/eval directories:
- `research-codebase-workspace/` — 7 evals, 2 iterations
- `create-plan-workspace/` — 7 evals, 2 iterations
- `implement-plan-workspace/` — 7 evals, 3 iterations
- `validate-plan-workspace/` — 7 evals, 2 iterations (+ adversarial evals in `evals/projects/`)
- `iterate-plan-workspace/` — multiple evals, 1 iteration
- `bugmagnet-workspace/` — 3 evals, 1 iteration

#### Eval Definition Format (`evals/evals.json`)

Each eval entry contains:
- `id` — numeric eval identifier
- `prompt` — the exact text sent to the skill
- `expected_output` — human-readable description of what good output looks like
- `files` / `project_dir` — optional: fixture files or project directory for the eval
- `assertions` — array of checks, each with:
  - `id` — assertion identifier
  - `text` — description of what must hold
  - `type` — `"behavior"`, `"capability"`, `"content_check"`, or `"structure_check"`

Example assertion types across the eval suites:
- `"behavior"` — what the skill does procedurally (e.g., "asks for clarification before spawning agents")
- `"capability"` — factual accuracy of output (e.g., "identifies all 5 directories created by thoughts-init")
- `"content_check"` — output artifact content (e.g., "make test exits 0 with all tests passing")
- `"structure_check"` — document shape (e.g., "research document has YAML frontmatter with date and git_commit")

#### Fixture Projects for Eval Scenarios

Several skills use small Python/Go/TypeScript fixture projects as eval inputs, stored in `evals/projects/`:

- `implement-plan-workspace/evals/projects/` — 7 Python projects, each with `inventory.py`/`test_inventory.py`-style files and a plan in `thoughts/shared/plans/`
- `validate-plan-workspace/evals/projects/` — 4 Python projects testing semantic mismatch, lying tests, hidden regressions, and ambiguous plans
- `create-plan-workspace/evals/projects/` — projects for feature planning, contradictory requirements, refactoring, and ticket-based planning
- `iterate-plan-workspace/evals/projects/` — a Python project with validator hierarchy (`src/validators/`)
- `bugmagnet-workspace/evals/files/` — standalone source files (Python `price_calculator.py`, TypeScript `user_validator.ts`, Go `string_utils.go`) with existing test files

All fixture projects use `Makefile` with a `make test` target (typically `pytest` for Python, `go test` for Go, `vitest` for TypeScript).

#### Benchmark Results Structure

`benchmark.json` in each iteration directory tracks per-eval pass rates for `with_skill` vs `without_skill`, providing a delta that shows skill impact. The `iteration-1/benchmark.json` for `research-codebase` was marked `INVALIDATED` because assertions were redesigned: the old assertions measured template conformity (section names, frontmatter), while new assertions measure capability (factual accuracy), behavior (clarification requests, agent ordering), and anti-hallucination.

---

### 3. How the Two Testing Layers Relate

| Layer | What it tests | Where | How to run |
|---|---|---|---|
| Automated bash tests | Bash scripts (thoughts-init, thoughts-metadata), plugin file structure | `test/` + `Makefile` | `make test` |
| E2E manual checklist | Claude Code runtime behavior, LLM quality | `test/E2E_CHECKLIST.md` | Human review |
| Skill evals | Skill output quality per iteration, with_skill vs without_skill delta | `*-workspace/evals/` | Manual eval harness |

---

## Code References

- `test/test-helpers.sh` — assertion library with 9 functions
- `test/thoughts-structure-test.sh` — functional tests for thoughts scripts (~88 lines, 2 test groups)
- `test/plugin-structure-test.sh` — structural tests for all 4 plugins (~134 lines, 5 test groups)
- `test/E2E_CHECKLIST.md` — manual testing checklist
- `Makefile` — test orchestration (4 targets: test, test-verbose, check, ci)
- `core/skills/research-codebase-workspace/evals/evals.json` — 7 research-codebase eval scenarios
- `core/skills/implement-plan-workspace/evals/evals.json` — 7 implement-plan eval scenarios
- `core/skills/validate-plan-workspace/evals/evals.json` — 7 validate-plan eval scenarios
- `core/skills/create-plan-workspace/evals/evals.json` — 7 create-plan eval scenarios
- `core/skills/bugmagnet-workspace/evals/evals.json` — 3 bugmagnet eval scenarios
- `core/skills/thoughts-management/scripts/thoughts-init` — bash script tested by functional tests
- `core/skills/thoughts-management/scripts/thoughts-metadata` — bash script tested by functional tests

## Architecture Documentation

### Automated Test Execution Flow

```
make test (Makefile)
    ├─→ test/thoughts-structure-test.sh
    │       ├─→ source test/test-helpers.sh
    │       ├─→ mktemp -d → isolated temp dir with trap cleanup
    │       ├─→ adds scripts/ to PATH
    │       ├─→ Test 1: thoughts-init directory structure (6 assertions)
    │       └─→ Test 2: thoughts-metadata output format (8 assertions)
    └─→ test/plugin-structure-test.sh
            ├─→ source test/test-helpers.sh
            ├─→ Test 1: marketplace.json validity
            ├─→ Test 2: stepwise-core plugin files
            ├─→ Test 3: stepwise-git plugin files
            ├─→ Test 4: stepwise-web plugin files
            └─→ Test 5: root documentation
```

### Eval Framework Structure

Each skill's eval suite is designed to measure:
1. Behavioral compliance (does the skill follow its own instructions?)
2. Capability (does it produce factually correct, complete output?)
3. Anti-hallucination (does it correctly report absence of things that don't exist?)
4. Procedural ordering (does it read files before spawning agents, wait before synthesizing?)

The `with_skill` vs `without_skill` split allows measuring the delta the skill introduces over a baseline Claude response to the same prompt.

### Test Isolation Pattern

The functional test suite uses:
```bash
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT
cd "$TEST_DIR"
setup_git_repo "$TEST_DIR"
```

This ensures each test run starts from a clean filesystem state with a valid git repo, required by the scripts under test.

## Historical Context (from thoughts/)

- `thoughts/searchable/shared/research/2025-11-12-testing-infrastructure.md` — Previous research on the testing infrastructure when it was a single plugin (pre-multiPlugin refactor). Documents the original 124 assertions, hardlink-based `thoughts-sync` tests, and CI integration via GitHub Actions.

- `thoughts/searchable/shared/plans/2025-11-13-simplify-tests.md` — Plan that simplified the test suite: removed 8 for-loops from `plugin-structure-test.sh`, reduced from ~330 lines to ~120 lines, eliminated redundant assertions (content checks, cross-reference validation), streamlined Makefile from 12 targets to 4. Final result: 28 assertions, 0.68s execution time.

## Related Research

- `thoughts/shared/research/2025-11-12-testing-infrastructure.md` — Full historical analysis of the testing infrastructure

## Open Questions

- No GitHub Actions CI workflow file was found in the current repository state. The old research document references `.github/workflows/ci.yml` but it may have been removed during the multi-plugin restructuring.
- The `research-codebase-workspace/iteration-1/benchmark.json` is marked `INVALIDATED` — iteration-2 benchmark results for this skill are not yet present in the workspace.
