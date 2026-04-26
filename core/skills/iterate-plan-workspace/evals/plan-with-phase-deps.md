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

### Phase 2: Event-to-Notification Router

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

### Phase 3: Email Digest Service

**Scope**: Aggregate notifications into periodic email digests. Depends on Phase 2 for notification routing.

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

### Phase 4: Webhook Delivery

**Scope**: Deliver notifications to external webhook endpoints. Depends on Phase 2 for notification routing.

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
- `make test-router` — event routing works
- `make test-digest` — email digest works
- `make test-webhooks` — webhook delivery works
- `make check` — linting and type checks

### Manual Verification
- End-to-end: domain event → notification → email digest
- End-to-end: domain event → notification → webhook delivery
- User preferences correctly filter notification channels
- Webhook signatures are verifiable
