# Hamburger Method: Product Recommendation Engine with ML

Let's apply the Hamburger Method to slice this feature into deliverable vertical pieces.

---

## Feature Description

> Build a product recommendation engine that uses machine learning to suggest relevant items to users based on their browsing and purchase history.

---

## Step 1: Identify Layers

The complete flow for a product recommendation engine involves these functional layers:

1. **Collect user behavior signals** — capture what users browse, click, and buy
2. **Build user/item profiles** — aggregate signals into a usable representation
3. **Generate recommendations** — compute which products to suggest
4. **Serve recommendations** — deliver suggestions at the right moment in the UI
5. **Evaluate & improve** — measure whether recommendations are good and iterate

These are 5 distinct functional layers. Each one can be implemented at different quality levels independently.

---

## Step 2: Generate 4–5 Options per Layer

### Layer 1 — Collect User Behavior Signals

| # | Option | Description |
|---|--------|-------------|
| 1.1 | **Manual export** | Analyst queries the DB manually (e.g., `SELECT * FROM orders`) and exports a CSV once |
| 1.2 | **Batch query on existing data** | Scheduled script reads purchase/browse history from existing tables nightly |
| 1.3 | **Structured event logging** | App fires structured events (product_viewed, product_purchased) into a log file or DB table |
| 1.4 | **Event stream** | Events flow into a message broker (Kafka/SQS); consumers process in near real-time |
| 1.5 | **Real-time behavioral tracking** | Full clickstream platform (e.g., Segment, Amplitude) with session tracking, dwell time, scroll depth |

---

### Layer 2 — Build User / Item Profiles

| # | Option | Description |
|---|--------|-------------|
| 2.1 | **Hardcoded list** | Manually curate "top 10 products for our best customers" — no computation |
| 2.2 | **Simple frequency count** | Per user: count which products they bought/viewed most; store as ranked list in a CSV/table |
| 2.3 | **Collaborative filtering matrix** | Build a user-item interaction matrix; use cosine similarity or Pearson to find similar users |
| 2.4 | **Embeddings with a pre-trained model** | Use a pre-trained model (e.g., LightFM, Surprise, or a sentence transformer on product descriptions) to produce dense vectors |
| 2.5 | **Full ML pipeline with feature store** | Real-time feature store (Feast, Tecton) feeding a trained neural embedding model; re-trained nightly or on-trigger |

---

### Layer 3 — Generate Recommendations

| # | Option | Description |
|---|--------|-------------|
| 3.1 | **Static "bestsellers" list** | Same recommendations for every user — top 10 globally popular products |
| 3.2 | **Rule-based filtering** | "Users who bought X also frequently bought Y" — hardcoded or analyst-written rules |
| 3.3 | **Item-item collaborative filtering** | For each item the user interacted with, find similar items via cosine similarity on the interaction matrix |
| 3.4 | **User-user collaborative filtering or matrix factorization** | Find users similar to the current user; recommend what they bought (Surprise/ALS/SVD) |
| 3.5 | **Two-tower deep learning model** | Train a retrieval + ranking model (e.g., TensorFlow Recommenders, RecBole); serve via an approximate nearest-neighbor index (FAISS/ScaNN) |

---

### Layer 4 — Serve Recommendations

| # | Option | Description |
|---|--------|-------------|
| 4.1 | **Static file / spreadsheet** | Pre-compute recommendations weekly; paste them into the product page template as hardcoded HTML |
| 4.2 | **Precomputed table in DB** | Nightly batch job writes top-N recommendations per user to a `recommendations` table; product page reads from it |
| 4.3 | **REST API (synchronous)** | A lightweight API endpoint (`GET /recommendations?user_id=123`) computes or fetches recommendations on request |
| 4.4 | **Cached API with fallback** | API with Redis cache (TTL = 1h); on cache miss, fall back to global bestsellers |
| 4.5 | **Real-time personalized API with A/B testing** | Sub-100ms latency serving layer with feature flags, canary rollout, and experiment framework |

---

### Layer 5 — Evaluate & Improve

| # | Option | Description |
|---|--------|-------------|
| 5.1 | **No measurement** | Ship it and hope users click |
| 5.2 | **Manual spot-check** | Developer or analyst manually reviews the recommendations for a handful of users weekly |
| 5.3 | **Offline metrics** | Compute precision@K, recall@K, or NDCG on a held-out test set; log to a report |
| 5.4 | **Online click-through tracking** | Track clicks on recommended items; compute CTR and purchase conversion via analytics |
| 5.5 | **A/B testing + continuous retraining loop** | Statistically significant A/B tests comparing recommendation strategies; automatic model retraining triggered by metric regression |

---

## Step 3: Force Radical Slicing

**"If you had to ship something by tomorrow, what would you build?"**

Pick the lowest viable option from each layer:

| Layer | Choice | Rationale |
|-------|--------|-----------|
| 1 — Collect signals | **1.2** Batch query existing purchase data | The data is already in the DB. No new infrastructure needed. |
| 2 — Build profiles | **2.2** Simple frequency count per user | A SQL GROUP BY query gives us "most purchased categories/products per user" in minutes. |
| 3 — Generate recs | **3.1** Global bestsellers list | Same for everyone. Zero ML. Ships in an hour. |
| 4 — Serve recs | **4.2** Precomputed table in DB | A nightly cron job writes top-N rows; the product page does a SELECT. No new service. |
| 5 — Evaluate | **5.2** Manual spot-check | Look at the output yourself before shipping to real users. |

**This slice can be deployed in 1–2 days with no new infrastructure and no ML code.**
It delivers real value: users see "Recommended for you" sections instead of nothing. The team learns whether users actually click on recommendations before investing in ML.

---

## Step 4: Filter & Prioritize

**Options eliminated from Slice 1:**
- 1.5, 2.5, 3.5, 4.5 — all require new infrastructure (Kafka, feature stores, deep learning, A/B platform). Too costly before validating user interest.
- 3.5 (two-tower model) — would take 2–4 weeks to train, validate, and serve. Not reversible once you've built the serving infrastructure.

**Options kept:**
- 1.2 + 2.2 + 3.1 + 4.2 + 5.2 — each is fast to build, testable with real users, and expandable in the next slice without throwing away work.

---

## Step 5: Compose the Smallest Vertical Slice

### Slice 1 — "Something is better than nothing" (1–2 days)

**Goal:** Show personalized-ish recommendations on the product page for all users.

| Layer | Choice |
|-------|--------|
| Collect signals | 1.2: Batch query — read existing `orders` and `page_views` tables |
| Build profiles | 2.2: Frequency count — top 5 most-purchased categories per user, stored in `user_top_categories` table |
| Generate recs | 3.1: Fallback to global bestsellers if no user history; otherwise filter bestsellers by user's top categories |
| Serve recs | 4.2: Precomputed table — nightly cron writes top-10 recs per user to `user_recommendations` table |
| Evaluate | 5.2: Manual spot-check — developer reviews output for 5 test users before launch |

**What this proves:** Users see recommendations. The team validates the UI placement and product page integration before writing a single line of ML.

---

## Step 6: Plan Next Slices

### Slice 2 — "Real ML, minimal infrastructure" (3–5 days, after Slice 1)

Upgrade one layer at a time:

| Layer | Upgrade |
|-------|---------|
| Build profiles | **2.3** — Build a user-item interaction matrix using `scikit-surprise` or `implicit`. Run offline, output a similarity file. |
| Generate recs | **3.3** — Item-item collaborative filtering: for each product the user viewed, find the 5 most similar products. |
| Everything else | Keep from Slice 1 |

**What this adds:** Real personalization based on behavior patterns, not just category preferences. Still no new serving infrastructure.

---

### Slice 3 — "Online metrics & trust" (3–5 days, after Slice 2)

| Layer | Upgrade |
|-------|---------|
| Serve recs | **4.4** — Add Redis cache with 1-hour TTL; fallback to global bestsellers on cache miss |
| Evaluate | **5.4** — Track clicks on recommended items via an analytics event; build a simple CTR dashboard in your existing BI tool |

**What this adds:** You now know whether recommendations are working. Cache reduces DB load as traffic grows.

---

### Slice 4 — "Production-grade ML" (2–4 weeks, after Slice 3 proves value)

| Layer | Upgrade |
|-------|---------|
| Collect signals | **1.3** — Structured event logging for real-time browsing behavior (not just purchases) |
| Build profiles | **2.4** — Use LightFM or a pre-trained sentence transformer on product descriptions to generate dense embeddings |
| Generate recs | **3.5** — Two-tower retrieval model + FAISS index for sub-10ms candidate retrieval |
| Serve recs | **4.5** — Dedicated recommendation microservice with A/B testing capability |
| Evaluate | **5.5** — A/B test Slice 4 vs. Slice 3; trigger model retraining when CTR drops >10% |

**What this adds:** True ML-powered personalization at scale, but only after you've validated that users click on recommendations and the business cares enough to invest.

---

## Self-Check

- [x] Identified 5 clear functional layers (not "frontend/backend/DB")
- [x] Generated 5 options per layer following the quality gradient (manual → scripted → automated → scalable → enterprise)
- [x] Forced radical slicing — "ship by tomorrow" exercise completed
- [x] Smallest vertical slice uses level 1–2 options from each layer
- [x] Smallest slice delivers value to real users (visible recommendations on the product page)
- [x] Smallest slice can be deployed in 1–2 days with no new infrastructure
- [x] Proposed 3 follow-up slices with clear incremental improvements

---

## Summary

| Slice | Key Technology | Build Time | Value Delivered |
|-------|----------------|------------|-----------------|
| **Slice 1** | SQL + cron job | 1–2 days | "Recommended for you" section appears; validates UI/UX |
| **Slice 2** | Collaborative filtering (scikit-surprise) | 3–5 days | Real personalization based on behavior; no new infra |
| **Slice 3** | Redis cache + CTR tracking | 3–5 days | Measurable impact; reduced DB load |
| **Slice 4** | Two-tower model + FAISS + A/B testing | 2–4 weeks | Production ML with continuous improvement |

**The trap to avoid:** Building Slice 4 first. Most teams that do this spend 6 weeks on ML infrastructure and then discover users don't click on recommendations because the UI placement was wrong — something Slice 1 would have revealed in 2 days.
