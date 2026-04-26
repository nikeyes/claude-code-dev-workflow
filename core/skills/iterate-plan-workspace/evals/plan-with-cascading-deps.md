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

### Phase 2: Search Query Service

**Scope**: Build the search query layer that uses the index from Phase 1

**Changes**:
- Create `src/services/search_service.py` with `search(query, filters)` method
- Implement relevance ranking using `ts_rank`
- Add tag-based faceted filtering
- Add pagination support

**Success Criteria**:
- Automated:
  - `make test-search` passes — queries return ranked results
  - Search respects tag filters
  - Pagination returns correct pages
- Manual:
  - Search for common terms returns results in <100ms

### Phase 3: Search API Endpoint and Highlighting

**Scope**: Expose search via REST API with result highlighting. Uses the search service from Phase 2.

**Changes**:
- Add `GET /api/documents/search?q=...&tags=...&page=...` endpoint
- Implement `ts_headline` for search result highlighting
- Add result count and pagination metadata to response
- Update OpenAPI spec

**Success Criteria**:
- Automated:
  - `make test` passes — all tests including new search endpoint tests
  - `make test-api` passes — search endpoint returns correct structure
  - Response includes highlighted snippets with `<mark>` tags
- Manual:
  - Search endpoint works end-to-end with real queries
  - Highlighting shows matched terms in context

## Success Criteria (Overall)

### Automated Verification
- `make test` — all tests pass (existing + new search tests)
- `make test-search` — search-specific tests pass
- `make test-api` — API endpoint tests pass
- `make db-migrate` — migration runs cleanly
- `make check` — linting and type checks

### Manual Verification
- Search returns relevant results ranked by relevance
- Highlighting shows matched terms correctly
- Tag filtering narrows results appropriately
- Performance acceptable for 10k+ documents
