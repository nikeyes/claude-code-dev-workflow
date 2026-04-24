# Response: Refactoring thoughts-management to Support Config File

## Research Findings

### What exists today

The `thoughts-management` skill lives in `/core/skills/thoughts-management/` and consists of three files:

- `SKILL.md` — the Claude Code skill entry point
- `scripts/thoughts-init` — bash script that creates the directory tree
- `scripts/thoughts-metadata` — bash script that prints git/date metadata for frontmatter

#### Hardcoded paths and values

Every directory name in the thoughts system is hardcoded in `thoughts-init`:

```
THOUGHTS_DIR="thoughts"                          # root (line 8)
USERNAME="${THOUGHTS_USER:-nikey_es}"            # personal folder (line 7)
mkdir -p "$THOUGHTS_DIR/$USERNAME/tickets"       # line 37
mkdir -p "$THOUGHTS_DIR/$USERNAME/notes"         # line 38
mkdir -p "$THOUGHTS_DIR/shared/research"         # line 39
mkdir -p "$THOUGHTS_DIR/shared/plans"            # line 40
mkdir -p "$THOUGHTS_DIR/shared/prs"              # line 41
```

The only existing customisation point is the `THOUGHTS_USER` environment variable, which overrides the personal directory name (`nikey_es` by default). There is no way to:
- Rename `shared/` to something else (e.g., `team/`)
- Change the root from `thoughts/` to another name (e.g., `docs/thoughts/`)
- Add or remove subdirectories
- Persist any of this configuration in the repository

#### Downstream consumers with hardcoded paths

The hardcoded paths propagate to every skill that writes or reads documents:

| Skill / Agent | Hardcoded path |
|---|---|
| `create-plan/SKILL.md` | `thoughts/shared/plans/` |
| `research-codebase/SKILL.md` | `thoughts/shared/research/` |
| `iterate-plan/SKILL.md` | `thoughts/shared/plans/` |
| `implement-plan/SKILL.md` | `thoughts/shared/plans/` |
| `validate-plan/SKILL.md` | `thoughts/shared/plans/` |
| `thoughts-locator.md` (agent) | `thoughts/shared/`, `thoughts/{username}/` |

#### Tests

`test/thoughts-structure-test.sh` asserts the default layout by name (`thoughts/nikey_es/tickets`, etc.), so any changes must keep those green.

---

## Implementation Plan

The full plan is saved at:
`create-plan-workspace/iteration-1/eval-3-refactoring/without_skill/outputs/plan.md`

### Summary of the approach

Introduce a `thoughts/thoughts.config.json` file (written by `thoughts-init` at first run, read by all scripts thereafter) that captures the full directory layout. A new shared bash library (`thoughts-config-lib`) is sourced by both scripts so config-loading logic is defined once.

Default values are preserved identically, making this a pure opt-in change with no breaking impact on existing projects.

### Six-phase breakdown

| Phase | What it does | Files changed |
|---|---|---|
| 1 | Create `thoughts-config-lib` — the shared config reader | New file |
| 2 | Update `thoughts-init` to write and read `thoughts.config.json` | `thoughts-init` |
| 3 | Update `thoughts-metadata` to expose config-derived paths | `thoughts-metadata` |
| 4 | Update `SKILL.md` documentation | `SKILL.md` |
| 5 | Update `thoughts-locator` agent to read config before searching | `thoughts-locator.md` |
| 6 | Update tests to cover config-driven layouts | `thoughts-structure-test.sh` |

### Key design decisions

1. **JSON over env vars** — the config file travels with the repository and is visible to all team members, unlike env vars which must be set per-machine.
2. **Python3 for JSON parsing** — available on all modern macOS/Linux without adding `jq` as a dependency.
3. **No breaking changes** — projects without `thoughts.config.json` behave exactly as today; all existing tests must remain green.
4. **`THOUGHTS_USER` env var still works** — it overrides `personal_dir` from config, preserving the current escape hatch.
5. **Agents read config too** — `thoughts-locator` is updated to check `thoughts.config.json` before assuming the default paths, so custom layouts work end-to-end without manual agent reconfiguration.

### Config file format

```json
{
  "version": "1",
  "root": "thoughts",
  "personal_dir": "nikey_es",
  "shared_dir": "shared",
  "personal_subdirs": ["tickets", "notes"],
  "shared_subdirs": ["research", "plans", "prs"]
}
```

### Success criteria (automated only)

```bash
make test    # All assertions green, including new config-driven layout test
make check   # shellcheck clean on all scripts including new lib
```
