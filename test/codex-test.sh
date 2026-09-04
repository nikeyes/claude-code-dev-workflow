#!/usr/bin/env bash
set -uo pipefail

# codex-test.sh - Behavioral tests for the Codex compatibility layer.
# Unlike plugin-structure-test.sh (which checks that files exist), this suite
# actually runs install.sh and transpile-agents.sh and asserts on what they do.
# Every test runs against a temporary HOME / output dir, never the real one.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=test/test-helpers.sh
source "$SCRIPT_DIR/test-helpers.sh"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Codex Compatibility Behavioral Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_ROOT" || exit 1

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

fresh_home() {
  local h
  h="$(mktemp -d "$TMP_ROOT/home.XXXXXX")"
  echo "$h"
}

# ============================================================================
# Test 1: A clean install produces working skill symlinks and agent files
# ============================================================================
section "Test 1: Clean install"

HOME_1="$(fresh_home)"
INSTALL_OUT="$(HOME="$HOME_1" ./codex/install.sh 2>&1)"

assert_output_contains "$INSTALL_OUT" "Installed 16 skills" "installs exactly 16 skills"
assert_output_contains "$INSTALL_OUT" "Installed 9 agents" "installs exactly 9 agents"

SKILL_COUNT="$(find "$HOME_1/.agents/skills" -maxdepth 1 -mindepth 1 | wc -l | tr -d ' ')"
assert_equals "16" "$SKILL_COUNT" "16 entries land in ~/.agents/skills"

AGENT_COUNT="$(find "$HOME_1/.codex/agents" -name '*.toml' | wc -l | tr -d ' ')"
assert_equals "9" "$AGENT_COUNT" "9 agent TOMLs land in ~/.codex/agents"

# Codex scans for SKILL.md through the symlink, so the link must resolve.
assert_file_exists "$HOME_1/.agents/skills/commit/SKILL.md" "SKILL.md resolves through the symlink"
assert_file_exists "$HOME_1/.agents/skills/deep-research/scripts/generate-report" \
  "skill scripts resolve through the symlink"

# ============================================================================
# Test 2: Eval workspaces are never installed as skills
# ============================================================================
section "Test 2: Workspace exclusion"

# small-safe-steps-workspace contains a byte-identical copy of a real SKILL.md;
# a naive `find -name SKILL.md` would install it as a duplicate skill.
assert_file_not_exists "$HOME_1/.agents/skills/small-safe-steps-workspace" \
  "eval workspace is not installed"
assert_file_not_exists "$HOME_1/.agents/skills/skill-snapshot" \
  "workspace skill snapshot is not installed"

# ============================================================================
# Test 3: Install is idempotent
# ============================================================================
section "Test 3: Idempotency"

if HOME="$HOME_1" ./codex/install.sh >/dev/null 2>&1; then
  TESTS_RUN=$((TESTS_RUN + 1)); TESTS_PASSED=$((TESTS_PASSED + 1))
  echo -e "${GREEN}✓${NC} re-running install over an existing install succeeds"
else
  TESTS_RUN=$((TESTS_RUN + 1)); TESTS_FAILED=$((TESTS_FAILED + 1))
  echo -e "${RED}✗${NC} re-running install over an existing install succeeds"
fi

SKILL_COUNT_2="$(find "$HOME_1/.agents/skills" -maxdepth 1 -mindepth 1 | wc -l | tr -d ' ')"
assert_equals "16" "$SKILL_COUNT_2" "re-install does not duplicate skills"

# ============================================================================
# Test 4: REGRESSION - install refuses to clobber a real directory
# ============================================================================
section "Test 4: Regression - pre-existing real directory"

# Bug: `ln -sfn` links *inside* an existing real directory, producing
# ~/.agents/skills/commit/commit and a silently broken install.
HOME_2="$(fresh_home)"
mkdir -p "$HOME_2/.agents/skills/commit"

assert_fails "install fails when a skill path is a real directory" \
  env HOME="$HOME_2" ./codex/install.sh

assert_file_not_exists "$HOME_2/.agents/skills/commit/commit" \
  "no symlink is nested inside the existing directory"

# ============================================================================
# Test 5: A stale symlink is still replaced
# ============================================================================
section "Test 5: Stale symlink replacement"

# The guard in Test 4 must not break the legitimate re-link case.
HOME_3="$(fresh_home)"
mkdir -p "$HOME_3/.agents/skills"
ln -sfn "/nonexistent/old/path" "$HOME_3/.agents/skills/commit"

if HOME="$HOME_3" ./codex/install.sh >/dev/null 2>&1; then
  TESTS_RUN=$((TESTS_RUN + 1)); TESTS_PASSED=$((TESTS_PASSED + 1))
  echo -e "${GREEN}✓${NC} install succeeds over a stale symlink"
else
  TESTS_RUN=$((TESTS_RUN + 1)); TESTS_FAILED=$((TESTS_FAILED + 1))
  echo -e "${RED}✗${NC} install succeeds over a stale symlink"
fi

assert_file_exists "$HOME_3/.agents/skills/commit/SKILL.md" \
  "stale symlink is repointed at the repo"

# ============================================================================
# Test 6: REGRESSION - transpiler clears stale output
# ============================================================================
section "Test 6: Regression - stale generated agents"

# Bug: a renamed or deleted agent left its old .toml behind, which then got
# committed and copied into ~/.codex/agents forever.
OUT_1="$TMP_ROOT/out1"
mkdir -p "$OUT_1"
touch "$OUT_1/removed-agent.toml"

TRANSPILE_OUT="$(./codex/transpile-agents.sh "$OUT_1" 2>&1)"

assert_file_not_exists "$OUT_1/removed-agent.toml" "stale .toml is removed on regeneration"
assert_output_contains "$TRANSPILE_OUT" "Transpiled 9 agents" "count reflects agents actually written"

GENERATED="$(find "$OUT_1" -name '*.toml' | wc -l | tr -d ' ')"
assert_equals "9" "$GENERATED" "exactly 9 agents are generated"

# ============================================================================
# Test 7: Generated agents carry real content, not just a filename
# ============================================================================
section "Test 7: Generated agent content"

for agent in codebase-locator codebase-analyzer codebase-pattern-finder \
             thoughts-locator thoughts-analyzer \
             research-lead research-worker citation-analyst web-search-researcher; do
  assert_contains "$OUT_1/$agent.toml" "^name = \"$agent\"$" "$agent.toml declares its name"
  assert_contains "$OUT_1/$agent.toml" "^developer_instructions = '''" \
    "$agent.toml carries developer_instructions"
done

# Only research-lead has Write in its tools, so only it may write to the workspace.
assert_contains "$OUT_1/research-lead.toml" 'sandbox_mode = "workspace-write"' \
  "research-lead is workspace-write"
assert_contains "$OUT_1/codebase-locator.toml" 'sandbox_mode = "read-only"' \
  "codebase-locator is read-only"

READONLY_COUNT="$(grep -l 'sandbox_mode = "read-only"' "$OUT_1"/*.toml | wc -l | tr -d ' ')"
assert_equals "8" "$READONLY_COUNT" "8 of 9 agents are read-only"

# Every agent declares `model: inherit`, which maps to pinning no model at all:
# a Codex agent without a model key runs on whatever the session config says.
PINNED_COUNT="$(grep -l '^model = ' "$OUT_1"/*.toml | wc -l | tr -d ' ')"
assert_equals "0" "$PINNED_COUNT" "inherit pins no model on any agent"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$TESTS_FAILED" -eq 0 ]; then
  exit 0
else
  exit 1
fi
