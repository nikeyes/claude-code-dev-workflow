# Hamburger Method: Sales Dashboard for CEO Decision-Making

**Task:** Build a sales dashboard that shows monthly revenue, top products, and customer acquisition trends so our CEO can make decisions.

---

## Step 1: Identify Layers

The sales dashboard feature breaks down into these functional layers:

1. **Data Source** — Where does the sales/customer data come from?
2. **Data Processing** — How is raw data aggregated and transformed into metrics?
3. **Output Format** — How is the data presented to the CEO?
4. **Delivery Mechanism** — How does the CEO access the dashboard?
5. **Refresh / Timeliness** — How current is the data?
6. **Access & Security** — Who can see the data and how is access controlled?

---

## Step 2: Generate 4-5 Options per Layer

### Layer 1 — Data Source

- **1.1:** Hardcoded spreadsheet (CSV exported manually from the DB once)
- **1.2:** Single database table queried directly via SQL script
- **1.3:** Dedicated read replica or reporting DB view
- **1.4:** Data warehouse (e.g., BigQuery, Redshift) fed by ETL pipeline
- **1.5:** Federated data from multiple sources (CRM, billing, analytics) via unified data platform

### Layer 2 — Data Processing / Aggregation

- **2.1:** Manual formula calculations in a spreadsheet (SUM, VLOOKUP)
- **2.2:** SQL query that pre-aggregates revenue by month, ranks products by revenue, counts new customers per period
- **2.3:** Scheduled script (cron/Airflow) that writes aggregated results to a summary table
- **2.4:** Streaming aggregation pipeline with incremental updates
- **2.5:** ML-enriched analytics (forecasting, anomaly detection, cohort analysis)

### Layer 3 — Output Format

- **3.1:** Plain text email with numbers copy-pasted from the spreadsheet
- **3.2:** Static HTML page or PDF with tables and basic charts generated from the query
- **3.3:** Interactive chart tool (Google Sheets chart, Metabase, Superset) with drill-down
- **3.4:** Custom-built single-page app (React + charting library) with filters and date range picker
- **3.5:** Executive narrative dashboard with AI-generated commentary and trend interpretation

### Layer 4 — Delivery Mechanism

- **4.1:** Manual: analyst runs query, pastes into email, sends to CEO
- **4.2:** Scheduled email report (cron sends PDF/CSV attachment once a week)
- **4.3:** Shared URL (e.g., Metabase public link, Google Data Studio, Observable notebook)
- **4.4:** Internal web app behind company SSO
- **4.5:** Mobile app with push notifications on significant metric changes

### Layer 5 — Refresh / Timeliness

- **5.1:** On-demand (CEO requests a refresh manually)
- **5.2:** Daily batch refresh (scheduled overnight)
- **5.3:** Hourly refresh
- **5.4:** Near-real-time (< 5 min lag)
- **5.5:** Fully real-time streaming

### Layer 6 — Access & Security

- **6.1:** No access control — file shared via Slack/email
- **6.2:** Password-protected link
- **6.3:** Google/GitHub OAuth — only people with company email can view
- **6.4:** Role-based access control (RBAC) with audit logs
- **6.5:** Enterprise SSO with row-level security per org/region

---

## Step 3: Force Radical Slicing

> **"If you had to ship something by tomorrow, what would you build?"**

Pick one option from each layer — the absolute minimum that still delivers value to the CEO:

| Layer | Choice | Rationale |
|-------|--------|-----------|
| 1 — Data Source | **1.2** Single DB query | Real data, no new infrastructure |
| 2 — Processing | **2.2** SQL aggregation query | One query computes all three metrics |
| 3 — Output Format | **3.2** Static HTML page with basic charts | Readable without tooling, shareable |
| 4 — Delivery | **4.1** Analyst runs query, sends email | Zero infra, ships in hours |
| 5 — Timeliness | **5.1** On-demand | CEO asks → analyst runs → sends |
| 6 — Access | **6.1** Shared via email | No auth needed for a single recipient |

**Smallest vertical slice (ship by tomorrow):**

> An analyst runs a SQL query against the production DB, pastes the output into a simple HTML page with three sections (monthly revenue table, top-10 products by revenue, new customer count per month), and emails it to the CEO.

**Why this is valid:**
- Delivers all three requested metrics (revenue, top products, acquisition) in one slice
- Wait — actually, per skill rule: "If the user requested multiple outputs or metrics, the first slice must pick EXACTLY ONE — the most informative single output."

**Revised Smallest Slice — pick the single most decision-relevant metric:**

The CEO's stated need is to "make decisions." The most actionable single metric for a CEO is **monthly revenue** — it drives pricing, hiring, and investment decisions immediately.

**Revised Slice 1 (ship by tomorrow):**

| Layer | Choice |
|-------|--------|
| 1 — Data Source | **1.2** Single DB table query |
| 2 — Processing | **2.2** SQL query: `SELECT month, SUM(amount) FROM orders GROUP BY month ORDER BY month DESC LIMIT 12` |
| 3 — Output Format | **3.1** Plain text / simple table in an email body |
| 4 — Delivery | **4.1** Analyst manually sends email to CEO |
| 5 — Timeliness | **5.1** On-demand |
| 6 — Access | **6.1** Direct email, no auth |

**This slice can be deployed today.** It answers: "Is revenue growing, flat, or declining month over month?" — which is the decision the CEO needs to make.

---

## Step 4: Filter & Prioritize Options

**Eliminated:**
- 1.5 (Federated platform) — massive infrastructure cost, blocks delivery for months
- 2.5 (ML forecasting) — high complexity, not needed for basic CEO visibility
- 3.4 / 3.5 (Custom app / AI narrative) — weeks of engineering, irreversible if wrong assumptions
- 4.5 (Mobile app with push) — unrelated to core need, large scope
- 5.5 (Real-time streaming) — overkill for monthly trend decisions
- 6.4 / 6.5 (RBAC / Enterprise SSO) — add only when multiple stakeholders need access

**Kept for early slices:**
- Options 1.1–1.3, 2.1–2.3, 3.1–3.3, 4.1–4.3, 5.1–5.2, 6.1–6.3 — all fast, reversible, expandable

---

## Step 5: Vertical Slices

### Slice 1 — "Revenue pulse" (Ship today, ~2-4 hours)
**Answers: Is our revenue growing?**

- 1.2 Single DB query on orders table
- 2.2 SQL: monthly revenue aggregation for last 12 months
- 3.1 Plain text table in email body
- 4.1 Analyst manually emails CEO
- 5.1 On-demand
- 6.1 Direct email

**Value:** CEO sees revenue trend immediately. No infrastructure. Reversible. Tests whether this is even the right metric.

---

### Slice 2 — "Top products snapshot" (1-2 days after Slice 1)
**Answers: Which products are driving revenue?**

- Keep layers 1, 2, 4, 5, 6 the same as Slice 1
- Extend the SQL query to also return `TOP 10 products by revenue this month`
- 3.2 Add a second section to the email with a simple ranked table

**Value:** CEO can now make product prioritization decisions. One additional SQL JOIN, no new infrastructure.

---

### Slice 3 — "Customer acquisition trend" + shared link (2-3 days)
**Answers: Are we acquiring more customers month over month?**

- 1.2 Same DB query, add `COUNT(DISTINCT customer_id) WHERE is_new_customer = true GROUP BY month`
- 2.2 Three-query bundle (revenue + products + acquisition)
- 3.3 Move from email to a shared Metabase or Google Data Studio link with three charts
- 4.3 CEO bookmarks URL, accesses anytime
- 5.2 Daily scheduled refresh
- 6.2 Password-protected link

**Value:** CEO has a persistent, self-service view of all three metrics. Still zero custom code. Analyst stops sending manual emails.

---

### Slice 4 — "CEO self-service dashboard" (1 week)
**Adds: Date range filters, interactivity, company auth**

- 1.3 Dedicated reporting DB view or read replica (no load on production)
- 2.3 Scheduled aggregation job writes to summary tables
- 3.3 Metabase or Superset with drill-down by product category, region
- 4.3 Internal URL
- 5.2 Daily refresh (upgrade to 5.3 hourly if needed)
- 6.3 Google OAuth — company email required

---

## Self-Check

- [x] 3-6 clear functional layers identified (6 layers)
- [x] At least 4-5 options per layer generated (5 options each)
- [x] Options follow quality gradient (manual → scripted → automated → scalable → enterprise)
- [x] Forced radical slicing: "ship by tomorrow" question asked and answered explicitly
- [x] Smallest slice picks EXACTLY ONE metric (monthly revenue) per skill rule
- [x] Smallest slice delivers value to a named user (CEO) and answers a specific question
- [x] Smallest slice deployable in < 1 day with no new infrastructure
- [x] 3 follow-up slices proposed showing clear incremental improvement

---

## Summary

| Slice | What it delivers | Time to build | Key decision enabled |
|-------|-----------------|---------------|----------------------|
| **Slice 1** | Monthly revenue table via email | 2-4 hours | Is revenue growing? |
| **Slice 2** | + Top 10 products by revenue | 1-2 days | Which products to prioritize? |
| **Slice 3** | + Customer acquisition + shared link | 2-3 days | Are we growing our customer base? |
| **Slice 4** | Full interactive dashboard with auth | ~1 week | Self-service CEO analytics |

Start with Slice 1 today. If the CEO looks at it and says "this is exactly what I needed" — you've validated the direction before building any infrastructure.
