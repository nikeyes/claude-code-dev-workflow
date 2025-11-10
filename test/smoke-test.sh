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
# Test 5: install.sh copies files correctly
# ============================================================================
section "Test 5: install.sh installs files correctly"

# Create fake HOME for installation test
FAKE_HOME="$TEST_DIR/fake-home"
mkdir -p "$FAKE_HOME"

# Run installer with auto-yes and fake HOME
cd "$PROJECT_ROOT"
HOME="$FAKE_HOME" bash -c "echo 'y' | ./install.sh > /dev/null 2>&1"

# Check commands installed
assert_file_exists "$FAKE_HOME/.claude/commands/research_codebase.md" "research_codebase.md installed"
assert_file_exists "$FAKE_HOME/.claude/commands/create_plan.md" "create_plan.md installed"
assert_file_exists "$FAKE_HOME/.claude/commands/iterate_plan.md" "iterate_plan.md installed"
assert_file_exists "$FAKE_HOME/.claude/commands/implement_plan.md" "implement_plan.md installed"
assert_file_exists "$FAKE_HOME/.claude/commands/validate_plan.md" "validate_plan.md installed"
assert_file_exists "$FAKE_HOME/.claude/commands/commit.md" "commit.md installed"

# Check agents installed
assert_file_exists "$FAKE_HOME/.claude/agents/codebase-locator.md" "codebase-locator.md installed"
assert_file_exists "$FAKE_HOME/.claude/agents/codebase-analyzer.md" "codebase-analyzer.md installed"
assert_file_exists "$FAKE_HOME/.claude/agents/codebase-pattern-finder.md" "codebase-pattern-finder.md installed"
assert_file_exists "$FAKE_HOME/.claude/agents/thoughts-locator.md" "thoughts-locator.md installed"
assert_file_exists "$FAKE_HOME/.claude/agents/thoughts-analyzer.md" "thoughts-analyzer.md installed"

# Check scripts installed
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-init" "thoughts-init installed"
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-sync" "thoughts-sync installed"
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-metadata" "thoughts-metadata installed"
assert_file_exists "$FAKE_HOME/.local/bin/thoughts-version" "thoughts-version installed"

# Check scripts are executable
assert_executable "$FAKE_HOME/.local/bin/thoughts-init" "thoughts-init is executable"
assert_executable "$FAKE_HOME/.local/bin/thoughts-sync" "thoughts-sync is executable"
assert_executable "$FAKE_HOME/.local/bin/thoughts-metadata" "thoughts-metadata is executable"
assert_executable "$FAKE_HOME/.local/bin/thoughts-version" "thoughts-version is executable"

# Check VERSION file installed
assert_file_exists "$FAKE_HOME/.claude/claude-code-dev-workflow-version" "VERSION file installed"

# ============================================================================
# Test 6: VERSION file format and thoughts-version script
# ============================================================================
section "Test 6: VERSION file format and thoughts-version"

# Check VERSION file format
version_content=$(cat "$FAKE_HOME/.claude/claude-code-dev-workflow-version")
assert_output_contains "$version_content" "version=" "VERSION contains version field"
assert_output_contains "$version_content" "installed=" "VERSION contains installed field"
assert_output_contains "$version_content" "commit=" "VERSION contains commit field"

# Test thoughts-version with matching versions (up-to-date scenario)
cd "$PROJECT_ROOT"
HOME="$FAKE_HOME" bash -c "PATH=\"$FAKE_HOME/.local/bin:\$PATH\" thoughts-version > /dev/null 2>&1"
version_exit=$?

if [ $version_exit -eq 0 ] || [ $version_exit -eq 1 ]; then
  echo -e "${GREEN}✓${NC} thoughts-version executes without errors"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} thoughts-version returned unexpected exit code: $version_exit"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# ============================================================================
# Test 7: install.sh creates backup when files exist
# ============================================================================
section "Test 7: install.sh creates backup of existing files"

# Create another fake HOME with pre-existing file
FAKE_HOME2="$TEST_DIR/fake-home2"
mkdir -p "$FAKE_HOME2/.claude/commands"
echo "OLD CONTENT" > "$FAKE_HOME2/.claude/commands/research_codebase.md"

# Run installer again
cd "$PROJECT_ROOT"
HOME="$FAKE_HOME2" bash -c "echo 'y' | ./install.sh > /dev/null 2>&1"

# Check backup directory was created (it will have a timestamp)
backup_dir=$(find "$FAKE_HOME2" -maxdepth 1 -type d -name ".claude-workflow-backup-*" 2>/dev/null | head -1)
if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
  echo -e "${GREEN}✓${NC} backup directory created"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} backup directory not created"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Check old file is in backup
if [ -n "$backup_dir" ] && [ -f "$backup_dir/.claude/commands/research_codebase.md" ]; then
  echo -e "${GREEN}✓${NC} old file backed up"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} old file not backed up"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# Check new file is installed
assert_file_exists "$FAKE_HOME2/.claude/commands/research_codebase.md" "new file installed"

# Verify new content (should not be "OLD CONTENT")
if ! grep -q "OLD CONTENT" "$FAKE_HOME2/.claude/commands/research_codebase.md" 2>/dev/null; then
  echo -e "${GREEN}✓${NC} new file has updated content"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}✗${NC} new file still has old content"
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
