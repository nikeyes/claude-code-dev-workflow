---
name: commit
description: Create git commits with user approval, semantic commit format, and no Claude attribution
model: sonnet
disable-model-invocation: true
allowed-tools: Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git add:*) Bash(git commit:*)
---

<!-- SPDX-License-Identifier: Apache-2.0
     SPDX-FileCopyrightText: 2024 humanlayer Authors (original)
     SPDX-FileCopyrightText: 2025 Jorge Castro (modifications) -->

# Commit Changes

Create git commit(s) for the changes in this session. Present a plan first, then commit only after the user confirms.

## Rules

- **Format**: `TYPE([SCOPE])[!]: description` (e.g. `feat(kyc): add disapproval reason to kyc mail`)
  - **Types**: `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `docs`, `build`, `ops`, `chore`, `revert`, `reapply`
  - **Scope**: optional, contextual (never a ticket id)
  - **Breaking change**: `!` before `:`, or a `BREAKING CHANGES:` footer
  - **Description**: imperative present tense, lowercase, no trailing period
  - **Body/footer**: optional; use to explain motivation and contrast with previous behavior
- **Splitting**: group related changes; multiple commits if the changes have distinct purposes
- **Staging**: `git add` specific files only — never `-A` or `.`
- **Never include**: ticket identifiers (Jira, Linear, etc.), Claude attribution, `Co-Authored-By` lines
- **Confirmation**: show the plan (files + messages) and ask before running `git commit`
