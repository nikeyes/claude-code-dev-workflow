---
date: 2026-04-26
topic: "Investiga los tests"
eval: ambiguous-prompt
iteration: 2
mode: without_skill
---

# Research: Tests in stepwise-dev

## Clarification Note

The prompt "Investiga los tests" is intentionally ambiguous. The codebase contains several distinct types of tests:

1. **Automated bash smoke tests** (functional + structural)
2. **Skill eval suites** (per-skill JSON eval definitions with fixture projects)
3. **Benchmark result tracking** (iteration-based benchmark.md files)
4. **Manual E2E checklist**
5. **Test helper utilities**

This document covers all of them rather than picking one interpretation.

---

## 1. Automated Bash Tests

### Location
- `/Users/jorge.castro/mordor/personal/stepwise-dev/test/`

### Files
| File | Purpose |
|------|---------|
| `test/test-helpers.sh` | Shared assertion functions |
| `test/thoughts-structure-test.sh` | Functional tests for thoughts bash scripts |
| `test/plugin-structure-test.sh` | Structural validation of all 4 plugins |
| `test/E2E_CHECKLIST.md` | Manual E2E checklist (not automated) |

### Running Tests

Defined in `/Users/jorge.castro/mordor/personal/stepwise-dev/Makefile`:

```bash
make test          # Run all automated tests (functional + structure)
make test-verbose  # Run with bash -x debug output
make check         # shellcheck on all bash scripts
make ci            # test + check + jq manifest validation
```

### Test Helpers (`test/test-helpers.sh`)

Provides reusable assertion functions:
- `assert_file_exists PATH desc`
- `assert_dir_exists PATH desc`
- `assert_executable PATH desc`
- `assert_contains FILE PATTERN desc`
- `assert_file_not_exists PATH desc`
- `assert_output_contains OUTPUT PATTERN desc`
- `assert_not_empty VALUE desc`
- `setup_git_repo DIR` — initializes a git repo for tests that need git context
- `print_summary` — prints TESTS_RUN / TESTS_PASSED / TESTS_FAILED counts
- `section "Name"` — yellow section header

Tracks counters via global variables: `TESTS_RUN`, `TESTS_PASSED`, `TESTS_FAILED`.

### Functional Tests (`test/thoughts-structure-test.sh`)

Tests the two bash scripts in `core/skills/thoughts-management/scripts/`:

**Test 1 — `thoughts-init` creates directory structure:**
- Creates a temp dir, initializes a git repo via `setup_git_repo`
- Runs `thoughts-init`
- Asserts that 5 subdirectories are created: `thoughts/nikey_es/tickets`, `thoughts/nikey_es/notes`, `thoughts/shared/research`, `thoughts/shared/plans`, `thoughts/shared/prs`
- Asserts `thoughts/README.md` is created

**Test 2 — `thoughts-metadata` generates valid metadata:**
- Runs `thoughts-metadata` and captures output
- Asserts output contains: `Current Date/Time`, `ISO DateTime`, `Git User: Test User`, `Git Email: test@example.com`, `Current Git Commit Hash`, `Current Branch Name`, `Timestamp For Filename`
- Validates ISO 8601 date format using regex `[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}`

### Structure Tests (`test/plugin-structure-test.sh`)

Validates the multi-plugin marketplace structure:

**Test 1 — Marketplace manifest:**
- `assert_file_exists ".claude-plugin/marketplace.json"`
- jq validates JSON, checks `name`, `owner.name` fields, asserts `plugins` count >= 3

**Test 2 — stepwise-core plugin:**
- plugin.json and README.md exist
- All 5 workflow skills exist: `research-codebase`, `create-plan`, `iterate-plan`, `implement-plan`, `validate-plan`
- All 5 agents exist: `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, `thoughts-locator`, `thoughts-analyzer`
- `thoughts-management` Skill structure: SKILL.md, scripts directory
- `thoughts-init` and `thoughts-metadata` scripts exist and are executable

**Test 3 — stepwise-git plugin:**
- `git/.claude-plugin/plugin.json`, `git/README.md`, `git/skills/commit/SKILL.md` exist

**Test 4 — stepwise-web plugin:**
- `web/.claude-plugin/plugin.json`, `web/README.md`, `web/agents/web-search-researcher.md` exist

**Test 5 — Root documentation:**
- `README.md`, `CLAUDE.md`, `.gitignore` exist
- `README.md` contains the text "stepwise-dev"

---

## 2. Skill Eval Suites

Each skill workspace has a `evals/evals.json` file defining evaluation scenarios. These are **not automated** — they are run manually by invoking the skill and comparing output against assertions.

### Per-Skill Eval Files

| Skill | Eval File | Num Evals |
|-------|-----------|-----------|
| research-codebase | `core/skills/research-codebase-workspace/evals/evals.json` | 7 |
| create-plan | `core/skills/create-plan-workspace/evals/evals.json` | 7 |
| implement-plan | `core/skills/implement-plan-workspace/evals/evals.json` | 7 |
| iterate-plan | `core/skills/iterate-plan-workspace/evals/evals.json` | 7 |
| validate-plan | `core/skills/validate-plan-workspace/evals/evals.json` | 7 |
| bugmagnet | `core/skills/bugmagnet-workspace/evals/evals.json` | 3 |

### Eval Structure (per eval entry)

```json
{
  "id": 3,
  "prompt": "Investiga los tests",
  "expected_output": "Should ask for clarification...",
  "project_dir": "evals/projects/eval-N-name",  // optional fixture project
  "files": ["evals/some-file.md"],               // optional input files
  "assertions": [
    {"id": "asks-clarification", "text": "...", "type": "behavior"},
    {"id": "no-premature-research", "text": "...", "type": "behavior"}
  ]
}
```

### Assertion Types

- `behavior` — what the skill should or should not do (e.g., spawn agents, ask clarification)
- `capability` — factual accuracy of output (e.g., identifies correct class names)
- `content_check` — what appears in output files (e.g., plan checkboxes marked)
- `structure_check` — document structure (e.g., YAML frontmatter present)
- `output` — literal content in output (e.g., specific phase text unchanged)

### Fixture Projects

Eval scenarios that test code-aware behavior use fixture projects under `evals/projects/`:

- `create-plan-workspace/evals/projects/eval-3-feature-planning/` — `user_service.py`, `test_user_service.py`
- `create-plan-workspace/evals/projects/eval-4-contradictory/` — `notification_service.py`
- `create-plan-workspace/evals/projects/eval-5-refactoring/` — `data_processor.py` (if/elif chain)
- `create-plan-workspace/evals/projects/eval-6-ticket/` — `inventory.py`, `auth.py`, `tickets/eng-1234.md`
- `implement-plan-workspace/evals/projects/eval-1-phase-discipline/` — `inventory.py`, `test_inventory.py`
- `implement-plan-workspace/evals/projects/eval-2-ambiguous-mismatch/` — `order.py`, `test_order.py`
- `implement-plan-workspace/evals/projects/eval-3-manual-verification/` — `formatter.py`, `test_formatter.py`
- `implement-plan-workspace/evals/projects/eval-4-cascade-dependencies/` — `tracker.py`, `test_tracker.py`
- `implement-plan-workspace/evals/projects/eval-5-evolved-codebase/` — `text_utils.py`, `text_transforms.py`, `test_text.py`
- `implement-plan-workspace/evals/projects/eval-6-resume-buggy-phase/` — `registration.py`, `test_registration.py`
- `implement-plan-workspace/evals/projects/eval-7-completion-messaging/` — `converter.py`, `test_converter.py`
- `validate-plan-workspace/evals/projects/eval-4-semantic-mismatch/`
- `validate-plan-workspace/evals/projects/eval-5-lying-tests/`
- `validate-plan-workspace/evals/projects/eval-6-hidden-regression/`
- `validate-plan-workspace/evals/projects/eval-7-ambiguous-plan/`
- `iterate-plan-workspace/evals/projects/eval-4-research-dependent/`

Bugmagnet uses standalone files in `bugmagnet-workspace/evals/files/`:
- `price_calculator.py`, `test_price_calculator.py`
- `user_validator.ts`, `user_validator.test.ts`
- `string_utils.go`, `string_utils_test.go`

---

## 3. Benchmark Result Tracking

Each skill workspace tracks eval runs per iteration:

### Structure

```
{skill}-workspace/
  iteration-1/
    eval-{n}-{name}/
      eval_metadata.json       # eval definition snapshot
      with_skill/outputs/      # skill output artifacts
      without_skill/outputs/   # baseline output artifacts
    benchmark.md               # aggregate results summary
  iteration-2/
    ...
```

### Benchmark Files Found

| File | Skill |
|------|-------|
| `create-plan-workspace/iteration-1/benchmark.md` | create-plan |
| `create-plan-workspace/iteration-2/benchmark.md` | create-plan |
| `implement-plan-workspace/iteration-2/benchmark.md` | implement-plan |
| `iterate-plan-workspace/iteration-2/benchmark.md` | iterate-plan |
| `validate-plan-workspace/iteration-2/benchmark.md` | validate-plan |

Note: All benchmark.md files currently show placeholder values (0% pass rate, 0 tokens) — they are templates awaiting real benchmark run data.

### Benchmark Invalidation

`research-codebase-workspace/iteration-1/benchmark.json` has `"status": "INVALIDATED"` with the explanation:
> "Previous results measured template conformity only (section names, frontmatter presence). New assertions measure capability (factual accuracy, anti-hallucination, cross-component tracing)..."

This means the iteration-1 results for research-codebase are explicitly marked non-comparable to iteration-2 assertions.

---

## 4. Manual E2E Checklist (`test/E2E_CHECKLIST.md`)

Documents manual tests that require Claude Code runtime (cannot be automated):

- Plugin installation and `/help` command verification
- Workflow quality: verifying research document quality, plan actionability, parallel agent spawning, context management warnings
- Plugin lifecycle: disable/enable plugin and verify command availability

---

## Summary

| Test Category | Location | Automated? | Count |
|---------------|----------|------------|-------|
| Bash functional tests | `test/thoughts-structure-test.sh` | Yes | 14 assertions (Test 1: 6, Test 2: 8) |
| Plugin structure tests | `test/plugin-structure-test.sh` | Yes | ~30+ assertions across 5 sections |
| Skill eval suites | `*/evals/evals.json` | No (manual) | 38 total evals across 6 skills |
| Benchmark tracking | `*/iteration-N/benchmark.md` | No (manual runs) | 5 benchmark files |
| E2E checklist | `test/E2E_CHECKLIST.md` | No (manual) | ~10 checklist items |
| Test helpers | `test/test-helpers.sh` | N/A (library) | 8 assertion functions |

The automated tests (`make test`) focus exclusively on the bash scripts in `thoughts-management/scripts/` and the plugin file/manifest structure. All skill behavior testing is done manually through eval fixtures.
