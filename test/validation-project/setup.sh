#!/bin/bash
set -euo pipefail

# Setup script for validation project
# Prepares environment for E2E workflow testing

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/temperature-cli"

echo "=== Setting up validation project ==="

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Install dependencies
cd "${PROJECT_DIR}"
echo "Installing dependencies..."
pip3 install -q -r requirements.txt

# Run initial tests to verify baseline
echo "Running baseline tests..."
if ! pytest tests/ -v; then
    echo "ERROR: Baseline tests failed"
    exit 1
fi

# Initialize thoughts directory structure
echo "Initializing thoughts/ structure..."
cd "${SCRIPT_DIR}/.."
if command -v thoughts-init &> /dev/null; then
    thoughts-init
else
    echo "WARNING: thoughts-init not found in PATH"
    echo "Run 'make install' from project root first"
fi

echo ""
echo "=== Setup complete ==="
echo "Project: ${PROJECT_DIR}"
echo "Next steps:"
echo "  1. Run workflow commands (/research_codebase, /create_plan, etc.)"
echo "  2. Validate with: ./validate-workflow-artifacts.sh"
