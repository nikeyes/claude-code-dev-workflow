# Research: thoughts-init script

**File analyzed**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/thoughts-management/scripts/thoughts-init`

---

## Overview

`thoughts-init` is a bash script that initializes a `thoughts/` directory structure inside the current project. It is part of the `stepwise-core` plugin and is invoked by the `thoughts-management` skill.

---

## Configuration

The script reads one environment variable:

| Variable | Default | Purpose |
|---|---|---|
| `THOUGHTS_USER` | `nikey_es` | Sets the username subdirectory under `thoughts/` |

The root directory is hardcoded as `thoughts` (relative to the working directory where the script is executed).

---

## Directories created

The script creates **5 directories** using `mkdir -p` (so intermediate directories are also created as needed):

```
thoughts/
├── {USERNAME}/           # e.g. thoughts/nikey_es/
│   ├── tickets/          # Ticket documentation and tracking
│   └── notes/            # Personal notes and observations
└── shared/
    ├── research/         # Research documents
    ├── plans/            # Implementation plans
    └── prs/              # PR descriptions and documentation
```

Exact `mkdir -p` calls (lines 37–41):

```bash
mkdir -p "$THOUGHTS_DIR/$USERNAME/tickets"
mkdir -p "$THOUGHTS_DIR/$USERNAME/notes"
mkdir -p "$THOUGHTS_DIR/shared/research"
mkdir -p "$THOUGHTS_DIR/shared/plans"
mkdir -p "$THOUGHTS_DIR/shared/prs"
```

---

## README generated

The script creates `thoughts/README.md` **only if it does not already exist** (guarded by `if [ ! -f "$THOUGHTS_DIR/README.md" ]`, line 54).

### Exact content of the generated README

The README is written with a heredoc (lines 56–78). The `{USERNAME}` placeholder is expanded at generation time to the value of `$USERNAME`:

```markdown
# Thoughts Directory

This directory contains research documents, implementation plans, and notes for this project.

## Structure

- `{USERNAME}/` - Personal notes and tickets
  - `tickets/` - Ticket documentation and tracking
  - `notes/` - Personal notes and observations
- `shared/` - Team-shared documents
  - `research/` - Research documents from /stepwise-core:research-codebase
  - `plans/` - Implementation plans from /stepwise-core:create-plan
  - `prs/` - PR descriptions and documentation

## Usage

Use Claude Code slash commands:
- `/stepwise-core:research-codebase [topic]` - Research and document codebase
- `/stepwise-core:create-plan [description]` - Create implementation plan
- `/stepwise-core:implement-plan [plan-file]` - Execute a plan
- `/stepwise-core:validate-plan [plan-file]` - Validate implementation
```

---

## Idempotency behaviour

- If `thoughts/` already exists, the script emits a warning but continues (does **not** abort). Existing files are preserved.
- The README is only written on first run (skipped if `thoughts/README.md` already exists).
- All `mkdir -p` calls are safe to re-run; they silently succeed if the directory already exists.

---

## Error handling

- `set -euo pipefail` is set at the top: the script exits immediately on any unhandled error, unbound variable, or pipe failure.
- An `error()` helper function prints a red message and calls `exit 1`.

---

## Summary table

| Item | Detail |
|---|---|
| Script location | `core/skills/thoughts-management/scripts/thoughts-init` |
| Root directory created | `thoughts/` (relative to cwd) |
| Personal directories | `thoughts/{USERNAME}/tickets/`, `thoughts/{USERNAME}/notes/` |
| Shared directories | `thoughts/shared/research/`, `thoughts/shared/plans/`, `thoughts/shared/prs/` |
| README path | `thoughts/README.md` |
| README created | Only on first run (if file does not exist) |
| Default username | `nikey_es` (override with `THOUGHTS_USER` env var) |
