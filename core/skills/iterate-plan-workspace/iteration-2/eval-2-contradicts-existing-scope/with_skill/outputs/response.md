# iterate-plan Response

## Request

**Plan**: `thoughts/shared/plans/2026-04-20-background-jobs.md`
**Requested change**: Add a database migration phase that requires scheduled downtime to restructure the job queue tables

---

## Step 1: Read and Understand Current Plan

I read the plan at `thoughts/shared/plans/2026-04-20-background-jobs.md` in full. It covers adding a Redis-backed background job processor with four phases:

1. Queue Infrastructure (Redis + rq worker)
2. Migrate Email to Async
3. Migrate Report Generation to Async
4. Monitoring and Dead-Letter Queue

## Step 2: Conflict Detected — Skeptical Review Required

Before proceeding, I need to flag a significant conflict between the requested change and the existing plan scope.

The plan's **"What We're NOT Doing"** section explicitly excludes **two things** that this request requires:

> - **"Not adding database migration tooling (handled by existing Alembic setup)"**
> - **"Not requiring downtime for deployment (must be zero-downtime rollout)"**

The requested change — "Add a database migration phase that requires scheduled downtime to restructure the job queue tables" — directly contradicts both exclusions:

1. **It adds a database migration phase** — the plan explicitly says migration tooling is already handled by the existing Alembic setup and is out of scope for this work.
2. **It requires scheduled downtime** — the plan explicitly mandates a zero-downtime rollout as a hard constraint.

## Step 3: Raising the Conflict (No Changes Made)

Based on your feedback, you want to:
- Add a new phase for database migration of job queue tables
- Accept scheduled downtime to restructure those tables

However, my review of the current plan found:
- The plan explicitly excludes database migration work (delegated to existing Alembic setup)
- The plan explicitly excludes any deployment requiring downtime — zero-downtime rollout is a stated constraint
- These two exclusions appear intentional: the job queue uses Redis (not a relational DB table), and the plan was designed for zero-downtime deployment

**I am NOT making this change yet** because it contradicts two explicit scope decisions in the plan.

Before proceeding, I need clarification on the following:

### Questions

1. **Has the architecture changed?** The current plan uses Redis + `rq` for the job queue — there is no relational database table being introduced. If the architecture has changed to store jobs in a SQL database instead (or in addition to Redis), that is a significant architectural shift that requires more than a simple phase addition. Is this the case?

2. **Is the zero-downtime constraint being deliberately removed?** The plan states "Not requiring downtime for deployment (must be zero-downtime rollout)" as an explicit constraint. If this constraint is being lifted, we should update the scope exclusions and validate that the rest of the plan (e.g., Phase 1-4 rollout strategy) still holds.

3. **Can the migration be zero-downtime?** If a database migration is truly required, standard patterns (expand-contract via Alembic, blue-green deployment, dual-write during transition) can often achieve zero downtime. Should I instead research how to add a migration phase that maintains the zero-downtime constraint rather than accepting scheduled downtime?

4. **Is this replacing or extending the Redis queue?** If the intent is to add a Postgres-backed job queue alongside or instead of Redis/rq, that is a significant scope change that should also update the "Desired End State" and "What We're NOT Doing" sections.

---

**Please clarify your intent and I will update the plan accordingly. I will not modify the plan until these conflicts are resolved — every change must be complete and actionable.**
