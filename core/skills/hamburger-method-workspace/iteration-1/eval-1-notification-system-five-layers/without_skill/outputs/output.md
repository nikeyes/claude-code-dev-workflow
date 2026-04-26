# Hamburger Method: Price Drop Notification Feature

## Feature Description

Notify users when a product they're watching drops in price.

---

## Step 1: Identify the Layers

The Hamburger Method decomposes a feature by cutting horizontally through the technical stack — each layer represents a distinct architectural or delivery concern. For this feature, the natural layers are:

### Layer 1: Data / Persistence
Storing watched products per user and recording price history so that comparisons are possible.

### Layer 2: Price Detection / Business Logic
The logic that determines whether a price has dropped for a watched product, including thresholds, frequency of checks, and deduplication of alerts.

### Layer 3: Notification Delivery
The mechanism that sends the alert to the user — email, push, SMS, in-app, etc.

### Layer 4: User Interface / Configuration
How users add products to their watch list, set preferences (threshold, notification channel, opt-out), and view watch history.

### Layer 5: Scheduling / Infrastructure
The background job or event-driven trigger that periodically checks prices and coordinates the end-to-end flow.

---

## Step 2: Implementation Options Per Layer

For each layer, four to five concrete implementation options are listed, ranging from the simplest/cheapest to the most sophisticated.

---

### Layer 1: Data / Persistence

| # | Option | Notes |
|---|--------|-------|
| 1 | **In-memory map (process-local)** | A simple dictionary `{user_id: [{product_id, last_known_price}]}` stored in application memory. No persistence across restarts. Suitable only for prototyping. |
| 2 | **Single database table** | A `watched_products` table with columns `user_id`, `product_id`, `target_price`, `last_notified_at`. Uses the existing application database. Simple, durable, no new infrastructure. |
| 3 | **Watched products table + price_history table** | Adds a `price_history(product_id, price, recorded_at)` table. Enables trend analysis and replay of alerts. More storage, more power. |
| 4 | **Dedicated cache layer (Redis)** | Store current prices in Redis for fast reads during the price-check loop; use the relational DB for durable watch records. Introduces a new infrastructure dependency. |
| 5 | **Event-sourced price ledger** | Every price change is an immutable event. Full audit trail, time-travel queries. High complexity; appropriate only if price analytics are a core product concern. |

---

### Layer 2: Price Detection / Business Logic

| # | Option | Notes |
|---|--------|-------|
| 1 | **Direct comparison on demand** | At notification time, fetch current price from the product catalog and compare to `last_known_price`. Simple; no separate detection job. |
| 2 | **Percentage threshold check** | Only trigger a notification when the price drops by at least N% (configurable). Avoids noise from trivial fluctuations. |
| 3 | **Absolute threshold check** | Trigger when price drops below a user-defined target price (e.g., "notify me when this is under $49"). Useful for budget-driven purchases. |
| 4 | **Debounce / cooldown window** | Prevent re-notifying a user within a configurable cooldown period (e.g., 24 hours) even if price continues to drop. Reduces notification fatigue. |
| 5 | **ML-based price anomaly detection** | Use a statistical model to distinguish meaningful drops from normal price variance. High complexity; justified only at large catalog scale. |

---

### Layer 3: Notification Delivery

| # | Option | Notes |
|---|--------|-------|
| 1 | **In-app notification (database record)** | Insert a row into a `notifications` table; render a badge or bell icon in the UI. Zero external dependencies. |
| 2 | **Email via transactional email service** | Send an email through SendGrid, SES, or Postmark. Simple integration, wide reach, but users may miss it. |
| 3 | **Browser push notification (Web Push API)** | Requires a service worker and subscription token. Works without the user having the app open. More complex setup. |
| 4 | **Mobile push notification (FCM / APNs)** | Requires a native or PWA mobile app with a registered device token. High reach for mobile-first users. |
| 5 | **Multi-channel with user preference routing** | User chooses preferred channel; system dispatches accordingly. Requires a notification preferences model and a routing layer. Maximum flexibility, maximum complexity. |

---

### Layer 4: User Interface / Configuration

| # | Option | Notes |
|---|--------|-------|
| 1 | **Hardcoded watch via API call (no UI)** | A developer or admin adds watch records directly via a REST endpoint or CLI script. Useful for the first vertical slice. |
| 2 | **Single "Watch this product" button** | Adds a watch with default settings (no threshold, default channel). One-click, no configuration dialog. |
| 3 | **Watch button + price threshold input** | User specifies the target price at the time of watching. Minimal form. |
| 4 | **Watch list management page** | Full CRUD: add/edit/remove watched products, set thresholds per item, view price history. Standard product feature. |
| 5 | **Notification preferences center** | Manage channels (email, push), global opt-out, frequency caps, and per-product settings. Full-featured; appropriate after adoption is proven. |

---

### Layer 5: Scheduling / Infrastructure

| # | Option | Notes |
|---|--------|-------|
| 1 | **Manual trigger (script / cURL)** | A developer runs a script to check prices on demand. No automation, but proves the logic works end-to-end before building automation. |
| 2 | **Cron job (server-side)** | A scheduled task (e.g., `0 * * * *`) calls the price-check function. Simple, widely understood, easy to deploy. |
| 3 | **Background job queue (Sidekiq, Celery, BullMQ)** | Enqueue price-check jobs per product or per user. Supports retries, concurrency control, and dead-letter queues. |
| 4 | **Event-driven trigger on price change** | When a product price is updated in the catalog, publish a `price_changed` event; a consumer checks watches and dispatches notifications. Lower latency than polling; requires an event bus (Kafka, SNS, etc.). |
| 5 | **Serverless scheduled function (Lambda + EventBridge)** | Fully managed, scales to zero, no server maintenance. Cold-start latency and vendor lock-in are trade-offs. |

---

## Step 3: Compose the Smallest Vertical Slice

A vertical slice must touch every layer — it must be demonstrably end-to-end while using the simplest option from each layer that still delivers real user value.

### Smallest Vertical Slice: "Email Alert When Price Drops — Manual Trigger"

#### Description

A user is manually added to a watch list for a product. A developer runs a script once per hour (or on demand). If the product's current price is lower than the stored price, the user receives a single email. The UI is a bare "Watch" button with no configuration. No scheduling infrastructure is automated yet.

#### Layer choices for this slice

| Layer | Chosen Option | Rationale |
|-------|--------------|-----------|
| Data / Persistence | Single database table (`watched_products` with `user_id`, `product_id`, `last_known_price`) | Durable, uses existing DB, minimal schema change. |
| Price Detection / Logic | Direct comparison: `current_price < last_known_price` | Simplest logic that is correct and understandable. |
| Notification Delivery | Email via existing transactional email service | Wide reach, no new infrastructure if the app already sends emails (e.g., welcome emails). |
| User Interface | Single "Watch this product" button (no configuration) | Delivers user value with one click; avoids premature UX complexity. |
| Scheduling / Infrastructure | Manual trigger / cron (developer runs a script) | Proves the full flow before investing in job queues or event buses. |

#### What this slice delivers

- A real user can watch a product with one click.
- When prices are checked (manually or via a simple cron), the user receives an email if the price dropped.
- The entire feature is observable and testable end-to-end.
- No new infrastructure dependencies beyond the existing database and email service.

#### What this slice intentionally defers

- Threshold configuration (percentage or absolute target price)
- Notification channel choice (push, SMS)
- Watch list management UI
- Cooldown / deduplication logic
- Automated scheduling infrastructure (job queues, event bus)
- Price history storage

#### Acceptance criteria for this slice

1. A `watched_products` table exists with at least `user_id`, `product_id`, and `last_known_price` columns.
2. A "Watch" button on the product page inserts a row (or is idempotent if the user already watches the product).
3. A script or job iterates all watched products, fetches the current price, and for each user whose product has dropped in price: sends an email and updates `last_known_price`.
4. The email includes the product name, old price, new price, and a link to the product page.
5. No email is sent if the price has not changed or has increased.

---

## Summary

The Hamburger Method reveals that this feature has five independent layers, each with a spectrum of complexity. By selecting the simplest viable option per layer and composing them into one vertical slice, the team can deliver end-to-end user value — a real email when a watched product drops in price — without building scheduling infrastructure, preference centers, or multi-channel delivery upfront. Subsequent iterations add sophistication layer by layer, each validated against real usage before investing in the next level of complexity.
