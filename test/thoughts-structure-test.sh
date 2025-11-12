#!/usr/bin/env bash
set -euo pipefail

# thoughts-functional-test.sh - Functional tests for thoughts/ bash scripts
# Tests thoughts-init, thoughts-sync, thoughts-metadata, and install-scripts.sh
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

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  Thoughts Scripts - Functional Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test directory: $TEST_DIR"
echo ""

# Use scripts from the Skill directory
SCRIPTS_DIR="$PROJECT_ROOT/skills/thoughts-management/scripts"
export PATH="$SCRIPTS_DIR:$PATH"

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
# Summary
# ============================================================================

print_summary

if [ "$TESTS_FAILED" -eq 0 ]; then
  echo ""
  echo "✅ All functional tests passed!"
  exit 0
else
  echo ""
  echo "❌ Some tests failed. Review output above."
  exit 1
fi
