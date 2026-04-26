# Research: thoughts-init script

**File analyzed**: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/thoughts-management/scripts/thoughts-init`

---

## Overview

`thoughts-init` is a bash script that initializes a `thoughts/` directory structure inside the current project. It creates a fixed set of subdirectories and optionally generates a `README.md`.

---

## Configuration

- **Username**: read from the environment variable `THOUGHTS_USER`. Defaults to `nikey_es` if the variable is not set.
- **Root directory**: always `thoughts` (relative to the working directory where the script is executed).

```bash
USERNAME="${THOUGHTS_USER:-nikey_es}"
THOUGHTS_DIR="thoughts"
```

---

## Directories created

The script runs five `mkdir -p` calls. Using the default username `nikey_es`, the directories created are:

```
thoughts/
├── nikey_es/
│   ├── tickets/
│   └── notes/
└── shared/
    ├── research/
    ├── plans/
    └── prs/
```

If `THOUGHTS_USER=alice` is exported before running the script, the personal branch becomes `thoughts/alice/tickets/` and `thoughts/alice/notes/` instead.

The exact `mkdir -p` calls (lines 37-41):

```bash
mkdir -p "$THOUGHTS_DIR/$USERNAME/tickets"
mkdir -p "$THOUGHTS_DIR/$USERNAME/notes"
mkdir -p "$THOUGHTS_DIR/shared/research"
mkdir -p "$THOUGHTS_DIR/shared/plans"
mkdir -p "$THOUGHTS_DIR/shared/prs"
```

---

## README generated

The script writes `thoughts/README.md` only if the file does **not already exist** (guarded by `if [ ! -f "$THOUGHTS_DIR/README.md" ]`). The file is generated with a heredoc (lines 54-79).

### Exact content of the generated README

```markdown
# Thoughts Directory

This directory contains research documents, implementation plans, and notes for this project.

## Structure

- `<USERNAME>/` - Personal notes and tickets
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

`<USERNAME>` is replaced at generation time with the resolved username (default: `nikey_es`).

---

## Idempotency behaviour

| Condition | Behaviour |
|-----------|-----------|
| `thoughts/` does not exist | Creates all directories and `README.md` |
| `thoughts/` already exists | Prints a warning, re-runs `mkdir -p` (existing files preserved), skips README creation |
| `thoughts/README.md` already exists | Skips README creation silently |

---

## Summary

The script always creates exactly **5 leaf directories** under `thoughts/` and generates one `README.md` file (on first run). The only runtime variable that changes the output is `THOUGHTS_USER`.
