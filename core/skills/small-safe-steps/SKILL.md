---
name: small-safe-steps
description: Small Safe Steps (S3): breaks work into 1-3h increments with zero downtime. Use when asking "how do I implement/migrate/refactor", "what steps to do X", "plan safe migration", or handling risky DB/API changes. Applies expand-contract pattern for migrations, refactorings, schema changes.
allowed-tools:
  - Read
  - AskUserQuestion
---

STARTER_CHARACTER = 🪜⚡

# Small Safe Steps

## Mission

Help you divide **ANY work** into the smallest, safest, most valuable steps possible — ideally **1-3 hours each**.

**Core belief:** Risk grows faster than the size of the change.

---

## How to Use This Skill

**Automatic activation - just ask:**
- "How do I migrate from SendGrid to AWS SES?"
- "I need to refactor this legacy code"
- "How do I rename this database column safely?"
- "What's the safest way to implement X?"

**Manual invocation:**
- `/small-safe-steps` + describe your work
- Example: `/small-safe-steps Migrate authentication from Auth0 to Keycloak`

**In workflow with other skills:**
1. Use **story-splitting** → Break large story into smaller ones
2. Use **complexity-review** → Simplify technical approach
3. Use **small-safe-steps** (THIS SKILL) → Plan 1-3h implementation steps

---

## When to Use This Skill

**Use when:**
- Work feels too big or risky (refactoring, migrations, performance fixes)
- Database schema changes, API changes, service replacements
- User asks "how do I implement" after deciding what to build
- Work will take more than 1 day

**Do NOT use when:**
- User is still deciding WHAT to build (use story-splitting or hamburger-method first)
- Work is already small (< 3 hours)
- User asks for architectural review (use complexity-review instead)

---

## Applies to ALL Types of Work

### Product Work
- Feature implementation
- User stories (after initial splitting)
- UX improvements

### Technical Work
- Refactorings
- Performance improvements
- Tech debt reduction
- Architecture changes
- Database migrations

### Research & Investigation
- Debugging complex issues
- Spike/POC work
- Technology evaluation
- Root cause analysis

### Operations & Deployment
- Infrastructure changes
- Service migrations
- Deployment process improvements

---

## Core Process

### Step 1: Understand the Goal

Clarify the goal by asking:
- "What's the end state we want?"
- "Why are we doing this now?"
- "What's the smallest outcome that would be valuable?"
- "How will we know it's done?"
- "What's the risk if this goes wrong?"

### Step 2: Detect Risky Changes

🚨 **Identify if this is a risky/breaking change:**

**Red flags for risky changes:**
- Renaming database columns, tables, or fields
- Changing data types or formats (string → object, XML → JSON)
- Modifying public APIs or contracts
- Replacing existing services/libraries
- Changes that break backward compatibility
- Anything that can't be easily reversed

**If risky change detected → Apply Expand-Contract Pattern**

See "Quick Reference: Risky Changes" below and [small-safe-steps.md](references/small-safe-steps.md) for detailed examples.

### Step 3: Break Down into Phases

Identify 3-5 major phases, each independently valuable:

**Example: "Improve API performance"**
- Phase 1: Establish baseline (measure current performance)
- Phase 2: Identify bottleneck
- Phase 3: Implement fix
- Phase 4: Measure improvement
- Phase 5: (If needed) Fix secondary issues

**Example: "Migrate from SendGrid to AWS SES" (risky change)**
- Phase 1: Expand (add AWS SES alongside SendGrid)
- Phase 2: Migrate (gradually switch to AWS SES)
- Phase 3: Contract (remove SendGrid)

### Step 4: Slice Each Phase into 1-3 Hour Steps

For **EACH phase**, force division into tiny steps.

**Mandatory criteria for each step:**
- ✅ Takes 1-3 hours maximum
- ✅ Deployable to production (or creates verifiable artifact)
- ✅ Reversible (can undo without pain)
- ✅ Safe (preserves existing functionality)
- ✅ Testable

**If a step fails these criteria, it's too big.**

### Step 5: Identify Learning vs. Earning Steps

Flag steps by type:

**Learning steps** (time-boxed research/investigation):
- Time-boxed: "Investigate X (max 2h)"
- Goal: Reduce uncertainty, inform decisions
- Output: Document, decision, or data

**Earning steps** (deliver value):
- Goal: Ship working software to production
- Output: Deployed feature, improvement, or fix
- Measurable user impact

**Key principle:** Learning before earning. Don't build before you understand.

---

## Quick Reference: Risky Changes → Expand-Contract Pattern

Use this table to quickly identify risky changes and apply the correct pattern.

| Change Type | Example | Expand-Contract Phases | Typical Duration |
|-------------|---------|----------------------|------------------|
| **Rename DB column** | `email` → `email_address` | 1. Add new column + dual-write<br>2. Switch reads to new<br>3. Drop old column | 2-3 weeks |
| **Change data type** | String → JSON object | 1. Add new column + parse/backfill<br>2. Switch to new format<br>3. Drop old column | 2-4 weeks |
| **API field rename** | `userName` → `username` | 1. Return both fields<br>2. Deprecate old, notify consumers<br>3. Remove old field | 2-3 months |
| **Replace service** | SendGrid → AWS SES | 1. Add new service + dual-call<br>2. Route traffic % to new<br>3. Remove old service | 1 month |
| **Replace library** | Lodash → Native JS | 1. Add new code alongside old<br>2. Migrate callers incrementally<br>3. Remove old library | 1-2 weeks |
| **Refactor logic** | `calculate_v1` → `calculate_v2` | 1. Implement new alongside old<br>2. Compare outputs, migrate callers<br>3. Remove old function | 1-2 weeks |

**For detailed step-by-step examples, see [small-safe-steps.md](references/small-safe-steps.md).**

---

## Expand-Contract Pattern (Summary)

When you detect a **risky/breaking change**, use the **Expand-Contract pattern** to maintain zero downtime:

### Phase 1: EXPAND (Add New Alongside Old)

**Goal:** System supports BOTH old and new

**Pattern:**
1. Add new implementation/column/field/service alongside the old (1-2h)
2. Implement dual-write: write to BOTH old and new (2h)
3. Deploy and verify both paths work in production (1h)
4. (Optional) Backfill: migrate existing data to new format (1-3h)

**Key principle:** Zero users are affected yet. System continues working with old.

---

### Phase 2: MIGRATE (Switch to New)

**Goal:** Gradually migrate reads/usage from old to new

**Pattern:**
1. Update readers/consumers to use new path (2h)
2. Deploy incrementally (feature flag, canary, percentage rollout) (1h)
3. Monitor for errors, performance issues (passive)
4. **Keep dual-write active** (safety net to rollback)

**Key principle:** System now uses new, but still maintains old as backup.

---

### Phase 3: CONTRACT (Remove Old)

**Goal:** Clean up by removing old implementation

**Pattern:**
1. Stop writing to old path (1h)
2. Deploy and monitor (verify old truly unused) (passive, 1-2 weeks)
3. Remove old code/column/service (1h)
4. Clean up migration/compatibility code (1h)

**Key principle:** Only remove after old path has ZERO usage for days/weeks.

---

### Expand-Contract Checklist

**✅ Before MIGRATE phase:**
- [ ] Dual-write is working (data going to both old and new)
- [ ] New path is fully functional in production
- [ ] Monitoring shows both paths are healthy
- [ ] Rollback plan is clear

**✅ Before CONTRACT phase:**
- [ ] Old path has ZERO usage (verified via logs/monitoring)
- [ ] New path has been stable for days/weeks
- [ ] No errors related to old path
- [ ] Team agrees it's safe to remove

---

## Techniques by Work Type (Quick Reference)

| Work Type | Primary Pattern | Phases | Key Considerations |
|-----------|----------------|--------|-------------------|
| **Refactoring** | Expand-Contract | Add new → Dual-call → Migrate → Remove old | Compare outputs if possible |
| **Performance** | Baseline → Fix → Verify | Measure → Identify → Implement → Measure again | Always measure before optimizing |
| **Migration** | Expand-Contract | Add new → Route % → Remove old | Use feature flags for gradual rollout |
| **Debugging** | Linear investigation | Reproduce → Log → Analyze → Fix → Verify | Time-box investigation steps |
| **Research/Spike** | Time-boxed learning | Define questions → Evaluate options → Decide | Max 2h per option, document findings |
| **DB Schema** | Expand-Contract | Add column → Dual-write → Migrate reads → Drop old | Never drop columns immediately |
| **API Changes** | Expand-Contract | Return both → Deprecate → Remove | Long migration period (months) |

**For detailed examples of each pattern, see [small-safe-steps.md](references/small-safe-steps.md).**

---

## Red Flags That a Step is Too Big

Watch for these signs:

- ❌ "Then we also need to..."
- ❌ "While we're at it, let's..."
- ❌ "This requires..."
- ❌ "First we have to..."
- ❌ Multiple verbs in the description ("implement and test and deploy")
- ❌ Takes more than one day
- ❌ Can't be easily reversed
- ❌ Affects multiple systems at once
- ❌ "We need to coordinate with X team first"

**When you spot these, force more slicing.**

---

## Coaching Tone

- **Be ruthless about 1-3 hour steps** (no exceptions)
- **Challenge anything that feels larger**
- **Detect risky changes proactively** and suggest expand-contract
- **Ask forcing questions:**
  - "What's the smallest thing we could deploy right now?"
  - "Can we learn this before building it?"
  - "What would we do if we had to ship tomorrow?"
  - "How would we roll this back if it fails?"
  - "Is this a breaking change? Should we use expand-contract?"
- Use Eduardo Ferro's phrases:
  - "What if we only had half the time?"
  - "What's the worst that could happen?"
  - "Can we avoid doing it entirely?"

---

## Integration with Other Skills

This skill works in sequence with other skills:

**Typical workflow:**
1. **story-splitting**: Break down large user stories into smaller ones
2. **hamburger-method**: Choose vertical slice to implement first
3. **complexity-review**: Review and simplify technical approach
4. **micro-steps-coach** (THIS SKILL): Break simplified approach into 1-3h steps

**Use this skill when:**
- User knows WHAT to build and asks HOW to implement it
- After architectural decisions are made (complexity-review)
- When planning execution of a story/feature/refactoring

**Integration examples:**
- Use **story-splitting** first → "Admin can create user" → Then use micro-steps-coach to plan the 1-3h steps
- Use **hamburger-method** first → Choose slice (manual email notification) → Then use micro-steps-coach for implementation steps
- Use **complexity-review** first → Simplify to PostgreSQL instead of Kafka → Then use micro-steps-coach for migration steps

**Do NOT use this skill when:**
- User hasn't decided what to build yet (use story-splitting first)
- User is proposing complex architecture (use complexity-review first)

---

## Self-Check: Did I Apply This Correctly?

After applying this skill, verify:

- [ ] Every step takes 1-3 hours (no step exceeds this)
- [ ] Every step is deployable to production (or creates verifiable artifact)
- [ ] Every step is reversible (can undo without major pain)
- [ ] Risky changes use expand-contract pattern (3 phases: Expand → Migrate → Contract)
- [ ] I separated learning steps (time-boxed investigation) from earning steps (ship value)
- [ ] Dual-write is active during ENTIRE migrate phase (not removed too early)
- [ ] Contract phase only starts after old path has ZERO usage for 1-2 weeks
- [ ] Each phase is independently valuable (delivers some benefit)

**If any checkbox fails, revisit the breakdown.**

**Red flags that I didn't do this right:**
- Steps are "research and implement" (not separated into learning vs. earning)
- Steps are "update database and API" (too many things at once)
- Risky change doesn't use expand-contract (trying to rename column in one step)
- No monitoring/verification steps between phases
- Contract phase happens immediately after 100% migration (no waiting period)

---

## Key Principles

1. **Risk grows faster than the size of the change**
   - Small steps = low risk = fast feedback

2. **Every step must be deployable**
   - If you can't deploy it, it's too big

3. **Every step must be reversible**
   - If you can't undo it easily, it's too risky

4. **Zero downtime is non-negotiable**
   - Use expand-contract for risky changes
   - System must keep working at all times

5. **Learning before earning**
   - Investigate before implementing
   - Time-box research
   - Don't build without understanding

6. **1-3 hours per step, no exceptions**
   - If it's bigger, slice more
   - If you can't slice it, you don't understand it yet

---

## Reference

For detailed step-by-step examples of expand-contract pattern across different contexts (database changes, API migrations, service replacements, refactorings), see [small-safe-steps.md](references/small-safe-steps.md) in this skill directory.

Examples included:
- Database schema changes (rename column, change data type)
- API contract changes (rename field, versioning)
- Service migrations (email provider, authentication, microservices extraction)
- Refactorings and performance improvements
- Complete interaction examples with user

Author: Eduardo Ferro (expand-contract pattern applied to micro-steps)
Source: https://www.eferro.net/
