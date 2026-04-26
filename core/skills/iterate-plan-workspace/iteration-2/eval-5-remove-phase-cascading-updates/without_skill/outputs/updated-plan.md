# Implementation Plan: Add Search Functionality

## Overview

Add full-text search to the document management system, including indexing, query API, and search result highlighting.

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
- Not supporting fuzzy/typo-tolerant search (exact + stemmed matches only)
- Not indexing file attachments (text content only)
- Not building a standalone search service layer (deferred to a separate ticket)

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

**Scope**: Expose search via REST API with result highlighting, implementing query logic directly against the PostgreSQL tsvector index.

**Changes**:
- Add `GET /api/documents/search?q=...&tags=...&page=...` endpoint
- Implement search query construction using PostgreSQL `to_tsquery` against the `search_vector` column from Phase 1
- Implement relevance ranking using `ts_rank`
- Add tag-based faceted filtering
- Add pagination support
- Implement `ts_headline` for search result highlighting
- Add result count and pagination metadata to response
- Update OpenAPI spec

**Success Criteria**:
- Automated:
  - `make test` passes — all tests including new search endpoint tests
  - `make test-api` passes — search endpoint returns correct structure, queries return ranked results, tag filters are respected, pagination returns correct pages
  - Response includes highlighted snippets with `<mark>` tags
- Manual:
  - Search endpoint works end-to-end with real queries
  - Highlighting shows matched terms in context
  - Search for common terms returns results in <100ms

## Success Criteria (Overall)

### Automated Verification
- `make test` — all tests pass (existing + new search tests)
- `make test-api` — API endpoint tests pass
- `make db-migrate` — migration runs cleanly
- `make check` — linting and type checks

### Manual Verification
- Search returns relevant results ranked by relevance
- Highlighting shows matched terms correctly
- Tag filtering narrows results appropriately
- Performance acceptable for 10k+ documents
