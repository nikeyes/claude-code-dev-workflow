# Research: Agents used by create-plan, execution order, and parallelism

## Source file

`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/create-plan/SKILL.md`

---

## Summary

The `create-plan` skill uses up to **5 specialized agents**, distributed across two workflow phases. The first batch is launched in parallel during initial context gathering, and the second batch is also launched in parallel during deeper investigation. The two batches run sequentially (batch 2 only starts after clarification from the user).

---

## Phase 1 — Step 1: Initial research (parallel)

**Trigger**: Immediately after reading ticket/task files, before asking the user any questions.

**Reference**: `SKILL.md` lines 59-69 (Step 1, sub-step 2):
> "Before asking the user any questions, use specialized agents to research in parallel"

Agents launched **concurrently**:

| Agent | Plugin | Purpose |
|---|---|---|
| `codebase-locator` | `stepwise-core` | Find all files related to the ticket/task |
| `codebase-analyzer` | `stepwise-core` | Understand how the current implementation works |
| `thoughts-locator` | `stepwise-core` | Find any existing thoughts documents about the feature (conditional: "If relevant") |

After this parallel batch completes, the skill reads all identified files and presents findings + focused questions to the user.

---

## Phase 2 — Step 2: Deeper investigation (parallel)

**Trigger**: After the user provides initial clarifications (post-interaction).

**Reference**: `SKILL.md` lines 116-129 (Step 2, sub-step 3):
> "Spawn parallel sub-tasks for comprehensive research"

Agents launched **concurrently**:

| Agent | Plugin | Purpose |
|---|---|---|
| `codebase-locator` | `stepwise-core` | Find more specific files for a targeted component |
| `codebase-analyzer` | `stepwise-core` | Understand implementation details in depth |
| `codebase-pattern-finder` | `stepwise-core` | Find similar features that can be modeled after |
| `thoughts-locator` | `stepwise-core` | Find research, plans, or decisions about this area |
| `thoughts-analyzer` | `stepwise-core` | Extract key insights from the most relevant documents |

All 5 agents can be spawned concurrently. The skill explicitly states: **"Wait for ALL sub-tasks to complete" before proceeding** (`SKILL.md` line 132).

---

## Complete list of agents (5 total)

| Agent | File | Model | Tools | Role |
|---|---|---|---|---|
| `codebase-locator` | `core/agents/codebase-locator.md` | haiku | Grep, Glob, LS | Locates files and directories by topic |
| `codebase-analyzer` | `core/agents/codebase-analyzer.md` | sonnet | Read, Grep, Glob, LS | Analyzes implementation details and data flow |
| `codebase-pattern-finder` | `core/agents/codebase-pattern-finder.md` | sonnet | Grep, Glob, Read, LS | Finds similar implementations and code patterns |
| `thoughts-locator` | `core/agents/thoughts-locator.md` | haiku | Grep, Glob, LS | Discovers documents in the `thoughts/` directory |
| `thoughts-analyzer` | `core/agents/thoughts-analyzer.md` | sonnet | Read, Grep, Glob, LS | Extracts high-value insights from thoughts documents |

---

## Execution order diagram

```
[User invokes /create-plan with ticket/task]
         |
         v
[Skill reads ticket file(s) fully in main context]
         |
         v
[BATCH 1 — Parallel]
  ┌─────────────────────┐
  │ codebase-locator    │
  │ codebase-analyzer   │ ← all 3 launched concurrently
  │ thoughts-locator *  │
  └─────────────────────┘
         |  (wait for all)
         v
[Skill reads all files identified, presents summary + questions to user]
         |
         v
[User answers clarification questions]
         |
         v
[BATCH 2 — Parallel]
  ┌──────────────────────────┐
  │ codebase-locator         │
  │ codebase-analyzer        │ ← all 5 launched concurrently
  │ codebase-pattern-finder  │
  │ thoughts-locator         │
  │ thoughts-analyzer        │
  └──────────────────────────┘
         |  (wait for all)
         v
[Skill presents design options, plan structure, and writes final plan]
```

*`thoughts-locator` in batch 1 is conditional ("If relevant").

---

## Key observations

1. **Two parallel batches, not one**: The skill separates initial orientation research (batch 1) from deep investigation research (batch 2). They are separated by a user interaction checkpoint.
2. **`codebase-locator` and `codebase-analyzer` appear in both batches**: They serve different scopes — batch 1 is broad orientation, batch 2 is targeted deep-dive.
3. **`codebase-pattern-finder` and `thoughts-analyzer` only appear in batch 2**: These are reserved for the deeper investigation phase when specific areas have been confirmed.
4. **Explicit wait semantics**: The skill instructions explicitly require waiting for ALL sub-tasks before synthesizing results (`SKILL.md` lines 132, 443-446).
5. **User interaction between batches**: The workflow is interactive by design — the user must confirm understanding before batch 2 is spawned.
