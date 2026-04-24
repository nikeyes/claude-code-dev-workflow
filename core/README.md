# Stepwise Core Plugin

Core workflow plugin for structured development following the Research → Plan → Implement → Validate cycle.

## What's Included

### Skills (11)
- `/stepwise-core:research-codebase` - Document codebase as-is with comprehensive research
- `/stepwise-core:create-plan` - Create detailed implementation plans iteratively
- `/stepwise-core:iterate-plan` - Update existing implementation plans
- `/stepwise-core:implement-plan` - Execute plans phase by phase with validation
- `/stepwise-core:validate-plan` - Validate implementation against plan
- `thoughts-management` - Manage thoughts/ directory (auto-triggered)
- `bugmagnet` - Comprehensive test coverage and bug discovery
- `hamburger-method` - Vertical story slicing
- `small-safe-steps` - Break work into safe deployable increments
- `story-splitting` - Detect and split oversized stories
- `test-desiderata` - Analyze test quality using Kent Beck's framework

### Agents (5)
- `codebase-locator` - Find WHERE code lives in the codebase
- `codebase-analyzer` - Understand HOW code works
- `codebase-pattern-finder` - Find similar patterns to model after
- `thoughts-locator` - Discover documents in thoughts/
- `thoughts-analyzer` - Extract insights from thoughts docs

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
/stepwise-core:research-codebase How does authentication work?

# 2. Plan
/stepwise-core:create-plan Add OAuth support

# 3. Implement
/stepwise-core:implement-plan @thoughts/shared/plans/YYYY-MM-DD-oauth.md

# 4. Validate
/stepwise-core:validate-plan @thoughts/shared/plans/YYYY-MM-DD-oauth.md
```

## Philosophy

- Keep context < 60% (attention threshold)
- Split work into phases
- Clear between phases, save to thoughts/
- Never lose research or decisions

## Related Plugins

- **stepwise-git**: Git commit workflow without Claude attribution
- **stepwise-web**: Web search and research capabilities
- **stepwise-research**: Multi-agent deep research with parallel web searches

## License

Apache License 2.0 - See LICENSE file for details.
