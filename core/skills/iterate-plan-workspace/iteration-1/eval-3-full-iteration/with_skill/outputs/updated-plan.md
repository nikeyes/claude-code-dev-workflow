# Implementation Plan: Add "bugfix" Skill

## Overview

Add a new `bugfix` skill to stepwise-core that helps users debug failing tests by analyzing test output, identifying root causes, and suggesting targeted fixes.

## Current State Analysis

The stepwise-core plugin currently has 10 skills in `core/skills/`. Existing diagnostic-adjacent skills:
- `bugmagnet/SKILL.md` (line 1-7): Generates edge-case test inputs — focuses on test creation, not debugging
- `test-desiderata/SKILL.md` (line 1-5): Evaluates test quality against Kent Beck's framework — focuses on test design, not failure analysis

No existing skill addresses the workflow of: test fails → analyze output → find root cause → suggest fix.

### Key Discoveries

1. **Skill frontmatter pattern** (`core/skills/bugmagnet/SKILL.md:1-7`):
   ```yaml
   name: bugmagnet
   description: Generate edge-case test inputs...
   model: sonnet
   ```
2. **Plugin registration** (`core/.claude-plugin/plugin.json:15-22`): Skills auto-discovered from `skills/` directories
3. **Test infrastructure** (`test/smoke-test.sh:41-73`): Existing tests validate script behavior, not skill content

## Desired End State

A new `core/skills/bugfix/SKILL.md` that:
- Accepts test output (paste or file path) as input
- Analyzes failure patterns (assertion failures, exceptions, timeouts)
- Spawns codebase-analyzer to find relevant source code
- Produces a structured diagnosis with suggested fix

## What We're NOT Doing

- Not building an auto-fix tool that modifies code without user approval
- Not replacing existing test frameworks or runners
- Not handling CI/CD pipeline failures (only local test output)
- Not supporting non-text test outputs (screenshots, videos)

## Implementation Phases

### Phase 1: Create SKILL.md

**Scope**: Create the skill file with frontmatter and instructions

**Changes**:
- Create `core/skills/bugfix/SKILL.md` following the pattern from `bugmagnet/SKILL.md`
- Define frontmatter: name, description, model (sonnet), allowed-tools
- Write instructions for: parsing test output, spawning research agents, structuring diagnosis

**Success Criteria**:
- Automated:
  - `test -f core/skills/bugfix/SKILL.md` exits 0
  - Frontmatter contains required fields (name, description)
  - `make check` passes (shellcheck on any scripts)
- Manual:
  - Skill appears in Claude Code after plugin reload
  - Invoking `/stepwise-core:bugfix` with no args shows help

### Phase 1.5: Error Handling and Rollback Procedures

**Scope**: Define and validate error handling for skill creation failures and rollback steps to restore a clean state if the skill causes problems

**Changes**:
- Document expected failure modes:
  - Malformed SKILL.md frontmatter (missing required fields)
  - Invalid `allowed-tools` values causing plugin load errors
  - Conflicting skill name with an existing skill
- Add rollback procedure to the implementation notes:
  1. Remove the broken skill directory: `rm -rf core/skills/bugfix/`
  2. Verify removal: `test ! -d core/skills/bugfix/`
  3. Restart Claude Code (or run `/reload-plugins`) to confirm plugin loads cleanly
  4. Confirm no regressions: `make test` passes
- Add a validation gate: before proceeding to Phase 2, confirm plugin loads without errors

**Success Criteria**:
- Automated:
  - `test ! -d core/skills/bugfix/` exits 0 after rollback (rollback works)
  - `make test` passes after rollback (no regressions introduced)
  - `make check` passes after rollback
- Manual:
  - Intentionally introduce a malformed frontmatter, confirm Claude Code reports a clear error
  - Execute rollback steps, confirm plugin reloads cleanly with no bugfix skill present
  - Confirm existing skills (`bugmagnet`, `test-desiderata`, etc.) still appear after rollback
- Error scenario tests:
  - Skill invoked with empty input returns a helpful error message, not a crash
  - Skill invoked with a non-text input path (e.g. a binary file) returns a clear unsupported-format message
  - Skill invoked when no test runner output is detected prompts the user for clarification

### Phase 2: Update Plugin Test Assertions

**Scope**: Add the new skill to test expectations

**Changes**:
- Update `test/smoke-test.sh` to include bugfix in skill count assertions
- Add basic validation that SKILL.md exists and has valid frontmatter

**Success Criteria**:
- Automated:
  - `make test` passes with updated assertions
  - `make check` passes
- Manual:
  - Test output shows bugfix skill validated

## Success Criteria (Overall)

### Automated Verification
- `test -f core/skills/bugfix/SKILL.md` — skill file exists
- `make test` — all tests pass including new assertions
- `make check` — shellcheck passes
- `test ! -d core/skills/bugfix/` exits 0 after rollback — rollback procedure is confirmed working

### Manual Verification
- Skill triggers correctly when user pastes failing test output
- Diagnosis includes specific file:line references
- Suggested fixes are actionable and relevant

### Error Scenario Tests
- **Empty input**: invoking `/stepwise-core:bugfix` with no arguments or empty string returns a clear usage message, not an unhandled error
- **Unrecognized format**: providing a binary file path or non-test output produces a readable "unsupported format" response
- **No failures detected**: if the pasted output contains no test failures, the skill informs the user rather than producing a spurious diagnosis
- **Rollback coverage**: after executing the rollback procedure, `make test` passes and all pre-existing skills remain registered in the plugin
