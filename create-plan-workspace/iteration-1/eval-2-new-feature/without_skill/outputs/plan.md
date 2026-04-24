# `bugfix` Skill Implementation Plan

## Overview

Add a new `bugfix` skill to the `stepwise-core` plugin. This skill helps users debug failing tests by reading test output, analyzing the failure, and suggesting targeted fixes — following the same structural conventions as existing skills in `core/skills/`.

## Current State Analysis

The `stepwise-core` plugin already contains 11 skills in `core/skills/`, each as a directory with a `SKILL.md` entrypoint. The closest precedent is the `bugmagnet` skill, which is test-focused but targets **discovery of missing tests**, not **diagnosis of failing tests**. No skill currently addresses the "red phase" of TDD: a test is already written and failing, and the user needs help understanding why and how to fix it.

### Key Discoveries

- All skills live under `core/skills/<skill-name>/SKILL.md` (`core/skills/bugmagnet/SKILL.md`, etc.)
- The `plugin.json` at `core/.claude-plugin/plugin.json` does not enumerate individual skills; Claude Code discovers them by convention from the `skills/` directory — no manifest update is required.
- The `marketplace.json` at `.claude-plugin/marketplace.json` lists the four top-level plugins. No change needed there either.
- Skill frontmatter pattern (from all existing skills):
  ```yaml
  ---
  name: <skill-name>
  description: <trigger description for the skill system>
  argument-hint: [optional hint shown to the user]
  model: opus | sonnet | haiku
  disable-model-invocation: true
  allowed-tools:           # optional
    - Read
    - Bash
  ---
  ```
- `disable-model-invocation: true` appears on skills that orchestrate sub-agents (research-codebase, create-plan, implement-plan, validate-plan). Skills that are purely advisory and do not run Bash or spawn agents omit it (hamburger-method, small-safe-steps, test-desiderata, bugmagnet).
- The `bugfix` skill will need to run tests and read files, so it should include `allowed-tools: [Read, Bash]` and omit `disable-model-invocation` (Claude will run within the skill itself, not delegate to a sub-agent).
- Attribution comment block appears in all non-trivial skills immediately after the frontmatter close (`---`).

### Skill Description Trigger Language (existing patterns)

| Skill | Trigger phrases |
|---|---|
| bugmagnet | "find bugs in", "test coverage gaps", "exploratory testing on `<file>`" |
| test-desiderata | "analyzing test files", "reviewing test code", "evaluate tests" |
| research-codebase | "research codebase", "document codebase" |

The `bugfix` skill description must use trigger language that is clearly distinct from `bugmagnet` (which focuses on _finding_ bugs through edge-case tests) and `test-desiderata` (which reviews _quality_ of existing tests).

## Desired End State

A new skill `core/skills/bugfix/SKILL.md` exists and is loadable by Claude Code under the `stepwise-core` plugin. When a user invokes `/stepwise-core:bugfix` (optionally passing a test file or error output), Claude:

1. Reads the failing test file and the corresponding implementation file.
2. Asks the user to paste (or reads from a file) the current test run output if not provided as an argument.
3. Diagnoses the root cause of each failure.
4. Proposes a minimal fix (preferring changes to the implementation, not the test, unless the test expectation is genuinely wrong).
5. Implements the fix if the user confirms, then re-runs the tests to verify.

### Verification

- The skill file exists at `core/skills/bugfix/SKILL.md`.
- Running `make check` (shellcheck) passes — the new file is markdown-only, no scripts to check.
- The skill is listed when running `claude plugin list` after reinstalling the `stepwise-core` plugin.
- Manual: invoking `/stepwise-core:bugfix` in Claude Code launches the skill with the correct behaviour.

## What We Are NOT Doing

- Not modifying `core/.claude-plugin/plugin.json` or `.claude-plugin/marketplace.json` (plugin discovery is convention-based).
- Not adding a new plugin; `bugfix` belongs in the existing `stepwise-core` plugin.
- Not adding bash scripts under a `scripts/` subdirectory (no automation beyond Claude's own tooling is needed).
- Not modifying `bugmagnet` or any other existing skill.
- Not writing automated unit tests for the skill itself (skills are markdown files validated through manual invocation; see CLAUDE.md "Manual Testing" section).
- Not adding the skill to the `README.md` (not explicitly requested).

## Implementation Approach

Create a single file `core/skills/bugfix/SKILL.md`. The skill will:

1. Accept an optional argument (test file path or pasted error output).
2. Walk through a structured workflow: gather context → analyse failure → propose fix → implement on confirmation → verify.
3. Be self-contained (no supporting scripts or reference files needed for v1).
4. Follow the tone and formatting conventions established by `bugmagnet` and `test-desiderata`.

---

## Phase 1: Create the `bugfix` Skill File

### Overview

Create `core/skills/bugfix/SKILL.md` with correct frontmatter, attribution, and a clear multi-phase workflow.

### Changes Required

#### 1. New skill directory and file

**File**: `core/skills/bugfix/SKILL.md`

**Frontmatter**:
```yaml
---
name: bugfix
description: Debug failing tests by analyzing test output and suggesting targeted fixes. Use when tests are failing and the user needs help understanding why and how to fix them. Triggers on phrases like "fix failing test", "test is failing", "debug test failure", "why is this test failing", or "help me fix my tests".
argument-hint: [test-file-path or pasted test output]
model: sonnet
allowed-tools:
  - Read
  - Bash
---
```

**Rationale for `model: sonnet`**: The skill performs focused diagnosis and targeted code edits — `sonnet` is the right balance of capability and speed. The longer analytical skills (create-plan, research-codebase) use `opus`; the lightweight commit skill uses `haiku`.

**Workflow structure** (inside the SKILL.md body):

```
## Phase 1: Gather Context
- Accept $ARGUMENTS (test file path or raw output) or prompt the user
- Read the test file in full
- Locate the implementation file being tested
- Read the implementation file in full

## Phase 2: Collect Test Output
- If test output was not provided, ask the user to run the tests and paste the output
  OR run the tests automatically: bash <test-command>
- Parse failures: extract test names, assertion mismatches, stack traces

## Phase 3: Diagnose Each Failure
For each failing test:
- Identify whether the failure is in the implementation or in the test expectation
- State the root cause clearly

## Phase 4: Propose Fixes
- Prefer fixing the implementation over the test
- Show a minimal diff for each proposed change
- Ask for user confirmation before making changes

## Phase 5: Implement and Verify
- Apply the approved fix using Edit
- Re-run the tests
- Report pass/fail; iterate if tests still fail (max 3 attempts per failure)
```

### Success Criteria

- [ ] File exists at `core/skills/bugfix/SKILL.md`
- [ ] `make check` passes (no shellcheck regressions)
- [ ] Frontmatter is valid YAML (no syntax errors)
- [ ] Skill can be invoked in Claude Code after plugin reload

---

## Phase 2: Register in Smoke Tests (Optional but Recommended)

### Overview

The existing smoke tests in `test/smoke-test.sh` cover only the bash scripts in `thoughts-management`. The skill itself cannot be smoke-tested via bash. However, adding a simple file-existence check ensures the file does not get accidentally deleted in future refactoring.

### Changes Required

#### 1. Add existence assertion to smoke tests

**File**: `test/smoke-test.sh`

**Change**: Add one line asserting the new skill file exists, following the pattern used for other file checks in the test file.

```bash
assert_file_exists "core/skills/bugfix/SKILL.md" "bugfix skill file exists"
```

### Success Criteria

- [ ] `make test` passes with the new assertion included

---

## Testing Strategy

### Automated Tests

- `make check` — shellcheck on all bash scripts (no new scripts added; should still pass cleanly)
- `make test` — smoke tests, including the new file-existence assertion

### Manual Testing

1. Install or reload the `stepwise-core` plugin in Claude Code.
2. Invoke `/stepwise-core:bugfix` with no arguments — confirm the skill prompts for context.
3. Invoke `/stepwise-core:bugfix <path-to-a-failing-test-file>` — confirm the skill reads the file and the corresponding implementation.
4. Paste a sample test failure output when prompted — confirm the skill diagnoses the failure correctly and proposes a fix.
5. Confirm the fix — verify the skill applies the edit and re-runs the tests.

## Performance Considerations

None. This is a markdown-only skill file. No performance impact on build, CI, or plugin loading.

## Migration Notes

None. This is a purely additive change with no modifications to existing files (except the optional smoke test addition).

## References

- Closest existing skill: `core/skills/bugmagnet/SKILL.md`
- Test-quality counterpart: `core/skills/test-desiderata/SKILL.md`
- Plugin structure: `core/.claude-plugin/plugin.json`
- Testing guidance: `CLAUDE.md` — "Manual Testing (for skills/agents)" section
- Smoke test runner: `test/smoke-test.sh`, `Makefile`
