# Validation Project

End-to-end testing framework for the claude-code-dev-workflow tooling.

## Overview

This directory contains a **validation project** that exercises the complete workflow cycle:

```
Research → Plan → Implement → Validate
```

The validation project is a simple Python CLI tool (temperature converter) with intentionally missing features, designed to test the workflow's ability to:

1. Research an existing codebase
2. Create implementation plans
3. Implement missing features
4. Validate success criteria

## Project Structure

```
validation-project/
├── temperature-cli/           # Python project to test against
│   ├── src/converter.py       # Intentionally incomplete (missing Kelvin)
│   ├── tests/test_converter.py
│   ├── requirements.txt
│   └── README.md
├── setup.sh                   # Initialize validation environment
├── validate-workflow-artifacts.sh  # Check generated artifacts
├── e2e-workflow-test.sh       # Test orchestrator
└── README.md                  # This file
```

## Quick Start

### 1. Setup Environment

```bash
make validate-setup
```

This will:
- Install Python dependencies
- Run baseline tests (should pass 8 tests)
- Initialize `thoughts/` directory structure

### 2. Run Workflow

**Option A: Automated (Recommended)**

```bash
make validate-automated
```

This automatically executes all workflow phases using `claude -p`:
- Phase 1: `/research_codebase`
- Phase 2: `/create_plan "Add Kelvin temperature scale support"`
- Phase 3: `/implement_plan thoughts/shared/plans/<plan>.md`
- Phase 4: `/validate_plan thoughts/shared/plans/<plan>.md`

**Option B: Manual**

```bash
make validate-manual
```

Shows instructions for running workflow commands interactively in Claude Code:

```bash
# In Claude Code interactive mode
cd test/validation-project/temperature-cli
/research_codebase
/create_plan "Add Kelvin temperature scale support"
/implement_plan thoughts/shared/plans/<plan-file>.md
/validate_plan thoughts/shared/plans/<plan-file>.md
```

### 3. Validate Artifacts

After completing the workflow (automated or manual):

```bash
make validate-artifacts
```

This checks:
- ✓ Research document exists (`thoughts/shared/research/temperature-cli.md`)
- ✓ Plan document exists with success criteria and implementation steps
- ✓ Kelvin conversion functions implemented
- ✓ Kelvin tests implemented
- ✓ All tests pass

### 4. Clean Up

```bash
make validate-clean
```

Removes generated artifacts and cache files.

## Complete Automated Test

Run the entire cycle with a single command:

```bash
make validate-setup && make validate-automated && make validate-artifacts
```

This will:
1. Setup the environment
2. Execute the workflow automatically
3. Validate all artifacts were created correctly

## What Gets Validated

### Phase 1: Research
- `thoughts/shared/research/temperature-cli.md` exists
- Contains "## Architecture" section
- Contains "## Key Files" section

### Phase 2: Plan
- `thoughts/shared/plans/*kelvin*.md` or `*temperature*.md` exists
- Contains "## Success Criteria"
- Contains "## Implementation Steps"

### Phase 3: Implementation
- `celsius_to_kelvin()` and `kelvin_to_celsius()` functions exist
- Test classes `TestCelsiusToKelvin` and `TestKelvinToCelsius` exist
- All pytest tests pass

### Phase 4: Validation
- Optional validation report in `thoughts/shared/plans/`

## Test Scripts

### `setup.sh`
Prepares the validation environment:
- Checks Python installation
- Installs dependencies
- Runs baseline tests
- Initializes thoughts directory

### `validate-workflow-artifacts.sh`
Validates workflow outputs:
- Checks file existence
- Searches for required content patterns
- Runs tests
- Returns exit code 0 (success) or 1 (failure)

### `e2e-workflow-test.sh`
Orchestrates the complete test cycle:

```bash
./e2e-workflow-test.sh setup      # Run setup
./e2e-workflow-test.sh manual     # Show instructions
./e2e-workflow-test.sh automated  # Execute workflow with claude -p
./e2e-workflow-test.sh validate   # Check artifacts
./e2e-workflow-test.sh clean      # Clean up
./e2e-workflow-test.sh full       # Interactive full cycle
```

### `run-automated-workflow.sh`
Automated workflow runner using `claude -p`:
- Executes all 4 workflow phases sequentially
- Uses slash commands: `/research_codebase`, `/create_plan`, `/implement_plan`, `/validate_plan`
- Sets `--max-turns` limits for each phase
- Provides colored output for progress tracking
- Exits on first failure for fast feedback

## The Temperature CLI Project

### Current Features
- Convert Celsius ↔ Fahrenheit
- CLI interface: `python -m src.converter --celsius 25`
- 8 passing unit tests

### Intentionally Missing
- Kelvin temperature scale support
- `celsius_to_kelvin()` function
- `kelvin_to_celsius()` function
- `--kelvin` CLI argument
- Kelvin unit tests

These gaps are **by design** to give the workflow real work to do.

## Integration with Main Project

These validation tests are integrated into the main project's Makefile:

```bash
# From project root
make validate-setup      # Setup
make validate-manual     # Instructions (manual mode)
make validate-automated  # Execute workflow (automated mode)
make validate-artifacts  # Validate
make validate-clean      # Clean
```

## Continuous Integration

The validation project supports **two execution modes**:

### Automated Mode (CI-friendly)
Uses `claude -p` to execute workflow non-interactively:
- ✅ Can run in CI/CD pipelines
- ✅ Deterministic execution
- ✅ Fast feedback (<5 minutes typically)
- ✅ No human intervention needed

### Manual Mode (Development)
Interactive Claude Code sessions:
- ✅ Real-world workflow patterns
- ✅ Human decision-making during planning
- ✅ Exploratory testing
- ✅ UI/UX validation

**Recommended for CI:**
```bash
make validate-setup && make validate-automated && make validate-artifacts
```

## Troubleshooting

### Setup fails with Python errors
- Ensure Python 3.7+ is installed: `python3 --version`
- Check pip is available: `pip3 --version`

### Baseline tests fail
- Check you're in the right directory
- Verify `requirements.txt` installed correctly
- Run `pytest tests/ -v` manually for details

### Validation fails
- Ensure you've run all workflow commands in Claude Code
- Check `thoughts/shared/research/` for research docs
- Check `thoughts/shared/plans/` for plan docs
- Verify implementation with `grep -r "kelvin" temperature-cli/src/`

### thoughts-init not found
- Run `make install` from project root
- Ensure `~/.local/bin` is in your PATH
- Check installation with `which thoughts-init`

## Design Goals

This validation project follows these principles:

1. **Simple enough to understand quickly** - Temperature conversion is universally understood
2. **Complex enough to be realistic** - Multiple functions, tests, CLI interface
3. **Clear success criteria** - Binary pass/fail for each phase
4. **Reproducible** - Same starting state every time
5. **Fast feedback** - Full cycle completes in minutes

## Contributing

When modifying validation tests:

1. Update this README with any new validation checks
2. Ensure shellcheck passes: `shellcheck test/validation-project/*.sh`
3. Test the full cycle manually before committing
4. Update Makefile targets if adding new scripts
