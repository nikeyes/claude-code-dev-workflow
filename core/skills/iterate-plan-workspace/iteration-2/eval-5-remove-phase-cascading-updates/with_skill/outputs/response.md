# iterate-plan Response

**Plan**: `thoughts/shared/plans/2026-04-18-search.md`
**Request**: Remove Phase 2 (Search Query Service) entirely — handle the search service in a separate ticket. Adjust the rest of the plan accordingly.

---

## Understanding

Based on your feedback, I understand you want to:
- Remove Phase 2 (Search Query Service) and its `src/services/search_service.py` entirely from this ticket
- Preserve the search API endpoint and highlighting work (original Phase 3)
- Resolve the broken dependency: original Phase 3 explicitly stated "Uses the search service from Phase 2"

**Key dependency issue identified**: Removing Phase 2 would leave Phase 3 with no implementation path for the search query logic (ranking, filtering, pagination). The service was the layer that talked to the database using the Phase 1 index. Removing it without adjustment would leave Phase 3 with no way to actually query the search index.

**Resolution approach**: Fold the search query logic (currently in the service) directly into the route handler. This is a reasonable short-term choice — the service abstraction is deferred to a separate ticket, but the functionality still ships.

---

## Changes Made

### 1. Overview updated
Replaced "including indexing, query API, and search result highlighting" with "including indexing, search API endpoint, and result highlighting" to reflect the removal of the service layer.

### 2. "What We're NOT Doing" updated
Added: "Not building a search service abstraction (`src/services/search_service.py`) — search query logic lives directly in the route handler; service layer is a separate ticket"

### 3. Phase 2 (Search Query Service) removed entirely
The phase, its scope, changes, and success criteria are gone.

### 4. Former Phase 3 renumbered to Phase 2 and updated
- Renamed from "Phase 3: Search API Endpoint and Highlighting" to **"Phase 2: Search API Endpoint and Highlighting"**
- Scope updated: removed "Uses the search service from Phase 2" — now says "Implements search query logic inline in the route handler using the index from Phase 1 (no separate service layer)"
- Changes list expanded to incorporate the query logic previously owned by Phase 2:
  - Added: implement full-text query using `to_tsquery` and `search_vector` directly in route handler
  - Added: implement relevance ranking using `ts_rank`
  - Added: tag-based faceted filtering
  - Added: pagination support with result count metadata
  - (highlighting and OpenAPI spec were already present)
- Success criteria consolidated from both old Phase 2 and Phase 3:
  - Added: "Search respects tag filters"
  - Added manual: "Search for common terms returns results in <100ms" (moved from removed Phase 2)

### 5. Overall Success Criteria updated
Removed `make test-search` (it was the service-layer test target; no longer applicable). The `make test-api` entry updated to note it covers search endpoint tests.

---

## The Updated Plan

The plan now has a clean two-phase structure:

| Phase | Scope |
|-------|-------|
| Phase 1 | Search Index Setup — tsvector column, GIN index, migration |
| Phase 2 | Search API Endpoint and Highlighting — query logic inline in route handler, ranking, filtering, pagination, `ts_headline` |

No broken dependencies remain. Phase 2 builds directly on the Phase 1 index.

---

## Plan updated: `thoughts/shared/plans/2026-04-18-search.md`

Next steps in the workflow:
- Review the updated plan
- Use `/stepwise-core:implement-plan thoughts/shared/plans/2026-04-18-search.md` to execute it
- Or use `/stepwise-core:iterate-plan thoughts/shared/plans/2026-04-18-search.md [more changes]` for further refinement

Tip: Use `/clear` to free up context before starting implementation
