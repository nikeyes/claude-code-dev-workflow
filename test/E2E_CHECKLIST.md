# Testing Checklist

## Automated Tests

Run before every commit:

```bash
make test-functional # 33 functional tests for thoughts scripts (~3 sec)
make test-structure  # 91 plugin structure validation tests (~1 sec)
make check           # Shellcheck validation
make validate-plugin # Plugin manifest validation

# Or run all at once:
make test-plugin     # Runs all automated tests above (124 total assertions)
```

## Manual Plugin Tests

**These tests require Claude Code runtime and cannot be automated:**

### Installation & Setup
- [ ] `/plugin install workflow-dev@workflow-dev-marketplace`
- [ ] Restart Claude Code
- [ ] `/help` shows 6 commands (automated test verifies files exist)
- [ ] `./install-scripts.sh` installs scripts (automated test verifies script works)

### Workflow Quality (LLM behavior)
- [ ] `/stepwise-dev:research_codebase [real topic]` - Verify research document quality
- [ ] `/stepwise-dev:create_plan [from ticket]` - Verify plan is actionable and thorough
- [ ] Agents spawn correctly and run in parallel
- [ ] Context management warnings appear appropriately

### Plugin Lifecycle
- [ ] `/plugin disable workflow-dev@workflow-dev-marketplace`
- [ ] Commands disappear from `/help`
- [ ] `/plugin enable workflow-dev@workflow-dev-marketplace`
- [ ] Commands return

## Before Release

- [ ] All automated tests pass
- [ ] Manual tests complete
- [ ] Documentation accurate
- [ ] Version numbers consistent
- [ ] No sensitive data

## Notes

Record issues found:
-
-
