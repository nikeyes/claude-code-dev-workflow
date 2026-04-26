# Research: Agents used by the create-plan skill

## Source Files

- Skill definition: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/create-plan/SKILL.md`
- Agent definitions: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/`

---

## Agents used by create-plan

The `create-plan` skill uses **5 agents**, all from the `stepwise-core` plugin:

| Agent | File | Model | Purpose |
|---|---|---|---|
| `stepwise-core:codebase-locator` | `core/agents/codebase-locator.md` | haiku | Locate files relevant to the ticket/task (Grep, Glob, LS only) |
| `stepwise-core:codebase-analyzer` | `core/agents/codebase-analyzer.md` | sonnet | Understand how the current implementation works (Read, Grep, Glob, LS) |
| `stepwise-core:codebase-pattern-finder` | `core/agents/codebase-pattern-finder.md` | sonnet | Find similar features/patterns that can be modeled after (Grep, Glob, Read, LS) |
| `stepwise-core:thoughts-locator` | `core/agents/thoughts-locator.md` | haiku | Find existing thoughts documents about the feature (Grep, Glob, LS only) |
| `stepwise-core:thoughts-analyzer` | `core/agents/thoughts-analyzer.md` | sonnet | Extract key insights from the most relevant thoughts documents (Read, Grep, Glob, LS) |

---

## Execution order and parallelism

### Step 1 — Initial context gathering (PARALLEL launch, Step 1 of the skill)

Defined in `SKILL.md` lines 59–68 under "Step 1: Context Gathering & Initial Analysis":

> "Before asking the user any questions, use specialized agents to research in parallel"

Three agents are launched **concurrently**:

1. `stepwise-core:codebase-locator` — find all files related to the ticket/task
2. `stepwise-core:codebase-analyzer` — understand how the current implementation works
3. `stepwise-core:thoughts-locator` — find any existing thoughts documents about the feature (conditional: "If relevant")

The skill explicitly states: "Wait for ALL sub-tasks to complete before proceeding" (line 132 / Step 2, point 3).

### Step 2 — Deep research (PARALLEL launch, Step 2 of the skill)

Defined in `SKILL.md` lines 113–132 under "Step 2: Research & Discovery", after user clarifications are received:

> "Spawn parallel sub-tasks for comprehensive research"

Up to **5 agents** can be launched concurrently at this stage (exact set depends on the ticket's needs):

1. `stepwise-core:codebase-locator` — find more specific files
2. `stepwise-core:codebase-analyzer` — understand implementation details
3. `stepwise-core:codebase-pattern-finder` — find similar features to model after
4. `stepwise-core:thoughts-locator` — find research/plans/decisions about this area
5. `stepwise-core:thoughts-analyzer` — extract key insights from the most relevant documents

The skill says: "Wait for ALL sub-tasks to complete" before synthesizing and presenting findings.

---

## Summary of execution flow

```
User invokes /create-plan
         |
         v
[Main context] Reads ticket/context files directly (no agents yet)
         |
         v
PARALLEL LAUNCH (Step 1):
  ├── codebase-locator    (find relevant files)
  ├── codebase-analyzer   (understand existing implementation)
  └── thoughts-locator    (find existing thoughts — if relevant)
         |
         v
[Wait for ALL to complete]
         |
         v
[Main context] Reads all identified files, presents understanding + focused questions
         |
         v
[Interactive: user provides clarifications]
         |
         v
PARALLEL LAUNCH (Step 2 — deep research):
  ├── codebase-locator       (find more specific files)
  ├── codebase-analyzer      (deeper implementation details)
  ├── codebase-pattern-finder (find patterns/examples)
  ├── thoughts-locator        (find historical context)
  └── thoughts-analyzer       (extract insights from key documents)
         |
         v
[Wait for ALL to complete]
         |
         v
[Interactive: present findings → agree on approach → write plan]
```

---

## Key observations

- **All agent launches within each step are parallel** — agents in Step 1 run concurrently, and agents in Step 2 run concurrently. There is a sequential dependency between the two steps (Step 2 starts after user clarification following Step 1).
- `codebase-locator` and `thoughts-locator` appear in **both** parallel phases; they are lighter agents (haiku, read-only grep/glob/ls) used for navigation.
- `codebase-analyzer`, `codebase-pattern-finder`, and `thoughts-analyzer` are heavier agents (sonnet, can read files) used for deeper analysis, primarily in Step 2.
- The `thoughts-locator` in Step 1 is conditional ("If relevant"), while in Step 2 it is listed as a standard option.
- `codebase-pattern-finder` and `thoughts-analyzer` are **only** introduced in Step 2, not in the initial Step 1 batch.
- The skill enforces a "wait for all" barrier after each parallel batch before proceeding.
