# Plan: Rename `email` to `email_address` in `users` Table

## Goal

Rename the `email` column to `email_address` in the `users` SQLite table used by `UserService`, with zero downtime and the ability to roll back at any point.

## Risk Assessment

This is a **risky breaking change**: renaming a database column affects all queries, application code, and tests that reference the old name. A direct rename would break every caller simultaneously.

**Pattern to apply:** Expand-Contract (3 phases).

**Estimated total time:** 12-15 hours spread over 2-3 weeks.

---

## Phase 1: EXPAND — Add `email_address` alongside `email`

**Goal:** Both columns exist. The system writes to both so existing code keeps working.

### Step 1.1 — Add new column `email_address` to schema (1h)

**Type:** Earning step

- Add `email_address TEXT` to the `CREATE TABLE` statement in `_setup_schema`.
- Write and run a database migration (e.g. `ALTER TABLE users ADD COLUMN email_address TEXT`).
- Deploy and verify: `SELECT id, email, email_address FROM users LIMIT 5;` — `email_address` should be `NULL` for existing rows.
- All existing tests must still pass (no behaviour changed yet).

**Reversible:** Yes — drop the column to roll back.

**Criteria met:** Deployable, reversible, safe, testable, under 1h.

---

### Step 1.2 — Implement dual-write in application code (2h)

**Type:** Earning step

- Update every `INSERT` and `UPDATE` statement in `UserService` to write to **both** `email` and `email_address`:
  - `create_user`: `INSERT INTO users (username, email, email_address, role) VALUES (?, ?, ?, ?)`
  - `update_email`: `UPDATE users SET email = ?, email_address = ? WHERE id = ?`
- Keep all **reads** pointing at `email` (no change to `get_user`, `get_user_by_email`, `list_users`).
- Update tests: after `create_user` or `update_email`, assert both `user["email"]` and `user["email_address"]` contain the expected value.
- Deploy and verify: create/update a user, confirm both columns are populated.

**Reversible:** Yes — revert code deploy; data in `email_address` can be dropped safely.

**Criteria met:** Deployable, reversible, safe, testable, under 2h.

---

### Step 1.3 — Backfill `email_address` for existing rows (1h)

**Type:** Earning step

- Run a one-time migration script (or add to schema setup):
  ```sql
  UPDATE users SET email_address = email WHERE email_address IS NULL;
  ```
- Verify: `SELECT COUNT(*) FROM users WHERE email_address IS NULL;` must return `0`.
- For large tables, run in batches (e.g. `LIMIT 1000`).

**Reversible:** Yes — `email_address` values can be cleared; `email` is untouched.

**Criteria met:** Deployable, reversible, safe, testable, under 1h.

**Expand-phase checklist before proceeding:**
- [ ] Dual-write confirmed working in production
- [ ] `email_address` has no NULLs
- [ ] All existing tests pass
- [ ] Rollback plan clear: revert code + drop column

---

## Phase 2: MIGRATE — Switch reads to `email_address`

**Goal:** All reads use the new column. Dual-write remains active as a safety net.

### Step 2.1 — Switch reads in `UserService` to `email_address` (2h)

**Type:** Earning step

- Update every `SELECT` and `WHERE` clause that references `email` to use `email_address`:
  - `get_user_by_email`: `SELECT * FROM users WHERE email_address = ?`
  - `get_user` / `list_users`: already use `SELECT *`; no SQL change needed, but the returned dict key will still be `email` (from the column) — leave that for cleanup in Phase 3.
- Deploy behind a feature flag if available; otherwise deploy to staging first.
- All tests must continue to pass (assertions on `user["email"]` still work because `email` column still exists).

**Reversible:** Yes — flip feature flag or revert deploy; dual-write keeps both columns in sync.

**Criteria met:** Deployable, reversible, safe, testable, under 2h.

---

### Step 2.2 — Monitor and verify zero errors (passive, 1 week)

**Type:** Learning step (time-boxed observation)

- Monitor logs and error rates for any reference to `email` column failing.
- Confirm `email_address` is populated on 100% of rows.
- Confirm no code path still reads exclusively from `email`.
- Duration: 1 week of production traffic.

**Output:** Decision to proceed to Contract phase (or rollback if issues found).

---

**Migrate-phase checklist before proceeding:**
- [ ] All reads confirmed using `email_address`
- [ ] No errors referencing the old `email` column
- [ ] `email_address` 100% populated
- [ ] Dual-write still active

---

## Phase 3: CONTRACT — Remove old `email` column

**Goal:** Clean up the old column and all migration scaffolding.

### Step 3.1 — Stop writing to `email` column (1h)

**Type:** Earning step

- Update `create_user` and `update_email` to write only to `email_address`.
- Deploy and monitor. Old `email` column now frozen (no new writes).
- Verify: `SELECT MAX(created_at) FROM users WHERE email IS NOT NULL;` — timestamps stop advancing.

**Reversible:** Yes — revert code deploy; data in `email` column is stale but intact.

**Criteria met:** Deployable, reversible, safe, testable, under 1h.

---

### Step 3.2 — Monitor for 1-2 weeks that `email` is unused (passive)

**Type:** Learning step (time-boxed observation)

- Check slow query logs, application logs, and analytics for any read of `email` column.
- Search codebase for any remaining reference to the old column name.
- Duration: 1-2 weeks.

**Output:** Confirmation that `email` is truly unused.

---

### Step 3.3 — Drop `email` column from database (30min)

**Type:** Earning step

- Run migration:
  ```sql
  ALTER TABLE users DROP COLUMN email;
  ```
  (SQLite 3.35+; for older SQLite, use the table-rebuild approach.)
- Remove `email` from `_setup_schema` `CREATE TABLE` statement.
- Deploy and verify: `SELECT * FROM users LIMIT 1;` should not include `email`.

**Reversible:** Requires restoring from backup — only execute after the waiting period.

**Criteria met:** Deployable (with backup), testable, under 30min.

---

### Step 3.4 — Update tests and clean up code (1h)

**Type:** Earning step

- Update all test assertions from `user["email"]` to `user["email_address"]`.
- Rename Python method parameter `email` → `email_address` in `create_user`, `update_email`, `get_user_by_email` signatures (purely internal rename, safe now).
- Remove any dual-write scaffolding or feature flags.
- Run full test suite: all tests green.

**Reversible:** Code-only changes; no schema impact.

**Criteria met:** Deployable, reversible, safe, testable, under 1h.

---

## Summary

| Phase | Steps | Time per step | Duration |
|-------|-------|---------------|----------|
| **Expand** | 1.1 Add column, 1.2 Dual-write, 1.3 Backfill | 1-2h each | Day 1 |
| **Migrate** | 2.1 Switch reads, 2.2 Monitor | 2h + 1 week passive | Week 1-2 |
| **Contract** | 3.1 Stop writes, 3.2 Monitor, 3.3 Drop column, 3.4 Cleanup | 30min-1h each + 1-2 weeks passive | Week 3-5 |

**Total active work:** ~8-10 hours  
**Total calendar time:** 2-3 weeks

## Self-Check

- [x] Every step takes 1-3 hours (no step exceeds this)
- [x] Every step is deployable to production or creates a verifiable artifact
- [x] Every step is reversible (dual-write preserved through entire Migrate phase)
- [x] Risky change uses Expand-Contract (3 phases)
- [x] Learning steps (monitoring/observation) separated from earning steps
- [x] Dual-write active during entire Migrate phase
- [x] Contract phase only starts after old path has zero usage for 1-2 weeks
- [x] Each phase is independently valuable
