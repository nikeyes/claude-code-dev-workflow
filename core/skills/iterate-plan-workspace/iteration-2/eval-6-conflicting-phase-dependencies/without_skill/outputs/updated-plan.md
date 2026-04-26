# Implementation Plan: Add Notification System

## Overview

Add a notification system with in-app notifications, email digests, and webhook integrations for external consumers.

## Current State Analysis

The application has no notification mechanism. Events happen silently — users must manually check for updates.

### Key Discoveries

1. **Event emitter** (`src/events/emitter.py:1-42`): Publishes domain events but nothing subscribes
2. **User preferences** (`src/models/user_preferences.py:8-25`): Has email_notifications boolean, unused
3. **Webhook model** (`src/models/webhook.py:1-30`): Exists but is not wired to any event flow

## Desired End State

Domain events trigger notifications that are routed to the correct channels (in-app, email, webhook) based on user and organization preferences.

## What We're NOT Doing

- Not building a notification preferences UI (API only)
- Not implementing push notifications (mobile is separate project)
- Not adding SMS notifications
- Not building real-time WebSocket delivery (polling + email for v1)

## Implementation Phases

### Phase 1: Notification Model and Storage

**Scope**: Create notification storage and basic CRUD

**Changes**:
- Create `src/models/notification.py` with Notification model (id, user_id, type, title, body, read, created_at)
- Add Alembic migration
- Create `src/services/notification_store.py` with create/read/mark-read/delete operations
- Add `GET /api/notifications` and `PATCH /api/notifications/{id}/read` endpoints

**Success Criteria**:
- Automated:
  - `make db-migrate` runs without errors
  - `make test-notifications` passes — CRUD operations work
  - `make test-api` passes — endpoints return correct responses
- Manual:
  - Notifications persist and can be marked as read

### Phase 2: Notification Analytics Dashboard

**Scope**: Expose delivery metrics from the webhook delivery service (Phase 4) in a queryable dashboard API. Depends on Phase 1 for notification storage and Phase 4 for webhook delivery data.

> **Note — dependency conflict**: This phase is placed between Phase 1 and the original Phase 2 (now Phase 3) as requested, but it depends on data produced by Phase 4 (Webhook Delivery). You cannot fully implement or test this phase until Phase 4 is complete. The recommended approach is to implement the schema and stub endpoints now, then wire up the real aggregation queries after Phase 4 is merged. See the success-criteria note below.

**Changes**:
- Create `src/services/analytics_aggregator.py`
  - Aggregates webhook delivery metrics from `src/services/webhook_delivery.py`:
    - Total deliveries attempted, succeeded, failed, and retried
    - Average delivery latency (p50 / p95)
    - Per-webhook-endpoint success rate
    - Delivery failure reasons breakdown
- Create `src/models/delivery_metric.py` with a `DeliveryMetric` model (id, webhook_id, event_type, status, latency_ms, attempted_at, delivered_at, failure_reason)
- Add Alembic migration for `delivery_metric` table
- Add `GET /api/analytics/notifications/delivery` endpoint:
  - Query params: `from`, `to`, `webhook_id`, `event_type`
  - Returns aggregated counts and latency percentiles
- Add `GET /api/analytics/notifications/delivery/{webhook_id}` for per-endpoint drilldown

**Success Criteria**:
- Automated:
  - `make db-migrate` runs without errors
  - `make test-analytics` passes — aggregation logic returns correct totals and rates using fixture data
  - Endpoints return 200 with correct schema (can be tested with seed data before Phase 4 is wired)
  - `make test` passes — no regressions
- Manual (requires Phase 4 to be complete):
  - After a webhook delivery attempt (success or failure), the dashboard reflects updated counts and latency within one polling cycle
  - Filtering by `webhook_id` and date range returns consistent subsets

### Phase 3: Event-to-Notification Router

**Scope**: Subscribe to domain events and create notifications. Depends on Phase 1 for notification storage.

**Changes**:
- Create `src/services/notification_router.py` with event-to-notification mapping
- Subscribe to events from `src/events/emitter.py`
- Create notification templates per event type
- Route notifications based on user preferences

**Success Criteria**:
- Automated:
  - `make test-router` passes — events create correct notifications
  - Template rendering works for all event types
  - User preference filtering works (opted-out users don't get notifications)
- Manual:
  - Publishing a domain event creates the correct notification

### Phase 4: Email Digest Service

**Scope**: Aggregate notifications into periodic email digests. Depends on Phase 3 for notification routing.

**Changes**:
- Create `src/services/email_digest.py` with digest aggregation logic
- Add digest frequency to user preferences (immediate, daily, weekly)
- Create email templates for digest format
- Add background job for digest sending (uses existing job queue)

**Success Criteria**:
- Automated:
  - `make test-digest` passes — aggregation groups notifications correctly
  - Frequency settings respected (daily collects 24h of notifications)
  - `make test` passes — no regressions
- Manual:
  - Daily digest email contains all unread notifications from last 24h

### Phase 5: Webhook Delivery

**Scope**: Deliver notifications to external webhook endpoints. Depends on Phase 3 for notification routing.

**Changes**:
- Create `src/services/webhook_delivery.py` with HTTP delivery and retry logic
- Wire webhook model to notification router
- Add webhook signature verification (HMAC-SHA256)
- Add `POST /api/webhooks` and `DELETE /api/webhooks/{id}` management endpoints

**Success Criteria**:
- Automated:
  - `make test-webhooks` passes — delivery, retry, and signature work
  - Failed deliveries retry with exponential backoff (3 attempts)
  - `make test` passes — no regressions
- Manual:
  - Webhook receives payload within 5 seconds of event
  - Signature can be verified by consumer

## Success Criteria (Overall)

### Automated Verification
- `make test` — all tests pass
- `make test-notifications` — notification CRUD works
- `make test-analytics` — delivery analytics work
- `make test-router` — event routing works
- `make test-digest` — email digest works
- `make test-webhooks` — webhook delivery works
- `make check` — linting and type checks

### Manual Verification
- End-to-end: domain event → notification → email digest
- End-to-end: domain event → notification → webhook delivery → analytics dashboard updated
- User preferences correctly filter notification channels
- Webhook signatures are verifiable
- Analytics dashboard shows correct delivery metrics after webhook events
