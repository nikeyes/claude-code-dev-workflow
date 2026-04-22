# Micro-Steps Reference: Detailed Examples

## Contents

1. [Expand-Contract Pattern: Detailed Examples](#expand-contract-pattern-detailed-examples)
   - Example 1: Database Schema Change - Rename Column
   - Example 2: Database Schema Change - Change Data Type
   - Example 3: API Contract Change - Rename Field
   - Example 4: Service Migration - Email Provider Replacement
   - Example 5: Refactoring - Extract Service
2. [Techniques by Work Type](#techniques-by-work-type)
   - Performance Improvements
   - Debugging Complex Issues
   - Research/Spike Work
3. [Complete Interaction Examples](#complete-interaction-examples)
4. [Anti-Patterns](#anti-patterns)
5. [Key Principles Recap](#key-principles-recap)

---

## Expand-Contract Pattern: Detailed Examples

### Example 1: Database Schema Change - Rename Column

**Scenario:** Rename column `email` to `email_address` in `users` table

#### Phase 1: EXPAND

```sql
-- Step 1: Add new column (1h)
ALTER TABLE users ADD COLUMN email_address VARCHAR(255);
-- Deploy migration
-- Verify: SELECT * FROM users LIMIT 1;

-- Step 2: Implement dual-write in application (2h)
def update_user_email(user_id, email):
    db.execute(
        "UPDATE users SET email = ?, email_address = ? WHERE id = ?",
        email, email, user_id
    )
-- Deploy application code
-- Test: Update a user, verify both columns updated

-- Step 3: Backfill existing data (1h)
UPDATE users SET email_address = email WHERE email_address IS NULL;
-- Run in batches if large table
-- Verify: SELECT COUNT(*) FROM users WHERE email_address IS NULL;
-- Should return 0
```

#### Phase 2: MIGRATE

```python
# Step 1: Update readers to use new column (2h)
# Before:
def get_user_email(user_id):
    return db.query("SELECT email FROM users WHERE id = ?", user_id)

# After:
def get_user_email(user_id):
    return db.query("SELECT email_address FROM users WHERE id = ?", user_id)

# Deploy behind feature flag
# Enable for 10% → 50% → 100%

# Step 2: Update all queries (2-3h, may need multiple deploys)
# Search codebase for "SELECT email FROM users"
# Replace with "SELECT email_address FROM users"
# Deploy incrementally, verify each deploy

# Still dual-writing at this point!
```

#### Phase 3: CONTRACT

```python
# Step 1: Stop dual-writing (1h)
def update_user_email(user_id, email):
    db.execute(
        "UPDATE users SET email_address = ? WHERE id = ?",
        email, user_id
    )
# Deploy, monitor for 1-2 weeks

# Step 2: Verify old column unused (1h)
# Check logs, monitoring, slow query logs
# Search codebase for any reference to old column

# Step 3: Drop old column (30min)
ALTER TABLE users DROP COLUMN email;

# Step 4: Clean up code (30min)
# Remove any commented code or feature flags
```

**Total time:** ~12-15 hours spread over 2-3 weeks

---

### Example 2: Change Data Type - String to Object

**Scenario:** Change `address` field from string to JSON object

```
Before: address = "123 Main St, Springfield, IL 62701"
After:  address = {"street": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701"}
```

#### Phase 1: EXPAND

```sql
-- Step 1: Add new column (1h)
ALTER TABLE users ADD COLUMN address_structured JSONB;
-- PostgreSQL example

-- Step 2: Implement dual-write (2h)
def update_address(user_id, address_obj):
    address_string = f"{address_obj['street']}, {address_obj['city']}, {address_obj['state']} {address_obj['zip']}"
    address_json = json.dumps(address_obj)

    db.execute(
        "UPDATE users SET address = ?, address_structured = ? WHERE id = ?",
        address_string, address_json, user_id
    )

-- Step 3: Parse existing addresses and backfill (3h - may need custom logic)
def parse_address(address_string):
    # Custom parsing logic or use library
    parts = address_string.split(", ")
    return {
        "street": parts[0],
        "city": parts[1],
        "state": parts[2].split()[0],
        "zip": parts[2].split()[1]
    }

# Run migration script
for user in db.query("SELECT id, address FROM users WHERE address_structured IS NULL"):
    parsed = parse_address(user.address)
    db.execute("UPDATE users SET address_structured = ? WHERE id = ?",
               json.dumps(parsed), user.id)
```

#### Phase 2: MIGRATE

```python
# Step 1: Update readers (2h)
# Before:
def get_user_address(user_id):
    return db.query("SELECT address FROM users WHERE id = ?", user_id)

# After:
def get_user_address(user_id):
    result = db.query("SELECT address_structured FROM users WHERE id = ?", user_id)
    return json.loads(result)

# Step 2: Update UI to display structured address (2h)
# Now can display fields separately:
# {{ address.street }}
# {{ address.city }}, {{ address.state }} {{ address.zip }}

# Still dual-writing!
```

#### Phase 3: CONTRACT

```python
# Step 1: Stop writing to old column (1h)
def update_address(user_id, address_obj):
    db.execute(
        "UPDATE users SET address_structured = ? WHERE id = ?",
        json.dumps(address_obj), user_id
    )

# Step 2: Drop old column (30min, after 1-2 weeks)
ALTER TABLE users DROP COLUMN address;
```

---

### Example 3: API Contract Change - Rename Field

**Scenario:** Rename API field `userName` to `username` (breaking change for API consumers)

#### Phase 1: EXPAND

```python
# Step 1: Return both fields in API response (1h)
@app.route('/api/users/<user_id>')
def get_user(user_id):
    user = db.get_user(user_id)
    return {
        "id": user.id,
        "userName": user.username,  # Old field (deprecated)
        "username": user.username,  # New field
        "email": user.email
    }
# Deploy, both fields available

# Step 2: Update API documentation (1h)
# Mark userName as deprecated
# Recommend using username
# Set deprecation timeline: "userName will be removed in 3 months"

# Step 3: Accept both fields in POST/PUT requests (2h)
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username') or data.get('userName')  # Accept both

    if not username:
        return {"error": "username or userName required"}, 400

    user = create_user(username=username)
    return {
        "id": user.id,
        "userName": user.username,  # Still return both
        "username": user.username
    }
```

#### Phase 2: MIGRATE

```
# Step 1: Email API consumers (1h)
# Notify all known API users
# Provide migration guide
# Give 2-month timeline

# Step 2: Monitor usage of old field (passive)
# Add logging to track userName vs username usage
# Log deprecation warnings

# Step 3: After 2 months, check if userName still used (1h)
# Review logs
# Contact remaining users
# Give final 1-month extension if needed
```

#### Phase 3: CONTRACT

```python
# Step 1: Stop returning userName in response (1h)
@app.route('/api/users/<user_id>')
def get_user(user_id):
    user = db.get_user(user_id)
    return {
        "id": user.id,
        "username": user.username,  # Only new field
        "email": user.email
    }

# Step 2: Stop accepting userName in requests (1h)
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')  # Only accept new field

    if not username:
        return {"error": "username required"}, 400

    user = create_user(username=username)
    return {"id": user.id, "username": user.username}

# Step 3: Remove deprecation notices from docs (30min)
```

**Total time:** ~10-12 hours spread over 3 months

---

### Example 4: Service Migration - Email Provider

**Scenario:** Migrate from SendGrid to AWS SES

#### Phase 1: EXPAND

```python
# Step 1: Add AWS SES SDK (1h)
# pip install boto3
# Add AWS credentials to config
# Deploy (not used yet)

# Step 2: Create abstraction for email sending (2h)
class EmailService:
    def __init__(self):
        self.sendgrid_client = SendGridAPIClient(api_key=SENDGRID_KEY)
        self.ses_client = boto3.client('ses', region_name='us-east-1')

    def send(self, to, subject, body, provider='sendgrid'):
        if provider == 'aws_ses':
            return self._send_via_ses(to, subject, body)
        return self._send_via_sendgrid(to, subject, body)

    def _send_via_sendgrid(self, to, subject, body):
        # Existing SendGrid logic
        pass

    def _send_via_ses(self, to, subject, body):
        return self.ses_client.send_email(
            Source='noreply@example.com',
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )

# Step 3: Test AWS SES with internal emails (1h)
# Send to team members only
# Verify delivery

# Step 4: Add feature flag for provider selection (1h)
@app.route('/send-notification')
def send_notification():
    provider = feature_flags.get('email_provider', default='sendgrid')
    email_service.send(to=user.email, subject="...", body="...", provider=provider)
```

#### Phase 2: MIGRATE

```python
# Step 1: Enable AWS SES for 1% of emails (1h)
feature_flags.set('email_provider', 'aws_ses', percentage=1)
# Monitor delivery rates, bounce rates

# Step 2: Compare metrics (passive, 1 week)
# SendGrid: 99.5% delivery, 0.2% bounce
# AWS SES: 99.4% delivery, 0.3% bounce
# Acceptable difference

# Step 3: Increase to 10% (1h)
feature_flags.set('email_provider', 'aws_ses', percentage=10)
# Monitor

# Step 4: Increase to 50% (1h)
feature_flags.set('email_provider', 'aws_ses', percentage=50)
# Monitor

# Step 5: Enable for 100% (1h)
feature_flags.set('email_provider', 'aws_ses', percentage=100)
# Monitor for 2 weeks

# SendGrid still configured but unused
```

#### Phase 3: CONTRACT

```python
# Step 1: Remove SendGrid API key from config (30min)
# After verifying no emails sent via SendGrid for 2 weeks

# Step 2: Remove SendGrid code (1h)
class EmailService:
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name='us-east-1')

    def send(self, to, subject, body):
        return self.ses_client.send_email(...)

# Step 3: Remove feature flag (30min)
# Email provider is now always AWS SES

# Step 4: Uninstall SendGrid SDK (30min)
# pip uninstall sendgrid
# Remove from requirements.txt

# Step 5: Cancel SendGrid subscription
```

**Total time:** ~12-15 hours spread over 1 month

---

### Example 5: Architecture Change - Monolith to Microservice

**Scenario:** Extract user authentication into separate service

#### Phase 1: EXPAND

```python
# Step 1: Create new auth service skeleton (3h)
# New repository, basic Flask/FastAPI app
# Deploy to staging

# Step 2: Replicate auth logic in new service (3h)
# Copy user validation, JWT generation
# Keep as exact copy of monolith logic

# Step 3: Deploy auth service to production (1h)
# Not handling traffic yet

# Step 4: Add proxy/router to support both (2h)
# Monolith continues handling auth
# Auth service ready but not used

# Step 5: Implement dual-call for auth verification (2h)
def verify_user_token(token):
    # Call both old (monolith) and new (auth service)
    old_result = monolith_verify(token)
    new_result = auth_service_verify(token)

    # Compare results (shadow traffic)
    if old_result != new_result:
        log_discrepancy(old_result, new_result)

    # Return old result (safe)
    return old_result
```

#### Phase 2: MIGRATE

```python
# Step 1: Route 1% of auth requests to new service (1h)
def verify_user_token(token):
    if feature_flags.enabled('auth_service', percentage=1):
        return auth_service_verify(token)
    return monolith_verify(token)

# Step 2: Monitor and compare (passive, 1 week)
# Compare latency, error rates

# Step 3: Increase to 10% → 50% → 100% (3h total)
# Each step: deploy, monitor, verify
```

#### Phase 3: CONTRACT

```python
# Step 1: Remove auth logic from monolith (2h)
# Delete old verify function
# All calls now route to auth service

# Step 2: Remove auth database tables from monolith (1h)
# After verifying no queries to auth tables

# Step 3: Remove feature flags (30min)
```

**Total time:** ~20-25 hours spread over 1-2 months

---

## Common Patterns

### Pattern: Database Column Rename
1. Add new column
2. Dual-write to both
3. Backfill data
4. Switch reads to new column
5. Stop writing to old
6. Drop old column

**Phases:** 3 (Expand → Migrate → Contract)
**Time:** 10-15 hours over 2-3 weeks

---

### Pattern: API Field Rename
1. Return both old and new fields
2. Accept both in requests
3. Deprecate old field (docs)
4. Notify consumers
5. Remove old field after grace period

**Phases:** 3 (Expand → Migrate → Contract)
**Time:** 8-12 hours over 2-3 months

---

### Pattern: Service/Library Migration
1. Add new service alongside old
2. Abstract with provider selection
3. Shadow traffic (dual-call, compare)
4. Gradually route traffic (1% → 100%)
5. Remove old service

**Phases:** 3 (Expand → Migrate → Contract)
**Time:** 15-20 hours over 1 month

---

### Pattern: Data Format Change
1. Add new format column
2. Dual-write both formats
3. Parse and backfill existing data
4. Switch reads to new format
5. Stop writing old format
6. Drop old column

**Phases:** 3 (Expand → Migrate → Contract)
**Time:** 10-18 hours over 2-4 weeks

---

## Key Metrics to Monitor During Migration

### Expand Phase
- ✅ Dual-write success rate (should be 100%)
- ✅ Data consistency between old and new
- ✅ Performance impact (latency, throughput)
- ✅ Error rates

### Migrate Phase
- ✅ Traffic split (old vs new)
- ✅ Error rate comparison (old vs new)
- ✅ Performance comparison (latency, throughput)
- ✅ User impact (complaints, support tickets)

### Contract Phase
- ✅ Old path usage (should be 0)
- ✅ Errors after removal (should be 0)
- ✅ System stability
- ✅ Rollback readiness

---

## Rollback Procedures

### During Expand Phase
**Rollback is easy:**
- Revert code deploy
- New column/service unused, no data loss

### During Migrate Phase
**Rollback is straightforward:**
- Flip feature flag back to old path
- Dual-write still active, no data loss

### During Contract Phase
**Rollback is harder:**
- If old code removed, need to redeploy previous version
- If old column dropped, need to restore from backup
- **This is why we wait weeks before contracting**

---

## Anti-Patterns to Avoid

### ❌ Skipping Expand Phase
**Don't:** Immediately replace old with new

**Why:** No safety net, high risk of breaking production

**Do:** Add new alongside old, verify it works first

---

### ❌ Not Dual-Writing
**Don't:** Write only to new during expand phase

**Why:** Old code still reading from old path will break

**Do:** Write to both old and new during expand

---

### ❌ Contracting Too Quickly
**Don't:** Remove old immediately after 100% migration

**Why:** Hidden dependencies, edge cases, monitoring gaps

**Do:** Wait 1-2 weeks, verify zero usage, then remove

---

### ❌ No Monitoring
**Don't:** Deploy changes without observability

**Why:** Can't detect issues, can't compare old vs new

**Do:** Add metrics, logs, alerts for both paths

---

### ❌ Big Bang Migration
**Don't:** Flip 0% → 100% in one step

**Why:** High risk, hard to isolate issues

**Do:** Gradual rollout: 1% → 10% → 50% → 100%

---

Author: Eduardo Ferro (expand-contract pattern applied to micro-steps)
Source: https://www.eferro.net/
