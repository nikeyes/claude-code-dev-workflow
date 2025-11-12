#!/usr/bin/env bash
set -euo pipefail

# plugin-structure-test.sh - Essential structural validation for Claude Code plugin
# Tests only critical requirements: manifest valid, required files exist, scripts executable

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source test helpers
# shellcheck source=test/test-helpers.sh
source "$SCRIPT_DIR/test-helpers.sh"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Plugin Structure Tests (Essential Only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# ============================================================================
# Test 1: Plugin manifest is valid JSON
# ============================================================================
section "Test 1: Plugin manifest"

assert_file_exists ".claude-plugin/plugin.json" "plugin.json exists"

if command -v jq >/dev/null 2>&1; then
  if jq empty .claude-plugin/plugin.json 2>/dev/null; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} plugin.json is valid JSON"
  else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} plugin.json is invalid JSON"
  fi

  NAME=$(jq -r '.name // empty' .claude-plugin/plugin.json)
  assert_not_empty "$NAME" "plugin.json has name field"
fi

# ============================================================================
# Test 2: All required files exist
# ============================================================================
section "Test 2: Required files"

# Commands
assert_file_exists "commands/research_codebase.md" "research_codebase command"
assert_file_exists "commands/create_plan.md" "create_plan command"
assert_file_exists "commands/iterate_plan.md" "iterate_plan command"
assert_file_exists "commands/implement_plan.md" "implement_plan command"
assert_file_exists "commands/validate_plan.md" "validate_plan command"
assert_file_exists "commands/commit.md" "commit command"

# Agents
assert_file_exists "agents/codebase-locator.md" "codebase-locator agent"
assert_file_exists "agents/codebase-analyzer.md" "codebase-analyzer agent"
assert_file_exists "agents/codebase-pattern-finder.md" "codebase-pattern-finder agent"
assert_file_exists "agents/thoughts-locator.md" "thoughts-locator agent"
assert_file_exists "agents/thoughts-analyzer.md" "thoughts-analyzer agent"

# Documentation
assert_file_exists "README.md" "README.md"
assert_file_exists "CLAUDE.md" "CLAUDE.md"

# ============================================================================
# Test 3: Skill structure (core functionality)
# ============================================================================
section "Test 3: Skill structure"

# Directory structure
assert_dir_exists "skills/thoughts-management" "Skill directory exists"
assert_dir_exists "skills/thoughts-management/scripts" "scripts directory exists"

# SKILL.md with valid content
assert_file_exists "skills/thoughts-management/SKILL.md" "SKILL.md exists"
assert_contains "skills/thoughts-management/SKILL.md" "name: thoughts-management" "SKILL.md has name"

# All three required scripts exist and are executable
assert_file_exists "skills/thoughts-management/scripts/thoughts-init" "thoughts-init exists"
assert_executable "skills/thoughts-management/scripts/thoughts-init" "thoughts-init is executable"

assert_file_exists "skills/thoughts-management/scripts/thoughts-sync" "thoughts-sync exists"
assert_executable "skills/thoughts-management/scripts/thoughts-sync" "thoughts-sync is executable"

assert_file_exists "skills/thoughts-management/scripts/thoughts-metadata" "thoughts-metadata exists"
assert_executable "skills/thoughts-management/scripts/thoughts-metadata" "thoughts-metadata is executable"

# ============================================================================
# Test 4: Critical content validation
# ============================================================================
section "Test 4: Critical content"

assert_contains "README.md" "stepwise-dev" "README documents plugin"
assert_file_exists ".gitignore" ".gitignore exists"

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
