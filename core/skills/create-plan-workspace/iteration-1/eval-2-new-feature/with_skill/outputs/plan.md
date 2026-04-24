# Bugfix Skill Implementation Plan

## Overview

Add a new `bugfix` skill to the stepwise-core plugin that helps users debug failing tests by analyzing test output and suggesting (and optionally applying) fixes. This skill bridges the gap between the existing `bugmagnet` skill (which discovers bugs via exploratory testing) and the `implement-plan` skill (which applies pre-planned changes): it diagnoses failing tests from their output and proposes targeted code fixes.

## Current State Analysis

### Existing Skill Inventory (core/skills/):
- `bugmagnet` — explores test coverage gaps and documents bugs, explicitly does NOT fix them
- `test-desiderata` — analyzes test code quality, does NOT run or fix tests
- `research-codebase` — documents codebase as-is, does NOT fix anything
- `create-plan` / `implement-plan` / `validate-plan` — workflow orchestration skills

### Key Discoveries:
- All skills in `core/skills/<name>/SKILL.md` are automatically registered in the stepwise-core plugin (`core/.claude-plugin/plugin.json:1`)
- No `plugin.json` changes are required to add a new skill — the plugin system auto-discovers skills from the `skills/` directory
- Frontmatter fields used by skills: `name`, `description`, `model`, `disable-model-invocation`, `allowed-tools`, `argument-hint` (`core/skills/research-codebase/SKILL.md:1-7`)
- Heavy orchestration skills use `model: opus` + `disable-model-invocation: true` (create-plan, research-codebase); lighter interactive skills use `allowed-tools` to restrict tool access (small-safe-steps, hamburger-method, story-splitting)
- Structural test (`test/plugin-structure-test.sh:67-91`) validates specific skill files exist; the new skill must be added to that test
- `bugmagnet` explicitly states "DO NOT IMPLEMENT FIXES OR CHANGE THE IMPLEMENTATION FILE, ONLY WRITE TESTS" (`core/skills/bugmagnet/SKILL.md:158`) — the new `bugfix` skill has the opposite intent

### What Does NOT Exist:
- No skill exists that takes failing test output as input and diagnoses + fixes the underlying code
- No agent exists specialized in test failure root cause analysis

## Desired End State

A new `bugfix` skill at `core/skills/bugfix/SKILL.md` that:
1. Accepts test output (or a test command) as its argument
2. Parses the failure output to identify failing tests and error messages
3. Reads the failing test code and the implementation code under test
4. Diagnoses root cause of each failure
5. Proposes concrete code fixes with diffs/snippets
6. Optionally applies fixes (with user confirmation) and re-runs tests to verify

### Verification:
- `make test` passes after adding the new skill
- The skill file appears in `core/skills/bugfix/SKILL.md`
- The structural test is updated to assert the new file exists

### Key Discoveries:
- `core/skills/bugmagnet/SKILL.md:158` — reference for boundary with bugmagnet
- `core/skills/research-codebase/SKILL.md:1-7` — frontmatter pattern to follow
- `test/plugin-structure-test.sh:67-91` — where to add the structural test assertion
- `Makefile:11` — `make test` runs both test scripts

## What We're NOT Doing

- NOT creating a new plugin — the skill belongs in the existing `stepwise-core` plugin
- NOT creating supporting bash scripts — the skill workflow is pure Claude instructions (no scripts needed like thoughts-management has)
- NOT modifying `bugmagnet` — the two skills have different purposes (discover vs fix)
- NOT creating a specialized agent — the skill can use the existing `codebase-analyzer` and `codebase-locator` agents
- NOT auto-applying fixes without user confirmation — always show the fix and ask
- NOT handling compiler errors or runtime crashes (out of scope — focus on test failures)

## Implementation Approach

The `bugfix` skill follows the same pattern as `bugmagnet` but with inverted purpose: instead of writing tests to discover bugs, it reads test failures to diagnose bugs and fix the implementation. The workflow is:

1. Accept test output or a test run command as `$ARGUMENTS`
2. If a command is provided, run it and capture output; if output text is provided, parse it directly
3. Identify each failing test: test name, assertion failure, actual vs expected
4. For each failure: read the test code, read the implementation, diagnose root cause
5. Present a diagnosis with proposed fix (diff/snippet) for each failure
6. Ask user confirmation before applying any fix
7. After applying fixes, re-run the test suite to verify

## Phase 1: Create the Bugfix Skill

### Overview
Create `core/skills/bugfix/SKILL.md` with the complete workflow for diagnosing and fixing failing tests.

### Changes Required:

#### 1. New Skill File
**File**: `core/skills/bugfix/SKILL.md`
**Changes**: Create new file with standard frontmatter and full workflow

```markdown
---
name: bugfix
description: Debug failing tests by analyzing test output and suggesting fixes. Use when tests are failing and you need to diagnose root causes and apply fixes. Triggers on "bugfix", "fix failing tests", "tests are failing", "debug test failure", or when given test output with failures.
argument-hint: [test command or pasted test output]
model: opus
disable-model-invocation: true
---

# Bugfix - Debug Failing Tests

You are tasked with diagnosing failing tests and proposing (and optionally applying) fixes to the implementation code.

## Complementary Skills

This skill is intentionally different from related skills:
- **bugmagnet**: Discovers bugs by writing new tests — does NOT fix code
- **test-desiderata**: Analyzes test quality — does NOT run or fix tests
- **bugfix** (THIS SKILL): Diagnoses failing tests and fixes the implementation

## Initial Response

**Input**: $ARGUMENTS

1. **If $ARGUMENTS contains a test command** (e.g., `make test`, `pytest tests/`, `npm test`):
   - Run the command and capture output
   - Proceed to diagnosis

2. **If $ARGUMENTS contains pasted test output** (contains failure markers):
   - Parse the output directly
   - Proceed to diagnosis

3. **If $ARGUMENTS is empty**, respond with:
   ```
   I'll help you debug failing tests. Please provide either:
   1. A test command to run: e.g., `make test`, `pytest tests/foo.py`, `npm test`
   2. Paste the test output directly with the failures

   I'll analyze the failures, diagnose root causes, and propose fixes.

   Examples:
   - `/stepwise-core:bugfix make test`
   - `/stepwise-core:bugfix pytest tests/test_calculator.py -v`
   ```
   Then wait for input.

## Workflow

### Step 1: Collect Test Output

If a command was provided, run it:
```bash
<test command from $ARGUMENTS>
```

Capture the full output including:
- Which tests failed (test names)
- Assertion errors (expected vs actual)
- Stack traces or error messages
- Exit code

### Step 2: Parse Failures

For each failing test, extract:
- **Test name and location** (file:line)
- **Failure type**: assertion error, exception, timeout, etc.
- **Expected value** (what the test expected)
- **Actual value** (what the code produced)
- **Error message** (full message with context)

Present a summary:
```
Found X failing test(s):

1. `test_name` in `test_file.py:42`
   - Expected: <value>
   - Actual: <value>
   - Error: <message>

2. ...

I'll now diagnose each failure.
```

### Step 3: Diagnose Each Failure

For each failing test:

1. **Read the test code fully** — understand what behavior is being tested
2. **Identify the implementation under test** — find the function/class/module being called
3. **Read the implementation code fully** — trace the logic
4. **Use codebase agents if needed**:
   - Use **stepwise-core:codebase-locator** to find files if they're not obvious from the test
   - Use **stepwise-core:codebase-analyzer** to understand how the relevant code works

4. **Diagnose the root cause**:
   - What is the code actually doing vs. what the test expects?
   - Is this a logic bug, off-by-one error, missing condition, wrong variable, etc.?
   - Is the test correct and the implementation wrong, or is the test expectation outdated?

### Step 4: Propose Fixes

For each diagnosed failure, present:

```
### Failure 1: `test_name`

**Root Cause**: [Clear 1-2 sentence explanation]

**Location**: `path/to/implementation.py:42`

**Current Code**:
```[language]
[current broken code snippet]
```

**Proposed Fix**:
```[language]
[corrected code snippet]
```

**Why this fixes it**: [Brief explanation of how the fix addresses the root cause]

**Confidence**: High / Medium / Low
- High: Clear logic error with obvious fix
- Medium: Likely cause but may have edge effects
- Low: Uncertain root cause, needs investigation
```

After presenting all fixes, ask:
```
Shall I apply these fixes?
- [y] Apply all fixes
- [n] Don't apply any fixes (review manually)
- [1,3] Apply only fixes 1 and 3

Or let me know if any diagnosis seems wrong and I'll investigate further.
```

### Step 5: Apply Fixes (with confirmation)

After user confirmation:

1. **Apply each approved fix** using the Edit tool
2. **Re-run the test suite**:
   ```bash
   <original test command>
   ```
3. **Report results**:
   - If all fixed tests now pass: "All X fixed tests are now passing."
   - If some still fail: Re-diagnose the remaining failures
   - If new failures appeared: Alert the user and diagnose them

### Step 6: Verify and Summarize

Once tests pass:

```
## Fix Summary

**Tests fixed**: X/Y
**Tests still failing**: Z (if any)

**Changes made**:
1. `path/to/file.py:42` — [Brief description of change]
2. ...

**Remaining failures** (if any):
- `test_name`: [Reason why it wasn't fixed and recommendation]
```

## Important Guidelines

1. **Tests are the truth**: If a test is well-named and logically correct, assume the implementation is wrong (not the test)
2. **Ask before changing tests**: If you believe the test expectation itself is wrong, explain why and ask for confirmation before modifying test code
3. **One fix at a time**: Apply fixes incrementally and re-verify rather than applying all at once for complex cases
4. **Preserve existing behavior**: Fixes must not break currently-passing tests
5. **Be explicit about confidence**: Low-confidence diagnoses should be flagged clearly
6. **Don't over-engineer**: The simplest fix that makes the test pass is usually correct
7. **Read fully**: Always read implementation files completely before diagnosing (no partial reads)
```

### Success Criteria:
- [ ] `core/skills/bugfix/SKILL.md` exists with valid frontmatter
- [ ] Frontmatter has: `name: bugfix`, `description`, `argument-hint`, `model: opus`, `disable-model-invocation: true`
- [ ] Skill workflow covers: input parsing, failure diagnosis, fix proposal, apply with confirmation, re-verify

---

## Phase 2: Update Structural Test

### Overview
Add an assertion to `test/plugin-structure-test.sh` so the CI validates the new skill file exists.

### Changes Required:

#### 1. test/plugin-structure-test.sh
**File**: `test/plugin-structure-test.sh`
**Changes**: Add one assertion in the "stepwise-core plugin" test section (after line 71 where other skills are validated)

```bash
assert_file_exists "core/skills/bugfix/SKILL.md" "bugfix skill"
```

This follows the exact same pattern as the existing skill assertions at `test/plugin-structure-test.sh:67-73`.

### Success Criteria:
- [ ] `test/plugin-structure-test.sh` contains assertion for `core/skills/bugfix/SKILL.md`
- [ ] `make test` passes: all structural tests pass including the new assertion

---

## Testing Strategy

### Automated Tests:
```bash
make test
```
This runs both `test/thoughts-structure-test.sh` and `test/plugin-structure-test.sh`. The structural test will assert the new skill file exists.

```bash
make ci
```
Full CI validation including shellcheck and manifest validation.

### Manual Testing (skill behavior):
Since skills are Claude instructions (not bash code), automated testing only covers file existence. Behavioral testing is manual:

1. In a project with failing tests, invoke:
   `/stepwise-core:bugfix make test`
2. Verify the skill runs the command, parses failures, and presents diagnoses
3. Confirm the fix proposal format is clear (root cause, location, current code, proposed fix)
4. Approve a fix and verify the test passes after application
5. Test with pasted test output (no command) to verify argument parsing

## Performance Considerations

No performance implications — this is a new SKILL.md file only. No bash scripts, no database changes, no API changes.

## Migration Notes

No migration needed. The skill is purely additive.

## References

- Similar skill (discovery focus): `core/skills/bugmagnet/SKILL.md`
- Similar skill (analysis focus): `core/skills/test-desiderata/SKILL.md`
- Orchestration skill pattern: `core/skills/research-codebase/SKILL.md:1-7`
- Structural test to update: `test/plugin-structure-test.sh:67-73`
- Available agents: `core/agents/codebase-locator.md`, `core/agents/codebase-analyzer.md`
