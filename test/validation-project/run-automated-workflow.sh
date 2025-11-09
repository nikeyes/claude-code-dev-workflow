#!/bin/bash
set -euo pipefail

# Automated workflow runner using claude -p
# Executes Research → Plan → Implement → Validate cycle non-interactively

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/temperature-cli"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=== Automated Workflow Runner ==="
echo ""
echo "Project: ${PROJECT_DIR}"
echo ""

# Check claude is installed
if ! command -v claude &> /dev/null; then
    echo -e "${RED}✗ claude command not found${NC}"
    echo "Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

cd "${PROJECT_DIR}"

# Phase 1: Research
echo -e "${BLUE}--- Phase 1: Research ---${NC}"
echo "Running: claude -p \"/research_codebase\""
echo ""

if claude -p "/research_codebase" --max-turns 10; then
    echo -e "${GREEN}✓ Research completed${NC}"
else
    echo -e "${RED}✗ Research failed${NC}"
    exit 1
fi
echo ""

# Phase 2: Plan
echo -e "${BLUE}--- Phase 2: Plan ---${NC}"
echo "Running: claude -p \"/create_plan 'Add Kelvin temperature scale support'\""
echo ""

if claude -p "/create_plan \"Add Kelvin temperature scale support\"" --max-turns 10; then
    echo -e "${GREEN}✓ Plan created${NC}"
else
    echo -e "${RED}✗ Plan creation failed${NC}"
    exit 1
fi
echo ""

# Find the plan file
PLAN_FILE=$(find thoughts/shared/plans -name "*kelvin*.md" -o -name "*temperature*.md" 2>/dev/null | head -1)

if [[ -z "${PLAN_FILE}" ]]; then
    echo -e "${RED}✗ Plan file not found${NC}"
    echo "Expected: thoughts/shared/plans/*kelvin*.md or *temperature*.md"
    exit 1
fi

echo "Plan file: ${PLAN_FILE}"
echo ""

# Phase 3: Implement
echo -e "${BLUE}--- Phase 3: Implement ---${NC}"
echo "Running: claude -p \"/implement_plan ${PLAN_FILE}\""
echo ""

if claude -p "/implement_plan \"${PLAN_FILE}\"" --max-turns 20; then
    echo -e "${GREEN}✓ Implementation completed${NC}"
else
    echo -e "${RED}✗ Implementation failed${NC}"
    exit 1
fi
echo ""

# Phase 4: Validate
echo -e "${BLUE}--- Phase 4: Validate ---${NC}"
echo "Running: claude -p \"/validate_plan ${PLAN_FILE}\""
echo ""

if claude -p "/validate_plan \"${PLAN_FILE}\"" --max-turns 10; then
    echo -e "${GREEN}✓ Validation completed${NC}"
else
    echo -e "${RED}✗ Validation failed${NC}"
    exit 1
fi
echo ""

echo "==================================="
echo -e "${GREEN}✓ Automated workflow completed successfully${NC}"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Review generated artifacts in thoughts/"
echo "  2. Run: make validate-artifacts"
echo "  3. Check implementation in src/converter.py"
