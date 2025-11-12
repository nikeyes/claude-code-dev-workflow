#!/usr/bin/env bash
set -euo pipefail

# plugin-structure-test.sh - Structural validation tests for Claude Code plugin
# Validates plugin manifest, command files, agent files, and their consistency

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source test helpers
# shellcheck source=test/test-helpers.sh
source "$SCRIPT_DIR/test-helpers.sh"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Plugin Structure Validation Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# ============================================================================
# Test 1: Plugin manifest exists and is valid JSON
# ============================================================================
section "Test 1: Plugin manifest validation"

assert_file_exists ".claude-plugin/plugin.json" "plugin.json exists"

# Validate JSON syntax
if command -v jq >/dev/null 2>&1; then
	jq empty .claude-plugin/plugin.json 2>/dev/null
	assert_exit_code 0 "plugin.json is valid JSON"
else
	echo "⚠️  jq not installed, skipping JSON validation"
fi

# Extract and validate required fields
if command -v jq >/dev/null 2>&1; then
	NAME=$(jq -r '.name // empty' .claude-plugin/plugin.json)
	VERSION=$(jq -r '.version // empty' .claude-plugin/plugin.json)
	DESCRIPTION=$(jq -r '.description // empty' .claude-plugin/plugin.json)

	assert_not_empty "$NAME" "plugin.json has 'name' field"
	assert_not_empty "$VERSION" "plugin.json has 'version' field"
	assert_not_empty "$DESCRIPTION" "plugin.json has 'description' field"

	# Validate version format (semver-ish)
	if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		pass "Version format is valid: $VERSION"
	else
		fail "Version format invalid (expected semver): $VERSION"
	fi
fi

# ============================================================================
# Test 2: All declared commands have corresponding markdown files
# ============================================================================
section "Test 2: Command files validation"

# Expected commands based on project structure
EXPECTED_COMMANDS=(
	"research_codebase"
	"create_plan"
	"iterate_plan"
	"implement_plan"
	"validate_plan"
	"commit"
)

for cmd in "${EXPECTED_COMMANDS[@]}"; do
	CMD_FILE="commands/${cmd}.md"
	assert_file_exists "$CMD_FILE" "Command file exists: $cmd"

	# Check file is not empty
	if [ -s "$CMD_FILE" ]; then
		pass "Command file not empty: $cmd"
	else
		fail "Command file is empty: $cmd"
	fi

	# Check for frontmatter (optional but recommended)
	if head -n 1 "$CMD_FILE" | grep -q "^---$"; then
		pass "Command has frontmatter: $cmd"
	else
		echo "⚠️  Command missing frontmatter: $cmd (optional)"
	fi
done

# Count total command files
TOTAL_CMD_FILES=$(find commands -name "*.md" -type f | wc -l | tr -d ' ')
EXPECTED_CMD_COUNT=${#EXPECTED_COMMANDS[@]}

if [ "$TOTAL_CMD_FILES" -eq "$EXPECTED_CMD_COUNT" ]; then
	pass "Command file count matches expected: $TOTAL_CMD_FILES"
else
	echo "⚠️  Command file count mismatch: found $TOTAL_CMD_FILES, expected $EXPECTED_CMD_COUNT"
fi

# ============================================================================
# Test 3: All declared agents have corresponding markdown files
# ============================================================================
section "Test 3: Agent files validation"

# Expected agents based on project structure
EXPECTED_AGENTS=(
	"codebase-locator"
	"codebase-analyzer"
	"codebase-pattern-finder"
	"thoughts-locator"
	"thoughts-analyzer"
)

for agent in "${EXPECTED_AGENTS[@]}"; do
	AGENT_FILE="agents/${agent}.md"
	assert_file_exists "$AGENT_FILE" "Agent file exists: $agent"

	# Check file is not empty
	if [ -s "$AGENT_FILE" ]; then
		pass "Agent file not empty: $agent"
	else
		fail "Agent file is empty: $agent"
	fi

	# Check for frontmatter (required for agents)
	if head -n 1 "$AGENT_FILE" | grep -q "^---$"; then
		pass "Agent has frontmatter: $agent"
	else
		fail "Agent missing frontmatter: $agent (required)"
	fi
done

# Count total agent files
TOTAL_AGENT_FILES=$(find agents -name "*.md" -type f | wc -l | tr -d ' ')
EXPECTED_AGENT_COUNT=${#EXPECTED_AGENTS[@]}

if [ "$TOTAL_AGENT_FILES" -eq "$EXPECTED_AGENT_COUNT" ]; then
	pass "Agent file count matches expected: $TOTAL_AGENT_FILES"
else
	echo "⚠️  Agent file count mismatch: found $TOTAL_AGENT_FILES, expected $EXPECTED_AGENT_COUNT"
fi

# ============================================================================
# Test 4: Bash scripts in Skill exist and are executable
# ============================================================================
section "Test 4: Skill scripts validation"

EXPECTED_SCRIPTS=(
	"skills/thoughts-management/scripts/thoughts-init"
	"skills/thoughts-management/scripts/thoughts-sync"
	"skills/thoughts-management/scripts/thoughts-metadata"
)

# Optional scripts (nice to have but not required)
OPTIONAL_SCRIPTS=(
	# None currently
)

for script in "${EXPECTED_SCRIPTS[@]}"; do
	assert_file_exists "$script" "Script exists: $script"

	# Check executable permission
	if [ -x "$script" ]; then
		pass "Script is executable: $script"
	else
		fail "Script not executable: $script"
	fi

	# Check shebang
	if head -n 1 "$script" | grep -q "^#!.*bash"; then
		pass "Script has bash shebang: $script"
	else
		fail "Script missing bash shebang: $script"
	fi
done

# Check optional scripts (if any exist)
if [ ${#OPTIONAL_SCRIPTS[@]} -gt 0 ]; then
	for script in "${OPTIONAL_SCRIPTS[@]}"; do
		if [ -f "$script" ]; then
			pass "Optional script exists: $script"
			if [ -x "$script" ]; then
				pass "Optional script is executable: $script"
			fi
		else
			echo "⚠️  Optional script missing: $script (not required)"
		fi
	done
fi

# ============================================================================
# Test 5: Skill structure validation
# ============================================================================
section "Test 5: Skill validation"

# Check Skill directory exists
assert_dir_exists "skills/thoughts-management" "Skill directory exists"

# Check SKILL.md exists
assert_file_exists "skills/thoughts-management/SKILL.md" "SKILL.md exists"

# Check SKILL.md has valid frontmatter
if grep -q "^---$" "skills/thoughts-management/SKILL.md" && \
   grep -q "^name: thoughts-management$" "skills/thoughts-management/SKILL.md" && \
   grep -q "^description:" "skills/thoughts-management/SKILL.md"; then
	pass "SKILL.md has valid frontmatter"
else
	fail "SKILL.md missing valid frontmatter"
fi

# Check scripts directory exists
assert_dir_exists "skills/thoughts-management/scripts" "Skill scripts directory exists"

# ============================================================================
# Test 6: Documentation files exist
# ============================================================================
section "Test 6: Documentation validation"

EXPECTED_DOCS=(
	"README.md"
	"CLAUDE.md"
)

for doc in "${EXPECTED_DOCS[@]}"; do
	assert_file_exists "$doc" "Documentation exists: $doc"

	# Check file is not trivially small
	DOC_SIZE=$(wc -c < "$doc" | tr -d ' ')
	if [ "$DOC_SIZE" -gt 100 ]; then
		pass "Documentation has content: $doc (${DOC_SIZE} bytes)"
	else
		fail "Documentation too small: $doc (${DOC_SIZE} bytes)"
	fi
done

# ============================================================================
# Test 7: Cross-reference validation
# ============================================================================
section "Test 7: Cross-reference validation"

# Check that README mentions all commands
for cmd in "${EXPECTED_COMMANDS[@]}"; do
	if grep -q "/$cmd" README.md; then
		pass "README mentions command: /$cmd"
	else
		echo "⚠️  README doesn't mention command: /$cmd"
	fi
done

# Check that CLAUDE.md is comprehensive
if grep -q "commands/" CLAUDE.md && grep -q "agents/" CLAUDE.md; then
	pass "CLAUDE.md documents project structure"
else
	echo "⚠️  CLAUDE.md may be missing structure documentation"
fi

# ============================================================================
# Test 7: Version consistency
# ============================================================================
section "Test 7: Version consistency check"

# Check if VERSION file exists
if [ -f ".version" ]; then
	VERSION_FILE=$(cat .version)
	pass "Version file exists: $VERSION_FILE"

	# Compare with plugin.json version if jq available
	if command -v jq >/dev/null 2>&1; then
		PLUGIN_VERSION=$(jq -r '.version' .claude-plugin/plugin.json)
		if [ "$VERSION_FILE" = "$PLUGIN_VERSION" ]; then
			pass "Version consistency: .version matches plugin.json"
		else
			echo "⚠️  Version mismatch: .version=$VERSION_FILE, plugin.json=$PLUGIN_VERSION"
		fi
	fi
else
	echo "⚠️  .version file not found (created after installation)"
fi

# ============================================================================
# Test 8: Gitignore and Git setup
# ============================================================================
section "Test 8: Git configuration validation"

assert_file_exists ".gitignore" ".gitignore exists"

# Check that important paths are ignored
SHOULD_IGNORE=(
	".DS_Store"
	"*.swp"
	".version"
)

for pattern in "${SHOULD_IGNORE[@]}"; do
	if grep -q "$pattern" .gitignore; then
		pass ".gitignore contains: $pattern"
	else
		echo "⚠️  .gitignore missing pattern: $pattern"
	fi
done

# ============================================================================
# Test 9: Command content validation (basic checks)
# ============================================================================
section "Test 9: Command content validation"

for cmd in "${EXPECTED_COMMANDS[@]}"; do
	CMD_FILE="commands/${cmd}.md"

	# Check for common required patterns
	if grep -q "Instructions" "$CMD_FILE" || grep -q "instructions" "$CMD_FILE"; then
		pass "Command has instructions section: $cmd"
	else
		echo "⚠️  Command may be missing instructions: $cmd"
	fi

	# Check word count (should be substantial)
	WORD_COUNT=$(wc -w < "$CMD_FILE" | tr -d ' ')
	if [ "$WORD_COUNT" -gt 100 ]; then
		pass "Command has substantial content: $cmd ($WORD_COUNT words)"
	else
		echo "⚠️  Command may be too short: $cmd ($WORD_COUNT words)"
	fi
done

# ============================================================================
# Test 10: Agent frontmatter validation
# ============================================================================
section "Test 10: Agent frontmatter validation"

for agent in "${EXPECTED_AGENTS[@]}"; do
	AGENT_FILE="agents/${agent}.md"

	# Extract frontmatter (lines between first two ---)
	if head -n 20 "$AGENT_FILE" | grep -q "name:"; then
		pass "Agent has 'name' in frontmatter: $agent"
	else
		fail "Agent missing 'name' in frontmatter: $agent"
	fi

	if head -n 20 "$AGENT_FILE" | grep -q "description:"; then
		pass "Agent has 'description' in frontmatter: $agent"
	else
		fail "Agent missing 'description' in frontmatter: $agent"
	fi

	if head -n 20 "$AGENT_FILE" | grep -q "tools:"; then
		pass "Agent declares tools in frontmatter: $agent"
	else
		echo "⚠️  Agent may be missing 'tools' declaration: $agent"
	fi
done

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_summary_named "Plugin Structure Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit "$FAILURES"
