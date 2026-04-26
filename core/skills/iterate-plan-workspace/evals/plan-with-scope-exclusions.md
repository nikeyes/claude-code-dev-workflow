# Implementation Plan: Add Background Job Processor

## Overview

Add a background job processor to handle async tasks (email sending, report generation, image resizing) without blocking the main request thread.

## Current State Analysis

The application currently processes everything synchronously in the request cycle. Long-running operations cause timeout errors for users.

### Key Discoveries

1. **Request handler** (`src/handlers/request_handler.py:45-89`): All operations are synchronous
2. **Email module** (`src/services/email_service.py:12-34`): Sends emails inline during request
3. **Report generator** (`src/services/report_generator.py:8-67`): Generates PDFs synchronously

## Desired End State

A Redis-backed job queue that processes tasks asynchronously with retry logic, dead-letter queue, and monitoring dashboard.

## What We're NOT Doing

- Not adding database migration tooling (handled by existing Alembic setup)
- Not implementing scheduled/cron jobs (only on-demand async jobs)
- Not requiring downtime for deployment (must be zero-downtime rollout)
- Not replacing the existing sync API — async is opt-in per endpoint
- Not building a custom queue — using Redis + existing rq library

## Implementation Phases

### Phase 1: Queue Infrastructure

**Scope**: Set up Redis connection and base job queue

**Changes**:
- Add `src/queue/worker.py` with Redis connection and job runner
- Add `src/queue/config.py` with queue settings (retry policy, TTL, concurrency)
- Add `requirements.txt` entry for `rq>=1.16`

**Success Criteria**:
- Automated:
  - `make test-queue` passes — worker starts, processes a no-op job, shuts down
  - `make check` passes — linting and type checks
- Manual:
  - Redis connection works with default and custom configs

### Phase 2: Migrate Email to Async

**Scope**: Move email sending to the background queue

**Changes**:
- Refactor `src/services/email_service.py` to enqueue instead of send inline
- Add `src/queue/jobs/email_job.py` with the actual send logic
- Update `src/handlers/request_handler.py` to use async email

**Success Criteria**:
- Automated:
  - `make test` passes — all existing email tests still work
  - `make test-queue` passes — email job processes correctly
- Manual:
  - Email arrives within 30 seconds of request (was inline before)

### Phase 3: Migrate Report Generation to Async

**Scope**: Move report generation to background queue

**Changes**:
- Refactor `src/services/report_generator.py` to enqueue report jobs
- Add `src/queue/jobs/report_job.py` with generation logic
- Add status polling endpoint `GET /reports/{id}/status`

**Success Criteria**:
- Automated:
  - `make test` passes
  - New endpoint returns correct status (pending, processing, complete, failed)
- Manual:
  - Large report generates without request timeout

### Phase 4: Monitoring and Dead-Letter Queue

**Scope**: Add observability and failure handling

**Changes**:
- Add `src/queue/monitor.py` with job status dashboard data
- Implement dead-letter queue for permanently failed jobs
- Add `GET /admin/queue/stats` endpoint

**Success Criteria**:
- Automated:
  - `make test` passes
  - Failed jobs appear in dead-letter queue after max retries
- Manual:
  - Admin dashboard shows queue depth, success rate, average processing time

## Success Criteria (Overall)

### Automated Verification
- `make test` — all tests pass
- `make test-queue` — queue-specific tests pass
- `make check` — linting and type checks pass

### Manual Verification
- Email and reports process asynchronously
- No request timeouts for long-running operations
- Failed jobs retry and eventually dead-letter
- Zero-downtime deployment works
