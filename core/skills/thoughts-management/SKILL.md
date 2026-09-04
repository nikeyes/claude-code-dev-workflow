---
name: thoughts-management
description: Manage thoughts directory operations including initialization and metadata generation. Use when initializing a new project's thoughts/ structure or when gathering git metadata for document frontmatter.
allowed-tools: Bash
---

# Thoughts Directory Management

Manage the thoughts/ directory system for organizing research, plans, and notes.

## When to use this Skill

Use this Skill automatically in these situations:

- **When gathering metadata** for document frontmatter (git commit, branch, author)
- **When initializing a new project** that needs thoughts/ structure

## Available operations

### Initialize thoughts directory

Creates the complete thoughts/ directory structure in the current project.

**When to use:**
- First time setting up thoughts/ in a new project
- When thoughts/ directory doesn't exist

**Command:**
```bash
bash ${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/thoughts-management/scripts/thoughts-init
```

**What it does:**
- Creates directory structure: `{username}/`, `shared/`
- Creates initial README.md

### Generate metadata

Generates git and project metadata for document frontmatter.

**When to use:**
- Before creating research document frontmatter
- Before creating implementation plan frontmatter
- When you need current git commit, branch, repository info
- When you need timestamp information

**Command:**
```bash
bash ${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/thoughts-management/scripts/thoughts-metadata
```

**Output format:**
```
Current Date/Time (TZ): 2025-01-12 14:30:45 PST
ISO DateTime: 2025-01-12T14:30:45-0800
Date Short: 2025-01-12
Current Git Commit Hash: abc123def456
Current Branch Name: main
Repository Name: my-project
Git User: John Doe
Git Email: john@example.com
Timestamp For Filename: 2025-01-12_14-30-45
```

**Use this metadata to populate:**
- Research document frontmatter fields
- Implementation plan frontmatter fields
- Any document requiring git context

## Workflow integration

### Metadata collection workflow

1. Need to create document with frontmatter
2. **Gather metadata:**
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/thoughts-management/scripts/thoughts-metadata
   ```
3. Use output to populate YAML frontmatter fields
4. Create the document

## Directory structure

The thoughts/ system maintains this structure:

```
thoughts/
├── {username}/              # Personal notes (default: nikey_es)
│   ├── tickets/            # Ticket documentation
│   └── notes/              # Personal observations
└── shared/                 # Team-shared documents
    ├── research/          # Research documents
    ├── plans/             # Implementation plans
    └── prs/               # PR descriptions
```

## Best practices

1. **Gather metadata before writing** - Populate frontmatter with real values, never placeholders
2. **Use `grep -r thoughts/` to search** - Searches all subdirectories recursively

## Configuration

Set custom username (optional):
```bash
export THOUGHTS_USER=your_name
```

Default username: `nikey_es`

## Troubleshooting

### Metadata returns "no-branch" or "no-commit"
**Cause:** Not in a git repository or git not available

**Solution:** Ensure you're in a git repository. For testing, the script provides fallback values.

### Permission denied on scripts
**Cause:** Scripts are not executable

**Solution:** Run chmod:
```bash
chmod +x ${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/thoughts-management/scripts/*
```

## Script reference

All scripts are located in: `${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/thoughts-management/scripts/`

| Script | Purpose | When to use |
|--------|---------|-------------|
| `thoughts-init` | Initialize directory structure | Once per project |
| `thoughts-metadata` | Generate git metadata | Before creating frontmatter |

## Integration with commands

The following slash commands use this Skill:

- `/stepwise-core:research-codebase` - Uses thoughts-init and thoughts-metadata
- `/stepwise-core:create-plan` - Uses thoughts-init and thoughts-metadata
- `/stepwise-core:implement-plan` - Uses thoughts-init
