---
name: hamburger-method
description: Slices features into vertical deliverable pieces using the Hamburger Method. Generates 4-5 implementation options per layer and composes minimal end-to-end slices. Use when slicing work, breaking down features into layers, or delivering incrementally.
allowed-tools:
  - Read
  - AskUserQuestion
---

# Hamburger Method - Vertical Story Slicing

Expert in applying the Hamburger Method (by Gojko Adzic) to break down large features into small, safe, deliverable vertical slices.

## When to Use This Skill

**Use when:**
- Feature feels large but not obviously splittable with story-splitting heuristics
- User asks "how to slice" or "how to deliver incrementally"
- Need to generate multiple implementation options
- Want to compose end-to-end vertical slices

**Do NOT use when:**
- Story has obvious "and", "or", "manage" indicators (use story-splitting instead)
- User is asking HOW to implement (use micro-steps-coach instead)
- Feature is already small (< 1 day work)

---

## Core Process

When user describes a feature or story that needs slicing:

### 1. Identify Layers (Technical or Logical Steps)

Identify the main technical or business steps involved.

List 3-6 layers that form the complete flow.

**Example for notification system:**
- Layer 1: Detect triggering event
- Layer 2: Decide whom to notify
- Layer 3: Format the message
- Layer 4: Deliver the message
- Layer 5: Record delivery status

### 2. Generate 4-5 Options per Layer

**This is MANDATORY**: For EACH layer, generate at least 4-5 implementation options, from simplest to most complete.

Use a numbered system: 1.1, 1.2, 1.3... for Layer 1, then 2.1, 2.2, 2.3... for Layer 2, etc.

**Quality gradient (low to high):**
- Manual / hardcoded
- Semi-automated / configurable
- Fully automated / robust
- Scalable / multi-channel
- Enterprise-grade / resilient

**Example for "Deliver the message" layer:**
- 4.1: Manual email from your personal account
- 4.2: Scripted email via command line
- 4.3: Email via SMTP service (no retries)
- 4.4: Email via queuing system with retries
- 4.5: Multi-channel (email, push, SMS) with fallbacks

### 3. Force Radical Slicing

Always ask this question out loud in your response — do not skip it:

> **"If you had to ship something by tomorrow, what would you build?"**

Then answer it explicitly by naming the specific options (by number) you would pick from each layer. This forces the absolute minimum viable slice, not just a "simple version".

---

## Quick Reference: Quality Gradients

Use this table to systematically generate 4-5 options per layer from simplest to most complete.

| Layer Type | Level 1 (Manual) | Level 2 (Scripted) | Level 3 (Automated) | Level 4 (Scalable) | Level 5 (Enterprise) |
|------------|------------------|-------------------|---------------------|--------------------|--------------------|
| **Trigger/Detection** | Manual check | Scheduled script | Event-driven | Real-time stream | ML-powered |
| **Data Source** | Hardcoded | Single file/DB | Multiple sources | External APIs | Federated |
| **Processing** | Manual steps | Script | Background job | Queue system | Distributed |
| **Validation** | None | Basic checks | Business rules | Comprehensive | Anomaly detection |
| **Output/Delivery** | Manual action | Email/file | API call | Multi-channel | Personalized |
| **Monitoring** | None | Console log | DB record | Dashboard | Real-time alerts |

**Example usage:**
- Layer: "Deliver notification"
- Quality dimension: "Output/Delivery"
- Options: (1) Manual email, (2) Scripted email, (3) SMTP service, (4) Queue + multi-channel, (5) Personalized dynamic content

---

### 4. Filter & Prioritize Options

Eliminate options that:
- Are too costly for the value they provide
- Block fast delivery
- Are irreversible

Keep options that are:
- Fast to build (ideally hours, max 1-3 days)
- Testable with real users
- Reversible or expandable later

### 5. Compose a Vertical Slice

Help the user select ONE option from EACH layer to form a complete end-to-end slice.

**If the user requested multiple outputs or metrics (e.g. "revenue, top products, and trends"), the first slice must pick EXACTLY ONE** — the most informative single output. Delivering all of them in slice-1 defeats the purpose of incremental validation.

**Criteria for a good slice:**
- Delivers value to at least one real user or stakeholder — name them explicitly
- Names the specific decision or question the slice answers for that person
- Can be tested in production (or near-production)
- Takes less than 1-3 days to build
- Preserves system stability (zero downtime)

### 6. Plan Next Slices

Once the first slice is identified, suggest 2-3 follow-up slices that:
- Improve one layer (e.g., automate what was manual)
- Add a missing quality attribute (e.g., logging, error handling)
- Expand reach (e.g., more users, more scenarios)

## Rules of Thumb

- **Every vertical slice must be usable by someone** — even if it's just one test user or internal stakeholder
- **You don't need the "best" version first** — just the smallest that teaches you something
- **Always list options explicitly** — don't just describe "simple vs. complex"; give concrete examples
- **Push for the lowest quality that still works** — hardcoded values, manual steps, no error handling if it helps ship faster

## Example Interaction

**User:** "We need to notify users when a product they're watching drops in price"

**You respond:**

Let's apply the Hamburger Method to slice this feature.

**Layers identified:**
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

This slice can be deployed today to validate the concept with zero infrastructure.

**Next slices:**
- Slice 2: Automate price detection (1.2), keep rest the same
- Slice 3: Expand to real watchlist users (2.2)
- Slice 4: Add basic SMTP delivery (4.3)

---

## Reference

For full details on the Hamburger Method, see [hamburger-method.md](references/hamburger-method.md) in this skill directory.

Author: Gojko Adzic
Source: https://gojko.net/2012/01/23/splitting-user-stories-the-hamburger-method/

---

## Coaching Tone

- Be pushy about generating ALL options (don't skip this step)
- Challenge the user if they propose a slice that's too big
- Always ask: "Can we make it even smaller?"
- Use Eduardo Ferro's phrases: "What if we only had half the time?" "Can we avoid doing it?"

---

## Integration with Other Skills

This skill works in sequence with other skills:

**Typical workflow:**
1. **story-splitting**: Detect and split oversized stories with obvious red flags
2. **hamburger-method** (THIS SKILL): For stories that are large but not obviously splittable, generate layers + options
3. **complexity-review**: Review proposed vertical slice, simplify if needed
4. **micro-steps-coach**: Break chosen vertical slice into 1-3h implementation steps

**Use this skill when:**
- Feature is large but doesn't have obvious "and", "or", "manage" indicators
- Need to explore multiple implementation options systematically
- Want to compose minimal end-to-end slice

**Vs. story-splitting:**
- **story-splitting**: Best for stories with clear linguistic red flags ("manage users and roles")
- **hamburger-method**: Best for features that need layered analysis ("implement notifications")
- Can use BOTH: Split story first, then apply hamburger method to each smaller story

**Integration example:**
- User: "Implement user notifications" (no obvious split points)
- Apply hamburger-method → Identify 5 layers, generate options, compose smallest slice
- Then use complexity-review → Ensure simplest slice is truly simple
- Then use micro-steps-coach → Break slice into 1-3h steps

---

## Self-Check: Did I Apply This Correctly?

After applying this skill, verify:

- [ ] I identified 3-6 clear layers (not too many, not too few)
- [ ] I generated at least 4-5 options per layer (not just "simple vs. complex")
- [ ] Options follow a quality gradient (manual → scripted → automated → scalable → enterprise)
- [ ] I forced radical slicing by asking "ship by tomorrow"
- [ ] The smallest vertical slice uses level 1-2 options from each layer
- [ ] The smallest slice delivers value to at least one user (even if it's just me)
- [ ] The smallest slice can be deployed in less than 1-3 days
- [ ] I proposed 2-3 follow-up slices showing incremental improvement

**If any checkbox fails, revisit the process.**

**Red flags that I didn't do this right:**
- Layers are too technical ("frontend, backend, database") instead of functional
- Only 2 options per layer ("manual or automated")
- Smallest slice still requires new infrastructure (Redis, Kafka, etc.)
- Smallest slice would take more than 3 days to build
- Follow-up slices aren't clear improvements over previous slices
