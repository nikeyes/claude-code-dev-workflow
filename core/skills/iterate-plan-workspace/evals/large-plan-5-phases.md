# Implementation Plan: Add Multi-Tenant Support

## Overview

Add multi-tenant isolation to the platform so that each organization's data is logically separated, with per-tenant configuration, rate limiting, and audit logging.

## Current State Analysis

The platform currently operates as a single-tenant system. All data lives in shared tables with no tenant context.

### Key Discoveries

1. **Database models** (`src/models/user.py:1-45`): No tenant_id foreign key on any model
2. **Auth middleware** (`src/middleware/auth.py:12-38`): Validates JWT but doesn't extract tenant context
3. **API routes** (`src/routes/api.py:1-120`): No tenant scoping on queries
4. **Config loader** (`src/config/loader.py:5-22`): Single global config, no per-tenant overrides

## Desired End State

Every API request is scoped to a tenant. Queries automatically filter by tenant_id. Each tenant can have custom rate limits, feature flags, and branding.

## What We're NOT Doing

- Not implementing physical database separation (shared DB, logical isolation only)
- Not building a tenant management UI (admin API only)
- Not migrating existing data to a default tenant (separate migration ticket)
- Not adding cross-tenant reporting (single-tenant views only)
- Not implementing tenant-level billing (handled by external billing service)

## Implementation Phases

### Phase 1: Tenant Model and Migration

**Scope**: Create the tenant table and add tenant_id to existing models

**Changes**:
- Create `src/models/tenant.py` with Tenant model (id, name, slug, settings JSON, created_at)
- Add `tenant_id` foreign key to User, Project, and Document models
- Create Alembic migration `migrations/versions/001_add_tenants.py`
- Add unique constraint on `(tenant_id, email)` for users

**Success Criteria**:
- Automated:
  - `make db-migrate` runs without errors
  - `make test-models` passes — new model validates correctly
  - `make check` passes — type checks and linting
- Manual:
  - Migration is reversible (`make db-downgrade` works)

### Phase 2: Auth Middleware Tenant Extraction

**Scope**: Extract tenant context from JWT and inject into request

**Changes**:
- Update `src/middleware/auth.py` to extract `tenant_id` from JWT claims
- Create `src/middleware/tenant_context.py` with thread-local tenant storage
- Add `get_current_tenant()` helper function
- Update JWT token generation to include tenant_id claim

**Success Criteria**:
- Automated:
  - `make test-auth` passes — JWT with tenant_id is validated correctly
  - `make test-middleware` passes — tenant context is available in request handlers
  - Requests without tenant_id in JWT return 401
- Manual:
  - Token refresh preserves tenant context

### Phase 3: Query Scoping

**Scope**: Automatically filter all database queries by current tenant

**Changes**:
- Create `src/db/scoped_session.py` with tenant-aware query builder
- Add SQLAlchemy event listener that appends `WHERE tenant_id = :tid` to all SELECT queries
- Update `src/routes/api.py` to use scoped queries
- Add `src/db/admin_session.py` for cross-tenant admin queries (explicitly unscoped)

**Success Criteria**:
- Automated:
  - `make test` passes — all existing tests work with tenant scoping
  - `make test-isolation` passes — tenant A cannot see tenant B's data
  - SQL query log shows tenant_id filter on every SELECT
- Manual:
  - API returns only current tenant's data
  - Admin endpoints can query across tenants

### Phase 4: Per-Tenant Configuration

**Scope**: Allow tenants to have custom rate limits, feature flags, and settings

**Changes**:
- Create `src/config/tenant_config.py` with per-tenant config loader
- Update `src/middleware/rate_limiter.py` to read limits from tenant config
- Add `src/services/feature_flags.py` with tenant-scoped feature checks
- Add `PUT /admin/tenants/{id}/config` endpoint

**Success Criteria**:
- Automated:
  - `make test-config` passes — tenant config overrides global defaults
  - `make test-rate-limit` passes — different tenants get different limits
  - `make test` passes — no regressions
- Manual:
  - Changing tenant config takes effect without restart
  - Default config applies to tenants without overrides

### Phase 5: Audit Logging

**Scope**: Log all data access and mutations with tenant context

**Changes**:
- Create `src/services/audit_logger.py` with structured audit events
- Add SQLAlchemy event listeners for INSERT/UPDATE/DELETE with tenant context
- Create `src/models/audit_log.py` with AuditLog model
- Add `GET /admin/tenants/{id}/audit-log` endpoint with pagination

**Success Criteria**:
- Automated:
  - `make test-audit` passes — CRUD operations create audit entries
  - Audit entries include tenant_id, user_id, action, timestamp, and diff
  - `make test` passes — no regressions
- Manual:
  - Audit log endpoint returns paginated results
  - Audit entries capture before/after state for updates

## Success Criteria (Overall)

### Automated Verification
- `make test` — all tests pass
- `make test-isolation` — tenant isolation verified
- `make test-audit` — audit logging works
- `make db-migrate && make db-downgrade && make db-migrate` — migrations are reversible
- `make check` — linting and type checks pass

### Manual Verification
- Complete request flow works with tenant context
- Tenant A's data is invisible to Tenant B
- Per-tenant rate limits and feature flags work
- Audit log captures all mutations with correct tenant context
- Zero cross-tenant data leakage under concurrent requests
