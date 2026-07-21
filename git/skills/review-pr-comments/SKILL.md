---
name: review-pr-comments
description: Review PR comments rigorously, present a justified summary, then post agreed responses individually
model: opus
disable-model-invocation: true
allowed-tools: Bash(gh:*) Read Glob Grep
argument-hint: "[PR number (optional — auto-detected from current branch)]"
---

# Review PR Comments

Review all open PR comments, present a summary with your position on each, iterate with the user until agreed, then post responses individually to each comment.

## Rules

- **PR target**: if no PR number is given, auto-detect from the current branch. If none exists, ask.
- **Scope**: only active comments (both inline and general). Ignore resolved and outdated ones.
- **Bias**: defend the existing code. Only accept a change with a concrete technical reason (bug, violated principle, demonstrable readability gain). Reject style preferences without objective justification.
- **Context**: before evaluating, read the full files affected plus related files (tests, types, direct dependencies).
- **Summary format**: after reviewing every comment, present all decisions together in this format:

  ```
  Comment by @{user} on {path:line or "general"}:
  > {body}

  [ACCEPT] / [REJECT]
  Reason: {2-3 lines, technical}
  Alternative: {only if REJECT and you propose something}
  ```

  Then ask: "Do you agree with these positions?"

- **Iteration**: the user may push back on any decision. Update your positions and re-present the full summary until the user confirms agreement.
- **Publishing**: once agreed, reply individually to each comment's thread (inline replies for inline comments, issue comment endpoint for general ones).
- **Language**: responses posted to GitHub are always in English, regardless of the comment's language.
