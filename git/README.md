# Stepwise Git Plugin

Git and GitHub workflow: clean commits without Claude attribution and rigorous PR comment review.

## What's Included

### Commands (2)
- `/stepwise-git:commit` - Create git commits with user approval and no Claude attribution
- `/stepwise-git:review-pr-comments` - Review open PR comments rigorously, agree on responses with the user, then post them individually

## Installation

```bash
# Add marketplace
/plugin marketplace add nikeyes/stepwise-dev

# Install this plugin
/plugin install stepwise-git@stepwise-dev
```

## Usage

```bash
# Create a commit
/stepwise-git:commit
```

This will:
1. Run `git status` to see untracked files
2. Run `git diff` to see changes
3. Run `git log` to match commit message style
4. Draft a commit message focusing on "why" not "what"
5. Stage relevant files
6. Create the commit
7. Verify with `git status`

```bash
# Review PR comments
/stepwise-git:review-pr-comments [PR-number]
```

This will:
1. Auto-detect the PR from the current branch (or use the given number)
2. Fetch all active comments (inline and general), ignoring resolved/outdated
3. Read the full affected files plus related files (tests, types, dependencies)
4. Present a summary with `[ACCEPT]` / `[REJECT]` and a technical reason for each comment
5. Iterate with you until every decision is agreed
6. Post each response individually in English to the correct comment thread

## Features

- **No Claude attribution**: Commits are attributed to you, not Claude
- **Smart staging**: Only stages relevant files, warns about secrets
- **Style matching**: Follows your existing commit message patterns
- **Pre-commit hook support**: Handles hook failures gracefully
- **Rigorous PR review**: Defends existing code, only accepts changes backed by a concrete technical reason
- **Individual inline replies**: Publishes each response directly to the correct comment thread on GitHub

## Related Plugins

- **stepwise-core**: Core workflow for Research → Plan → Implement → Validate
- **stepwise-web**: Web search and research capabilities

## License

Apache License 2.0 - See LICENSE file for details.
