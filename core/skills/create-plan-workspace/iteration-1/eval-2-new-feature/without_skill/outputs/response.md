# Response: Implementation Plan for the `bugfix` Skill

## Research Summary

I explored the full repository structure to understand how skills are built and how existing skills relate to each other. Key findings:

- All `stepwise-core` skills live under `core/skills/<skill-name>/SKILL.md`. The plugin discovery is convention-based — no manifest update is required when adding a new skill.
- The closest existing skill is `bugmagnet` (`core/skills/bugmagnet/SKILL.md`), but it focuses on _discovering missing tests_ through edge-case heuristics. No skill currently addresses diagnosing and fixing _already-failing_ tests.
- Skill frontmatter follows a consistent pattern: `name`, `description` (with explicit trigger phrases), optional `argument-hint`, `model` (opus/sonnet/haiku based on complexity), optional `allowed-tools`, and `disable-model-invocation: true` for skills that purely orchestrate agents without running Claude themselves.
- The `bugfix` skill needs `Read` and `Bash` tools (to read files and run test commands), so it should use `allowed-tools` and omit `disable-model-invocation`.
- `model: sonnet` is appropriate — focused diagnosis and targeted edits sit between the lightweight `commit` skill (haiku) and the deep research skills (opus).
- Smoke tests in `test/smoke-test.sh` cover only bash scripts; a simple file-existence assertion for the new skill is the right level of automated coverage.

---

## Implementation Plan

The full plan is saved to `plan.md` alongside this response. Here is a concise summary.

### What We Are Building

A new skill `core/skills/bugfix/SKILL.md` that helps users debug failing tests. When invoked, it:

1. Reads the test file and corresponding implementation file.
2. Collects test run output (from the user or by running tests directly).
3. Diagnoses each failure — distinguishing implementation bugs from incorrect test expectations.
4. Proposes a minimal fix (preferring implementation changes).
5. Implements the fix on user confirmation and re-runs tests to verify.

### What We Are NOT Doing

- Not creating a new plugin (this belongs in `stepwise-core`).
- Not modifying `plugin.json`, `marketplace.json`, or any existing skill.
- Not adding bash scripts or reference files (not needed for v1).
- Not updating `README.md` (not requested).

### Phases

#### Phase 1 — Create `core/skills/bugfix/SKILL.md` (required)

The skill file with correct frontmatter and a structured five-phase workflow:

```
Gather Context → Collect Test Output → Diagnose Failures → Propose Fixes → Implement & Verify
```

**Frontmatter highlights:**
```yaml
name: bugfix
description: Debug failing tests by analyzing test output and suggesting targeted fixes. Use when tests are failing and the user needs help understanding why and how to fix them. Triggers on phrases like "fix failing test", "test is failing", "debug test failure", "why is this test failing", or "help me fix my tests".
argument-hint: [test-file-path or pasted test output]
model: sonnet
allowed-tools:
  - Read
  - Bash
```

**Success criteria:**
- `core/skills/bugfix/SKILL.md` exists
- `make check` passes (no shellcheck regressions — no new scripts)
- Skill can be invoked in Claude Code after plugin reload

#### Phase 2 — Add file-existence assertion to `test/smoke-test.sh` (optional but recommended)

```bash
assert_file_exists "core/skills/bugfix/SKILL.md" "bugfix skill file exists"
```

**Success criteria:**
- `make test` passes with the new assertion

### Manual Testing Steps

1. Reload `stepwise-core` plugin in Claude Code.
2. Invoke `/stepwise-core:bugfix` with no arguments — skill should prompt for context.
3. Invoke `/stepwise-core:bugfix <path-to-failing-test>` — skill should read the test file and locate the implementation.
4. Paste a sample failure output — skill should diagnose and propose a minimal fix.
5. Confirm the fix — skill should apply the edit and re-run tests.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Belongs in `stepwise-core`, not a new plugin | It is a core development workflow skill, consistent with bugmagnet, test-desiderata |
| `model: sonnet` | Focused diagnosis and code edits; not as exploratory as research/plan skills (opus), not as trivial as commit (haiku) |
| No `disable-model-invocation` | Skill runs Claude directly with Read+Bash; no sub-agent delegation needed for v1 |
| Prefers fixing implementation over test | Aligns with TDD philosophy: tests describe desired behaviour; implementation must satisfy them |
| Max 3 attempts per failure | Mirrors the same cap in `bugmagnet` to avoid infinite loops |
| No scripts subdirectory | Not needed; all logic is expressed as Claude instructions in the SKILL.md |

---

## File Locations

- Plan: `create-plan-workspace/iteration-1/eval-2-new-feature/without_skill/outputs/plan.md`
- New skill to create: `core/skills/bugfix/SKILL.md`
- Smoke test to optionally update: `test/smoke-test.sh`
- Reference skills: `core/skills/bugmagnet/SKILL.md`, `core/skills/test-desiderata/SKILL.md`
- Plugin descriptor: `core/.claude-plugin/plugin.json`
