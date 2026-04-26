# Implementation Plan: Add "bugfix" Skill

## Overview

Add a new `bugfix` skill to stepwise-core that helps users debug failing tests by analyzing test output, identifying root causes, and suggesting targeted fixes.

## Current State Analysis

The stepwise-core plugin currently has 10 skills in `core/skills/`. Existing diagnostic-adjacent skills:
- `bugmagnet/SKILL.md`: Generates edge-case test inputs — focuses on test creation, not debugging
- `test-desiderata/SKILL.md`: Evaluates test quality against Kent Beck's framework — focuses on test design, not failure analysis

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
- Analyzes failure patterns (assertion failures, exceptions, timeouts, flaky failures)
- Spawns `codebase-analyzer` agent to find relevant source code context
- Produces a structured diagnosis (see Output Format below) with a suggested fix
- Invoked as `/stepwise-core:bugfix`

## Output Format

When the skill completes a diagnosis, it outputs:

```
## Bug Diagnosis

**Failure type**: [AssertionError | Exception | Timeout | Flaky | Unknown]
**Test**: <file>:<line> — <test name>
**Root cause**: 1-2 sentence plain-language explanation

## Relevant Code
<file>:<line-range> — <why this is relevant>

## Suggested Fix
<specific, actionable change — not "check your logic">

## Confidence
[High | Medium | Low] — <reason if not High>
```

## What We're NOT Doing

- Not building an auto-fix tool that modifies code without user approval
- Not replacing existing test frameworks or runners
- Not integrating with CI/CD APIs or pipeline systems (pasting CI output is fine)
- Not supporting non-text test outputs (screenshots, videos)

## Implementation Phases

### Phase 1: Create SKILL.md and Update Tests

**Scope**: Create the skill file and add it to the test baseline

**Changes**:
- Create `core/skills/bugfix/SKILL.md` following the pattern from `bugmagnet/SKILL.md`
- Frontmatter:
  - `name: bugfix`
  - `description: Analyze failing test output, identify root cause, and suggest a targeted fix`
  - `model: sonnet`
  - `allowed-tools: Task, Read, Bash`
- Instructions must cover:
  1. Accept test output as argument or prompt user to paste it
  2. Identify failure type (assertion, exception, timeout, flaky)
  3. Spawn `codebase-analyzer` agent with the failing test name and error message to locate relevant source
  4. Produce diagnosis in the Output Format defined above
- Update `test/smoke-test.sh` skill count assertion from 10 to 11

**Success Criteria**:
- Automated:
  - `test -f core/skills/bugfix/SKILL.md` exits 0
  - `grep -q "^name: bugfix" core/skills/bugfix/SKILL.md` exits 0
  - `grep -q "^description:" core/skills/bugfix/SKILL.md` exits 0
  - `make test` passes
  - `make check` passes (shellcheck)
- Manual:
  - Skill appears in Claude Code after plugin reload
  - Invoking `/stepwise-core:bugfix` with no args prompts user to paste test output

### Phase 2: Validate Skill Behavior

**Scope**: Verify the skill produces useful output on real failure cases

**Test cases** (manual, run in a sample project with failing tests):

| Input | Expected behavior |
|---|---|
| AssertionError with stack trace | Identifies assertion line, finds tested function, suggests fix |
| ImportError / ModuleNotFoundError | Identifies missing dependency, explains likely cause |
| Timeout failure | Flags as flaky/timeout type, notes confidence is Low |
| Garbled / non-test input | Skill asks for clarification rather than hallucinating a diagnosis |

**Success Criteria**:
- Manual:
  - Diagnosis includes specific `file:line` references from the actual codebase
  - Suggested fix names the specific function/variable to change (not generic advice)
  - Confidence is rated Low when the failure is ambiguous (e.g., timeout, flaky)
  - Skill does not auto-modify any files

## Risk / Notes

- **Model choice**: Sonnet is the default for all skills. If diagnosis quality is poor on complex traces, consider flagging this as a candidate for Opus in the frontmatter.
- **allowed-tools**: `Task` is needed to spawn `codebase-analyzer`. `Read` is needed if user provides a file path. `Bash` is optional — only needed if we want to run the test again to reproduce; leave it out in v1 to keep scope narrow.
- **Scope boundary**: This skill diagnoses — it does not fix. The user takes the suggested fix and applies it. This keeps the human in the loop and avoids the skill needing write permissions.

## Success Criteria (Overall)

### Automated Verification
- `test -f core/skills/bugfix/SKILL.md` — skill file exists
- `grep -q "^name: bugfix" core/skills/bugfix/SKILL.md` — correct name
- `make test` — all tests pass including updated skill count
- `make check` — shellcheck passes

### Manual Verification
- Diagnosis includes specific `file:line` references
- Suggested fixes name the exact code element to change
- Confidence field is populated and honest (Low for ambiguous failures)
- Skill does not modify any files autonomously
