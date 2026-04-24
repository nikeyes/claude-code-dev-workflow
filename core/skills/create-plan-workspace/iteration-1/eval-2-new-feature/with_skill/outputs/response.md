# Create Plan: Bugfix Skill

## Task Description

Add a new "bugfix" skill that helps users debug failing tests by analyzing test output and suggesting fixes.

---

## Step 1: Context Gathering & Initial Analysis

I read the task description (no ticket file provided) and researched the codebase to understand existing patterns before asking any questions.

### Research Findings

**Codebase structure** (`/Users/jorge.castro/mordor/personal/stepwise-dev`):
- 4 independent plugins: `core/`, `git/`, `web/`, `research/`
- All core skills live in `core/skills/<name>/SKILL.md` — auto-discovered by the plugin system
- No changes to `plugin.json` required when adding a new skill
- Structural test at `test/plugin-structure-test.sh:67-73` validates specific skill files exist; must be updated

**Existing related skills**:
- `core/skills/bugmagnet/SKILL.md` — discovers bugs via exploratory testing, **explicitly does NOT fix code** (line 158: "DO NOT IMPLEMENT FIXES OR CHANGE THE IMPLEMENTATION FILE")
- `core/skills/test-desiderata/SKILL.md` — analyzes test quality, does NOT run or fix tests
- No skill exists that takes failing test output and fixes the implementation

**Skill frontmatter pattern** (from `core/skills/research-codebase/SKILL.md:1-7`):
```yaml
---
name: <kebab-case>
description: <trigger phrases and use cases>
argument-hint: [description]
model: opus
disable-model-invocation: true
---
```

Heavy orchestration skills (create-plan, research-codebase) use `model: opus` + `disable-model-invocation: true`. Lighter interactive skills (story-splitting, hamburger-method) use `allowed-tools` restriction only.

**Available agents** that the new skill can leverage:
- `stepwise-core:codebase-locator` — finds files
- `stepwise-core:codebase-analyzer` — understands how code works

---

## Questions (proceeding with best judgment)

Before finalizing the plan, I have the following clarifying questions. Proceeding as if the user said "looks good, proceed with your best judgment":

**Q1: Should the skill use `model: opus` + `disable-model-invocation: true`?**
*Judgment*: Yes — diagnosing test failures requires deep code analysis, same as create-plan and research-codebase.

**Q2: Should it run test commands itself, or only accept pasted test output?**
*Judgment*: Both — accept a command as `$ARGUMENTS` and run it, OR accept pasted test output. This maximizes flexibility.

**Q3: Should it apply fixes, or only suggest them?**
*Judgment*: Suggest AND apply with user confirmation — the point of "bugfix" (vs "bugmagnet") is to fix. Always gate application behind explicit user approval.

---

## Step 2: Plan Structure

**Proposed Plan Structure:**

1. **Phase 1**: Create `core/skills/bugfix/SKILL.md` with the complete skill workflow
2. **Phase 2**: Update `test/plugin-structure-test.sh` to assert the new skill file exists

**Design approach:**
- The `bugfix` skill is a workflow document (pure Claude instructions), not a bash script
- Two phases only — minimal scope, clean separation
- Testing is automated (structural assertion) + manual (skill behavior in Claude Code)

---

## Detailed Implementation Plan

The full plan has been saved to:
`thoughts/shared/plans/2026-04-24-bugfix-skill.md`

### Summary of the Plan

#### Phase 1: Create the Bugfix Skill

**File**: `core/skills/bugfix/SKILL.md` (new file)

**Frontmatter**:
```yaml
---
name: bugfix
description: Debug failing tests by analyzing test output and suggesting fixes. Use when tests are failing and you need to diagnose root causes and apply fixes. Triggers on "bugfix", "fix failing tests", "tests are failing", "debug test failure", or when given test output with failures.
argument-hint: [test command or pasted test output]
model: opus
disable-model-invocation: true
---
```

**Workflow steps in the skill**:
1. Accept test command or pasted output from `$ARGUMENTS`; if empty, prompt user
2. Run command (if provided) and capture full output
3. Parse each failure: test name, location, expected vs actual, error message
4. For each failure: read test code fully, find and read implementation code, use `codebase-locator`/`codebase-analyzer` agents as needed
5. Diagnose root cause and present structured fix proposal (root cause, location, current code, proposed fix, confidence level)
6. Ask for confirmation before applying (all / none / specific fixes)
7. Apply approved fixes using Edit tool, re-run tests to verify
8. Report final summary: tests fixed, changes made, remaining failures (if any)

**Key guidelines baked into the skill**:
- Tests are the truth — assume implementation is wrong unless the test is clearly outdated
- Ask before modifying test code
- Always read files fully before diagnosing
- Apply fixes incrementally for complex cases
- Flag low-confidence diagnoses explicitly

**Success Criteria**:
- [ ] `core/skills/bugfix/SKILL.md` exists with valid frontmatter
- [ ] Frontmatter has: `name: bugfix`, `description`, `argument-hint`, `model: opus`, `disable-model-invocation: true`
- [ ] Skill workflow covers: input parsing, failure diagnosis, fix proposal, apply with confirmation, re-verify

---

#### Phase 2: Update Structural Test

**File**: `test/plugin-structure-test.sh` (modify)

**Change**: Add one line in the "stepwise-core plugin" test section (after line 73, alongside the existing skill assertions):
```bash
assert_file_exists "core/skills/bugfix/SKILL.md" "bugfix skill"
```

**Success Criteria**:
- [ ] `test/plugin-structure-test.sh` contains assertion for `core/skills/bugfix/SKILL.md`
- [ ] `make test` passes

---

### Testing Strategy

**Automated** (covers file existence):
```bash
make test   # runs plugin-structure-test.sh which asserts the skill file exists
make ci     # full CI: test + shellcheck + manifest validation
```

**Manual** (covers skill behavior — required since skills are Claude instructions):
1. In a project with failing tests: `/stepwise-core:bugfix make test`
2. Verify failure parsing, diagnosis format, and fix proposal structure
3. Approve a fix, verify tests pass after application
4. Test with pasted test output (no command argument)

---

## What We're NOT Doing

- Not creating a new plugin — belongs in existing `stepwise-core`
- Not modifying `bugmagnet` — different intent (discover vs fix)
- Not creating a specialized agent — existing `codebase-locator` and `codebase-analyzer` agents are sufficient
- Not auto-applying fixes without user confirmation
- Not handling compiler errors or runtime crashes — scope is test failures only

---

## Implementation Plan Location

`thoughts/shared/plans/2026-04-24-bugfix-skill.md`

Next steps in the workflow:
- Review and approve the plan
- Use `/stepwise-core:implement-plan thoughts/shared/plans/2026-04-24-bugfix-skill.md` to execute it
- Or use `/stepwise-core:iterate-plan thoughts/shared/plans/2026-04-24-bugfix-skill.md [changes]` to refine further

Tip: Use `/clear` to free up context before starting implementation
