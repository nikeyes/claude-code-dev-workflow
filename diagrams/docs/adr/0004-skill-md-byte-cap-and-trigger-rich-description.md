# ADR 0004 — SKILL.md byte cap and the trigger-rich description

**Status:** accepted (v2.3, cap raised after review)

## Context

`SKILL.md` loads into an agent's context on every skill invocation, so it must stay lean; a byte cap keeps growth honest. But v2.3 initially set the cap at 35,000 bytes and slimmed the frontmatter `description` to fit — deleting all 27 type names. The description is the only text an agent sees *before* deciding to load the skill: removing "flowchart", "Gantt", "org chart" from it removes the lexical hooks that make "make me a flowchart" invoke the skill at all.

## Decision

Two rules, in priority order:

1. The frontmatter `description` must name every visual type in the selection table (enforced by `scripts/verify-docs-sync.py`) plus the import formats and major feature vocabulary. Routing surface is never traded for body prose.
2. `MAX_SKILL_BYTES` is 40,000 (enforced by `scripts/verify-semantic-motion.py`). When the file approaches the cap, cut body prose or move detail into `references/` — never the description.

## Consequences

- Adding a visual type requires touching the description; CI fails otherwise, by design.
- The cap is measured on raw bytes with `core.autocrlf=false` pinned in CI checkout; Windows contributors should keep LF endings for `SKILL.md`.
