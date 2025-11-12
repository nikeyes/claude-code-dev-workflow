# Variables
FUNCTIONAL_TEST := test/thoughts-structure-test.sh
STRUCTURE_TEST := test/plugin-structure-test.sh
PLUGIN_MANIFEST := .claude-plugin/plugin.json

# Phony targets
.PHONY: help test test-functional test-structure test-verbose test-plugin check
.PHONY: validate-plugin validate-setup validate-manual validate-artifacts validate-clean

# Default target
help:
	@echo "Claude Code Dev Workflow - Available targets:"
	@echo ""
	@echo "Testing:"
	@echo "  make test               - Run all tests (functional + structure)"
	@echo "  make test-functional    - Run functional tests (thoughts scripts)"
	@echo "  make test-structure     - Run structure validation tests (plugin)"
	@echo "  make test-verbose       - Run functional tests with debug output"
	@echo "  make test-plugin        - Run tests + plugin validation (CI)"
	@echo "  make check              - Run shellcheck on all bash scripts"
	@echo ""
	@echo "Plugin validation:"
	@echo "  make validate-plugin    - Validate plugin manifest"
	@echo ""
	@echo "Validation project (manual E2E):"
	@echo "  make validate-setup     - Setup validation project environment"
	@echo "  make validate-manual    - Show manual workflow test instructions"
	@echo "  make validate-artifacts - Validate workflow artifacts"
	@echo "  make validate-clean     - Clean validation project artifacts"
	@echo ""

# ============================================================================
# Test targets
# ============================================================================

# Run all automated tests
test: test-functional test-structure
	@echo ""
	@echo "✓ All automated tests completed"

# Run functional tests (thoughts scripts)
test-functional:
	@echo "Running functional tests..."
	@$(FUNCTIONAL_TEST)

# Run plugin structure validation tests
test-structure:
	@echo "Running plugin structure tests..."
	@$(STRUCTURE_TEST)

# Run functional tests with verbose output
test-verbose:
	@echo "Running functional tests (verbose mode)..."
	@bash -x $(FUNCTIONAL_TEST)

# Run all tests + plugin validation (for CI)
test-plugin: test check validate-plugin
	@echo ""
	@echo "✓ All plugin tests passed"

# Run shellcheck on all bash scripts
check:
	@echo "Running shellcheck..."
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck skills/thoughts-management/scripts/* test/*.sh && echo "✓ Shellcheck passed"; \
	else \
		echo "⚠ shellcheck not installed, skipping..."; \
		echo "  Install with: brew install shellcheck (macOS) or apt install shellcheck (Linux)"; \
	fi

# ============================================================================
# Plugin validation
# ============================================================================

validate-plugin:
	@echo "Validating plugin manifest..."
	@if command -v jq >/dev/null 2>&1; then \
		jq empty $(PLUGIN_MANIFEST) && echo "✓ Plugin manifest valid"; \
	else \
		echo "⚠ jq not installed, skipping validation"; \
	fi
	@echo "Running claude plugin validate..."; \
	if [ -f "$$HOME/.claude/local/claude" ]; then \
		$$HOME/.claude/local/claude plugin validate . && echo "✓ Claude plugin validation passed"; \
	elif command -v claude >/dev/null 2>&1; then \
		claude plugin validate . && echo "✓ Claude plugin validation passed"; \
	else \
		echo "⚠ claude CLI not available or validation failed (this is optional)"; \
	fi

# ============================================================================
# Manual E2E validation project
# ============================================================================

validate-setup:
	@echo "Setting up validation project..."
	@cd test/validation-project && chmod +x setup.sh && ./setup.sh

validate-manual:
	@echo "Manual workflow test instructions:"
	@cd test/validation-project && chmod +x e2e-workflow-test.sh && ./e2e-workflow-test.sh manual

validate-artifacts:
	@echo "Validating workflow artifacts..."
	@cd test/validation-project && chmod +x validate-workflow-artifacts.sh && ./validate-workflow-artifacts.sh temperature-cli

validate-clean:
	@echo "Cleaning validation artifacts..."
	@cd test/validation-project && chmod +x e2e-workflow-test.sh && ./e2e-workflow-test.sh clean
