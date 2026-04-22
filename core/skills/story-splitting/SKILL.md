---
name: story-splitting
description: Detects stories that are too big and applies splitting heuristics. Identifies linguistic red flags (and, or, manage, handle, including) and suggests concrete splitting strategies. Use when breaking down requirements or splitting large work.
allowed-tools:
  - Read
  - AskUserQuestion
---

# Story Splitting Expert

Expert at detecting when work is too big and applying proven splitting heuristics to break it down into small, safe, valuable increments.

## When to Use This Skill

**Use when:**
- Story has obvious red flags: "and", "or", "manage", "handle", "including"
- User describes multiple features bundled together
- Story feels vague or too large
- User asks "how to split this story"

**Do NOT use when:**
- Story is already small and focused (< 1 day work)
- Feature needs layered analysis without obvious split points (use hamburger-method instead)
- User asks HOW to implement (use micro-steps-coach instead)

---

## Detection: Red Flags in Stories

Always scan for these **linguistic indicators** that signal a story is too big:

### 1. Coordinating Conjunctions: "and", "or", "but", "yet"
- "Users can upload **and** download files" → Split into 2 stories
- "Admin can view **or** edit users" → Split into 2 stories

### 2. Action-Related Connectors: "manage", "handle", "support", "process", "administer"
- "Admin can **manage** users" → Hides create, edit, delete, list
- "System **handles** payments" → Hides initiate, process, refund, report

### 3. Sequence Connectors: "before", "after", "then", "while", "when"
- "Save work **before** submitting" → 2 separate stories
- "Process payment **then** send receipt" → 2 steps, 2 stories

### 4. Scope Indicators: "including", "as-well-as", "also", "additionally", "plus"
- "Notifications via email **and** SMS" → Split channels
- "Report **including** charts and exports" → Split outputs

### 5. Option Indicators: "either/or", "whether", "optionally", "alternatively"
- "Login with password **or** Google" → 2 authentication methods
- "Export to CSV **or** PDF" → 2 format stories

### 6. Exception Indicators: "except", "unless", "however", "although"
- "Delete account **unless** admin" → Base case + exception

**When you spot these words, immediately flag the story as too big.**

---

## Decision Tree: Red Flag → Recommended Technique

Use this table to quickly select the best splitting technique based on the red flag detected.

| Red Flag Detected | Likely Problem | Recommended Technique(s) | Example Split |
|-------------------|----------------|-------------------------|---------------|
| **"manage"** / **"handle"** / **"administer"** | Hides multiple CRUD operations | #1 (Start with outputs) + Split by action | "Manage users" → (1) Create user, (2) Edit user, (3) Delete user |
| **"and"** | Multiple independent features | Split by conjunction | "Upload and download files" → (1) Upload files, (2) Download files |
| **"or"** / **"either/or"** | Multiple options/alternatives | #5 (Simplify outputs) or Split by option | "Export to CSV or PDF" → (1) Export to CSV, (2) Export to PDF |
| **"for all users"** / **"everyone"** | Too broad scope | #2 (Narrow customer segment) | "All users export data" → (1) Admins export, (2) Power users export, (3) All users export |
| **"including"** / **"with"** | Feature bundling | #3 (Extract basic utility) | "Upload with drag-drop and progress bar" → (1) Basic upload, (2) Add drag-drop, (3) Add progress bar |
| **"before/after/then"** | Sequential steps bundled | Split by workflow step | "Save before submitting" → (1) Save work, (2) Submit work |
| **Complex output** (reports, dashboards) | Too many outputs | #1 (Start with outputs) | "Financial report with charts" → (1) Basic summary, (2) Add charts |
| **Multiple data sources** | Integration complexity | #4 (Dummy to dynamic) | "Dashboard from 3 DBs" → (1) Dummy data dashboard, (2) Integrate DB 1, (3) Add DB 2+3 |
| **"real-time"** / **"automated"** | Over-engineered solution | #4 (Dummy to dynamic) + #9 (Put it on crutches) | "Real-time sync" → (1) Manual export/import, (2) Scripted sync, (3) Automated |
| **Large scope** (entire subsystem) | Too big conceptually | #7 (Examples of usefulness) | "Add API auth" → (1) Auth for read endpoints, (2) Auth for write endpoints |

**How to use:**
1. Scan story for red flags
2. Look up red flag in table
3. Apply recommended technique
4. If multiple red flags, apply techniques sequentially

---

## Core Splitting Heuristics

When a story is too big, apply these techniques (in rough priority order):

### 1. Start with the Outputs
Focus on delivering **specific outputs incrementally**, not all at once.

**Example:** "Generate financial report"
- Split: "Generate revenue summary only"
- Split: "Add expense breakdown"
- Split: "Add charts"

### 2. Narrow the Customer Segment
Deliver **full functionality for a smaller group** instead of partial functionality for everyone.

**Example:** "All users can export data"
- Split: "Admins can export data"
- Split: "Power users can export data"
- Split: "All users can export data"

### 3. Extract Basic Utility First
Deliver the **bare minimum** to complete the task, then improve usability later.

**Example:** "Users can upload files with drag-and-drop, progress bars, and previews"
- Split 1: "Users can upload files via form (no UX polish)"
- Split 2: "Add drag-and-drop"
- Split 3: "Add progress indicators"
- Split 4: "Add previews"

### 4. Start with Dummy, Move to Dynamic
Build the UI/workflow with **hardcoded data first**, integrate real data later.

**Example:** "Show user dashboard with real-time stats"
- Split 1: "Dashboard with dummy/static stats"
- Split 2: "Integrate real backend data"
- Split 3: "Make it real-time"

### 5. Simplify Outputs
Use simpler output formats initially (CSV instead of PDF, console instead of UI).

**Example:** "Generate and email PDF reports"
- Split 1: "Generate CSV report saved to disk"
- Split 2: "Convert to PDF format"
- Split 3: "Email the report"

### 6. Split by Capacity
Limit initial scope by capacity constraints (file size, user count, data volume).

**Example:** "Support unlimited file uploads"
- Split 1: "Support files up to 1MB"
- Split 2: "Increase to 10MB"
- Split 3: "Support unlimited size with chunking"

### 7. Split by Examples of Usefulness
For large technical changes, identify **concrete use cases** that can be delivered with a subset of the solution.

**Example:** "Add API authentication"
- Split 1: "API auth for read-only endpoints"
- Split 2: "API auth for write endpoints"
- Split 3: "Add rate limiting"

### 8. Split Learning from Earning
Separate **research/investigation** (time-boxed learning) from **value delivery** (earning).

**Example:** "Implement machine learning recommendations"
- Learning: "Spike: Evaluate ML libraries (3 days max)"
- Earning: "Implement basic recommendation algorithm"
- Earning: "Deploy recommendations to 10% of users"

### 9. Forget the Walking Skeleton – Put it on Crutches
Deliver minimal user-facing functionality using **manual steps or simpler backends** initially.

**Example:** "Automated inventory sync between systems"
- Split 1: "Manual CSV export/import between systems"
- Split 2: "Semi-automated with script"
- Split 3: "Fully automated sync"

---

## Process When User Describes Work

1. **Listen for red flag words** (and, or, manage, handle, etc.)
2. **Challenge immediately**: "This sounds like multiple stories"
3. **Ask clarifying questions**:
   - "What's the smallest piece that delivers value?"
   - "Who is the narrowest user segment we could start with?"
   - "What's the simplest output format that would work?"
   - "Can we do this manually first?"
4. **Propose 3-5 specific split options** using the heuristics above
5. **Force radical slicing**: "If you had to ship something by tomorrow, what would it be?"

---

## Examples

### Example 1: Story Too Big

**User:** "As an admin, I can manage users and roles, including creating, editing, deleting, and assigning permissions."

**Your response:**

🚨 **Red flags detected:**
- "**manage**" (hides multiple actions)
- "**and**" (multiple features)
- "**including**" (scope expansion)

This story is doing at least 5-6 different things. Let's split it:

**Proposed splits:**
1. "Admin can create a new user (with hardcoded default role)"
2. "Admin can edit user basic info (name, email)"
3. "Admin can delete a user"
4. "Admin can assign one predefined role to a user"
5. "Admin can create custom roles"
6. "Admin can assign multiple roles to a user"

**Smallest slice to ship first:**
"Admin can create a new user with a hardcoded 'viewer' role"
- Takes 2-3 hours
- Delivers immediate value
- Testable in production
- Expands later with role selection

---

### Example 2: Narrowing Customer Segment

**User:** "All users need to export their data to CSV or PDF"

**Your response:**

Let's narrow the segment and simplify the output:

**Split 1:** "Admins can export data to CSV"
- Why admins first? They need it most and can tolerate rough UX
- CSV is simpler than PDF
- Delivers value immediately

**Split 2:** "Power users can export to CSV"

**Split 3:** "All users can export to CSV"

**Split 4:** "Admins can export to PDF" (only if there's proven demand)

**Smallest slice:** Split 1 (admin + CSV only)

---

### Example 3: Dummy to Dynamic

**User:** "Show a dashboard with real-time sales metrics pulled from 3 different databases"

**Your response:**

Let's start with dummy data to validate the UI/UX first:

**Split 1:** "Dashboard shows hardcoded dummy sales metrics"
- Build the UI/layout
- No backend integration
- Stakeholders can validate design
- 1 day of work

**Split 2:** "Dashboard pulls metrics from one database (no real-time)"
- Integrate one data source
- Refresh on page load
- 2 days of work

**Split 3:** "Add second database"

**Split 4:** "Add third database"

**Split 5:** "Make it real-time with WebSockets" (only if needed)

**Smallest slice:** Split 1 (dummy data dashboard)

---

### Example 4: Multiple Techniques Applied Sequentially

**User:** "As a user, I want to manage my account settings and privacy preferences, including profile information, notification settings, email preferences, and data export, with the ability to preview changes before saving."

**Your response:**

🚨 **Multiple red flags detected:**
- **"manage"** (hides multiple actions)
- **"and"** appears 3 times (multiple features)
- **"including"** (scope expansion)
- **"with"** (additional feature bundled)

This story is doing at least 8 different things. Let's apply multiple techniques to break it down.

---

**Step 1: Split by "manage" (hidden CRUD operations)**

"Manage account settings" hides:
1. View current settings
2. Edit settings
3. Reset to defaults

**Step 2: Split by "and" (multiple feature areas)**

Even just "edit settings" includes:
1. Profile information (name, bio, avatar)
2. Notification settings (email, push, SMS toggles)
3. Email preferences (frequency, topics)
4. Data export (download all user data)

**Step 3: Split by "including" (remove bundled features)**

Each feature area can be split further:
- Profile info: (a) Basic info (name, email), (b) Extended (bio, avatar, location)
- Notifications: (a) Email toggles, (b) Push toggles, (c) SMS toggles
- Data export: Separate story entirely

**Step 4: Extract basic utility (remove preview feature)**

"Preview changes before saving" is a UX enhancement, not core functionality:
- Story A: Edit and save directly (no preview)
- Story B: Add preview feature later

---

**Final proposed splits (after applying all techniques):**

1. **"User can view current profile name and email"**
   - Time: 1 hour
   - Value: Users see their basic info

2. **"User can edit profile name"**
   - Time: 2 hours
   - Value: Users can update their name

3. **"User can edit email address"**
   - Time: 3 hours (includes email verification)
   - Value: Users can change email

4. **"User can toggle email notifications on/off"**
   - Time: 2 hours
   - Value: Users control email notifications

5. **"User can upload profile avatar"**
   - Time: 4 hours
   - Value: Users personalize their profile

6. **"User can preview changes before saving profile"**
   - Time: 3 hours
   - Value: Better UX (only after basic editing works)

7. **"User can export their data as JSON"**
   - Time: 5 hours
   - Value: Data portability (compliance requirement)

---

**Recommended delivery order:**
- **Week 1**: Stories #1, #2, #3 (basic profile editing)
- **Week 2**: Story #4 (notifications toggle)
- **Week 3**: Story #5 (avatar upload)
- **Later**: Stories #6, #7 (enhancements)

**Techniques applied:**
- Split by "manage" → Separated view/edit/reset
- Split by "and" → Separated profile/notifications/email/export
- Split by "including" → Removed bundled features
- Extract basic utility → Removed preview (add later)
- Narrow outputs → Name before bio/location
- Start simple → Toggles before complex preferences

---

## Coaching Tone

- **Be pushy**: Call out "too big" work immediately
- **Challenge**: "Can we make it smaller?"
- **Probe**: "What would we ship if we had half the time?"
- Use Eduardo Ferro's phrases:
  - "What's the worst that could happen if we ship the simplest version?"
  - "Can we avoid doing it entirely?"
  - "Let's remove it and monitor the impact"

## Integration with Other Skills

This skill works in sequence with other skills:

**Typical workflow:**
1. **story-splitting** (THIS SKILL): Detect linguistic red flags, split stories into smaller ones
2. **hamburger-method**: For stories still large after splitting, apply layered analysis
3. **complexity-review**: Review technical approach for each small story
4. **micro-steps-coach**: Break each story into 1-3h implementation steps

**Use this skill when:**
- Story contains obvious red flags ("manage", "and", "or", "including")
- User describes multiple features bundled together
- Story feels too big or vague

**Vs. hamburger-method:**
- **story-splitting**: Best when story has clear linguistic indicators of multiple features
- **hamburger-method**: Best when feature is large but doesn't have obvious split points
- Use **story-splitting FIRST** to remove obvious bundling, **then** hamburger-method if still needed

**Integration example:**
- Original: "Admin can manage users and roles"
- Apply story-splitting → Split into: (1) "Create user", (2) "Edit user", (3) "Assign role"
- Story #1 still feels large → Apply hamburger-method to identify layers + options
- Choose simplest vertical slice → Apply micro-steps-coach to plan 1-3h steps

---

## Self-Check: Did I Apply This Correctly?

After applying this skill, verify:

- [ ] I scanned the story for all 6 red flag categories
- [ ] I flagged the story as too big when red flags were present
- [ ] I identified which splitting technique(s) to apply using the decision tree
- [ ] I proposed 3-5 concrete split stories (not just vague suggestions)
- [ ] Each split story is independently valuable (can be deployed alone)
- [ ] Each split story takes less than 2-3 days to complete
- [ ] I specified the smallest story to ship first
- [ ] I applied multiple techniques if the story had multiple red flags

**If any checkbox fails, revisit the splitting process.**

**Red flags that I didn't do this right:**
- I accepted the story without challenging it (missed red flags)
- Proposed splits are still too large (>3 days each)
- Splits are horizontal ("build database, build API, build UI") not vertical
- Splits don't deliver independent value (one depends on another finishing first)
- I only proposed 1-2 splits instead of fully decomposing the story

---

## Reference

For comprehensive splitting heuristics, see [story-splitting.md](references/story-splitting.md) in this skill directory.

---

## Key Principle

**Risk grows faster than the size of the change.**

Small stories = Low risk = Fast feedback = Learning
Large stories = High risk = Slow feedback = Waste

Always push for the smallest, safest, most valuable slice possible.
