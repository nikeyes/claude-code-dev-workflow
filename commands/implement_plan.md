---
description: Implement technical plans from thoughts/shared/plans with verification
argument-hint: [plan-file-path]
model: sonnet
---

<!--
Based on HumanLayer project
Copyright (c) 2024, humanlayer Authors
Licensed under Apache License 2.0
Modified by: Jorge Castro
Modifications: Adapted for local-only operation with thoughts/ directory integration
-->

# Implement Plan

You are tasked with implementing an approved technical plan from `thoughts/shared/plans/`. These plans contain phases with specific changes and success criteria.

## Getting Started

When given a plan path:
- Read the plan completely and check for any existing checkmarks (- [x])
- Read the original ticket and all files mentioned in the plan
- **Read files fully** - never use limit/offset parameters, you need complete context
- Think deeply about how the pieces fit together
- Create a todo list to track your progress
- Start implementing if you understand what needs to be done

If no plan path provided, ask for one.

## Implementation Philosophy

Plans are carefully designed, but reality can be messy. Your job is to:
- Follow the plan's intent while adapting to what you find
- Implement each phase fully before moving to the next
- Verify your work makes sense in the broader codebase context
- Update checkboxes in the plan as you complete sections

When things don't match the plan exactly, think about why and communicate clearly. The plan is your guide, but your judgment matters too.

If you encounter a mismatch:
- STOP and think deeply about why the plan can't be followed
- Present the issue clearly:
  ```
  Issue in Phase [N]:
  Expected: [what the plan says]
  Found: [actual situation]
  Why this matters: [explanation]

  How should I proceed?
  ```

## Verification Approach

After implementing a phase:
- Run all automated success criteria checks (usually `make check test` covers everything)
- Fix any issues before proceeding
- Update your progress in both the plan and your todos
- Check off completed items in the plan file itself using Edit

**Pause for manual verification ONLY if the plan has a "Manual Verification" section:**
- If no manual verification → Continue to next phase immediately
- If manual verification exists → Pause and inform the human:
  ```
  Phase [N] Complete - Ready for Manual Verification

  Automated verification passed:
  - [List automated checks that passed]

  Please perform manual verification:
  - [List manual verification items from the plan]

  Let me know when complete so I can proceed to Phase [N+1].
  ```

If instructed to execute multiple phases consecutively, skip pauses until the last phase.

Do not check off manual verification items until the user confirms completion.


## If You Get Stuck

When something isn't working as expected:
- First, make sure you've read and understood all the relevant code
- Consider if the codebase has evolved since the plan was written
- Present the mismatch clearly and ask for guidance

Use sub-tasks sparingly - mainly for targeted debugging or exploring unfamiliar territory.

## Resuming Work

If the plan has existing checkmarks:
- Trust that completed work is done
- Pick up from the first unchecked item
- Verify previous work only if something seems off

Remember: You're implementing a solution, not just checking boxes. Keep the end goal in mind and maintain forward momentum.

## Completion

When all phases are complete:
1. **Run final verification**:
   ```bash
   make check test  # Or project-specific command
   ```

2. **Update the plan file**:
   - Ensure all checkboxes are marked
   - Note any deviations from the original plan

3. **Sync the plan**:
   ```bash
   thoughts-sync
   ```

4. **Inform the user**:
   ```
   ✓ Implementation complete for: [Plan Name]

   All phases implemented and verified:
   - [List key accomplishments]

   Next steps in the workflow:
   - Use `/validate_plan thoughts/shared/plans/[filename].md` to verify completeness
   - Use `/commit` to create git commits for the changes

   💡 Tip: Use `/clear` to free up context before validation
   ```
