# Thoughts Directory

This directory contains research documents, implementation plans, and notes for this project.

## Structure

- `nikey_es/` - Personal notes and tickets
  - `tickets/` - Ticket documentation and tracking
  - `notes/` - Personal notes and observations
- `shared/` - Team-shared documents
  - `research/` - Research documents from /stepwise-core:research_codebase
  - `plans/` - Implementation plans from /stepwise-core:create_plan
  - `prs/` - PR descriptions and documentation

## Usage

Use Claude Code slash commands:
- `/stepwise-core:research_codebase [topic]` - Research and document codebase
- `/stepwise-core:create_plan [description]` - Create implementation plan
- `/stepwise-core:implement_plan [plan-file]` - Execute a plan
- `/stepwise-core:validate_plan [plan-file]` - Validate implementation

Use `grep -r thoughts/` to search across all documents.
