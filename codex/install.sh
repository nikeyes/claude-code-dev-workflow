#!/usr/bin/env bash
# Installs stepwise-dev skills and agents for OpenAI Codex.
# Skills are symlinked (Codex follows symlinks when scanning skill directories);
# agents are copied as generated TOML. Idempotent, no sudo.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$HOME/.agents/skills"
AGENTS_DIR="$HOME/.codex/agents"

mkdir -p "$SKILLS_DIR" "$AGENTS_DIR"

count=0
for skill in "$REPO_ROOT"/core/skills/*/ \
             "$REPO_ROOT"/git/skills/*/ \
             "$REPO_ROOT"/research/skills/*/ \
             "$REPO_ROOT"/slides/plugins/frontend-slides/skills/*/ \
             "$REPO_ROOT"/diagrams/skills/*/; do
  case "$skill" in *-workspace/*) continue ;; esac
  [ -f "$skill/SKILL.md" ] || continue

  target="$SKILLS_DIR/$(basename "$skill")"
  # ln -sfn would link *inside* an existing real directory, leaving a broken install.
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "error: $target already exists and is not a symlink." >&2
    echo "       Remove it and re-run, or install elsewhere." >&2
    exit 1
  fi

  ln -sfn "${skill%/}" "$target"
  count=$((count + 1))
done

tomls=("$REPO_ROOT"/codex/agents/*.toml)
if [ ! -e "${tomls[0]}" ]; then
  echo "error: no agents in $REPO_ROOT/codex/agents — run 'make transpile-codex' first" >&2
  exit 1
fi
cp "${tomls[@]}" "$AGENTS_DIR/"

echo "Installed $count skills into $SKILLS_DIR"
echo "Installed ${#tomls[@]} agents into $AGENTS_DIR"
