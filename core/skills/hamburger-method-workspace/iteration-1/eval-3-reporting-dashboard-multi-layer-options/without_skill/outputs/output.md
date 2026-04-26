# Hamburger Method — Sales Dashboard for CEO Decision-Making

## Feature Description

> Build a sales dashboard that shows monthly revenue, top products, and customer acquisition trends so our CEO can make decisions.

This feature is large but doesn't have obvious "and/or/manage" linguistic red flags that story-splitting would catch cleanly. It is well-suited for the Hamburger Method: a layered analysis that generates multiple implementation options per layer and composes the smallest vertical end-to-end slice.

---

## Step 1: Identify Layers

The complete flow for a CEO sales dashboard involves the following 5 functional layers:

1. **Data Source** — Where does the raw sales, product, and customer data come from?
2. **Data Processing** — How is raw data aggregated, calculated, and structured into metrics?
3. **Storage / Access** — Where are computed metrics stored and how are they retrieved?
4. **Presentation / Visualization** — How are metrics displayed to the CEO?
5. **Delivery / Access Control** — How does the CEO reach the dashboard and who else can see it?

These layers cover the end-to-end journey from raw data to CEO decision. They are functional, not purely technical (not "frontend/backend/DB"), and each one can independently vary in quality.

---

## Step 2: Generate 4–5 Implementation Options per Layer

### Layer 1 — Data Source

How raw sales, product, and customer acquisition data enters the system.

- **1.1 — Hardcoded sample data:** Manually create a JSON/CSV file with 3 months of fake but realistic data (revenue, products sold, new customers). No real system connected.
- **1.2 — Manual export from existing system:** Someone runs a SQL query or exports a CSV from Salesforce/Shopify/ERP once a day and drops it in a shared folder.
- **1.3 — Scheduled pull from a single database:** A cron job queries the production database (or a read replica) nightly and writes results to a reporting table.
- **1.4 — Multiple sources unified via ETL:** A lightweight ETL script (e.g., dbt, Airbyte) pulls from CRM + e-commerce + billing system on a schedule.
- **1.5 — Real-time streaming from all sources:** Event-driven pipeline (Kafka, Firehose) ingests sales events as they happen, enabling near real-time metrics.

---

### Layer 2 — Data Processing

How raw data is transformed into the three metrics: monthly revenue, top products, customer acquisition trends.

- **2.1 — Hardcoded calculations in code:** Metrics are computed inline from the hardcoded dataset with no configurable logic. Works only for the sample data.
- **2.2 — Manual SQL queries run on demand:** A set of SQL queries (or a spreadsheet formula) someone runs manually each time the CEO asks for a report.
- **2.3 — Scheduled batch job:** A script/job runs nightly, computes the three metrics, and writes them to a summary table or file.
- **2.4 — Parameterized queries with date range support:** Processing logic accepts date range and filters, allowing the CEO to explore different time windows.
- **2.5 — Automated anomaly detection and enrichment:** Processing layer includes trend analysis, YoY comparisons, forecasting, and flags significant changes automatically.

---

### Layer 3 — Storage / Access

Where computed metrics live and how they are retrieved for display.

- **3.1 — Static file (JSON/CSV):** Computed metrics are saved as a flat file committed to a repo or placed in a shared folder. No database needed.
- **3.2 — Single database table:** Metrics are stored in a simple SQL table (e.g., `monthly_revenue`, `top_products`, `acquisition_trends`). Queried directly by the presentation layer.
- **3.3 — Dedicated reporting schema:** A read-optimized schema or materialized views in the production DB, separate from operational tables, updated on a schedule.
- **3.4 — Data warehouse layer:** Metrics stored in a dedicated warehouse (BigQuery, Redshift, Snowflake), decoupled from production DB, enabling complex historical queries.
- **3.5 — Cached API with invalidation:** A caching layer (Redis, CDN) sits in front of the data store, serving pre-computed metrics instantly and invalidating on update.

---

### Layer 4 — Presentation / Visualization

How the three KPIs are shown to the CEO.

- **4.1 — Plain text email or Slack message:** Monthly revenue, top 5 products, and new customer count sent as formatted plain text. No UI, no browser needed.
- **4.2 — Static HTML page or shared spreadsheet:** A generated HTML file or Google Sheet that is updated manually or by a script and shared via link.
- **4.3 — Simple web dashboard (tables + basic charts):** A minimal web app (e.g., React + Chart.js, or Metabase) showing the three metrics with bar/line charts. No interactivity beyond viewing.
- **4.4 — Interactive dashboard with filters:** CEO can filter by date range, product category, region. Drill-down into monthly detail.
- **4.5 — Embedded analytics with annotations and alerts:** Full BI tool experience (Tableau, Looker, Power BI) with annotations, commentary, scheduled email digests, and threshold-based alerts.

---

### Layer 5 — Delivery / Access Control

How the CEO reaches the dashboard and who has access.

- **5.1 — Direct file share or email attachment:** Send the report as a file or email directly to the CEO. No authentication, no URL, no login.
- **5.2 — Shared link (no login required):** The report is accessible via a URL shared only with the CEO. Security by obscurity.
- **5.3 — Password-protected page or basic auth:** Simple username/password protects the URL. Works for small teams with minimal security requirements.
- **5.4 — SSO / company login:** Access controlled via the company's identity provider (Google Workspace, Okta). Only authenticated employees can view.
- **5.5 — Role-based access with audit log:** Full RBAC: CEO sees all, sales managers see their region, access log records every view. Suitable for sensitive financial data.

---

## Step 3: Force Radical Slicing

**"If you had to ship something by tomorrow so the CEO can make a decision, what would you build?"**

The CEO needs: monthly revenue numbers, top products, new customer count. The CEO does NOT need: interactivity, filters, real-time data, or fancy charts — not on day one.

The smallest thing that is still useful to a real stakeholder (the CEO) is a report they can read today with real data.

---

## Step 4: Filter & Prioritize Options

Options eliminated:
- **1.5** (real-time streaming): Requires Kafka/Firehose infrastructure. Days to weeks to set up. No value on day one.
- **2.5** (anomaly detection): Over-engineering for a first slice. Forecasting adds no value until the CEO trusts the basic numbers.
- **3.4 / 3.5** (data warehouse, Redis cache): Overkill. A single DB table is sufficient for weekly-updated CEO metrics.
- **4.4 / 4.5** (interactive filters, Tableau/Looker): CEO can request drill-down later. Start with readable numbers.
- **5.4 / 5.5** (SSO, RBAC): Security is important but not a day-one blocker if the report is sent directly to the CEO.

Options kept for the first slice: the lowest tier that still uses real data and is readable by the CEO.

---

## Step 5: Compose the Smallest Vertical Slice

**Slice 1 — "The Weekly Email Report" (can be shipped in 1 day)**

| Layer | Choice | Rationale |
|---|---|---|
| **1. Data Source** | 1.2 — Manual export from existing system | Real data, zero new infrastructure. Someone runs a query or exports a CSV from the existing DB/CRM. |
| **2. Data Processing** | 2.2 — Manual SQL queries run on demand | Three SQL queries (monthly revenue, top 10 products by revenue, new customers per month). Can be run in any SQL client. |
| **3. Storage / Access** | 3.1 — Static file (JSON/CSV) | Query results saved as a CSV or copy-pasted into a doc. No new table needed. |
| **4. Presentation** | 4.1 — Plain text email or Slack message | Format the three metrics as a readable Slack message or email. CEO reads it immediately. |
| **5. Delivery** | 5.1 — Direct email or Slack DM to CEO | Send it. No URL, no login, no deploy. |

**What this slice delivers:**
- CEO sees this month's revenue vs. last month
- CEO sees top 5 products by revenue this month
- CEO sees new customer count trend (last 3 months)
- CEO can make a real decision TODAY

**What it does NOT include:**
- Charts or visualizations
- A URL or hosted page
- Automated refresh
- Any new code deployed to production

**Build time estimate:** 2–4 hours (1h to write the queries, 1h to validate with real data, 1h to format and send)

---

## Step 6: Next Slices — Incremental Improvements

### Slice 2 — "The Automated Weekly Report" (~1–2 days)

Improve Layer 2 and Layer 5: replace the manual export with a scheduled script that runs the three SQL queries and sends the formatted Slack/email message automatically every Monday morning.

- **1.3** — Scheduled pull from DB (cron job)
- **2.3** — Batch job computes and formats metrics
- **3.1** — Still a static file or in-memory result
- **4.1** — Same Slack/email format
- **5.1** — Automated delivery (no manual step)

**New value:** CEO gets the report without anyone doing manual work. Removes operational burden.

---

### Slice 3 — "The Linkable Dashboard" (~2–3 days)

Improve Layer 4: replace the text message with a simple web page the CEO can bookmark and share with the board.

- **1.3** — Keep scheduled DB pull
- **2.3** — Keep batch job
- **3.2** — Metrics written to a DB table
- **4.3** — Simple web dashboard (Metabase, Retool, or a minimal React page) showing bar chart for revenue, ranked list for top products, line chart for customer acquisition
- **5.2** — Shared link (URL sent to CEO, no login required for now)

**New value:** CEO can reference the dashboard in board meetings, share the link with the CFO, and see a visual trend at a glance.

---

### Slice 4 — "The Secure, Self-Service Dashboard" (~3–5 days)

Improve Layer 5 and Layer 4: add authentication and basic date filtering.

- **4.4** — Interactive dashboard with date range picker
- **5.3** — Password-protected page or SSO login
- **3.3** — Reporting schema / materialized views for performance

**New value:** CEO and other executives can log in, explore different time windows, and the report is secure enough for sensitive financial data.

---

## Self-Check

- [x] Identified 3–6 clear functional layers (5 layers: data source, processing, storage, presentation, delivery)
- [x] Generated at least 4–5 options per layer (5 options each)
- [x] Options follow a quality gradient (manual → scripted → automated → scalable → enterprise)
- [x] Forced radical slicing ("ship by tomorrow")
- [x] Smallest vertical slice uses level 1–2 options from each layer
- [x] Smallest slice delivers value to the CEO (one real stakeholder) today
- [x] Smallest slice can be deployed in less than 1 day (2–4 hours)
- [x] Proposed 3 follow-up slices showing clear incremental improvement

---

## Summary

The Hamburger Method reveals that a "sales dashboard" is not a single big thing — it is at least 5 independent quality decisions. The CEO does not need a polished web app to make a decision. They need three numbers, formatted clearly, delivered to their inbox.

The smallest vertical slice (a manually-run SQL query formatted as a Slack/email message) takes a few hours, uses real data, and produces immediate CEO value. Every subsequent slice improves exactly one layer without disrupting what already works.

This prevents the common trap of spending weeks building a full-stack dashboard that the CEO never opens because it required a login they forgot.
