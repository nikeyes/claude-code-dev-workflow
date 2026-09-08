#!/usr/bin/env bash
set -euo pipefail

# plugin-structure-test.sh - Essential structural validation for multi-plugin marketplace
# Tests marketplace manifest and all 4 plugins (stepwise-core, stepwise-git, stepwise-web, stepwise-research)

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

# Skills (workflow)
assert_file_exists "core/skills/research-codebase/SKILL.md" "research-codebase skill"
assert_file_exists "core/skills/create-plan/SKILL.md" "create-plan skill"
assert_file_exists "core/skills/iterate-plan/SKILL.md" "iterate-plan skill"
assert_file_exists "core/skills/implement-plan/SKILL.md" "implement-plan skill"
assert_file_exists "core/skills/validate-plan/SKILL.md" "validate-plan skill"

# Skills (practices)
assert_file_exists "core/skills/tdd/SKILL.md" "tdd skill"
assert_file_exists "core/skills/grill-me/SKILL.md" "grill-me skill"
assert_file_exists "core/skills/bugmagnet/SKILL.md" "bugmagnet skill"
assert_file_exists "core/skills/hamburger-method/SKILL.md" "hamburger-method skill"
assert_file_exists "core/skills/small-safe-steps/SKILL.md" "small-safe-steps skill"
assert_file_exists "core/skills/story-splitting/SKILL.md" "story-splitting skill"
assert_file_exists "core/skills/test-desiderata/SKILL.md" "test-desiderata skill"

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
assert_file_exists "git/skills/commit/SKILL.md" "commit skill exists"
assert_file_exists "git/skills/review-pr-comments/SKILL.md" "review-pr-comments skill exists"

# ============================================================================
# Test 4: Web plugin structure (stepwise-web)
# ============================================================================
section "Test 4: stepwise-web plugin"

assert_file_exists "web/.claude-plugin/plugin.json" "web/plugin.json exists"
assert_file_exists "web/README.md" "web/README.md exists"
assert_file_exists "web/agents/web-search-researcher.md" "web-search-researcher agent exists"

# ============================================================================
# Test 5: Research plugin structure (stepwise-research)
# ============================================================================
section "Test 5: stepwise-research plugin"

assert_file_exists "research/.claude-plugin/plugin.json" "research/plugin.json exists"
assert_file_exists "research/README.md" "research/README.md exists"
assert_file_exists "research/skills/deep-research/SKILL.md" "deep-research skill exists"
assert_file_exists "research/skills/deep-research/scripts/generate-report" "generate-report exists"
assert_executable "research/skills/deep-research/scripts/generate-report" "generate-report is executable"
assert_file_exists "research/agents/research-lead.md" "research-lead agent exists"
assert_file_exists "research/agents/research-worker.md" "research-worker agent exists"
assert_file_exists "research/agents/citation-analyst.md" "citation-analyst agent exists"

# ============================================================================
# Test 6: Slides plugin structure (stepwise-slides, vendored)
# ============================================================================
section "Test 6: stepwise-slides plugin"

assert_file_exists "slides/LICENSE" "slides/LICENSE exists"
assert_contains "slides/LICENSE" "MIT License" "slides/LICENSE is MIT"
assert_file_exists "slides/plugins/frontend-slides/.claude-plugin/plugin.json" "vendored plugin.json exists"
assert_file_exists "slides/plugins/frontend-slides/skills/frontend-slides/SKILL.md" "frontend-slides SKILL.md exists"
assert_contains "slides/plugins/frontend-slides/skills/frontend-slides/SKILL.md" "^name: frontend-slides" "SKILL.md declares name"

if command -v jq >/dev/null 2>&1; then
  UPSTREAM_NAME=$(jq -r '.name // empty' slides/plugins/frontend-slides/.claude-plugin/plugin.json)
  if [ "$UPSTREAM_NAME" = "frontend-slides" ]; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} vendored plugin.json .name == frontend-slides"
  else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} vendored plugin.json .name is '$UPSTREAM_NAME'"
  fi

  SLIDES_SOURCE=$(jq -r '.plugins[] | select(.name=="stepwise-slides") | .source' .claude-plugin/marketplace.json)
  if [ "$SLIDES_SOURCE" = "./slides/plugins/frontend-slides" ]; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} marketplace entry stepwise-slides points at vendored dir"
  else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} stepwise-slides source is '$SLIDES_SOURCE'"
  fi
fi

# ============================================================================
# Test 7: Codex compatibility layer
# ============================================================================
section "Test 7: codex/"

assert_file_exists "codex/transpile-agents.sh" "transpile-agents.sh exists"
assert_executable "codex/transpile-agents.sh" "transpile-agents.sh is executable"
assert_file_exists "codex/install.sh" "install.sh exists"
assert_executable "codex/install.sh" "install.sh is executable"

for agent in codebase-locator codebase-analyzer codebase-pattern-finder \
             thoughts-locator thoughts-analyzer \
             research-lead research-worker citation-analyst web-search-researcher; do
  assert_file_exists "codex/agents/$agent.toml" "$agent.toml is generated"
  # An empty file would satisfy existence alone; require real generated content.
  assert_contains "codex/agents/$agent.toml" "^name = \"$agent\"$" "$agent.toml declares its name"
  assert_contains "codex/agents/$agent.toml" "^developer_instructions" "$agent.toml has instructions"
done

# Every skill Claude Code opts out of implicit invocation must carry the Codex
# equivalent. The list is derived from the frontmatter rather than hardcoded, so
# a new opt-out skill that forgets its openai.yaml fails here.
OPT_OUT_SKILLS="$(grep -rl '^disable-model-invocation: *true' --include="SKILL.md" core git research web | sort)"
assert_not_empty "$OPT_OUT_SKILLS" "found skills that opt out of implicit invocation"

while IFS= read -r skill_md; do
  skill="$(dirname "$skill_md")"
  assert_contains "$skill/agents/openai.yaml" "allow_implicit_invocation: false" \
    "$(basename "$skill") opts out of implicit invocation"
done <<< "$OPT_OUT_SKILLS"

# ============================================================================
# Test 8: Root documentation
# ============================================================================
section "Test 8: Root documentation"

assert_file_exists "README.md" "README.md exists"
assert_file_exists "AGENTS.md" "AGENTS.md exists"
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
