# Variables
FUNCTIONAL_TEST := test/thoughts-structure-test.sh
STRUCTURE_TEST := test/plugin-structure-test.sh
MARKETPLACE_MANIFEST := .claude-plugin/marketplace.json
PLUGIN_MANIFESTS := core/.claude-plugin/plugin.json git/.claude-plugin/plugin.json web/.claude-plugin/plugin.json research/.claude-plugin/plugin.json

# Phony targets
.PHONY: help test test-verbose check ci

# Default target
help:
	@echo "Claude Code Dev Workflow - Available targets:"
	@echo ""
	@echo "  make test               - Run all tests (default)"
	@echo "  make test-verbose       - Run tests with debug output"
	@echo "  make check              - Run shellcheck on all bash scripts"
	@echo "  make ci                 - Run full CI validation (test + check + plugin)"
	@echo ""

# ============================================================================
# Test targets
# ============================================================================

# Run all automated tests (functional + structure)
test:
	@echo "Running functional tests..."
	@$(FUNCTIONAL_TEST)
	@echo "Running plugin structure tests..."
	@$(STRUCTURE_TEST)
	@echo ""
	@echo "✓ All automated tests completed"

# Run tests with verbose debug output
test-verbose:
	@echo "Running functional tests (verbose mode)..."
	@bash -x $(FUNCTIONAL_TEST)
	@echo "Running plugin structure tests (verbose mode)..."
	@bash -x $(STRUCTURE_TEST)

# Run shellcheck on all bash scripts
check:
	@echo "Running shellcheck..."
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck core/skills/thoughts-management/scripts/* test/*.sh && echo "✓ Shellcheck passed"; \
	else \
		echo "⚠ shellcheck not installed, skipping..."; \
		echo "  Install with: brew install shellcheck (macOS) or apt install shellcheck (Linux)"; \
	fi

# Full CI validation (test + check + plugin manifest validation)
ci: test check
	@echo "Validating marketplace manifest..."
	@if command -v jq >/dev/null 2>&1; then \
		jq empty $(MARKETPLACE_MANIFEST) && echo "✓ Marketplace manifest valid"; \
	else \
		echo "⚠ jq not installed, skipping validation"; \
	fi
	@echo "Validating plugin manifests..."
	@if command -v jq >/dev/null 2>&1; then \
		for manifest in $(PLUGIN_MANIFESTS); do \
			echo "  Checking $$manifest..."; \
			jq empty $$manifest || exit 1; \
		done; \
		echo "✓ All plugin manifests valid"; \
	else \
		echo "⚠ jq not installed, skipping validation"; \
	fi
	@echo ""
	@echo "✓ All CI checks passed"
