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
- **Summary format**: after reviewing every comment, present all decisions together, one compact block per comment. Do NOT quote the full body verbatim — the user has GitHub open and can click through. Rephrase the claim in one sentence in your own words. Format:

  ```
  N. [ACCEPT|REJECT] {path}:{line or "general"} @{user} — {your one-sentence rephrase of the claim}
     Reason: {1-2 lines, technical}
     Fix: {concrete action you will take}          # only if ACCEPT
     Alternative: {what you propose instead}       # only if REJECT
     Link: {comment.html_url}
  ```

  Then ask: "Do you agree with these positions?"

  Exception: if a comment is genuinely short (<3 lines) and self-contained, quoting it verbatim is fine. The rule is "don't repeat information the user can read in one glance in GitHub".

- **Iteration**: the user may push back on any decision. Update your positions and re-present the full summary until the user confirms agreement.
- **Publishing**: once agreed, reply individually to each comment's thread (inline replies for inline comments, issue comment endpoint for general ones).
- **Language**: responses posted to GitHub are always in English, regardless of the comment's language.
