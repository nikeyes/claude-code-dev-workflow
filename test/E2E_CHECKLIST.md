# Testing Checklist

## Automated Tests

Run before every commit:

```bash
make test            # 61 automated tests (~3 sec)
make check           # Shellcheck validation
make validate-plugin # Plugin manifest validation
```

## Manual Plugin Tests

Cannot be automated (require Claude Code):

### Installation
- [ ] `/plugin marketplace add nikey-es/claude-code-dev-workflow`
- [ ] `/plugin install workflow-dev@workflow-dev-marketplace`
- [ ] Restart Claude Code
- [ ] `/help` shows 6 commands
- [ ] `./install-scripts.sh` installs scripts
- [ ] `which thoughts-init` finds scripts

### Workflow
- [ ] `thoughts-init` creates directory structure
- [ ] `/research_codebase test` generates document
- [ ] `/create_plan test` generates plan
- [ ] Agents spawn correctly
- [ ] `thoughts-sync` creates hardlinks

### Lifecycle
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
