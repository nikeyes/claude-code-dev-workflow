# Update: Phase 3 Success Criteria

I've updated the Phase 3 (Query Scoping) success criteria to include an integration test that verifies cross-tenant query isolation under concurrent requests.

## Change Made

In the **Automated** section of Phase 3's success criteria, I added:

```
- `make test-isolation-concurrent` passes — integration tests verify cross-tenant query isolation under concurrent requests: multiple tenants issuing simultaneous queries must not leak data across tenant boundaries
```

## Rationale

The existing `make test-isolation` criterion covers sequential isolation (tenant A cannot see tenant B's data in normal operation), but concurrent requests introduce race conditions that sequential tests cannot catch — for example:

- Thread-local tenant context being shared or overwritten when requests are handled by a thread pool
- Connection pool reuse carrying over the wrong tenant's session state
- SQLAlchemy event listeners reading stale tenant context during query compilation under load

A dedicated concurrent integration test (`make test-isolation-concurrent`) closes this gap by spinning up simultaneous requests across multiple tenants and asserting that every response contains only the requesting tenant's data.

The overall success criteria already calls out "Zero cross-tenant data leakage under concurrent requests" as a manual verification item, so this change promotes that concern into the automated suite where it can be enforced on every CI run.
