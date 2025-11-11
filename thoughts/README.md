# Thoughts Directory

This directory contains research documents, implementation plans, and notes for this project.

## Structure

- `nikey_es/` - Personal notes and tickets
  - `tickets/` - Ticket documentation and tracking
  - `notes/` - Personal notes and observations
- `shared/` - Team-shared documents
  - `research/` - Research documents from /research_codebase
  - `plans/` - Implementation plans from /create_plan
  - `prs/` - PR descriptions and documentation
- `searchable/` - Hardlinks for efficient grep searching (auto-generated)

## Usage

Use Claude Code slash commands:
- `/research_codebase [topic]` - Research and document codebase
- `/create_plan [description]` - Create implementation plan
- `/implement_plan [plan-file]` - Execute a plan
- `/validate_plan [plan-file]` - Validate implementation

Run `thoughts-sync` after adding/modifying files to update searchable/ hardlinks.
