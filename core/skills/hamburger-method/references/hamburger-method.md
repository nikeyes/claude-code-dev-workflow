Author: Gojko Adzic
Source: https://gojko.net/2012/01/23/splitting-user-stories-the-hamburger-method/

# The Hamburger Method for Story Slicing

The Hamburger Method is a technique to break down large stories or features into smaller, valuable, and deliverable slices using a structured visual metaphor. It helps avoid purely horizontal (technical-layered) thinking and encourages vertical slicing — delivering value early and iteratively.

## Contents

1. [Core Steps](#-core-steps)
   - Identify Layers
   - Define Quality Attributes
   - Generate Multiple Options
   - Filter & Prioritize
   - Compose Vertical Slices
2. [Quality Gradients Reference](#-quality-gradients-reference)
   - Trigger/Detection
   - Data Source
   - Processing
   - Validation
   - Output/Delivery
   - Monitoring
3. [Extended Examples](#-extended-examples)
   - E-commerce Product Search
   - User Authentication System
   - Reporting Dashboard
4. [Common Pitfalls](#-common-pitfalls)
5. [Integration with Other Techniques](#-integration-with-other-techniques)

---

## 🧱 Core Steps

### 1. Identify Layers (Technical or Logical Steps)
List the main technical or business steps involved in the feature. These form the "layers" of the hamburger.

Example layers for a notification system:
- Detect triggering event
- Decide whom to notify
- Format the message
- Deliver the message
- Record status

---

### 2. Define Quality Attributes per Layer
For each layer, ask:
- What makes this layer "good"?
- What is the simplest form that still delivers value?
- What are possible tradeoffs (e.g. manual vs. automated)?

---

### 3. Generate Multiple Options (Low to High Quality)
For each layer, propose different implementations from very basic to advanced.

Example: "Deliver the message"
- Manual email
- Scripted email
- Email via queuing system with retries
- Multi-channel notification (email, push, SMS)

---

### 4. Filter & Prioritize
Eliminate options that are too costly, unnecessary, or redundant.
Focus on options that are:
- Fast to build
- Testable
- Reversible

---

### 5. Compose Vertical Slices
Create a cross-layer combination (one option per layer) that:
- Delivers value to real users
- Is the smallest usable unit
- Can be iterated upon

---

### 6. Iterate by Adding More Slices
Each new slice can improve a layer, handle an edge case, or increase robustness.

---

## ✅ Rules of Thumb

- Every vertical slice should be usable by someone.
- You don't need to build the "best" version first — just the smallest that works.
- If you're unsure where to start, prioritize reach (touch as many real users or flows as possible).

> **Coach's Question:** "If you had to ship something by tomorrow, what would you build?"
> Use this to force radical slicing and focus on immediate value.

---

## 🧠 Complete Examples

### Example 1: Notification System (from SKILL.md)

**Problem**: Implement "Notify users when a product they're watching drops in price"

**Layers**:
1. Detect price change
2. Identify watching users
3. Format notification
4. Deliver notification
5. Track delivery

**Options per layer:**

**Layer 1 - Detect price change:**
- 1.1: Manual check once per day
- 1.2: Cron job checking specific products
- 1.3: Automated price scraping for all products
- 1.4: Real-time event-driven detection
- 1.5: ML-based anomaly detection for price drops

**Layer 2 - Identify watching users:**
- 2.1: Hardcode one test user
- 2.2: Query existing watchlist table
- 2.3: Multi-tier watchlist with preferences
- 2.4: User segmentation based on behavior
- 2.5: Personalized relevance scoring

**Layer 3 - Format notification:**
- 3.1: Plain text string
- 3.2: Simple template with product name + price
- 3.3: HTML email with branding
- 3.4: Rich notification with images and CTAs
- 3.5: Personalized dynamic content

**Layer 4 - Deliver notification:**
- 4.1: Manual email from personal account
- 4.2: Scripted email via Gmail API
- 4.3: SMTP service (no retries)
- 4.4: Email queue with retries
- 4.5: Multi-channel (email + push + SMS)

**Layer 5 - Track delivery:**
- 5.1: No tracking
- 5.2: Log to console
- 5.3: Store delivery status in DB
- 5.4: Dashboard with delivery analytics
- 5.5: Real-time monitoring with alerts

**Smallest vertical slice (ship by tomorrow):**
- 1.1: Manual price check
- 2.1: Notify one test user (you)
- 3.1: Plain text message
- 4.1: Send via personal email
- 5.1: No tracking

**Next slices:**
- Slice 2: Automate price detection (1.2), keep rest the same
- Slice 3: Expand to real watchlist users (2.2)
- Slice 4: Add basic SMTP delivery (4.3)

---

### Example 2: E-commerce Product Search

**Feature:** "Build product search with filters, sorting, and recommendations"

**Layers:**
1. Accept search query
2. Execute search
3. Apply filters
4. Sort results
5. Display recommendations

**Options per layer:**

**Layer 1 - Accept search query:**
- 1.1: Single text input, no validation
- 1.2: Text input with basic validation
- 1.3: Text input + autocomplete
- 1.4: Text input + autocomplete + recent searches
- 1.5: Natural language processing

**Layer 2 - Execute search:**
- 2.1: SQL LIKE query on product name
- 2.2: Full-text search (PostgreSQL)
- 2.3: Dedicated search index (Elasticsearch)
- 2.4: Fuzzy matching + synonyms
- 2.5: ML-powered semantic search

**Layer 3 - Apply filters:**
- 3.1: No filters
- 3.2: Single filter (category)
- 3.3: Multiple filters (category, price range)
- 3.4: Advanced filters (brand, rating, availability)
- 3.5: Dynamic filters based on search results

**Layer 4 - Sort results:**
- 4.1: No sorting (database order)
- 4.2: Single sort (relevance)
- 4.3: Multiple sort options (price, date, rating)
- 4.4: User-selected default sort preference
- 4.5: Personalized ranking

**Layer 5 - Display recommendations:**
- 5.1: No recommendations
- 5.2: "Popular products" (hardcoded list)
- 5.3: "Similar products" (same category)
- 5.4: "Frequently bought together"
- 5.5: ML-powered personalized recommendations

**Smallest vertical slice:**
- 1.1: Single text input
- 2.1: SQL LIKE query
- 3.1: No filters
- 4.1: No sorting
- 5.1: No recommendations

Deploys in 2-3 hours. Users can search products immediately.

**Next slices:**
- Slice 2: Add full-text search (2.2)
- Slice 3: Add category filter (3.2)
- Slice 4: Add price sorting (4.2)

---

### Example 3: API Rate Limiting

**Feature:** "Implement rate limiting for our public API"

**Layers:**
1. Identify client
2. Track requests
3. Enforce limit
4. Respond to violations
5. Monitor usage

**Options per layer:**

**Layer 1 - Identify client:**
- 1.1: No identification (all requests treated equally)
- 1.2: API key in header
- 1.3: API key + user association
- 1.4: OAuth token
- 1.5: Multiple authentication methods

**Layer 2 - Track requests:**
- 2.1: No tracking
- 2.2: In-memory counter (single server)
- 2.3: Redis counter (multi-server)
- 2.4: Sliding window (Redis)
- 2.5: Distributed rate limiter with quotas

**Layer 3 - Enforce limit:**
- 3.1: No enforcement
- 3.2: Hard limit (block after N requests)
- 3.3: Soft limit (warn before blocking)
- 3.4: Tiered limits (different per plan)
- 3.5: Adaptive limits based on load

**Layer 4 - Respond to violations:**
- 4.1: Return 429 status
- 4.2: Return 429 + retry-after header
- 4.3: Return detailed error message
- 4.4: Return error + quota info
- 4.5: Allow burst + detailed analytics

**Layer 5 - Monitor usage:**
- 5.1: No monitoring
- 5.2: Log violations to file
- 5.3: Store metrics in database
- 5.4: Real-time dashboard
- 5.5: Alerts + anomaly detection

**Smallest vertical slice:**
- 1.2: API key in header
- 2.2: In-memory counter
- 3.2: Hard limit (100 req/hour)
- 4.1: Return 429 status
- 5.2: Log violations

Deploys in 3-4 hours. Protects API from abuse immediately.

**Next slices:**
- Slice 2: Add Redis counter for multi-server (2.3)
- Slice 3: Add retry-after header (4.2)
- Slice 4: Add usage metrics (5.3)

---

### Example 4: Batch Data Processing Pipeline

**Feature:** "Process daily sales data from CSV files"

**Layers:**
1. Retrieve source data
2. Validate data
3. Transform data
4. Load into database
5. Report results

**Options per layer:**

**Layer 1 - Retrieve source data:**
- 1.1: Manual file placement in folder
- 1.2: SFTP download
- 1.3: S3 bucket polling
- 1.4: Event-driven (S3 notification)
- 1.5: Multi-source aggregation

**Layer 2 - Validate data:**
- 2.1: No validation
- 2.2: Basic schema check (column count)
- 2.3: Type validation (dates, numbers)
- 2.4: Business rule validation
- 2.5: ML-based anomaly detection

**Layer 3 - Transform data:**
- 3.1: No transformation (load as-is)
- 3.2: Basic cleaning (trim whitespace, normalize dates)
- 3.3: Enrichment (lookup product names)
- 3.4: Aggregation (daily totals)
- 3.5: Complex calculations (margins, forecasts)

**Layer 4 - Load into database:**
- 4.1: INSERT one row at a time
- 4.2: Batch INSERT (100 rows)
- 4.3: Upsert (handle duplicates)
- 4.4: Transaction (rollback on error)
- 4.5: Parallel loading + partitioning

**Layer 5 - Report results:**
- 5.1: No report
- 5.2: Console log (success/failure)
- 5.3: Email summary
- 5.4: Detailed report with error rows
- 5.5: Dashboard with trends

**Smallest vertical slice:**
- 1.1: Manual file placement
- 2.2: Basic schema check
- 3.2: Basic cleaning
- 4.1: INSERT one row at a time
- 5.2: Console log

Deploys in 2-3 hours. Processes first sales file immediately.

**Next slices:**
- Slice 2: Add SFTP download (1.2)
- Slice 3: Add batch INSERT for performance (4.2)
- Slice 4: Add email summary (5.3)

---

### Example 5: User Authentication System

**Feature:** "Add user authentication to the application"

**Layers:**
1. Collect credentials
2. Validate credentials
3. Create session
4. Protect resources
5. Handle logout

**Options per layer:**

**Layer 1 - Collect credentials:**
- 1.1: Hardcoded test user
- 1.2: Simple login form (username + password)
- 1.3: Login form with validation
- 1.4: Login + "remember me"
- 1.5: Social login + password

**Layer 2 - Validate credentials:**
- 2.1: Hardcoded check
- 2.2: Database lookup (plaintext password)
- 2.3: Hashed password (bcrypt)
- 2.4: Hashed + rate limiting
- 2.5: Multi-factor authentication

**Layer 3 - Create session:**
- 3.1: No session (re-login every request)
- 3.2: In-memory session (single server)
- 3.3: Cookie-based session
- 3.4: JWT token
- 3.5: JWT + refresh token

**Layer 4 - Protect resources:**
- 4.1: No protection (all endpoints open)
- 4.2: Check session on one endpoint
- 4.3: Middleware for all protected endpoints
- 4.4: Role-based access control
- 4.5: Fine-grained permissions

**Layer 5 - Handle logout:**
- 5.1: No logout
- 5.2: Clear session cookie
- 5.3: Invalidate session server-side
- 5.4: Redirect to login page
- 5.5: Logout from all devices

**Smallest vertical slice:**
- 1.2: Simple login form
- 2.3: Hashed password (bcrypt)
- 3.3: Cookie-based session
- 4.2: Protect one endpoint
- 5.2: Clear session cookie

Deploys in 4-5 hours. Basic authentication works immediately.

**Next slices:**
- Slice 2: Protect all endpoints with middleware (4.3)
- Slice 3: Add "remember me" (1.4)
- Slice 4: Add logout redirect (5.4)

---

### Example 6: Background Job Processing

**Feature:** "Process image uploads in the background"

**Layers:**
1. Receive upload
2. Queue job
3. Process image
4. Store result
5. Notify user

**Options per layer:**

**Layer 1 - Receive upload:**
- 1.1: Manual file placement
- 1.2: Form upload (small files only)
- 1.3: Form upload with size validation
- 1.4: Chunked upload (large files)
- 1.5: Direct S3 upload

**Layer 2 - Queue job:**
- 2.1: No queue (process synchronously)
- 2.2: Database table as queue
- 2.3: Redis queue
- 2.4: Dedicated queue (Celery, RabbitMQ)
- 2.5: Priority queues + retries

**Layer 3 - Process image:**
- 3.1: No processing (store as-is)
- 3.2: Simple resize (one size)
- 3.3: Multiple sizes (thumbnail, medium, large)
- 3.4: Format conversion + optimization
- 3.5: ML-based enhancement

**Layer 4 - Store result:**
- 4.1: Local filesystem
- 4.2: Local filesystem + database reference
- 4.3: S3 bucket
- 4.4: S3 + CDN
- 4.5: Multi-region storage

**Layer 5 - Notify user:**
- 5.1: No notification
- 5.2: Update status in database (user polls)
- 5.3: Email notification
- 5.4: Real-time notification (WebSocket)
- 5.5: Multi-channel (email + push + in-app)

**Smallest vertical slice:**
- 1.2: Form upload (small files)
- 2.2: Database table as queue
- 3.2: Simple resize
- 4.2: Local filesystem + DB reference
- 5.2: Update status in database

Deploys in 3-4 hours. Users can upload images immediately.

**Next slices:**
- Slice 2: Add Redis queue for better performance (2.3)
- Slice 3: Store in S3 (4.3)
- Slice 4: Add email notification (5.3)

---

## Quick Reference: Common Layers by Domain

Use these as starting points for identifying layers in your features.

### Web Application Features

**Typical layers:**
1. Accept input (form, API, file upload)
2. Validate input (schema, business rules)
3. Process/transform (calculation, enrichment)
4. Store data (database, file system, cache)
5. Display output (UI, API response, notification)

### Data Processing Features

**Typical layers:**
1. Retrieve data (file, API, database, stream)
2. Validate data (schema, quality checks)
3. Transform data (cleaning, enrichment, aggregation)
4. Load data (database, file, data warehouse)
5. Report results (logs, email, dashboard)

### API Features

**Typical layers:**
1. Authenticate/authorize request
2. Validate request (schema, permissions)
3. Execute business logic
4. Prepare response (format, pagination)
5. Log/monitor (metrics, errors, audit trail)

### Background Job Features

**Typical layers:**
1. Trigger job (schedule, event, manual)
2. Queue job (in-memory, database, message queue)
3. Execute job (process, calculate, external API call)
4. Store result (database, file, cache)
5. Handle completion (notify, cleanup, retry)

---

## Quality Gradient Reference Table

Use these quality gradients to generate 4-5 options per layer systematically.

| Dimension | Level 1 (Minimal) | Level 2 (Basic) | Level 3 (Standard) | Level 4 (Advanced) | Level 5 (Enterprise) |
|-----------|-------------------|-----------------|--------------------|--------------------|---------------------|
| **Automation** | Manual | Script/tool | Scheduled automation | Event-driven | Fully autonomous |
| **Data Source** | Hardcoded | Single file/table | Multiple sources | External APIs | Federated/streaming |
| **Validation** | None | Basic (type checks) | Business rules | Comprehensive | ML-based anomaly detection |
| **Error Handling** | Fail fast | Log errors | Retry logic | Circuit breaker | Self-healing |
| **Scalability** | Single instance | Vertical scaling | Horizontal scaling | Auto-scaling | Multi-region |
| **Monitoring** | None | Console logs | Structured logs | Metrics + dashboards | Real-time alerts + AI |
| **User Experience** | Command line | Basic UI | Polished UI | Rich interactive UI | Personalized UX |
| **Performance** | No optimization | Basic optimization | Caching | Advanced optimization | Edge computing |
| **Security** | None | Basic auth | Encryption + auth | RBAC + audit | Zero trust architecture |

**How to use this table:**
1. Identify the layer dimension (e.g., "Validate data")
2. Choose the most relevant quality dimension (e.g., "Validation")
3. Generate 5 options using the levels from the table
4. Example: Validate data → (1) None, (2) Type checks, (3) Business rules, (4) Comprehensive validation, (5) ML anomaly detection

---

## Common Mistakes to Avoid

### Mistake 1: Horizontal Slicing

**Wrong:** Split by technical layers
- Story 1: Build database schema
- Story 2: Build API endpoints
- Story 3: Build UI

**Right:** Vertical slices with options per layer
- Slice 1: Manual → Simple API → Basic UI for one feature
- Slice 2: Add validation + better UI
- Slice 3: Add additional features

### Mistake 2: Too Few Options

**Wrong:** Only 2 options per layer (simple vs. complete)
- Layer 1: (1) Manual, (2) Fully automated

**Right:** Generate 4-5 options with gradual quality increase
- Layer 1: (1) Manual, (2) Script, (3) Cron job, (4) Event-driven, (5) AI-powered

### Mistake 3: Starting with High Quality

**Wrong:** First slice uses advanced options
- Slice 1: Real-time processing + ML + multi-region

**Right:** First slice uses simplest options
- Slice 1: Manual processing + hardcoded rules + single server

### Mistake 4: Skipping Filtering

**Wrong:** Don't evaluate if options are worth building
- Just list all possible options without filtering

**Right:** Filter out options that are:
- Too costly for the value
- Block fast delivery
- Irreversible or risky

---

## Integration with Other Techniques

**Combine with story-splitting heuristics:**
- Use hamburger method for features that are large but not obviously splittable
- Use story-splitting heuristics for stories with clear "and", "or", "manage" indicators
- Use both: Split story first, then apply hamburger method to each split

**Combine with complexity-review:**
- Generate options using hamburger method
- Use complexity-review to challenge high-complexity options
- Result: Ensure simplest options are truly simple

**Combine with micro-steps-coach:**
- Use hamburger method to choose vertical slice
- Use micro-steps-coach to break the slice into 1-3h steps
- Result: Clear path from feature → slice → implementation steps

---

Use the Hamburger Method when stories feel too big, vague, or technically layered. It helps teams focus on value and safe, small steps.
