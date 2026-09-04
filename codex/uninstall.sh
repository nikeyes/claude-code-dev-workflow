#!/usr/bin/env bash
# Removes what codex/install.sh installed, and nothing else.
# Only symlinks pointing into this repo and TOMLs this repo generates are
# deleted, so a hand-installed skill or a third-party agent survives.
# Idempotent: uninstalling twice, or with nothing installed, succeeds.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$HOME/.agents/skills"
AGENTS_DIR="$HOME/.codex/agents"

skills_removed=0
if [ -d "$SKILLS_DIR" ]; then
  for link in "$SKILLS_DIR"/*; do
    # A real directory is never ours: install.sh refuses to create one.
    [ -L "$link" ] || continue
    case "$(readlink "$link")" in
      "$REPO_ROOT"/*)
        rm -f "$link"
        skills_removed=$((skills_removed + 1))
        ;;
    esac
  done
fi

agents_removed=0
if [ -d "$AGENTS_DIR" ]; then
  for generated in "$REPO_ROOT"/codex/agents/*.toml; do
    [ -f "$generated" ] || continue
    installed="$AGENTS_DIR/$(basename "$generated")"
    if [ -f "$installed" ]; then
      rm -f "$installed"
      agents_removed=$((agents_removed + 1))
    fi
  done
fi

# Clean up the directories we created, but only while they are empty.
rmdir "$SKILLS_DIR" "$HOME/.agents" "$AGENTS_DIR" 2>/dev/null || true

echo "Removed $skills_removed skills from $SKILLS_DIR"
echo "Removed $agents_removed agents from $AGENTS_DIR"
