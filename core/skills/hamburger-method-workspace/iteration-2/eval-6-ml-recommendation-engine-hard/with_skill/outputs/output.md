# Hamburger Method: Product Recommendation Engine

**Task:** Build a product recommendation engine that uses machine learning to suggest relevant items to users based on their browsing and purchase history.

---

## Applying the Hamburger Method

Let's slice this feature into vertical, deliverable pieces.

---

## Step 1: Identify Layers

The complete recommendation engine involves these functional layers:

1. **Collect user behavior data** — capture browsing/purchase events
2. **Store and retrieve history** — persist and query user activity
3. **Compute recommendations** — generate ranked candidate items
4. **Filter and rank results** — apply business rules and personalization
5. **Serve recommendations** — deliver results to the product UI
6. **Measure recommendation quality** — track whether suggestions work

---

## Step 2: Options per Layer (4-5 each, simplest to most complete)

---

### Layer 1 — Collect User Behavior Data

- **1.1** Manually export a CSV of past purchases from the orders database (no live instrumentation)
- **1.2** Query existing order/session tables directly (no new tracking, use what's there)
- **1.3** Add a lightweight event log: fire-and-forget POST to `/events` on page view and purchase
- **1.4** Client-side analytics (e.g., Segment, Snowplow) sending structured events to a data warehouse
- **1.5** Real-time event stream (Kafka/Kinesis) with schema registry and replay support

---

### Layer 2 — Store and Retrieve History

- **2.1** Flat CSV file with user_id, item_id, event_type, timestamp (local disk or S3)
- **2.2** Single existing relational table (orders or sessions) queried directly at recommendation time
- **2.3** Dedicated `user_events` table in the existing database with indexed user_id lookups
- **2.4** Feature store (Redis/DynamoDB) pre-computing user interaction vectors for fast lookups
- **2.5** Distributed data lake (Delta Lake / Iceberg) with streaming ingestion and historical replay

---

### Layer 3 — Compute Recommendations

- **3.1** Hardcoded list: return the 5 best-sellers sitewide regardless of user (zero personalization)
- **3.2** Rule-based: "users who bought X also bought Y" using a co-purchase count table built with a SQL query
- **3.3** Item-based collaborative filtering using cosine similarity on a user-item matrix (scikit-learn, offline batch job)
- **3.4** Matrix factorization model (ALS / SVD) trained nightly, recommendations pre-computed and cached
- **3.5** Neural collaborative filtering or two-tower model with near-real-time serving via an embedding index (FAISS/Weaviate)

---

### Layer 4 — Filter and Rank Results

- **4.1** No filtering (return raw recommendations as-is)
- **4.2** Remove out-of-stock items and items the user already purchased (simple SQL filter)
- **4.3** Apply business rules: exclude low-margin items, boost promoted products, cap categories
- **4.4** Re-rank using a lightweight gradient-boosted model trained on click-through data
- **4.5** Multi-objective ranking: blends relevance, diversity, freshness, and profitability in real time

---

### Layer 5 — Serve Recommendations

- **5.1** Admin/internal page showing recommendations for a given user_id (no user-facing integration)
- **5.2** REST endpoint `GET /recommendations?user_id=X` returning a JSON list, consumed by one page
- **5.3** Recommendations widget embedded in the product detail page and cart
- **5.4** Personalized homepage section + email digest pulling from the same recommendation endpoint
- **5.5** Real-time A/B testing infrastructure serving multiple recommendation strategies to segmented users

---

### Layer 6 — Measure Recommendation Quality

- **6.1** No measurement (trust gut feeling)
- **6.2** Manual spot-check: an analyst reviews 10 user profiles and their recommendations weekly
- **6.3** Log which recommendations were shown and whether the item was later purchased (click/conversion table)
- **6.4** Dashboard tracking CTR, conversion lift, and revenue attribution per recommendation slot
- **6.5** Automated online evaluation: multi-armed bandit or interleaving experiments with statistical significance alerts

---

## Step 3: Force Radical Slicing

> **"If you had to ship something by tomorrow, what would you build?"**

Pick the minimum viable slice — one option per layer:

| Layer | Pick | Rationale |
|---|---|---|
| 1. Collect data | **1.1** Export existing purchase CSV | No instrumentation work, data already exists |
| 2. Store history | **2.1** Flat CSV file | No infrastructure change, processed in memory |
| 3. Compute recommendations | **3.2** Co-purchase count table via SQL | Interpretable, no ML training pipeline, deployable in hours |
| 4. Filter results | **4.2** Remove already-purchased and out-of-stock | One SQL filter, prevents embarrassing suggestions |
| 5. Serve recommendations | **5.1** Internal admin page showing recommendations for a given user_id | Zero UI risk, lets a real stakeholder validate quality immediately |
| 6. Measure quality | **6.2** Manual analyst spot-check | Immediate feedback with no logging infrastructure |

**This slice can be built in one day.** A product manager or analyst can open the internal page, type in user IDs, and judge whether the suggestions make sense. That validation is worth more than any offline metric before you've confirmed the basic logic works.

---

## Step 4: Filter and Prioritize

Options eliminated for the first slice:
- 1.3–1.5: Require new event tracking infrastructure — blocks fast delivery
- 2.3–2.5: Require schema migrations or new services — irreversible without work
- 3.3–3.5: Require training pipelines, model serving, and offline evaluation — costly before validation
- 4.3–4.5: Business rule complexity adds risk without proven baseline
- 5.2–5.5: User-facing deployment before internal validation is premature
- 6.3–6.5: Logging and dashboards add no value until recommendations are live

---

## Step 5: Vertical Slice 1 (Ship by tomorrow)

**Slice 1 — "Can we even recommend anything sensible?"**

- **1.1** Export orders table to CSV (or query it directly at batch time)
- **2.1** Load CSV into a pandas DataFrame (or a single SQL query) at job time
- **3.2** Count co-purchase pairs with a GROUP BY query; store result in a `co_purchases` table
- **4.2** Filter out items the user already bought and items with `in_stock = false`
- **5.1** Internal Flask/FastAPI endpoint or admin script: `python recommend.py --user_id=42` prints top-5 items
- **6.2** Analyst runs the script for 10 users and rates quality in a spreadsheet

**Who gets value:** The product manager can immediately answer: "Does co-purchase logic produce sensible recommendations for our catalog?" before committing to any ML infrastructure.

**Build time estimate:** 4–8 hours for one developer.

---

## Step 6: Follow-up Slices

### Slice 2 — "Make it user-facing on one page" (Days 2–3)
- Keep layers 1–4 from Slice 1
- **5.2** Add a REST endpoint `GET /recommendations?user_id=X` and embed it in the product detail page
- **6.3** Log impressions and purchases to a `recommendation_events` table

### Slice 3 — "Improve recommendation quality with a real ML model" (Week 2)
- **1.3** Add lightweight event logging (page views + add-to-cart, not just purchases)
- **2.3** Persist events in a dedicated `user_events` table
- **3.3** Train an item-based collaborative filtering model (scikit-learn, weekend batch job)
- Keep layers 4–5 from Slice 2, plus **6.3** logging already in place

### Slice 4 — "Scale and personalize" (Week 3–4)
- **3.4** Move to matrix factorization (ALS) with nightly retraining, pre-computed recommendations cached in Redis
- **4.3** Add business rules: boost promoted items, cap per-category diversity
- **5.3** Expand recommendation widget to cart page and homepage
- **6.4** Add a dashboard tracking CTR and conversion lift per slot

---

## Self-Check

- [x] Identified 6 clear layers (functional, not frontend/backend/database)
- [x] Generated 4-5 options per layer following the quality gradient
- [x] Options go manual → scripted → automated → scalable → enterprise
- [x] Forced radical slicing with the "ship by tomorrow" question
- [x] Smallest slice uses level 1-2 options from each layer
- [x] Smallest slice delivers value to a real stakeholder (product manager / analyst)
- [x] Smallest slice builds in less than 1 day (4–8 hours)
- [x] Proposed 3 follow-up slices with clear incremental improvements

---

## Key Insight

The temptation with "ML recommendation engine" is to start with the ML. Don't. The hardest problems are: (1) confirming your data quality and coverage, (2) agreeing on what "good" looks like with stakeholders, and (3) integrating recommendations into the UI without breaking anything. A co-purchase SQL query solves all three problems on day one. The ML is an upgrade to step 3 only — everything else stays the same.
