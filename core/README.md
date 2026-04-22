# Stepwise Core Plugin

Core workflow plugin for structured development following the Research → Plan → Implement → Validate cycle.

## What's Included

### Commands (5)
- `/stepwise-core:research_codebase` - Document codebase as-is with comprehensive research
- `/stepwise-core:create_plan` - Create detailed implementation plans iteratively
- `/stepwise-core:iterate_plan` - Update existing implementation plans
- `/stepwise-core:implement_plan` - Execute plans phase by phase with validation
- `/stepwise-core:validate_plan` - Validate implementation against plan

### Agents (5)
- `codebase-locator` - Find WHERE code lives in the codebase
- `codebase-analyzer` - Understand HOW code works
- `codebase-pattern-finder` - Find similar patterns to model after
- `thoughts-locator` - Discover documents in thoughts/
- `thoughts-analyzer` - Extract insights from thoughts docs

### Skills (1)
- `thoughts-management` - Manage thoughts/ directory with 2 bash scripts:
  - `thoughts-init` - Initialize thoughts/ structure
  - `thoughts-metadata` - Generate git metadata

## Installation

```bash
# Add marketplace
/plugin marketplace add nikeyes/stepwise-dev

# Install this plugin
/plugin install stepwise-core@stepwise-dev
```

## Quick Start

```bash
# 1. Research
/stepwise-core:research_codebase How does authentication work?

# 2. Plan
/stepwise-core:create_plan Add OAuth support

# 3. Implement
/stepwise-core:implement_plan @thoughts/shared/plans/YYYY-MM-DD-oauth.md

# 4. Validate
/stepwise-core:validate_plan @thoughts/shared/plans/YYYY-MM-DD-oauth.md
```

## Philosophy

- Keep context < 60% (attention threshold)
- Split work into phases
- Clear between phases, save to thoughts/
- Never lose research or decisions

## Related Plugins

- **stepwise-git**: Git commit workflow without Claude attribution
- **stepwise-web**: Web search and research capabilities

## License

Apache License 2.0 - See LICENSE file for details.
