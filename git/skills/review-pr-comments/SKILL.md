---
name: review-pr-comments
description: Review PR comments rigorously, present a justified summary, then post agreed responses individually
model: inherit
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
- **Summary format**: after reviewing every comment, present all decisions grouped by severity, one compact block per comment. Do NOT quote the full body verbatim — the user has GitHub open and can click through. Rephrase the claim in one sentence in your own words.

  Extract severity from the comment's prefix when present (`[SECURITY — CRITICAL]`, `[CODE QUALITY — HIGH]`, `[TESTS — LOW]`, `[SUGGESTION]`, etc.). If no prefix, infer: correctness/security bugs → HIGH; performance, tests, or missing error paths → MEDIUM; style, docstrings, naming, "for symmetry", "for consistency" nits → LOW.

  Block format per comment:

  ```
  N. [ACCEPT|REJECT] {path}:{line or "general"} @{user} — {your one-sentence rephrase of the claim}
     Reason: {1-2 lines, technical}
     Fix: {concrete action you will take}          # only if ACCEPT
     Alternative: {what you propose instead}       # only if REJECT
     Link: {comment.html_url}
  ```

  Present them in this order:

  ```
  HIGH — decision required:
    <blocks>

  MEDIUM — decision required:
    <blocks>

  LOW / nits — proposed REJECT in batch (unless you rescue any):
    <blocks, but with just the one-line rephrase + link; no Reason/Alternative>
  ```

  Then ask ONE question: **"Confirm my ACCEPT/REJECT on HIGH+MEDIUM and I discard the LOW batch — or do you want to rescue any LOW?"**

  Omit a section entirely if it has no comments. If ALL comments are LOW and every one would be REJECT, offer: "This round is all low-severity nits and rehashes of earlier positions. Close the round without replying?" — closing without a reply is a valid outcome when the original threads already carry your positions.

  Exception: if a comment is genuinely short (<3 lines) and self-contained, quoting it verbatim is fine. The rule is "don't repeat information the user can read in one glance in GitHub".

- **Iteration**: the user may push back on any decision. Update your positions and re-present the full summary until the user confirms agreement.
- **Publishing**: once agreed, reply individually to each comment's thread (inline replies for inline comments, issue comment endpoint for general ones).
- **Language**: responses posted to GitHub are always in English, regardless of the comment's language.
