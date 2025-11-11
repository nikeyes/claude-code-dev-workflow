#!/usr/bin/env bash
set -euo pipefail

# smoke-test.sh - Integration smoke tests for Claude Code Dev Workflow
# Creates temporary directory, tests core functionality, auto-cleans

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source test helpers
# shellcheck source=test/test-helpers.sh
source "$SCRIPT_DIR/test-helpers.sh"

# Create temporary test directory
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Claude Code Dev Workflow - Smoke Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test directory: $TEST_DIR"
echo ""

# Ensure scripts are in PATH for testing
export PATH="$PROJECT_ROOT/bin:$PATH"

# ============================================================================
# Test 1: thoughts-init creates directory structure
# ============================================================================
section "Test 1: thoughts-init creates directory structure"

cd "$TEST_DIR"
setup_git_repo "$TEST_DIR"

# Run thoughts-init (always non-interactive)
thoughts-init

assert_dir_exists "thoughts/nikey_es/tickets" "thoughts/{user}/tickets/ created"
assert_dir_exists "thoughts/nikey_es/notes" "thoughts/{user}/notes/ created"
assert_dir_exists "thoughts/shared/research" "thoughts/shared/research/ created"
assert_dir_exists "thoughts/shared/plans" "thoughts/shared/plans/ created"
assert_dir_exists "thoughts/shared/prs" "thoughts/shared/prs/ created"
assert_dir_exists "thoughts/searchable" "thoughts/searchable/ created"
assert_file_exists "thoughts/.gitignore" "thoughts/.gitignore created"
assert_file_exists "thoughts/README.md" "thoughts/README.md created"
assert_contains "thoughts/.gitignore" "searchable/" ".gitignore contains searchable/"

# ============================================================================
# Test 2: thoughts-sync creates hardlinks correctly
# ============================================================================
section "Test 2: thoughts-sync creates hardlinks"

# Create test markdown file
echo "# Test Research Document" > thoughts/shared/research/test.md
echo "This is a test." >> thoughts/shared/research/test.md

# Run sync
thoughts-sync > /dev/null 2>&1

assert_file_exists "thoughts/searchable/shared/research/test.md" "hardlink created in searchable/"
assert_hardlink "thoughts/shared/research/test.md" "thoughts/searchable/shared/research/test.md" "files are hardlinked (same inode)"

# Verify content is identical
if diff thoughts/shared/research/test.md thoughts/searchable/shared/research/test.md > /dev/null 2>&1; then
  echo -e "${GREEN}✓${NC} hardlink content is identical"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} hardlink content differs"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# ============================================================================
# Test 3: thoughts-sync cleans orphaned links
# ============================================================================
section "Test 3: thoughts-sync removes orphaned links"

# Create a file, sync it, then delete source
echo "# Temporary" > thoughts/shared/plans/temp.md
thoughts-sync > /dev/null 2>&1

# Verify it was created
assert_file_exists "thoughts/searchable/shared/plans/temp.md" "temp hardlink created"

# Delete source file
rm thoughts/shared/plans/temp.md

# Run sync again - should clean up orphaned link
output=$(thoughts-sync 2>&1)

assert_file_not_exists "thoughts/searchable/shared/plans/temp.md" "orphaned link removed"
assert_output_contains "$output" "Orphaned links cleaned: 1" "sync reports orphaned link cleaned"

# ============================================================================
# Test 4: thoughts-metadata generates valid metadata
# ============================================================================
section "Test 4: thoughts-metadata generates valid metadata"

output=$(thoughts-metadata 2>&1)

assert_output_contains "$output" "Current Date/Time" "metadata contains date/time"
assert_output_contains "$output" "ISO DateTime" "metadata contains ISO datetime"
assert_output_contains "$output" "Git User: Test User" "metadata contains git user"
assert_output_contains "$output" "Git Email: test@example.com" "metadata contains git email"
assert_output_contains "$output" "Current Git Commit Hash" "metadata contains commit hash"
assert_output_contains "$output" "Current Branch Name" "metadata contains branch name"
assert_output_contains "$output" "Timestamp For Filename" "metadata contains filename timestamp"

# Verify date format (ISO 8601)
if echo "$output" | grep -qE "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"; then
  echo -e "${GREEN}✓${NC} ISO date format is valid"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} ISO date format is invalid"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# ============================================================================
# Test 5: install-scripts.sh installs scripts correctly
# ============================================================================
section "Test 5: install-scripts.sh installs scripts correctly"

# Create fake HOME for installation test
FAKE_HOME="$TEST_DIR/fake-home"
mkdir -p "$FAKE_HOME"

# Run script installer with auto-yes and fake HOME
cd "$PROJECT_ROOT"
HOME="$FAKE_HOME" bash -c "echo 'y' | ./install-scripts.sh > /dev/null 2>&1"

# Check scripts installed
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-init" "thoughts-init installed"
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-sync" "thoughts-sync installed"
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-metadata" "thoughts-metadata installed"

# Check scripts are executable
assert_executable "$FAKE_HOME/.local/bin/thoughts-init" "thoughts-init is executable"
assert_executable "$FAKE_HOME/.local/bin/thoughts-sync" "thoughts-sync is executable"
assert_executable "$FAKE_HOME/.local/bin/thoughts-metadata" "thoughts-metadata is executable"

# ============================================================================
# Test 6: install-scripts.sh creates backup when scripts exist
# ============================================================================
section "Test 6: install-scripts.sh creates backup of existing scripts"

# Create another fake HOME with pre-existing script
FAKE_HOME2="$TEST_DIR/fake-home2"
mkdir -p "$FAKE_HOME2/.local/bin"
echo "OLD SCRIPT" > "$FAKE_HOME2/.local/bin/thoughts-init"

# Run installer again
cd "$PROJECT_ROOT"
HOME="$FAKE_HOME2" bash -c "echo 'y' | ./install-scripts.sh > /dev/null 2>&1"

# Check backup directory was created
backup_dir=$(find "$FAKE_HOME2/.local/bin" -maxdepth 1 -type d -name "backup-*" 2>/dev/null | head -1)
if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
  echo -e "${GREEN}✓${NC} backup directory created"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} backup directory not created"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Check old script is in backup
if [ -n "$backup_dir" ] && [ -f "$backup_dir/thoughts-init" ]; then
  echo -e "${GREEN}✓${NC} old script backed up"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} old script not backed up"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Check new script is installed
assert_file_exists "$FAKE_HOME2/.local/bin/thoughts-init" "new script installed"

# Verify new content (should not be "OLD SCRIPT")
if ! grep -q "OLD SCRIPT" "$FAKE_HOME2/.local/bin/thoughts-init" 2>/dev/null; then
  echo -e "${GREEN}✓${NC} new script has updated content"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} new script still has old content"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# ============================================================================
# Test 7: Plugin manifest validates correctly
# ============================================================================
section "Test 7: Plugin manifest validation"

cd "$PROJECT_ROOT"

# Check .claude-plugin directory exists
assert_dir_exists ".claude-plugin" ".claude-plugin/ directory exists"

# Check plugin.json exists
assert_file_exists ".claude-plugin/plugin.json" "plugin.json exists"

# Validate JSON syntax (if jq available)
if command -v jq >/dev/null 2>&1; then
  if jq empty .claude-plugin/plugin.json 2>/dev/null; then
    echo -e "${GREEN}✓${NC} plugin.json has valid JSON syntax"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}✗${NC} plugin.json has invalid JSON syntax"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  TESTS_RUN=$((TESTS_RUN + 1))
fi

# Check required fields
plugin_content=$(cat .claude-plugin/plugin.json)
assert_output_contains "$plugin_content" '"name"' "manifest contains name field"
assert_output_contains "$plugin_content" '"version"' "manifest contains version field"
assert_output_contains "$plugin_content" '"description"' "manifest contains description field"

# Check marketplace.json exists and is valid
assert_file_exists ".claude-plugin/marketplace.json" "marketplace.json exists"

if command -v jq >/dev/null 2>&1; then
  if jq empty .claude-plugin/marketplace.json 2>/dev/null; then
    echo -e "${GREEN}✓${NC} marketplace.json has valid JSON syntax"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}✗${NC} marketplace.json has invalid JSON syntax"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  TESTS_RUN=$((TESTS_RUN + 1))
fi

# Check commands directory at root
assert_dir_exists "commands" "commands/ directory at root"

# Check agents directory at root
assert_dir_exists "agents" "agents/ directory at root"

# Check bin directory at root
assert_dir_exists "bin" "bin/ directory at root"

# Verify no old .claude/commands or .claude/agents directories
if [ ! -d ".claude/commands" ]; then
  echo -e "${GREEN}✓${NC} old .claude/commands/ removed"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} old .claude/commands/ still exists"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

if [ ! -d ".claude/agents" ]; then
  echo -e "${GREEN}✓${NC} old .claude/agents/ removed"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} old .claude/agents/ still exists"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Verify component counts (expected: 6 commands, 5 agents, 3 scripts)
COMMANDS=$(find commands -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
AGENTS=$(find agents -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
SCRIPTS=$(find bin -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$COMMANDS" -eq 6 ]; then
  echo -e "${GREEN}✓${NC} correct number of commands (6)"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} expected 6 commands, found $COMMANDS"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

if [ "$AGENTS" -eq 5 ]; then
  echo -e "${GREEN}✓${NC} correct number of agents (5)"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} expected 5 agents, found $AGENTS"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

if [ "$SCRIPTS" -eq 3 ]; then
  echo -e "${GREEN}✓${NC} correct number of scripts (3)"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} expected 3 scripts, found $SCRIPTS"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# ============================================================================
# Summary
# ============================================================================

print_summary

if [ "$TESTS_FAILED" -eq 0 ]; then
  echo ""
  echo "✅ All smoke tests passed! Safe to deploy."
  exit 0
else
  echo ""
  echo "❌ Some tests failed. Review output above."
  exit 1
fi
