# Response: Adding a Database Migration Phase with Scheduled Downtime

I've reviewed your request, but I need to flag a direct conflict with the existing plan's stated scope before making any changes.

## Conflict with Existing Plan Scope

The current plan explicitly rules out two things that your requested change would introduce:

> **What We're NOT Doing:**
> - Not adding database migration tooling (handled by existing Alembic setup)
> - Not requiring downtime for deployment (must be zero-downtime rollout)

A new phase that restructures the job queue tables AND requires scheduled downtime contradicts **both** of these exclusions. Adding it without revisiting those decisions would leave the plan internally inconsistent.

## What I Need From You

Before I update the plan, please clarify which of these is true:

**Option A — The scope exclusions are still correct.**
The database migration should be handled outside this plan (by the team responsible for Alembic migrations), and this plan should document a dependency on that work rather than own it. No downtime is still a hard requirement — the migration would need to use an online/rolling strategy (e.g., expand-contract pattern).

**Option B — The scope needs to change.**
The requirements have evolved: this plan now owns the schema migration, and a downtime window is acceptable. In that case I'll update the "What We're NOT Doing" section to remove those exclusions and add the migration phase.

**Option C — It's a hybrid.**
The migration work happens outside this plan but there is a coordination dependency that needs to be reflected (e.g., Phase 1 is blocked until the migration window is scheduled and complete).

## If You Confirm Option B

Here is what the new phase would look like:

---

### Phase 0: Database Migration (Scheduled Downtime Window)

**Scope**: Restructure job queue tables to support the Redis-backed queue

**Pre-requisites**:
- Downtime window agreed with stakeholders (estimated: 15–30 min)
- Migration script reviewed and tested in staging

**Changes**:
- Add Alembic migration in `alembic/versions/XXXX_restructure_job_queue.py`
- New schema: `job_queue` table with columns `id`, `job_type`, `payload` (JSONB), `status`, `retry_count`, `created_at`, `scheduled_at`, `completed_at`
- Add indexes on `(status, scheduled_at)` and `(job_type, status)`
- Drop legacy columns/tables no longer needed

**Rollout Steps**:
1. Announce and begin downtime window
2. Run `alembic upgrade head`
3. Verify migration with smoke queries
4. Resume traffic

**Rollback**:
- Run `alembic downgrade -1` if migration fails
- Rollback is safe because no application traffic during window

**Success Criteria**:
- Automated:
  - `alembic upgrade head` runs without error in CI
  - `alembic downgrade -1` runs without error (rollback tested)
  - Schema matches expected structure (`make test-db-schema`)
- Manual:
  - Migration completes within the agreed downtime window
  - No data loss confirmed by row count checks pre/post migration

---

Let me know which option applies and I'll update the plan accordingly.
