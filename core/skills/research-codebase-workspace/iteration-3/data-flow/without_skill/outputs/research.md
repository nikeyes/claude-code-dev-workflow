---
date: 2026-04-26T00:00:00+0000
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "¿Cómo fluyen los datos desde que un usuario invoca /research-codebase hasta que se genera el documento final en thoughts/?"
tags: [research, codebase, research-codebase, data-flow, thoughts, agents, skills]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Data Flow from /research-codebase to thoughts/ document

## Research Question

How does data flow from the moment a user invokes `/research-codebase` until the final document is generated in `thoughts/`? What are all the components involved?

## Summary

The `/research-codebase` skill is a Claude Code plugin skill that orchestrates a multi-step data flow: it receives a user query, optionally spawns up to 5 specialized sub-agents in parallel to explore the codebase and/or historical documents, synthesizes their findings, and then uses two bash scripts (`thoughts-init` and `thoughts-metadata`) to initialize the storage directory and collect git metadata before writing a structured markdown document into `thoughts/shared/research/`.

The entire flow is defined declaratively in markdown files — no compiled code exists. The skill SKILL.md provides instructions to Claude Code, which interprets and executes them as an LLM agent.

## Detailed Findings

### Phase 1: Invocation and Input Processing

**Entry point**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/research-codebase/SKILL.md`

The skill is registered as `research-codebase` within the `stepwise-core` plugin (defined at `/Users/jorge.castro/mordor/personal/stepwise-dev/core/.claude-plugin/plugin.json`). The plugin marketplace configuration is at `/Users/jorge.castro/mordor/personal/stepwise-dev/.claude-plugin/marketplace.json`.

Key frontmatter directives in the SKILL.md:
- `model: sonnet` — Claude Sonnet is used
- `disable-model-invocation: true` — This prevents the model from running independently; it only runs when explicitly invoked via the slash command
- `argument-hint: [research question or topic]` — Declares what arguments are expected

**Input validation logic** (SKILL.md lines 19-23):
- If `$ARGUMENTS` is empty → ask the user and wait
- If `$ARGUMENTS` is vague/ambiguous → ask user to clarify scope before proceeding
- If `$ARGUMENTS` is clear → proceed directly

The user's query is injected as `$ARGUMENTS` which becomes the "Research Query" driving the entire workflow.

### Phase 2: Research Execution via Sub-Agents

**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/research-codebase/SKILL.md` (lines 28-40)

The skill instructs Claude to "investigate the question" using one or more approaches:
1. Read files directly in the main context
2. Spawn specialized sub-agents in parallel via the `Task` tool

The 5 specialized sub-agents available to the skill are:

#### Sub-Agent 1: codebase-locator
**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-locator.md`
- **Model**: haiku (lighter, faster)
- **Tools**: Grep, Glob, LS (read-only navigation)
- **Role**: Finds WHERE files and components live — acts as a "Super Grep/Glob/LS" tool
- **Output format**: Structured list of file locations grouped by purpose (Implementation, Test, Config, Type Definitions, Related Directories)

#### Sub-Agent 2: codebase-analyzer
**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-analyzer.md`
- **Model**: sonnet (more capable, needed for deep analysis)
- **Tools**: Read, Grep, Glob, LS
- **Role**: Understands HOW specific code works — traces data flow, analyzes implementation details with file:line references
- **Output format**: Structured analysis with Entry Points, Core Implementation steps with line refs, Data Flow sequence, Key Patterns

#### Sub-Agent 3: codebase-pattern-finder
**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-pattern-finder.md`
- **Model**: sonnet
- **Tools**: Grep, Glob, Read, LS
- **Role**: Finds existing patterns and usage examples with concrete code snippets
- **Output format**: Pattern catalog with code examples and file:line references

#### Sub-Agent 4: thoughts-locator
**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/thoughts-locator.md`
- **Model**: haiku (lighter, only does location, not deep reading)
- **Tools**: Grep, Glob, LS
- **Role**: Discovers relevant documents in the `thoughts/` directory — finds historical context (tickets, research docs, plans, PRs, notes)
- **Output format**: Document list grouped by type (Tickets, Research, Plans, Discussions, PRs)

#### Sub-Agent 5: thoughts-analyzer
**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/thoughts-analyzer.md`
- **Model**: sonnet
- **Tools**: Read, Grep, Glob, LS
- **Role**: Deep-reads thoughts/ documents to extract high-value insights, decisions, constraints, and actionable information
- **Output format**: Analysis with Document Context, Key Decisions, Critical Constraints, Technical Specifications, Actionable Insights, Still Open/Unclear

#### Sub-Agent 6: web-search-researcher (optional)
**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/web/agents/web-search-researcher.md`
- **Plugin**: stepwise-web (separate plugin)
- **Model**: sonnet
- **Tools**: WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS
- **Role**: Web research for external context — only spawned if the user explicitly asks for web research

**Parallel execution**: The skill instructs Claude to "spawn agents in parallel for efficiency" when the question spans multiple components (SKILL.md line 37).

**Synthesis rule** (SKILL.md line 39): Live codebase findings take priority over historical `thoughts/` documents.

### Phase 3: Directory Initialization

**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/thoughts-management/scripts/thoughts-init`

After completing research, the skill checks if `thoughts/` exists. If not, it runs:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init
```

**What thoughts-init does** (lines 37-79):
1. Reads `THOUGHTS_USER` env var (defaults to `nikey_es`)
2. Creates directory tree:
   - `thoughts/{username}/tickets/`
   - `thoughts/{username}/notes/`
   - `thoughts/shared/research/`
   - `thoughts/shared/plans/`
   - `thoughts/shared/prs/`
3. Creates `thoughts/README.md` (only if it doesn't exist) with usage instructions

The script is idempotent: if `thoughts/` already exists it warns and re-initializes while preserving existing files.

### Phase 4: Metadata Collection

**File**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/thoughts-management/scripts/thoughts-metadata`

The skill runs:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
```

**What thoughts-metadata produces** (lines 20-51):
- `Current Date/Time (TZ)` — human-readable with timezone
- `ISO DateTime` — for YAML frontmatter `date:` field
- `Date Short` — YYYY-MM-DD for filename
- `Current Git Commit Hash` — from `git rev-parse HEAD`
- `Current Branch Name` — from `git branch --show-current`
- `Repository Name` — from `basename $(git rev-parse --show-toplevel)`
- `Git User` — from `git config user.name`
- `Git Email` — from `git config user.email`
- `Timestamp For Filename` — YYYY-MM-DD_HH-MM-SS for unique filenames

All git values have fallbacks (`no-commit`, `no-branch`, `no-repo`, `unknown`) if not inside a git repository.

### Phase 5: Document Generation and Persistence

**Defined in**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/research-codebase/SKILL.md` (lines 52-81)

Using the collected metadata, Claude writes the document to:
```
thoughts/shared/research/YYYY-MM-DD-description.md
```
With optional ticket prefix: `YYYY-MM-DD-ENG-XXXX-description.md`

**Document structure** (SKILL.md lines 54-79):
```yaml
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
```

With sections:
- `## Research Question`
- `## Summary`
- `## Detailed Findings`
- `## Code References`
- `## Architecture Documentation`
- `## Historical Context (from thoughts/)`
- `## Related Research`
- `## Open Questions`

### Phase 6: Post-Generation

After writing the document, the skill:
1. Presents a concise summary to the user
2. Includes the document path
3. Suggests `/stepwise-core:create-plan` as a next step if applicable (SKILL.md line 81)

### Follow-up Research

If the user asks follow-up questions, the skill appends to the same document (SKILL.md lines 83-85):
- Updates `last_updated` and `last_updated_by` frontmatter
- Adds a new `## Follow-up Research [timestamp]` section

## Code References

| Component | File Path | Role |
|-----------|-----------|------|
| Skill entrypoint | `core/skills/research-codebase/SKILL.md` | Main orchestration instructions |
| Plugin config | `core/.claude-plugin/plugin.json` | Plugin registration (stepwise-core v1.0.1) |
| Marketplace config | `.claude-plugin/marketplace.json` | Multi-plugin marketplace listing |
| Directory init script | `core/skills/thoughts-management/scripts/thoughts-init` | Creates thoughts/ structure |
| Metadata script | `core/skills/thoughts-management/scripts/thoughts-metadata` | Collects git/date metadata |
| thoughts-management skill | `core/skills/thoughts-management/SKILL.md` | Skill that wraps the two scripts |
| Agent: codebase-locator | `core/agents/codebase-locator.md` | File/directory location (haiku) |
| Agent: codebase-analyzer | `core/agents/codebase-analyzer.md` | Code implementation analysis (sonnet) |
| Agent: codebase-pattern-finder | `core/agents/codebase-pattern-finder.md` | Pattern/example discovery (sonnet) |
| Agent: thoughts-locator | `core/agents/thoughts-locator.md` | thoughts/ document discovery (haiku) |
| Agent: thoughts-analyzer | `core/agents/thoughts-analyzer.md` | thoughts/ document deep analysis (sonnet) |
| Agent: web-search-researcher | `web/agents/web-search-researcher.md` | Optional web research (sonnet, stepwise-web plugin) |

## Architecture Documentation

### Complete Data Flow Diagram

```
User types: /research-codebase <query>
        │
        ▼
Claude Code loads SKILL.md
(core/skills/research-codebase/SKILL.md)
        │
        ├─► [Input validation]
        │      - Empty? → Ask user
        │      - Vague? → Ask to clarify
        │      - Clear? → Proceed
        │
        ▼
[Research Phase] ─── Parallel sub-agents via Task tool ──────────────────┐
        │                                                                  │
        │   ┌────────────────────────────────────────────────────────┐   │
        │   │ codebase-locator (haiku)   → WHERE files live          │   │
        │   │ codebase-analyzer (sonnet) → HOW code works            │   │
        │   │ codebase-pattern-finder (sonnet) → Pattern examples    │   │
        │   │ thoughts-locator (haiku)   → Historical docs in thoughts/│  │
        │   │ thoughts-analyzer (sonnet) → Deep insights from thoughts/│  │
        │   │ web-search-researcher (sonnet) [OPTIONAL, explicit only]│  │
        │   └────────────────────────────────────────────────────────┘   │
        │                                                                  │
        ◄──────────────────────────────────────────────────────────────────┘
        │
        ▼
[Synthesis] — Prioritize live codebase > historical thoughts/
        │
        ▼
[thoughts/ initialization]
bash thoughts-init script
→ Creates thoughts/{username}/tickets/
→ Creates thoughts/{username}/notes/
→ Creates thoughts/shared/research/
→ Creates thoughts/shared/plans/
→ Creates thoughts/shared/prs/
→ Creates thoughts/README.md (if not exists)
        │
        ▼
[Metadata collection]
bash thoughts-metadata script
→ Reads: date, git commit, branch, repo name, git user
→ Outputs: key-value pairs in stdout
        │
        ▼
[Document writing]
Claude writes structured markdown to:
thoughts/shared/research/YYYY-MM-DD-<description>.md
with YAML frontmatter + standard sections
        │
        ▼
[Post-generation]
→ Present summary to user
→ Include document path
→ Suggest /stepwise-core:create-plan if relevant
```

### Key Design Characteristics

1. **Declarative orchestration**: All logic is expressed as natural language instructions to Claude in markdown files. There is no imperative code orchestrating the flow — Claude interprets and executes it.

2. **Plugin isolation**: The skill resides in `stepwise-core`; the web agent resides in `stepwise-web`. They are separate Claude Code plugins that must be installed independently.

3. **Model tiering**: Locator agents (find, not analyze) use haiku for speed/cost efficiency; analyzer agents (deep reading, synthesis) use sonnet.

4. **Tool access scoping**: Each agent declares only the tools it needs — `codebase-locator` gets only `Grep, Glob, LS` while `codebase-analyzer` additionally gets `Read`.

5. **`disable-model-invocation: true`**: This frontmatter directive on the skill means the model cannot invoke itself autonomously — it only runs when a user explicitly types the slash command.

6. **`$CLAUDE_PLUGIN_ROOT` variable**: The bash scripts are referenced using this environment variable, which Claude Code sets to the installed plugin's root directory at runtime.

7. **Idempotent initialization**: Running `thoughts-init` multiple times is safe; it warns about existing directories but preserves files.

8. **Synthesis priority rule**: Live codebase information always takes precedence over historical thoughts/ documents (SKILL.md line 39).

## Historical Context (from thoughts/)

No relevant prior research documents were found in thoughts/ for this specific data flow topic.

## Related Research

- The same `thoughts-init` and `thoughts-metadata` scripts are also used by `create-plan` and `implement-plan` skills (referenced in `thoughts-management/SKILL.md` line 139-141).
- The `thoughts-management` SKILL.md serves as documentation for when and how to use the two bash scripts directly.

## Open Questions

- The `$CLAUDE_PLUGIN_ROOT` variable is referenced but its exact resolution mechanism within Claude Code's plugin system is not documented in this codebase.
- The exact mechanism by which Claude Code detects and loads `disable-model-invocation: true` is not visible in these files (it is a Claude Code platform feature, not implemented in the plugin itself).
