# Hamburger Method: Sales Dashboard for CEO Decision-Making

## Feature Description

> "Build a sales dashboard that shows monthly revenue, top products, and customer acquisition trends so our CEO can make decisions"

---

## Step 1: Identify Layers

This feature involves several distinct technical and business steps. Let's break it down into layers:

1. **Data sourcing** — where does the data come from?
2. **Data processing** — how is data aggregated and computed?
3. **Visualization** — how are metrics presented visually?
4. **Access & delivery** — how does the CEO access the dashboard?
5. **Freshness & update cadence** — how current is the data?

---

## Step 2: Generate 4–5 Options per Layer

### Layer 1 — Data Sourcing

How do we get monthly revenue, top products, and customer acquisition data?

- **1.1** — Manually export CSV from the DB/ERP and place it in a shared folder
- **1.2** — Write a SQL query that team runs on demand and pastes results into a spreadsheet
- **1.3** — Scheduled script (e.g., cron) queries the DB and writes results to a flat file or Google Sheet
- **1.4** — Read-only DB view or materialized view exposed to the dashboard tool
- **1.5** — Real-time data pipeline (e.g., Kafka, CDC) feeding a data warehouse (BigQuery, Snowflake)

---

### Layer 2 — Data Processing

How are raw records turned into the three KPIs (monthly revenue, top products, customer acquisition)?

- **2.1** — Hardcoded summary numbers typed directly into a document or slide deck
- **2.2** — Spreadsheet with manual formulas (SUM, COUNTIF, VLOOKUP) that someone fills in
- **2.3** — SQL query that computes the aggregations on the fly (GROUP BY month, SUM revenue, rank products)
- **2.4** — Pre-computed summary table refreshed nightly by a script or scheduled job
- **2.5** — dbt models or ETL pipeline that maintains clean, versioned, tested aggregation logic

---

### Layer 3 — Visualization

How are the three KPIs shown to the CEO?

- **3.1** — Plain text email or Slack message with three numbers: "March revenue: $X, Top product: Y, New customers: Z"
- **3.2** — Spreadsheet (Google Sheets / Excel) with charts built from formulas
- **3.3** — Static report PDF or screenshot sent on a schedule (e.g., automated screenshot of a Google Sheet)
- **3.4** — BI tool dashboard (Metabase, Looker, Tableau, Power BI) with three charts: bar chart for revenue, ranked table for top products, line chart for customer acquisition
- **3.5** — Custom-built interactive web dashboard with drill-down, filters (date range, product category, region), and trend annotations

---

### Layer 4 — Access & Delivery

How does the CEO receive or access this information?

- **4.1** — Someone manually sends the numbers in a message (Slack/email) when asked
- **4.2** — Scheduled automated email with the summary (e.g., every Monday morning)
- **4.3** — Shared link to a Google Sheet or Notion page that the CEO can open on demand
- **4.4** — BI tool URL shared with the CEO (login required, self-serve)
- **4.5** — Embedded dashboard in an internal portal or mobile app with SSO

---

### Layer 5 — Freshness & Update Cadence

How current is the data the CEO sees?

- **5.1** — Data is as of last manual export (could be days or weeks old)
- **5.2** — Updated weekly when someone runs the query manually
- **5.3** — Refreshed nightly by a scheduled script or BI tool cache
- **5.4** — Refreshed every few hours (e.g., 4× per day via cron or scheduled BI refresh)
- **5.5** — Near real-time (streaming pipeline, sub-minute latency)

---

## Step 3: Force Radical Slicing

**If you had to ship something by tomorrow, what would you build?**

Answer: Pull the three numbers from the DB today, write them in a Slack message or email to the CEO, and repeat that manually every Monday. No infrastructure. No code. No dashboard tool. Just the data in front of the right person.

---

## Step 4: Filter & Prioritize Options

**Eliminate options that:**
- Require new infrastructure (streaming pipelines, data warehouses) — blocks fast delivery, high cost
- Are irreversible or hard to undo (custom-built web app from scratch before validating CEO's actual needs)
- Are too costly for the value they currently provide (5.5 real-time stream when a weekly summary is enough)

**Keep options that are:**
- Fast to build (hours to 1-2 days)
- Testable with the actual CEO
- Reversible (easy to upgrade later)
- Expose us to feedback about what the CEO actually needs

---

## Step 5: Compose the Smallest Vertical Slice

**Slice 1 — "Ship by tomorrow" (1-2 hours of work)**

| Layer | Choice | Description |
|-------|--------|-------------|
| Data Sourcing | **1.2** | Run a SQL query on demand |
| Data Processing | **2.3** | SQL aggregation query computes the three KPIs |
| Visualization | **3.1** | Plain text summary in Slack or email |
| Access & Delivery | **4.1** | Manually sent by a team member on Monday mornings |
| Freshness | **5.2** | Updated weekly when someone runs the query |

**What this delivers:**
- Monthly revenue (current month vs. prior month)
- Top 5 products by revenue
- New customers acquired this month vs. prior month

**Who gets value:** The CEO gets the three numbers every Monday without asking. That alone enables decision-making.

**Time to build:** Write the SQL query (~1-2 hours). Share results manually. Done.

**What we learn:** Does the CEO actually read it? Do they ask for more detail? Do they want it broken down differently (by region, by channel)? This feedback shapes the next slice.

---

## Step 6: Plan Next Slices

**Slice 2 — "Automate the delivery" (1 day)**

Upgrade Layer 4 from manual to automated. Set up a scheduled job (cron or Zapier) that runs the SQL query and sends the formatted results to the CEO via Slack or email every Monday morning.

- Data Sourcing: **1.3** (scheduled script)
- Data Processing: **2.3** (same SQL query)
- Visualization: **3.1** (plain text, same)
- Access & Delivery: **4.2** (automated scheduled message)
- Freshness: **5.3** (nightly refresh)

No new BI tool. No dashboard yet. Just automation of the manual step.

---

**Slice 3 — "Give the CEO a self-serve view" (1-2 days)**

Upgrade Layer 3 from text to a shareable spreadsheet or Metabase dashboard that the CEO can open anytime.

- Data Sourcing: **1.3** (scheduled script writing to a Google Sheet or DB)
- Data Processing: **2.4** (pre-computed summary table refreshed nightly)
- Visualization: **3.4** (Metabase or Google Sheets with three charts)
- Access & Delivery: **4.3** (shared link, no login friction)
- Freshness: **5.3** (nightly refresh)

This is the first real "dashboard." Still not custom-built — using an existing BI tool.

---

**Slice 4 — "Add trend context and drill-down" (2-3 days)**

Upgrade Layer 3 and Layer 2 to let the CEO answer follow-up questions independently.

- Data Processing: **2.5** (dbt models with clean aggregation logic, tested)
- Visualization: **3.4 → 3.5** (BI tool with date range filter, product category filter, MoM trend line)
- Access & Delivery: **4.4** (BI tool with CEO's own login)
- Freshness: **5.4** (4× per day refresh)

Only build this after the CEO has used Slice 3 and told you what follow-up questions they keep asking.

---

## Self-Check

- [x] Identified 5 clear functional layers (not just frontend/backend/database)
- [x] Generated 4-5 options per layer following a quality gradient (manual → scripted → automated → scalable → enterprise)
- [x] Forced radical slicing ("ship by tomorrow" question answered)
- [x] Smallest vertical slice uses level 1-2 options from each layer
- [x] Smallest slice delivers real value to the CEO (three KPIs every Monday)
- [x] Smallest slice can be built in hours, not days
- [x] Proposed 3 follow-up slices with clear incremental improvements

---

## Summary

| Slice | Core upgrade | Est. effort | Value delivered |
|-------|-------------|-------------|-----------------|
| **Slice 1** | SQL query + manual Slack message | 1-2 hours | CEO gets 3 KPIs every Monday |
| **Slice 2** | Automate the Monday message | ~1 day | Removes manual work, consistent delivery |
| **Slice 3** | Self-serve spreadsheet/Metabase dashboard | 1-2 days | CEO can check on demand, sees trends |
| **Slice 4** | Filters, drill-down, tested data models | 2-3 days | CEO answers follow-up questions independently |

**Start with Slice 1. Validate that the CEO reads it and finds it useful. Then decide if Slice 2, 3, or 4 is worth building.**

The biggest risk is not technical — it's building a beautiful dashboard that the CEO never opens. The smallest slice tests that assumption with near-zero investment.
