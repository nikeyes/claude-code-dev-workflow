# Variables
FUNCTIONAL_TEST := test/thoughts-structure-test.sh
STRUCTURE_TEST := test/plugin-structure-test.sh
MARKETPLACE_MANIFEST := .claude-plugin/marketplace.json
PLUGIN_MANIFESTS := core/.claude-plugin/plugin.json git/.claude-plugin/plugin.json web/.claude-plugin/plugin.json research/.claude-plugin/plugin.json

# Eval viewer
SKILL_CREATOR_PATH ?= $(HOME)/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator
GENERATE_REVIEW := $(SKILL_CREATOR_PATH)/eval-viewer/generate_review.py
ITER ?= LAST

# Phony targets
.PHONY: help test test-verbose check ci eval-list eval-view

# Default target
help:
	@echo "Claude Code Dev Workflow - Available targets:"
	@echo ""
	@echo "  make test               - Run all tests (default)"
	@echo "  make test-verbose       - Run tests with debug output"
	@echo "  make check              - Run shellcheck on all bash scripts"
	@echo "  make ci                 - Run full CI validation (test + check + plugin)"
	@echo ""
	@echo "Eval viewer:"
	@echo "  make eval-list                                      - List skills with eval iterations"
	@echo "  make eval-view SKILL=test-desiderata                - View latest iteration"
	@echo "  make eval-view SKILL=test-desiderata ITER=1         - View specific iteration"
	@echo "  make eval-view SKILL=test-desiderata PREV=1         - Compare latest vs iteration-1"
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

# ============================================================================
# Eval viewer targets
# ============================================================================

_check-skill:
ifndef SKILL
	$(error SKILL is required. Usage: make eval-view SKILL=test-desiderata)
endif

_check-viewer:
	@test -f "$(GENERATE_REVIEW)" || (echo "Error: generate_review.py not found at $(GENERATE_REVIEW)" && echo "Set SKILL_CREATOR_PATH to your skill-creator directory" && exit 1)

eval-list:
	@for ws in */skills/*-workspace; do \
		skill=$$(basename "$$ws" | sed 's/-workspace$$//'); \
		iters=$$(ls -d "$$ws"/iteration-* 2>/dev/null | sort -V); \
		if [ -n "$$iters" ]; then \
			count=$$(echo "$$iters" | wc -l | tr -d ' '); \
			last=$$(echo "$$iters" | tail -1 | xargs basename); \
			echo "  $$skill  ($$count iterations, latest: $$last)"; \
		fi; \
	done

eval-view: _check-skill _check-viewer
	$(eval _WS := $(shell ls -d */skills/$(SKILL)-workspace 2>/dev/null | head -1))
	$(eval _RESOLVED_ITER := $(if $(filter LAST,$(ITER)),$(shell ls -d $(_WS)/iteration-* 2>/dev/null | sort -V | tail -1 | xargs basename),iteration-$(ITER)))
	@python "$(GENERATE_REVIEW)" "$(_WS)/$(_RESOLVED_ITER)" \
		--skill-name "$(SKILL)" \
		--benchmark "$(_WS)/$(_RESOLVED_ITER)/benchmark.json" \
		$(if $(PREV),--previous-workspace "$(_WS)/iteration-$(PREV)")
