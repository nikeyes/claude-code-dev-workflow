# Response: Remove Phase 2 (Search Query Service)

Done. Phase 2 has been removed and the plan updated accordingly.

## What changed

### Removed
- **Phase 2: Search Query Service** — the entire phase is gone. `src/services/search_service.py`, `ts_rank` relevance ranking, tag-based faceted filtering as a service layer, and pagination support at the service level are all deferred to a separate ticket.

### Adjusted — Phase 3 (now Phase 2): Search API Endpoint and Highlighting
- Removed the note "Uses the search service from Phase 2" from the scope description, since that service layer no longer exists in this plan.
- The endpoint will implement the search query logic directly against the PostgreSQL `tsvector` index (rather than delegating to a service class). This keeps the plan self-contained.
- Added the query construction, `ts_rank` relevance ranking, tag filtering, and pagination directly into the changes list for this phase, since those concerns no longer have a dedicated phase.

### Adjusted — Overall Success Criteria
- Removed `make test-search` from the overall automated verification list. That target was specifically for the search service layer (Phase 2), which is no longer in scope. Search behavior is now covered by `make test-api` and the general `make test`.

## Phases after adjustment

| # | Phase | Status |
|---|-------|--------|
| 1 | Search Index Setup | Unchanged |
| 2 | Search API Endpoint and Highlighting | Updated (was Phase 3; query logic absorbed from removed Phase 2) |

The updated plan is saved as `updated-plan.md` alongside this response.
