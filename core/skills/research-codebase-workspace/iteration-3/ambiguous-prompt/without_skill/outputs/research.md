# Research: Tests in stepwise-dev

## Overview

The stepwise-dev project has two distinct and separate testing systems: **automated bash smoke tests** for the bash scripts, and **LLM evaluation suites (evals)** for measuring skill quality. These serve entirely different purposes and are not connected.

---

## 1. Automated Bash Tests

**Location**: `/Users/jorge.castro/mordor/personal/stepwise-dev/test/`

### Files

| File | Purpose |
|------|---------|
| `test/test-helpers.sh` | Shared assertion library |
| `test/plugin-structure-test.sh` | Validates the multi-plugin marketplace structure |
| `test/thoughts-structure-test.sh` | Functional tests for the `thoughts-init` and `thoughts-metadata` bash scripts |
| `test/E2E_CHECKLIST.md` | Manual end-to-end testing checklist |

### Test Helpers (`test/test-helpers.sh`)

Provides a reusable assertion framework with colored output:
- `assert_file_exists PATH [desc]`
- `assert_dir_exists PATH [desc]`
- `assert_executable PATH [desc]`
- `assert_contains FILE PATTERN [desc]`
- `assert_file_not_exists PATH [desc]`
- `assert_output_contains OUTPUT PATTERN [desc]`
- `assert_not_empty VALUE [desc]`
- `setup_git_repo DIR` — initialises a throwaway git repo for functional tests
- `print_summary` — prints pass/fail totals and returns exit code 1 on any failure
- `section "name"` — prints a yellow section header

Global counters `TESTS_RUN`, `TESTS_PASSED`, `TESTS_FAILED` are accumulated across all assertions.

### Plugin Structure Tests (`test/plugin-structure-test.sh`)

Validates the static file structure of all four plugins. Runs ~91 assertions across 5 sections:

1. **Marketplace manifest** — `.claude-plugin/marketplace.json` exists, is valid JSON, has `name`, `owner.name`, and at least 3 plugins listed.
2. **stepwise-core** — `core/.claude-plugin/plugin.json`, `core/README.md`, all 5 workflow SKILL.md files (`research-codebase`, `create-plan`, `iterate-plan`, `implement-plan`, `validate-plan`), all 5 agent markdown files, the `thoughts-management` Skill directory, its `scripts/` directory, both scripts (`thoughts-init`, `thoughts-metadata`) exist and are executable.
3. **stepwise-git** — `git/.claude-plugin/plugin.json`, `git/README.md`, `git/skills/commit/SKILL.md`.
4. **stepwise-web** — `web/.claude-plugin/plugin.json`, `web/README.md`, `web/agents/web-search-researcher.md`.
5. **Root docs** — `README.md`, `CLAUDE.md`, `.gitignore`, README contains "stepwise-dev".

### Functional Tests (`test/thoughts-structure-test.sh`)

Runs ~33 assertions against the two bash scripts in `core/skills/thoughts-management/scripts/`:

**Test 1 — `thoughts-init` creates directory structure**
Creates a temporary directory, initialises a git repo, runs `thoughts-init`, and asserts the five subdirectories and `README.md` are created:
- `thoughts/nikey_es/tickets/`
- `thoughts/nikey_es/notes/`
- `thoughts/shared/research/`
- `thoughts/shared/plans/`
- `thoughts/shared/prs/`
- `thoughts/README.md`

**Test 2 — `thoughts-metadata` generates valid metadata**
Runs `thoughts-metadata` in the same temporary directory (which now has a git repo) and asserts the output contains:
- "Current Date/Time", "ISO DateTime", "Git User: Test User", "Git Email: test@example.com"
- "Current Git Commit Hash", "Current Branch Name", "Timestamp For Filename"
- A valid ISO 8601 date (`YYYY-MM-DDTHH:MM:SS` pattern)

### Running Tests

Controlled by `Makefile` at project root:

```
make test           # functional + structure (default)
make test-verbose   # same with bash -x tracing
make check          # shellcheck on all bash scripts
make ci             # test + check + jq JSON validation of all manifests
```

The `ci` target validates both `marketplace.json` and the four `plugin.json` manifests using `jq`.

### E2E Manual Checklist (`test/E2E_CHECKLIST.md`)

Lists tests that require Claude Code runtime and cannot be automated:
- Plugin install/disable/enable lifecycle
- Workflow quality checks (research document quality, plan actionability, agent parallelism)
- Context management warning validation

---

## 2. LLM Evaluation Suites (Evals)

Each skill has an `evals/` workspace under `core/skills/<skill>-workspace/evals/`. These are NOT executable bash tests — they are structured JSON scenario definitions used to benchmark LLM skill performance by comparing `with_skill` vs `without_skill` configurations.

### Evals per Skill

#### research-codebase (`core/skills/research-codebase-workspace/evals/evals.json`)
7 scenarios testing:
- Factual accuracy (which agents create-plan uses, execution order)
- Cross-component data flow tracing
- **Ambiguous prompt handling** — eval 3 ("Investiga los tests") expects the model to ask for clarification rather than dive in
- Anti-hallucination on nonexistent topics (no database/SQL in this project)
- Explicit file-read ordering (read before spawning agents)
- Inter-plugin relationships
- Agent architecture (parallel spawning + locator vs analyzer distinction)

#### validate-plan (`core/skills/validate-plan-workspace/evals/evals.json`)
7 scenarios with fixture projects in `evals/projects/`:
- `eval-1`: Fully correct implementation
- `eval-2`: Plan checkboxes marked done but files are missing (incomplete lying)
- `eval-3`: Implementation naming deviations from plan
- `eval-4` (`eval-4-semantic-mismatch`): Plan says IP-based rate limiting, code uses session IDs
- `eval-5` (`eval-5-lying-tests`): 13 tests pass but many are tautological or assertion-free
- `eval-6` (`eval-6-hidden-regression`): Caching integration introduced a regression in `get_user_count`
- `eval-7` (`eval-7-ambiguous-plan`): Plan contains vague/unmeasurable criteria

#### implement-plan (`core/skills/implement-plan-workspace/evals/evals.json`)
7 scenarios with fixture projects in `evals/projects/`:
- `eval-1-phase-discipline`: 4 sequential phases with `make test` after each
- `eval-2-ambiguous-mismatch`: Class/method naming mismatches between plan and code
- `eval-3-manual-verification`: Agent must pause after Phase 2 for user confirmation
- `eval-4-cascade-dependencies`: 5 phases with strict ordering
- `eval-5-evolved-codebase`: `string_helpers.py` doesn't exist; code split into two files
- `eval-6-resume-buggy-phase`: Phase 1 marked done but has a bug; resume from Phase 2
- `eval-7-completion-messaging`: Completion message must reference `validate-plan` and `stepwise-git:commit`

#### create-plan (`core/skills/create-plan-workspace/evals/evals.json`)
7 scenarios:
- Vague prompt — should ask clarification, not plan
- Trivial task — one-line typo fix should not become a multi-phase plan
- Feature planning — caching layer for a real fixture `user_service.py`
- Contradictory requirements — stateless + WebSocket state persistence conflict
- Refactoring depth — strategy pattern from if/elif chain with 5 branches
- Ticket workflow — `eng-1234.md` ticket with an implicit auth dependency
- No-args help

#### iterate-plan (`core/skills/iterate-plan-workspace/evals/evals.json`)
7 scenarios:
- Vague feedback ("make it better") — must ask clarification
- Requested change contradicts existing scope exclusions
- Surgical edit to a large 5-phase plan (only Phase 3 must change)
- Research-dependent change (must discover real validator classes before updating plan)
- Remove a phase and handle cascading dependencies
- Conflicting phase dependency ordering (new phase requires output of a later phase)
- No-args help

#### bugmagnet (`core/skills/bugmagnet-workspace/evals/evals.json`)
3 scenarios using source files in `evals/files/`:
- `price_calculator.py` — Python: zero-division in `split_payment`, negative prices, floating-point rounding
- `user_validator.ts` — TypeScript: email edge cases, NaN/Infinity age, destructuring crash in `normalizeEmail`
- `string_utils.go` — Go: unicode truncation bug in `Truncate` (uses `len()` not rune count), index panic in `ExtractInitials` with empty string

### Benchmark Results

Results are stored as `benchmark.json` in each iteration directory.

**research-codebase** (iteration-2, latest complete run):
- `with_skill` mean pass rate: **0.86** | `without_skill`: **0.76** | delta: **+0.10**
- Eval-3 (ambiguous prompt): **both fail (0.0/2)** — the skill treats any non-empty `$ARGUMENTS` as a valid query and proceeds without asking for clarification. This is a known design gap.

**validate-plan** (iteration-3, simplified 56-line skill):
- `with_skill` mean: **0.980** | `without_skill`: **0.906** | delta: **+0.074**
- Compared to iteration-2 (206-line skill): delta grew from +0.018 to +0.074, while token overhead dropped 59% and time overhead dropped 61%.
- Biggest skill advantage on eval-5 (lying tests), eval-6 (hidden regression), eval-7 (ambiguous plan).

**implement-plan** (iteration-3):
- `with_skill` mean: **0.84** | `without_skill`: **0.45** | delta: **+0.39**
- Largest skill delta in the project. Biggest advantages: phase discipline (eval-1: 1.00 vs 0.29), manual verification pausing (eval-3: 1.00 vs 0.43), completion messaging (eval-7: 1.00 vs 0.43).
- Eval-6 with_skill dropped to 0.25 in iteration-3 due to Bash permissions issues in the eval environment.

**create-plan** (iteration-2):
- `with_skill` mean: **0.95** | `without_skill`: **0.67** | delta: **+0.28**
- Strongest on adversarial inputs: vague prompt (+67%), contradictory requirements (+50%).

**iterate-plan** (iteration-2):
- `with_skill` mean: **0.98** | `without_skill`: **0.77** | delta: **+0.21**
- Eval-1 (vague feedback) is the strongest discriminator: 4/4 vs 1/4.
- 3 of 7 evals are non-discriminating (evals 2, 3, 5 — the model handles these equally well without the skill).

---

## 3. Assertion Types

Eval assertions use three types:

| Type | Meaning |
|------|---------|
| `capability` | Factual accuracy, anti-hallucination, content correctness |
| `behavior` | Procedural correctness (order of operations, pausing, not acting prematurely) |
| `structure_check` | Document structure (frontmatter, file paths) |
| `content_check` | Verifiable artifacts (tests pass, files exist, checkboxes marked) |
| `output` | Exact output content (sections unchanged, specific text present) |

---

## 4. Test Fixture Projects

Validate-plan and implement-plan evals use isolated Python fixture projects in `evals/projects/`. Each has its own `Makefile` with a `make test` target. The fixture projects are self-contained and do not depend on the stepwise-dev codebase.

Example fixture projects:
- `core/skills/validate-plan-workspace/evals/projects/eval-5-lying-tests/` — payment processor with 13 passing but deceptive tests
- `core/skills/validate-plan-workspace/evals/projects/eval-6-hidden-regression/` — user service where caching introduced a regression in `get_user_count`
- `core/skills/implement-plan-workspace/evals/projects/eval-5-evolved-codebase/` — codebase where `string_helpers.py` was split into two files

---

## 5. Key Findings

1. The automated bash tests cover only the `thoughts-init` and `thoughts-metadata` scripts, plus static file structure. They run in ~3 seconds and have no LLM dependency.

2. The eval suites are the primary quality measurement tool for skills. They require manual execution and LLM inference.

3. Eval-3 of research-codebase ("Investiga los tests") is specifically designed to test whether the skill asks for clarification on ambiguous prompts. Both `with_skill` and `without_skill` configurations currently fail this eval — the skill treats any non-empty argument as a valid research query.

4. The E2E checklist (`test/E2E_CHECKLIST.md`) still references an old plugin name (`workflow-dev@workflow-dev-marketplace`) that does not match the current multi-plugin marketplace architecture.

5. Shellcheck is run via `make check` on `core/skills/thoughts-management/scripts/*` and `test/*.sh`.
