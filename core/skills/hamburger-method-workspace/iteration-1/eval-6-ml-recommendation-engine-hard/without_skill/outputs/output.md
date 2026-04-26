# Hamburger Method: ML-Powered Product Recommendation Engine

## Feature Description

Build a product recommendation engine that uses machine learning to suggest relevant items to users based on their browsing and purchase history.

---

## Step 1: Identify Layers

The recommendation engine is composed of the following 6 functional layers:

1. **Collect user behavior data** — Capture what users browse and buy
2. **Build user-item representation** — Transform raw events into a usable model input
3. **Generate recommendations** — Produce a ranked list of relevant products for each user
4. **Serve recommendations** — Deliver results to the UI or consuming service
5. **Present recommendations to the user** — Display them in the product interface
6. **Measure recommendation quality** — Track whether recommendations lead to engagement or conversion

---

## Step 2: Generate 4–5 Options per Layer

### Layer 1 — Collect user behavior data

- **1.1**: Manually curate a static CSV file of user–product interactions (hardcoded test data)
- **1.2**: Log page views and purchases to a simple database table via existing server-side events
- **1.3**: Instrument frontend with an event tracker (e.g., click, view, add-to-cart) sent to a logging endpoint
- **1.4**: Stream events in real time via a message queue (e.g., Kafka, SQS) with schema validation
- **1.5**: Full behavioral data platform with session stitching, identity resolution, and consent management

### Layer 2 — Build user-item representation

- **2.1**: Hardcode a manually crafted affinity matrix (e.g., "user A likes category X")
- **2.2**: Compute simple co-occurrence counts (items bought together) from the purchases table
- **2.3**: Build a user-item interaction matrix from behavioral logs; apply basic normalization (e.g., TF-IDF on views)
- **2.4**: Train a collaborative filtering model (matrix factorization, ALS) on historical interaction data
- **2.5**: Train a deep learning model (e.g., two-tower neural network) combining behavioral, contextual, and item features

### Layer 3 — Generate recommendations

- **3.1**: Return a hardcoded list of best-selling products (same for all users)
- **3.2**: Rule-based recommendations: "users who bought X also buy Y" from manual lookup table
- **3.3**: Item-based collaborative filtering using pre-computed similarity scores (offline batch)
- **3.4**: User-based collaborative filtering or matrix factorization inference run nightly; results cached in DB
- **3.5**: Real-time ML inference with a trained model served via a prediction API, personalized per request

### Layer 4 — Serve recommendations

- **4.1**: Hardcoded recommendations returned directly from application code (no separate service)
- **4.2**: Query a pre-populated recommendations table in the existing database
- **4.3**: Dedicated internal REST endpoint that reads cached recommendation rows for a given user
- **4.4**: Recommendation microservice with caching layer (Redis), fallback to popular items, and latency SLAs
- **4.5**: Feature store + real-time serving infrastructure with A/B experiment routing and shadow scoring

### Layer 5 — Present recommendations to the user

- **5.1**: Add a plain text list of product names to an existing page (no styling)
- **5.2**: Render a basic product card grid in an existing "You might also like" section
- **5.3**: Dedicated recommendation widget with product images, names, prices, and CTA buttons
- **5.4**: Contextual placement (homepage, PDP, cart page, email) with personalized section titles
- **5.5**: Fully dynamic, personalized page layouts driven by recommendation signals across all surfaces

### Layer 6 — Measure recommendation quality

- **6.1**: No measurement — ship and see what happens
- **6.2**: Log whether a recommended product was subsequently purchased (manual SQL query)
- **6.3**: Track click-through rate (CTR) on recommendation widgets via existing analytics
- **6.4**: Offline evaluation metrics (precision@k, recall@k, NDCG) computed on a held-out dataset
- **6.5**: Online A/B testing framework comparing recommendation strategies by revenue uplift and CTR

---

## Step 3: Force Radical Slicing

> "If you had to ship something by tomorrow, what would you build?"

The smallest meaningful end-to-end slice must:
- Deliver value to at least one real user or stakeholder
- Be testable with real or near-real data
- Be buildable in less than 1–3 days
- Require no new infrastructure

**Answer:** Show every user the same list of the 10 best-selling products in a plain section on the homepage, pulled from a query on the existing orders table, rendered as a minimal product list. This is real data, real users, zero new ML infrastructure, and it ships tomorrow.

---

## Step 4: Filter and Prioritize Options

**Eliminated options (too costly for this slice):**
- 1.4, 1.5 — Real-time event streaming requires Kafka/SQS setup; blocks fast delivery
- 2.4, 2.5 — Training ML models requires labeled data, compute, and model management infrastructure
- 3.5 — Real-time ML inference requires a model serving stack (e.g., TorchServe, SageMaker)
- 4.4, 4.5 — Microservice + Redis + feature store is significant new infrastructure
- 5.4, 5.5 — Multi-surface placement and dynamic layouts require extensive frontend work
- 6.4, 6.5 — Offline evaluation and A/B testing require instrumentation and experiment tooling

**Kept options for the minimal slice:**
- 1.1 or 1.2 — Static data or existing purchases table (no new instrumentation)
- 2.2 — Co-occurrence from purchases table (SQL query, no model training)
- 3.1 or 3.2 — Hardcoded bestsellers or simple lookup from query results
- 4.1 or 4.2 — Application code or simple DB read, no new service
- 5.1 or 5.2 — Plain list or basic card grid in existing page
- 6.1 or 6.2 — No tracking initially, or a simple manual SQL check afterward

---

## Step 5: Compose the Smallest Vertical Slice

**Slice 1 — "Bestsellers as recommendations" (ship in 1 day)**

| Layer | Choice | Description |
|---|---|---|
| 1. Collect data | **1.2** | Use existing purchases table — no new instrumentation needed |
| 2. Build representation | **2.2** | SQL query: top 10 most purchased products in the last 30 days |
| 3. Generate recommendations | **3.1** | Return the same top-10 bestseller list to all users |
| 4. Serve recommendations | **4.2** | Pre-populate a `recommendations` table nightly via a cron job or manual script |
| 5. Present to user | **5.2** | Render a basic product card grid in an existing "You might also like" section |
| 6. Measure quality | **6.2** | Log whether a recommended product was subsequently purchased (SQL query, checked weekly) |

**Why this works:**
- Zero new infrastructure required
- Uses existing orders data
- Every user gets served a recommendation
- Delivers measurable business value (bestsellers convert)
- The `recommendations` table acts as a stable contract, so future iterations can replace the data source without touching the UI

---

## Step 6: Plan Next Slices

**Slice 2 — "Also bought" personalization (2–3 days)**
- Upgrade 2.2 → **2.3**: Compute item co-occurrence matrix from purchases ("users who bought X also bought Y")
- Upgrade 3.1 → **3.2**: Return item-based recommendations per product page (not user-based yet)
- Keep layers 4, 5, 6 the same
- Result: Product Detail Pages show contextually relevant recommendations without requiring user identity

**Slice 3 — "Per-user history" recommendations (3–5 days)**
- Upgrade 1.2 → **1.3**: Instrument browse events (page views, add-to-cart) in addition to purchases
- Upgrade 3.2 → **3.3**: Offline batch collaborative filtering (item-based) from interaction matrix; run nightly
- Upgrade 4.2 → **4.3**: Dedicated REST endpoint reading cached user-specific rows
- Keep layer 5 the same
- Upgrade 6.2 → **6.3**: Track CTR on the widget via existing analytics
- Result: Each logged-in user gets personalized recommendations, validated by CTR data

**Slice 4 — "Real-time ML inference" (1–2 weeks)**
- Upgrade 2.3 → **2.4**: Train a matrix factorization (ALS) model on interaction data; schedule weekly retraining
- Upgrade 3.3 → **3.5**: Serve model predictions via a lightweight prediction API (e.g., FastAPI + joblib)
- Upgrade 4.3 → **4.4**: Add Redis caching to recommendation service with fallback to bestsellers
- Upgrade 6.3 → **6.4**: Compute offline precision@k against held-out purchases to evaluate model quality
- Result: Genuinely personalized ML recommendations with measured offline performance

---

## Self-Check

- [x] Identified 6 clear functional layers (not just frontend/backend/DB)
- [x] Generated 5 options per layer following manual → scripted → automated → scalable → enterprise gradient
- [x] Forced radical slicing: "ship by tomorrow" question answered with a concrete, deployable slice
- [x] Smallest vertical slice uses level 1–2 options from each layer
- [x] Smallest slice delivers real value (bestsellers are high-converting, shown to all users)
- [x] Smallest slice requires no new infrastructure (existing DB, existing UI section, cron job)
- [x] Smallest slice is deployable in 1 day
- [x] Proposed 3 follow-up slices showing incremental, layer-by-layer improvement
