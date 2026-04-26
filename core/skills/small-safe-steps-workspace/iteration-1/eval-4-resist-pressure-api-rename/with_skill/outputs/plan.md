# Plan: Rename `userName` to `username` in Public REST API Response

## Analysis: This Is a Risky Breaking Change

Although the request frames this as "just a field rename, shouldn't take long," renaming a field in a **public REST API response** is a **breaking change**. Any external consumers (mobile apps, third-party integrations, partner systems, frontend clients) that currently read `userName` will break the moment it disappears.

**Red flags detected:**
- This is a public API — consumers are outside our control
- Removing `userName` is irreversible without a versioned rollback
- We cannot know which consumers are using the field without monitoring
- A "quick rename" with no migration period = guaranteed breakage in production

**Approach: Expand-Contract Pattern**
**Estimated total time:** 10-12 hours of work spread over **2-3 months**

---

## Phase 1: EXPAND — Return Both Fields (Zero Breakage)

**Goal:** API returns both `userName` (old) and `username` (new) simultaneously. No consumer breaks.

### Step 1.1 — Audit current API surface (Learning step, 1-2h)

- Search the codebase for all endpoints that return `userName` in their response serializers/DTOs
- List every endpoint affected (e.g. GET /users, GET /users/:id, POST /users, etc.)
- Identify all request endpoints that accept `userName` as input (POST, PUT, PATCH)
- Document the list as a checklist — one item per endpoint
- Output: a written inventory of all affected endpoints

**Criteria:** Deployable artifact (document). Reversible. No production impact.

---

### Step 1.2 — Return both fields in GET response serializers (Earning step, 1-2h)

For each GET endpoint identified in Step 1.1, update the response serializer to include **both** fields pointing to the same underlying value:

```python
# Before
return {
    "id": user.id,
    "userName": user.username,
    "email": user.email
}

# After
return {
    "id": user.id,
    "userName": user.username,   # OLD — kept for backward compatibility
    "username": user.username,   # NEW — preferred field
    "email": user.email
}
```

- Deploy to production
- Verify both fields appear in API responses
- Verify existing consumers still receive `userName` without changes

**Criteria:** Deployable, reversible (revert the serializer change), safe (zero breakage).

---

### Step 1.3 — Accept both fields in POST/PUT/PATCH request bodies (Earning step, 1-2h)

Update request parsing so that write endpoints accept **either** `username` or `userName`:

```python
# Accept both field names in the request body
username = data.get('username') or data.get('userName')
if not username:
    return {"error": "username (or userName) is required"}, 400
```

- Deploy to production
- Verify new field name is accepted in requests
- Verify old field name still works

**Criteria:** Deployable, reversible, safe.

---

### Step 1.4 — Add deprecation notice to API documentation (Earning step, 1h)

- Update OpenAPI/Swagger spec or API docs to mark `userName` as `deprecated`
- Add a deprecation note: *"`userName` is deprecated and will be removed in 3 months. Use `username` instead."*
- Include the target removal date
- Deploy updated documentation

**Criteria:** Deployable artifact. No code risk.

---

## Phase 2: MIGRATE — Notify Consumers and Monitor Usage

**Goal:** All known consumers switch to `username`. Monitor until `userName` usage reaches zero.

### Step 2.1 — Instrument logging for field usage (Earning step, 1-2h)

Add server-side logging to track which consumers are still sending `userName` in requests:

```python
if 'userName' in data:
    logger.warning("Deprecated field 'userName' used", extra={
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent'),
        "endpoint": request.path
    })
```

- Deploy to production
- Verify deprecation logs appear when old field is used

**Criteria:** Deployable, reversible (remove the log line), zero user impact.

---

### Step 2.2 — Notify all known API consumers (Learning/coordination step, 1h)

- Email or contact all registered API consumers, partners, and internal teams
- Include: what's changing, why, the new field name, and the removal date
- Provide a migration guide (one paragraph: replace `userName` with `username`)
- Create a support channel or ticket for questions

**Criteria:** No code change. Communication artifact.

---

### Step 2.3 — Monitor deprecation logs (Passive monitoring, ongoing over ~2 months)

- Review logs weekly to track which consumers are still using `userName`
- Follow up individually with any consumers still on the old field after 4 weeks
- No code changes in this step — this is observation only

**Goal:** Confirm that `userName` usage in requests trends toward zero.

---

### Step 2.4 — Final check before removal (Learning step, 1h)

- Pull log data for the last 2 weeks
- Confirm zero (or negligible) requests using `userName`
- If usage is not zero: contact remaining consumers, extend deadline if needed
- Only proceed to Phase 3 when `userName` request usage has been zero for at least 1-2 weeks

**Criteria:** Decision point. Document the go/no-go decision.

---

## Phase 3: CONTRACT — Remove the Old Field

**Goal:** Remove `userName` from both responses and request parsing. Clean up the compatibility code.

**Only start this phase after:**
- [ ] `userName` in requests has been zero for 1-2 weeks (verified via logs)
- [ ] `userName` in responses has no known active readers (confirmed with consumers)
- [ ] Rollback plan is clear (previous version of the serializer code is tagged/documented)

---

### Step 3.1 — Stop accepting `userName` in request bodies (Earning step, 1h)

Update request parsing to only accept `username`:

```python
# Before (backward-compatible)
username = data.get('username') or data.get('userName')

# After (clean)
username = data.get('username')
if not username:
    return {"error": "username is required"}, 400
```

- Deploy to production
- Monitor error rates for 24-48 hours
- If errors spike: revert immediately (this step is fully reversible)

**Criteria:** Deployable, reversible, monitored.

---

### Step 3.2 — Remove `userName` from GET response serializers (Earning step, 1h)

Update each serializer to return only `username`:

```python
# After
return {
    "id": user.id,
    "username": user.username,   # Only the new field
    "email": user.email
}
```

- Deploy to production
- Monitor error rates and consumer-reported issues for 24-48 hours
- If errors are reported: revert and investigate

**Criteria:** Deployable, reversible, monitored.

---

### Step 3.3 — Remove deprecation notices and compatibility code (Earning step, 30min-1h)

- Update API documentation: remove deprecation markers from `userName`
- Remove the deprecation logging instrumentation added in Step 2.1
- Remove any feature flags or dual-path code if applicable
- Deploy

**Criteria:** Cleanup step. Deployable. Low risk.

---

## Summary

| Phase | Steps | Duration | When |
|-------|-------|----------|------|
| **Expand** | 1.1 Audit, 1.2 Return both fields, 1.3 Accept both fields, 1.4 Deprecation docs | ~5-7h of work | Week 1 |
| **Migrate** | 2.1 Add logging, 2.2 Notify consumers, 2.3 Monitor, 2.4 Final check | ~3-4h of work | Weeks 2-10 |
| **Contract** | 3.1 Stop accepting old field, 3.2 Remove from responses, 3.3 Cleanup | ~2-3h of work | Week 11-12 |

**Total work:** ~10-14 hours  
**Total calendar time:** ~2-3 months

---

## Why Not Just Do It Now?

Renaming a field in a public API response **is not a one-step change**. The temptation is to treat it as "just a rename," but:

- External consumers will break the moment `userName` disappears — they may not even know there's a new field
- Mobile apps may be on old versions that cannot be force-updated
- Third-party integrations may have long release cycles
- The damage happens silently: consumers get null values or parsing errors with no warning

The Expand-Contract pattern costs ~3 months of calendar time but near-zero downtime risk. A "quick rename" costs 30 minutes and risks breaking every API consumer simultaneously with no easy rollback.

**Risk grows faster than the size of the change. The only safe path is the slow one.**
