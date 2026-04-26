# Hamburger Method: Price Drop Notification System

**Task:** We need to notify users when a product they're watching drops in price

---

## Step 1: Identify Layers

The complete flow for this feature involves these 5 layers:

1. **Detect price change** — How do we know a price has dropped?
2. **Identify watching users** — Who should receive the notification?
3. **Format the notification** — What does the message look like?
4. **Deliver the notification** — How does the message reach the user?
5. **Track delivery** — Did the notification actually reach the user?

---

## Step 2: Generate 4-5 Options per Layer

### Layer 1 — Detect price change

- **1.1** Manual check: someone visits the product page and notes the new price
- **1.2** Cron job that queries the products table every hour and compares to previous price
- **1.3** Automated price scraper that polls a configurable list of products
- **1.4** Event-driven detection: price-update domain event triggers notification pipeline in real time
- **1.5** ML-based anomaly detection that identifies unusual or cyclical price drops

### Layer 2 — Identify watching users

- **2.1** Hardcode one test user (yourself) — no DB query needed
- **2.2** Query existing watchlist table: `SELECT user_id FROM watchlist WHERE product_id = ?`
- **2.3** Multi-tier watchlist with per-user preferences (e.g., only notify if drop > 10%)
- **2.4** User segmentation based on purchase history and browsing behavior
- **2.5** Personalized relevance scoring: rank users by likelihood to purchase after price drop

### Layer 3 — Format the notification

- **3.1** Plain text string: `"Product X dropped from $50 to $40"`
- **3.2** Simple template with product name, old price, new price, and direct link
- **3.3** HTML email with branding, product image, and styled CTA button
- **3.4** Rich notification with dynamic images, personalized copy, and urgency indicators ("Only 3 left!")
- **3.5** Fully personalized dynamic content based on user profile and past interactions

### Layer 4 — Deliver the notification

- **4.1** Manual email sent from your personal inbox
- **4.2** Scripted email via Gmail API or command-line mail tool
- **4.3** Email via SMTP service (SendGrid, SES) — no retries
- **4.4** Email via queuing system (SQS, RabbitMQ) with retries and dead-letter queue
- **4.5** Multi-channel delivery: email + push notification + SMS, with per-user channel preferences and fallbacks

### Layer 5 — Track delivery

- **5.1** No tracking at all
- **5.2** Log to console: `"Notification sent to user 42 for product 99"`
- **5.3** Store delivery record in DB: `notifications(user_id, product_id, sent_at, status)`
- **5.4** Dashboard with delivery analytics: open rate, click rate, conversion rate
- **5.5** Real-time monitoring with alerts on delivery failures and anomaly detection

---

## Step 3: Radical Slicing

> **"If you had to ship something by tomorrow, what would you build?"**

Pick the absolute minimum from each layer:

| Layer | Choice | Description |
|-------|--------|-------------|
| 1. Detect price change | **1.1** | Manually check one product — you notice the price dropped |
| 2. Identify watching users | **2.1** | Hardcode one test user (yourself or a willing colleague) |
| 3. Format notification | **3.1** | Plain text string: "Product X dropped from $50 to $40" |
| 4. Deliver notification | **4.1** | Send a manual email from your personal inbox |
| 5. Track delivery | **5.1** | No tracking |

**Why this works:** You can validate the entire concept in production today — a real user receives a real notification about a real price drop — with zero infrastructure changes. It answers the question: "Do users click through and buy when we notify them?"

---

## Step 4: Filter & Prioritize Options

**Eliminate for now:**
- 1.5 (ML anomaly detection) — high cost, zero additional value at this stage
- 2.4 / 2.5 (segmentation, scoring) — requires data that doesn't exist yet
- 3.4 / 3.5 (rich personalized content) — no evidence users need this yet
- 4.4 / 4.5 (queuing, multi-channel) — over-engineering before product-market fit
- 5.4 / 5.5 (dashboard, real-time monitoring) — analytics are only valuable after volume

**Keep for near-term iterations:**
- 1.2 (cron job) — simple, delivers automation quickly
- 2.2 (watchlist query) — unblocks real users immediately
- 3.2 (template with link) — small step up, high value
- 4.3 (SMTP service) — reliable, still simple
- 5.3 (DB record) — enables future analytics without building a dashboard now

---

## Step 5: Vertical Slice Composition

### Slice 1 — Ship by tomorrow (validate the concept)

| Layer | Option | Implementation |
|-------|--------|----------------|
| Detect price change | **1.1** | Manual check on one product |
| Identify users | **2.1** | One hardcoded test user |
| Format message | **3.1** | Plain text string |
| Deliver | **4.1** | Personal email |
| Track | **5.1** | None |

**Value delivered:** One real user (internal) receives a notification about a real price drop. Answers: "Does this prompt a click-through and purchase intent?"
**Effort:** 1-2 hours
**Who benefits:** Internal stakeholder or QA tester validating the concept

---

## Step 6: Next Slices

### Slice 2 — Automate detection, reach real users (1-2 days)

Improve Layer 1 and Layer 2 while keeping everything else minimal:

| Layer | Option | Change |
|-------|--------|--------|
| Detect price change | **1.2** | Cron job checks products table hourly |
| Identify users | **2.2** | Query watchlist table — notify all watchers |
| Format message | **3.1** | Plain text (unchanged) |
| Deliver | **4.2** | Scripted email via Gmail API |
| Track | **5.2** | Console log |

**Value delivered:** Real users with products on their watchlist receive notifications automatically when a price drops. No manual intervention needed.

---

### Slice 3 — Improve reliability and message quality (2-3 days)

Upgrade delivery and formatting:

| Layer | Option | Change |
|-------|--------|--------|
| Detect price change | **1.2** | Cron job (unchanged) |
| Identify users | **2.2** | Watchlist query (unchanged) |
| Format message | **3.2** | Template with product name, prices, and direct link |
| Deliver | **4.3** | SMTP service (no retries) |
| Track | **5.3** | Store delivery record in DB |

**Value delivered:** Professional-looking notification with a direct purchase link. Delivery is reliable. We can now query how many notifications were sent and start measuring conversion.

---

### Slice 4 — Add resilience and basic analytics (3-5 days)

| Layer | Option | Change |
|-------|--------|--------|
| Detect price change | **1.2** | Cron job (unchanged) |
| Identify users | **2.3** | Per-user preferences (e.g., only notify if drop > X%) |
| Format message | **3.3** | HTML email with branding |
| Deliver | **4.4** | Queue with retries |
| Track | **5.3** | DB record (unchanged) |

**Value delivered:** Users control their notification threshold. Deliverability improves with retries. Branded email builds trust.

---

## Self-Check

- [x] Identified 3-6 clear functional layers (5 layers)
- [x] Generated 4-5 options per layer following quality gradient
- [x] Options go from manual/hardcoded to enterprise-grade
- [x] Asked and answered the "ship by tomorrow" question explicitly
- [x] Smallest vertical slice uses only level-1 options
- [x] Smallest slice delivers value to at least one real user
- [x] Smallest slice can be deployed in under 1 day
- [x] Proposed 3 follow-up slices with clear incremental improvement
