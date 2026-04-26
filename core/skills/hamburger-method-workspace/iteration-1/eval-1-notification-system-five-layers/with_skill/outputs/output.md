# Hamburger Method: Price Drop Notification Feature

**Task:** We need to notify users when a product they're watching drops in price.

---

## Step 1: Identify Layers

The complete flow for this feature breaks down into 5 functional layers:

1. **Detect price change** — Know when a product's price has dropped
2. **Identify watching users** — Determine who cares about that product
3. **Format the notification** — Compose the message content
4. **Deliver the notification** — Send it to the user
5. **Track delivery** — Record that it was sent (and optionally opened/clicked)

---

## Step 2: Generate 4–5 Options per Layer

### Layer 1 — Detect price change

- **1.1** Manual check: a developer looks at a product page once a day and records the price in a spreadsheet
- **1.2** Cron job: a scheduled script queries the database for a hardcoded list of product IDs and compares current price to yesterday's snapshot
- **1.3** Automated polling: a background job runs every N minutes, fetches all products with watchers, and detects drops against a stored baseline
- **1.4** Event-driven: the price update service emits an event (e.g., `price.updated`) and a subscriber checks whether the new price is lower
- **1.5** Real-time stream: a change-data-capture (CDC) stream on the `products` table triggers downstream processing the moment a price column changes

---

### Layer 2 — Identify watching users

- **2.1** Hardcode one test user (yourself) in the script — no database query needed
- **2.2** Query an existing `watchlist` table: `SELECT user_id FROM watchlist WHERE product_id = ?`
- **2.3** Filter by user preferences: respect per-user thresholds (e.g., "only notify me if drop is > 10%")
- **2.4** Segment by behavior: prioritize users who recently viewed or added the product to cart
- **2.5** Personalized relevance scoring: ML model ranks users by likelihood to purchase given the new price

---

### Layer 3 — Format the notification

- **3.1** Plain text string: `"Product X dropped to $Y"`
- **3.2** Simple template: populate a fixed string with product name, old price, new price, and a bare URL
- **3.3** HTML email with branding: product image, price comparison table, CTA button, unsubscribe link
- **3.4** Rich push/in-app notification: deep link to product page, hero image, discount badge
- **3.5** Personalized dynamic content: message adapts to user's browsing history, preferred currency, locale, and recommended alternatives

---

### Layer 4 — Deliver the notification

- **4.1** Manual email: developer sends an email from a personal Gmail account
- **4.2** Scripted email via Gmail API or `sendmail` CLI — automated but uses a personal account
- **4.3** Transactional email via SMTP service (SendGrid, Mailgun) — no retries, fire-and-forget
- **4.4** Email via a queue with retries: job pushed to a queue (e.g., Sidekiq, BullMQ); retried on failure
- **4.5** Multi-channel with fallbacks: email + push notification + optional SMS; falls back to next channel if one fails

---

### Layer 5 — Track delivery

- **5.1** No tracking at all
- **5.2** Log to console / application log: `INFO: Notification sent to user 42 for product 99`
- **5.3** Write a row to a `notifications` table: `user_id`, `product_id`, `sent_at`, `channel`
- **5.4** Track open/click rates via pixel tracking or link wrapping; display in an internal dashboard
- **5.5** Real-time monitoring with alerts: delivery rate drops below threshold → PagerDuty alert; full analytics pipeline

---

## Step 3: Force Radical Slicing

**"If you had to ship something by tomorrow, what would you build?"**

The smallest vertical slice that delivers real value to at least one person:

| Layer | Choice | What it looks like |
|-------|--------|--------------------|
| 1. Detect price change | **1.1** Manual check | Developer checks one product's price once, by hand |
| 2. Identify watching users | **2.1** Hardcode one test user | Use your own email address in the script |
| 3. Format notification | **3.1** Plain text | `"Hey, Product X dropped from $50 to $39!"` |
| 4. Deliver notification | **4.1** Manual email | Send from personal Gmail |
| 5. Track delivery | **5.1** No tracking | Nothing recorded |

**What you learn from this slice:** Does the concept make sense to a real user? Does the message feel useful? You can validate this in a single afternoon with zero infrastructure.

---

## Step 4: Filter & Prioritize Options

Options eliminated for the first slice:
- Anything requiring new infrastructure (queues, CDC pipelines, ML models) — too costly for day 1
- Multi-channel delivery (4.5) — irreversible architecture decision; premature at this stage
- Personalized content (3.5) and relevance scoring (2.5) — no data yet to personalize
- Real-time monitoring (5.5) — no traffic to monitor yet

Options to keep in the backlog (fast, testable, reversible):
- 1.2, 2.2, 3.2, 4.3, 5.3 — the "scripted + simple DB + SMTP + basic logging" tier
- These can each be added incrementally without breaking anything

---

## Step 5: Vertical Slices Composed

### Slice 1 — "Prove It Works" (ship today)
- 1.1 Manual price check
- 2.1 One hardcoded test user (you)
- 3.1 Plain text message
- 4.1 Personal Gmail
- 5.1 No tracking

**Effort:** 2–4 hours. **Goal:** Validate the concept end-to-end with a real human.

---

### Slice 2 — "Automate Detection" (ship this week)
- **1.2** Cron job checking a list of products ← upgrade
- 2.1 Still hardcoded test user (keep it simple)
- 3.2 Simple template with product name + prices + URL ← small upgrade
- 4.3 Transactional SMTP service (SendGrid free tier) ← upgrade
- 5.2 Log to console ← small upgrade

**Effort:** 1–2 days. **Goal:** Remove the manual step; start getting real signal automatically.

---

### Slice 3 — "Real Users" (ship next sprint)
- 1.2 Cron job (keep)
- **2.2** Query real watchlist table ← upgrade
- 3.2 Simple template (keep)
- 4.3 SMTP service (keep)
- **5.3** Write row to `notifications` table ← upgrade

**Effort:** 1–2 days. **Goal:** Real users get notified; you have a record of what was sent.

---

### Slice 4 — "Quality & Preferences" (follow-up sprint)
- **1.3** Automated polling for all watched products ← upgrade
- **2.3** Respect per-user thresholds (e.g., only if drop > 10%) ← upgrade
- **3.3** HTML email with branding and unsubscribe link ← upgrade
- **4.4** Queue with retries for reliability ← upgrade
- 5.3 Notifications table (keep, extend with delivery status)

**Effort:** 3–5 days. **Goal:** Production-quality feature with user control and reliable delivery.

---

## Self-Check

- [x] 3–6 clear functional layers identified (5 layers)
- [x] At least 4–5 options generated per layer (5 per layer)
- [x] Options follow a quality gradient (manual → scripted → automated → scalable → enterprise)
- [x] Radical slicing forced by "ship by tomorrow" question
- [x] Smallest vertical slice uses level 1 options from each layer
- [x] Smallest slice delivers value to at least one user (the developer/test user)
- [x] Smallest slice can be deployed in less than 1 day
- [x] 3 follow-up slices proposed showing clear incremental improvement

---

## Key Insight

The first slice has no database schema changes, no new services, no infrastructure decisions. It answers the most important question — **"Is this notification useful to someone?"** — before investing in any automation. Each subsequent slice upgrades exactly one or two layers while keeping everything else stable.
