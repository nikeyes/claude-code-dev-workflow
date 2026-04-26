# Implementation Plan: Add Search Functionality

## Overview

Add full-text search to the document management system, including indexing, search API endpoint, and result highlighting.

## Current State Analysis

Documents are stored in PostgreSQL with no search indexing. Users currently filter by exact title match only.

### Key Discoveries

1. **Document model** (`src/models/document.py:1-35`): Has title, body, tags, created_at fields
2. **Document API** (`src/routes/documents.py:15-89`): CRUD endpoints, filter by title only
3. **Test suite** (`tests/test_documents.py:1-120`): 15 tests covering CRUD operations

## Desired End State

Full-text search across document title and body with relevance ranking, highlighting, and faceted filtering by tags.

## What We're NOT Doing

- Not building a search UI (API only, frontend is separate ticket)
- Not building a search service abstraction (`src/services/search_service.py`) — search query logic lives directly in the route handler; service layer is a separate ticket
- Not supporting fuzzy/typo-tolerant search (exact + stemmed matches only)
- Not indexing file attachments (text content only)

## Implementation Phases

### Phase 1: Search Index Setup

**Scope**: Add PostgreSQL tsvector column and GIN index for full-text search

**Changes**:
- Add `search_vector` tsvector column to Document model
- Create trigger to auto-update search_vector on INSERT/UPDATE
- Create GIN index on search_vector
- Add Alembic migration

**Success Criteria**:
- Automated:
  - `make db-migrate` runs without errors
  - `make test-models` passes — search_vector populated on document create/update
  - `make check` passes
- Manual:
  - Existing documents get search_vector via backfill migration

### Phase 2: Search API Endpoint and Highlighting

**Scope**: Expose search via REST API with result highlighting. Implements search query logic inline in the route handler using the index from Phase 1 (no separate service layer).

**Changes**:
- Add `GET /api/documents/search?q=...&tags=...&page=...` endpoint in `src/routes/documents.py`
- Implement full-text query using `to_tsquery` and `search_vector` directly in route handler
- Implement relevance ranking using `ts_rank`
- Add tag-based faceted filtering
- Add pagination support with result count metadata
- Implement `ts_headline` for search result highlighting
- Update OpenAPI spec

**Success Criteria**:
- Automated:
  - `make test` passes — all tests including new search endpoint tests
  - `make test-api` passes — search endpoint returns correct structure, ranked results, correct pagination
  - Response includes highlighted snippets with `<mark>` tags
  - Search respects tag filters
- Manual:
  - Search endpoint works end-to-end with real queries
  - Search for common terms returns results in <100ms
  - Highlighting shows matched terms in context

## Success Criteria (Overall)

### Automated Verification
- `make test` — all tests pass (existing + new search tests)
- `make test-api` — API endpoint tests pass, including search endpoint
- `make db-migrate` — migration runs cleanly
- `make check` — linting and type checks

### Manual Verification
- Search returns relevant results ranked by relevance
- Highlighting shows matched terms correctly
- Tag filtering narrows results appropriately
- Performance acceptable for 10k+ documents
