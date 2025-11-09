#!/usr/bin/env bash
# test-helpers.sh - Helper functions for smoke tests

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Assert that a file exists
# Usage: assert_file_exists PATH "description"
assert_file_exists() {
  local file="$1"
  local desc="${2:-file exists: $file}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if [ -f "$file" ]; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (file not found: $file)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Assert that a directory exists
# Usage: assert_dir_exists PATH "description"
assert_dir_exists() {
  local dir="$1"
  local desc="${2:-directory exists: $dir}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if [ -d "$dir" ]; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (directory not found: $dir)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Assert that a file is executable
# Usage: assert_executable PATH "description"
assert_executable() {
  local file="$1"
  local desc="${2:-file is executable: $file}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if [ -x "$file" ]; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (not executable: $file)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Assert that a file contains a pattern
# Usage: assert_contains FILE PATTERN "description"
assert_contains() {
  local file="$1"
  local pattern="$2"
  local desc="${3:-file contains pattern: $pattern}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if grep -q "$pattern" "$file" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (pattern not found: $pattern in $file)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Assert that two files are hardlinked (same inode)
# Usage: assert_hardlink FILE1 FILE2 "description"
assert_hardlink() {
  local file1="$1"
  local file2="$2"
  local desc="${3:-files are hardlinked}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if [ "$file1" -ef "$file2" ]; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (not same inode: $file1 vs $file2)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Assert that a file does NOT exist
# Usage: assert_file_not_exists PATH "description"
assert_file_not_exists() {
  local file="$1"
  local desc="${2:-file does not exist: $file}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if [ ! -e "$file" ]; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (file exists: $file)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Assert that output contains a pattern
# Usage: assert_output_contains OUTPUT PATTERN "description"
assert_output_contains() {
  local output="$1"
  local pattern="$2"
  local desc="${3:-output contains: $pattern}"

  TESTS_RUN=$((TESTS_RUN + 1))

  if echo "$output" | grep -q "$pattern"; then
    echo -e "${GREEN}✓${NC} $desc"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}✗${NC} $desc (pattern not found in output)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

# Setup a git repository in a directory
# Usage: setup_git_repo DIR
setup_git_repo() {
  local dir="$1"

  cd "$dir" || return
  git init > /dev/null 2>&1
  git config user.name "Test User" > /dev/null 2>&1
  git config user.email "test@example.com" > /dev/null 2>&1
}

# Print test summary
# Usage: print_summary
print_summary() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Test Summary:"
  echo "  Total: $TESTS_RUN"
  echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"

  if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 1
  else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 0
  fi
}

# Section header
# Usage: section "Test Name"
section() {
  echo ""
  echo -e "${YELLOW}▶ $1${NC}"
}
