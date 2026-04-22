#!/usr/bin/env bash
set -euo pipefail

# plugin-structure-test.sh - Essential structural validation for multi-plugin marketplace
# Tests marketplace manifest and all 3 plugins (stepwise-core, stepwise-git, stepwise-web)

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source test helpers
# shellcheck source=test/test-helpers.sh
source "$SCRIPT_DIR/test-helpers.sh"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Multi-Plugin Marketplace Structure Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# ============================================================================
# Test 1: Marketplace manifest is valid
# ============================================================================
section "Test 1: Marketplace manifest"

assert_file_exists ".claude-plugin/marketplace.json" "marketplace.json exists"

if command -v jq >/dev/null 2>&1; then
  if jq empty .claude-plugin/marketplace.json 2>/dev/null; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} marketplace.json is valid JSON"
  else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} marketplace.json is invalid JSON"
  fi

  NAME=$(jq -r '.name // empty' .claude-plugin/marketplace.json)
  assert_not_empty "$NAME" "marketplace.json has name field"

  OWNER_NAME=$(jq -r '.owner.name // empty' .claude-plugin/marketplace.json)
  assert_not_empty "$OWNER_NAME" "marketplace.json has owner.name field"

  PLUGINS_COUNT=$(jq '.plugins | length' .claude-plugin/marketplace.json)
  if [ "$PLUGINS_COUNT" -ge 3 ]; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} marketplace.json has $PLUGINS_COUNT plugins (expected: 3+)"
  else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} marketplace.json should have at least 3 plugins, has $PLUGINS_COUNT"
  fi
fi

# ============================================================================
# Test 2: Core plugin structure (stepwise-core)
# ============================================================================
section "Test 2: stepwise-core plugin"

assert_file_exists "core/.claude-plugin/plugin.json" "core/plugin.json exists"
assert_file_exists "core/README.md" "core/README.md exists"

# Commands
assert_file_exists "core/commands/research_codebase.md" "research_codebase command"
assert_file_exists "core/commands/create_plan.md" "create_plan command"
assert_file_exists "core/commands/iterate_plan.md" "iterate_plan command"
assert_file_exists "core/commands/implement_plan.md" "implement_plan command"
assert_file_exists "core/commands/validate_plan.md" "validate_plan command"

# Agents
assert_file_exists "core/agents/codebase-locator.md" "codebase-locator agent"
assert_file_exists "core/agents/codebase-analyzer.md" "codebase-analyzer agent"
assert_file_exists "core/agents/codebase-pattern-finder.md" "codebase-pattern-finder agent"
assert_file_exists "core/agents/thoughts-locator.md" "thoughts-locator agent"
assert_file_exists "core/agents/thoughts-analyzer.md" "thoughts-analyzer agent"

# Skill structure
assert_dir_exists "core/skills/thoughts-management" "Skill directory exists"
assert_dir_exists "core/skills/thoughts-management/scripts" "scripts directory exists"
assert_file_exists "core/skills/thoughts-management/SKILL.md" "SKILL.md exists"
assert_contains "core/skills/thoughts-management/SKILL.md" "name: thoughts-management" "SKILL.md has name"

# Scripts are executable
assert_file_exists "core/skills/thoughts-management/scripts/thoughts-init" "thoughts-init exists"
assert_executable "core/skills/thoughts-management/scripts/thoughts-init" "thoughts-init is executable"
assert_file_exists "core/skills/thoughts-management/scripts/thoughts-metadata" "thoughts-metadata exists"
assert_executable "core/skills/thoughts-management/scripts/thoughts-metadata" "thoughts-metadata is executable"

# ============================================================================
# Test 3: Git plugin structure (stepwise-git)
# ============================================================================
section "Test 3: stepwise-git plugin"

assert_file_exists "git/.claude-plugin/plugin.json" "git/plugin.json exists"
assert_file_exists "git/README.md" "git/README.md exists"
assert_file_exists "git/commands/commit.md" "commit command exists"

# ============================================================================
# Test 4: Web plugin structure (stepwise-web)
# ============================================================================
section "Test 4: stepwise-web plugin"

assert_file_exists "web/.claude-plugin/plugin.json" "web/plugin.json exists"
assert_file_exists "web/README.md" "web/README.md exists"
assert_file_exists "web/agents/web-search-researcher.md" "web-search-researcher agent exists"

# ============================================================================
# Test 5: Root documentation
# ============================================================================
section "Test 5: Root documentation"

assert_file_exists "README.md" "README.md exists"
assert_file_exists "CLAUDE.md" "CLAUDE.md exists"
assert_file_exists ".gitignore" ".gitignore exists"
assert_contains "README.md" "stepwise-dev" "README documents marketplace"

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
