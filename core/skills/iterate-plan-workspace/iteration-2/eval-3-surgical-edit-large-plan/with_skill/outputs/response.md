# iterate-plan Response: Update Phase 3 Success Criteria

## Task

`/iterate-plan thoughts/shared/plans/2026-04-15-multi-tenant.md Update Phase 3 success criteria to include integration tests that verify cross-tenant query isolation under concurrent requests`

## Understanding

The request is to add integration test coverage to Phase 3 (Query Scoping) success criteria. The specific concern is cross-tenant query isolation under concurrent requests — verifying that when multiple tenants issue simultaneous queries, tenant_id context does not leak between threads/workers.

The current Phase 3 success criteria already cover:
- Basic test suite passing with tenant scoping
- Static isolation (tenant A cannot see tenant B's data)
- SQL query log audit

What is missing is a concurrency-specific integration test that exercises the scenario where multiple tenants hit the system simultaneously — which can expose thread-local context leakage in the SQLAlchemy event listener approach used in `src/db/scoped_session.py`.

No codebase research was needed — the change is purely additive to success criteria and does not require understanding new code patterns.

## Changes Made

**File**: `thoughts/shared/plans/2026-04-15-multi-tenant.md`

**Section**: Phase 3: Query Scoping — Success Criteria — Automated

**Change**: Added one new criterion between `make test-isolation` and the SQL query log check:

```
  - `make test-isolation-concurrent` passes — integration tests verify cross-tenant query isolation under concurrent requests: multiple tenants issuing simultaneous queries must not leak data across tenant boundaries
```

### Before

```markdown
**Success Criteria**:
- Automated:
  - `make test` passes — all existing tests work with tenant scoping
  - `make test-isolation` passes — tenant A cannot see tenant B's data
  - SQL query log shows tenant_id filter on every SELECT
- Manual:
  - API returns only current tenant's data
  - Admin endpoints can query across tenants
```

### After

```markdown
**Success Criteria**:
- Automated:
  - `make test` passes — all existing tests work with tenant scoping
  - `make test-isolation` passes — tenant A cannot see tenant B's data
  - `make test-isolation-concurrent` passes — integration tests verify cross-tenant query isolation under concurrent requests: multiple tenants issuing simultaneous queries must not leak data across tenant boundaries
  - SQL query log shows tenant_id filter on every SELECT
- Manual:
  - API returns only current tenant's data
  - Admin endpoints can query across tenants
```

## Verification

- Only Phase 3 success criteria were modified
- All other phases (1, 2, 4, 5) are identical to the original
- The overall success criteria section at the bottom is unchanged
- The new criterion is measurable (automated `make` command) and actionable
- The criterion description precisely targets the concurrency concern: simultaneous multi-tenant queries and data boundary leakage

## Updated Plan

See `updated-plan.md` in this directory for the complete updated plan.

## Next Steps

- Review the updated plan at `thoughts/shared/plans/2026-04-15-multi-tenant.md`
- Use `/stepwise-core:implement-plan thoughts/shared/plans/2026-04-15-multi-tenant.md` to execute it
- Or use `/stepwise-core:iterate-plan thoughts/shared/plans/2026-04-15-multi-tenant.md [more changes]` for further refinement

Tip: Use `/clear` to free up context before starting implementation.
