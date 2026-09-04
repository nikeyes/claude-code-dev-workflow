---
name: research-codebase
description: Document codebase as-is with thoughts directory for historical context
argument-hint: [research question or topic]
model: inherit
disable-model-invocation: true
---

<!-- SPDX-License-Identifier: Apache-2.0
     SPDX-FileCopyrightText: 2024 humanlayer Authors (original)
     SPDX-FileCopyrightText: 2025 Jorge Castro (modifications) -->

# Research Codebase

You are tasked with researching the codebase to answer user questions. Your only job is to document and explain the codebase as it exists today — never suggest improvements, critique the implementation, or recommend changes unless the user explicitly asks.

## Input

**Research Query**: $ARGUMENTS

- If $ARGUMENTS is empty, ask the user for their research question and wait.
- If $ARGUMENTS is vague or ambiguous (e.g., "investigate tests", "look at the code"), ask the user to clarify scope before proceeding. A good research question names a specific component, flow, or concept.
- If $ARGUMENTS is clear, proceed directly.

## How to research

1. **Read mentioned files first.** If the user references specific files, read them fully in your main context before doing anything else.

2. **Investigate the question.** Use whatever approach makes sense — read files directly, spawn sub-agents for parallel research, or both. The specialized agents available to you are:
   - **stepwise-core:codebase-locator** — finds WHERE files and components live
   - **stepwise-core:codebase-analyzer** — understands HOW specific code works
   - **stepwise-core:codebase-pattern-finder** — finds examples of existing patterns with code
   - **stepwise-core:thoughts-locator** — discovers relevant documents in thoughts/
   - **stepwise-core:thoughts-analyzer** — extracts key insights from thoughts/ documents
   - **stepwise-web:web-search-researcher** — web research (only if user explicitly asks)

   When the question spans multiple components, spawn agents in parallel for efficiency.

3. **Synthesize findings.** Prioritize live codebase findings over historical thoughts/ documents. Include specific file paths and line numbers.

## Save the research document

1. If `thoughts/` doesn't exist, initialize it:
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init
   ```

2. Gather metadata:
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
   ```

3. Write the document to `thoughts/shared/research/YYYY-MM-DD-description.md` (add `ENG-XXXX-` after the date if there's a ticket number). Use this structure:

   ```markdown
   ---
   date: [ISO datetime from metadata]
   researcher: [name from metadata]
   git_commit: [commit hash from metadata]
   branch: [branch from metadata]
   repository: [repo name from metadata]
   topic: "[user's question]"
   tags: [research, codebase, relevant-component-names]
   status: complete
   last_updated: [YYYY-MM-DD]
   last_updated_by: [researcher name]
   ---

   # Research: [Topic]

   ## Research Question
   ## Summary
   ## Detailed Findings
   ## Code References
   ## Architecture Documentation
   ## Historical Context (from thoughts/)
   ## Related Research
   ## Open Questions
   ```

4. Present a concise summary to the user with the document path and suggest `/stepwise-core:create-plan` as a next step if applicable.

## Follow-up questions

Append to the same document. Update `last_updated` and `last_updated_by` in the frontmatter and add a `## Follow-up Research [timestamp]` section.
