---
name: thoughts-management
description: Manage thoughts directory operations including initialization, synchronization, and metadata generation. Use after creating or modifying research documents, implementation plans, or notes to keep the searchable directory synchronized. Also use when gathering git metadata for document frontmatter.
allowed-tools: Bash
---

# Thoughts Directory Management

Manage the thoughts/ directory system for organizing research, plans, and notes with efficient searchable hardlinks.

## When to use this Skill

Use this Skill automatically in these situations:

- **After creating research documents** in `thoughts/shared/research/`
- **After creating implementation plans** in `thoughts/shared/plans/`
- **After modifying any markdown files** in `thoughts/`
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
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init
```

**What it does:**
- Creates directory structure: `{username}/`, `shared/`, `searchable/`
- Generates `.gitignore` for searchable/ directory
- Creates initial README.md
- Runs initial sync to create hardlinks

### Sync searchable directory

Synchronizes hardlinks in `thoughts/searchable/` for efficient grep operations.

**When to use:**
- After creating new markdown files in thoughts/
- After modifying existing markdown files in thoughts/
- After completing a /stepwise-dev:research_codebase command
- After completing a /stepwise-dev:create_plan command
- After completing a /stepwise-dev:iterate_plan command

**Command:**
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-sync
```

**What it does:**
- Creates hardlinks for all .md files in searchable/
- Removes orphaned links (when source files are deleted)
- Maintains flat searchable/ structure for fast grep
- Reports statistics (added, removed, skipped)

**Important:** Always run this after creating or modifying documents in thoughts/

### Generate metadata

Generates git and project metadata for document frontmatter.

**When to use:**
- Before creating research document frontmatter
- Before creating implementation plan frontmatter
- When you need current git commit, branch, repository info
- When you need timestamp information

**Command:**
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
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

### Research workflow

1. Run `/stepwise-dev:research_codebase` command
2. Command generates research document in `thoughts/shared/research/`
3. **Automatically run sync:**
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-sync
   ```

### Planning workflow

1. Run `/stepwise-dev:create_plan` or `/stepwise-dev:iterate_plan` command
2. Command generates/updates plan in `thoughts/shared/plans/`
3. **Automatically run sync:**
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-sync
   ```

### Metadata collection workflow

1. Need to create document with frontmatter
2. **First, gather metadata:**
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
   ```
3. Use output to populate YAML frontmatter fields
4. Create the document
5. Sync after creation

## Directory structure

The thoughts/ system maintains this structure:

```
thoughts/
├── {username}/              # Personal notes (default: nikey_es)
│   ├── tickets/            # Ticket documentation
│   └── notes/              # Personal observations
├── shared/                 # Team-shared documents
│   ├── research/          # Research documents
│   ├── plans/             # Implementation plans
│   └── prs/               # PR descriptions
└── searchable/            # Auto-generated hardlinks
    └── [hardlinks to all .md files for fast grep]
```

## Key concepts

### Hardlinks vs copies
- `thoughts-sync` creates **hardlinks**, not copies
- Same file, multiple directory entries
- No disk space duplication
- Fast grep across all documents in searchable/

### Searchable directory
- Contains hardlinks to ALL .md files in thoughts/
- Flattened structure for efficient searching
- Automatically maintained by thoughts-sync
- Gitignored (generated, not source)

### Path handling
- When finding files in `searchable/`, always document paths by removing "searchable/"
- Preserve all other subdirectories: `thoughts/searchable/nikey_es/notes/X.md` → `thoughts/nikey_es/notes/X.md`
- Never change directory structure when removing "searchable/" prefix

## Best practices

1. **Always sync after document creation** - Keep searchable/ up to date
2. **Gather metadata before writing** - Populate frontmatter with real values, never placeholders
3. **Run sync even for single files** - Maintains consistency
4. **Don't edit files in searchable/** - Edit in original locations only
5. **Let the scripts handle hardlinks** - Don't create them manually

## Configuration

Set custom username (optional):
```bash
export THOUGHTS_USER=your_name
```

Default username: `nikey_es`

## Troubleshooting

### Sync reports orphaned links
**Cause:** Files were deleted from thoughts/ but hardlinks remain in searchable/

**Solution:** The script automatically cleans them up. No action needed.

### Metadata returns "no-branch" or "no-commit"
**Cause:** Not in a git repository or git not available

**Solution:** Ensure you're in a git repository. For testing, the script provides fallback values.

### Permission denied on scripts
**Cause:** Scripts are not executable

**Solution:** Run chmod:
```bash
chmod +x ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/*
```

## Script reference

All scripts are located in: `${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/`

| Script | Purpose | When to use |
|--------|---------|-------------|
| `thoughts-init` | Initialize directory structure | Once per project |
| `thoughts-sync` | Synchronize hardlinks | After every document change |
| `thoughts-metadata` | Generate git metadata | Before creating frontmatter |

## Integration with commands

The following slash commands automatically use this Skill:

- `/stepwise-dev:research_codebase` - Uses thoughts-metadata and thoughts-sync
- `/stepwise-dev:create_plan` - Uses thoughts-metadata and thoughts-sync
- `/stepwise-dev:iterate_plan` - Uses thoughts-sync
- `/stepwise-dev:implement_plan` - Uses thoughts-sync
- `/stepwise-dev:validate_plan` - Uses thoughts-sync

These commands will automatically invoke the appropriate scripts when needed.
