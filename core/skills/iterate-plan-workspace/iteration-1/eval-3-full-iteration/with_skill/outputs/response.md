# Skill Execution: /iterate-plan — Full Iteration

## Invocation

```
/iterate-plan thoughts/shared/plans/2026-04-24-bugfix-skill.md Add an error handling phase with rollback procedures between Phase 1 and Phase 2, and update success criteria to include error scenario tests
```

**$ARGUMENTS**: `thoughts/shared/plans/2026-04-24-bugfix-skill.md Add an error handling phase with rollback procedures between Phase 1 and Phase 2, and update success criteria to include error scenario tests`

Both a plan file path and feedback are provided — proceeding immediately to Step 1.

---

## Step 1: Read and Understand Current Plan

Reading `thoughts/shared/plans/2026-04-24-bugfix-skill.md` completely.

**Plan summary**:
- **Goal**: Add a `bugfix` skill to stepwise-core for debugging failing tests
- **Current structure**: 2 phases
  - Phase 1: Create SKILL.md (the actual skill file)
  - Phase 2: Update Plugin Test Assertions (update smoke tests)
- **What we're NOT doing**: No auto-fix, no CI/CD, no non-text outputs
- **Success Criteria**: File existence, `make test`, `make check`, manual skill invocation test

**Requested changes**:
1. Add an error handling phase with rollback procedures **between Phase 1 and Phase 2**
2. Update success criteria to include **error scenario tests**

**Assessment of whether research is needed**: Yes. The changes require understanding:
- What error modes are realistic when adding a skill file in this codebase
- What rollback patterns exist in existing plans/skills
- What error scenario test patterns the codebase uses

---

## Step 2: Research Findings

Research conducted across:
- `core/skills/small-safe-steps/SKILL.md` — Expand-Contract pattern, rollback checkpoints, "Rollback plan is clear" checklist item
- `core/skills/validate-plan/SKILL.md` — "No rollback handling in migration" listed as a potential issue to flag
- `core/skills/create-plan/SKILL.md` — Template includes "Migration Notes" section with rollback consideration
- `thoughts/shared/plans/2025-11-13-prevent-6000-token-limit-error.md` — Phase 2 explicitly tests "Agents return errors" as an edge case, shows error scenario test structure
- `core/skills/bugmagnet/SKILL.md` — Generates edge-case test inputs (natural companion for error scenario tests)
- `test/smoke-test.sh` — Existing tests validate script behavior, not skill content; tests use `test -f` and `make check`

**Key findings**:

1. **Rollback is simple for skill files**: Skills are pure markdown files with no database migrations, no deployed artifacts, no service dependencies. Rolling back a skill means `rm -rf core/skills/bugfix/` followed by a plugin reload. This is the correct pattern — not an expand-contract migration.

2. **Error modes for skill creation are narrow**:
   - Malformed YAML frontmatter (missing `name`, `description`, invalid `allowed-tools`)
   - Conflicting skill name with an existing skill
   - Skill causing plugin load failure entirely
   - Skill invoked with unexpected input (empty, binary, non-test-output)

3. **Error scenario test pattern from `2025-11-13-prevent-6000-token-limit-error.md`**: Phase 2 has "Edge Case Testing" with a table of scenarios (no agents return findings, agents return errors, very large single agent output) — this is the pattern to follow for behavioral error scenario tests.

4. **`make test` is the automation anchor**: All automated checks gate on `make test` and `make check`. Rollback verification also uses these.

5. **No existing skills have a dedicated error handling phase**: The new phase is additive and follows the pattern of other "verification gate" phases seen in the token limit error plan.

---

## Step 3: Understanding and Proposed Changes

Based on the feedback and research, here is my understanding:

**You want to**:
1. Add a Phase 1.5 (between Phase 1 and Phase 2) that:
   - Documents the realistic failure modes when creating the skill file
   - Provides a clear rollback procedure (remove the file, reload the plugin, verify clean state)
   - Acts as a verification gate before proceeding to Phase 2
2. Update the overall success criteria to include:
   - Error scenario tests (what happens when the skill is invoked with bad/empty/unexpected input)
   - Rollback verification (confirm rollback procedure is exercised and leaves the codebase clean)

**Research confirms**:
- Rollback for a skill file is `rm -rf core/skills/bugfix/` + reload — no database or service complexity
- Error scenarios for a skill are behavioral: empty input, unsupported format, no failures detected in pasted output
- The existing plan's automated criteria (`make test`, `make check`) are appropriate anchors for rollback verification
- Error scenario tests belong in both the new Phase 1.5 AND the overall success criteria

**Planned modifications**:
1. Insert new Phase 1.5 section after Phase 1 with: failure modes table, rollback procedure, validation gate, error scenario tests
2. Update `## Success Criteria (Overall)` to add: rollback verification check and behavioral error scenario tests

Proceeding with the update.

---

## Step 4: Plan Updates Made

### Change 1 — New Phase 1.5 inserted between Phase 1 and Phase 2

The new phase covers:

- **Scope statement**: Define and validate error handling for skill creation failures and rollback steps to restore a clean state if the skill causes problems
- **Failure modes documented**:
  - Malformed SKILL.md frontmatter (missing required fields)
  - Invalid `allowed-tools` values causing plugin load errors
  - Conflicting skill name with an existing skill
- **Rollback procedure** (3 steps):
  1. `rm -rf core/skills/bugfix/`
  2. `test ! -d core/skills/bugfix/`
  3. Restart Claude Code / `/reload-plugins`, then `make test`
- **Validation gate**: must confirm plugin loads without errors before proceeding to Phase 2
- **Success criteria** including:
  - Automated: `test ! -d core/skills/bugfix/` after rollback, `make test`, `make check`
  - Manual: intentionally introduce malformed frontmatter, verify error, execute rollback
  - Error scenario tests: empty input, binary file path, no test failures in pasted output

### Change 2 — Updated `## Success Criteria (Overall)`

Added two new sub-sections:
- Rollback automated check: `test ! -d core/skills/bugfix/` exits 0 after rollback
- **Error Scenario Tests** section listing four scenarios:
  - Empty input → clear usage message
  - Unrecognized format → "unsupported format" response
  - No failures detected → skill informs user rather than producing spurious diagnosis
  - Rollback coverage → `make test` passes and all pre-existing skills remain registered

---

## Step 5: Summary

I've updated the plan at `thoughts/shared/plans/2026-04-24-bugfix-skill.md`.

**Changes made**:
- Added Phase 1.5: Error Handling and Rollback Procedures (between Phase 1 and Phase 2)
- Updated overall Success Criteria to include rollback verification and error scenario tests

**The updated plan now**:
- Has an explicit safety gate before test assertion updates are written
- Documents realistic failure modes specific to skill-file creation (not over-engineered)
- Provides a simple, reversible rollback procedure appropriate for a pure markdown artifact
- Defines measurable behavioral error scenario tests (empty input, unsupported format, no-failure case)
- Maintains the two-category structure (Automated / Manual) for all success criteria

Would you like any further adjustments?

---

Plan updated: `thoughts/shared/plans/2026-04-24-bugfix-skill.md`

**Next steps in the workflow**:
- Review the updated plan
- Use `/stepwise-core:implement-plan thoughts/shared/plans/2026-04-24-bugfix-skill.md` to execute it
- Or use `/stepwise-core:iterate-plan thoughts/shared/plans/2026-04-24-bugfix-skill.md [more changes]` for further refinement

Tip: Use `/clear` to free up context before starting implementation
