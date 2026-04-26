# Small Safe Steps Plan: Migrate Email Sending from SendGrid to AWS SES

## Goal

Replace SendGrid as the email provider with AWS SES across the entire application, with zero downtime and a safe rollback path at every stage.

**End state:** All emails are sent via AWS SES. SendGrid SDK, credentials, and subscription are removed.

**Risk level:** HIGH — this is a service replacement (risky change). Applies the **Expand-Contract pattern**.

**Estimated total duration:** ~12-15 hours of work spread over ~1 month.

---

## Overview: Expand → Migrate → Contract

| Phase | Goal | Safety Net |
|-------|------|-----------|
| Phase 1: EXPAND | AWS SES installed and verified alongside SendGrid | SendGrid is still the active provider |
| Phase 2: MIGRATE | Gradually shift traffic from SendGrid to AWS SES | Feature flag allows instant rollback to SendGrid |
| Phase 3: CONTRACT | Remove SendGrid once AWS SES is proven stable | Only after 0% SendGrid usage confirmed for 1-2 weeks |

---

## Phase 1: EXPAND — Add AWS SES Alongside SendGrid

**Goal:** System supports both providers. No user is affected. SendGrid remains active.

---

### Step 1.1 — Verify AWS SES account setup and send limits (LEARNING)
**Type:** Learning (time-boxed)
**Duration:** 1-2h
**What to do:**
- Confirm AWS account has SES enabled in the target region (e.g., `us-east-1`)
- Verify sender domains/email addresses are verified in SES
- Check if SES is in sandbox mode (sandbox only allows sending to verified addresses — production requires a sending limit increase request)
- If in sandbox: open an AWS support request to move to production sending
- Document: region, verified sender addresses, IAM permissions needed
**Output:** Decision document — ready or blocked (if sandbox, note the ETA for production access)
**Reversible:** Yes (nothing deployed)

---

### Step 1.2 — Install AWS SDK and configure credentials (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Add `boto3` (Python) or the equivalent AWS SDK for your language to `requirements.txt` / `package.json`
- Add AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`) to environment config / secrets manager — do NOT hardcode
- Deploy this to all environments (dev, staging, production)
- Do NOT send any emails yet
**Deployable:** Yes (no behavior change)
**Reversible:** Yes (remove env vars and package)
**Verify:** `import boto3; boto3.client('ses')` initializes without error in staging

---

### Step 1.3 — Create an email abstraction layer with dual-provider support (EARNING)
**Type:** Earning
**Duration:** 2h
**What to do:**
- Wrap existing SendGrid calls behind an `EmailService` abstraction (if not already abstracted)
- Implement both `_send_via_sendgrid()` and `_send_via_ses()` methods inside the abstraction
- Add a `provider` parameter that defaults to `'sendgrid'` (no behavior change yet)
- Ensure the SES path covers all email types currently sent: transactional, password reset, notifications, etc.

Example structure:
```python
class EmailService:
    def send(self, to, subject, body, html_body=None, provider='sendgrid'):
        if provider == 'aws_ses':
            return self._send_via_ses(to, subject, body, html_body)
        return self._send_via_sendgrid(to, subject, body, html_body)
```

**Deployable:** Yes (SendGrid still default, SES path exists but unused)
**Reversible:** Yes (revert deploy)
**Verify:** Unit tests pass for both paths; integration test sends via SES to an internal/test address

---

### Step 1.4 — Send a test email via AWS SES to internal recipients only (LEARNING)
**Type:** Learning
**Duration:** 1h
**What to do:**
- Manually invoke `_send_via_ses()` in a staging or dev environment
- Send to a team-internal email address (not to real users)
- Verify: email received, formatting correct, links work, no SPF/DKIM failures
- Check SES delivery dashboard for bounce/complaint metrics
**Output:** Confirmed SES works end-to-end for all email templates used
**Reversible:** Yes (nothing in production changed)

---

### Step 1.5 — Add a feature flag for provider selection (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Add a feature flag (e.g., `email_provider` = `'sendgrid'` | `'aws_ses'`) to your feature flag system or environment config
- Wire the `EmailService.send()` method to read this flag
- Default value: `'sendgrid'` (no behavior change)
- Deploy to production
**Deployable:** Yes (default is still sendgrid)
**Reversible:** Yes (flip flag or revert)
**Verify:** Flag exists in config, default value returns `'sendgrid'`

---

### Phase 1 Checklist Before Moving to Phase 2

- [ ] AWS SES account is out of sandbox (or confirmed it won't affect scope)
- [ ] AWS SDK installed and credentials configured in all environments
- [ ] EmailService abstraction wraps all email sending
- [ ] SES send path implemented and tested with internal emails
- [ ] Feature flag is in place and defaults to `sendgrid`
- [ ] Monitoring / alerting is set up for email delivery rates and bounce rates in SES

---

## Phase 2: MIGRATE — Gradually Route Traffic to AWS SES

**Goal:** Shift email traffic from SendGrid to AWS SES incrementally, using the feature flag. Keep dual-write capability available as a safety net throughout.

---

### Step 2.1 — Enable AWS SES for 1% of emails (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Set feature flag to route 1% of emails to `aws_ses`
- Deploy to production
- Monitor for 24-48h:
  - SES delivery rate (target: ≥ 99%)
  - Bounce rate (target: ≤ 0.5%)
  - Complaint rate (target: ≤ 0.1%)
  - Any application errors from SES SDK
- Compare against SendGrid baseline metrics
**Reversible:** Yes (flip flag back to 100% sendgrid instantly)
**Verify:** SES dashboard shows emails sent and delivered; no error spike in application logs

---

### Step 2.2 — Monitor and compare metrics (LEARNING)
**Type:** Learning (passive, 48h–1 week)
**Duration:** 1h active monitoring setup + passive observation
**What to do:**
- Set up a dashboard comparing:
  - Delivery rate: SendGrid vs SES
  - Bounce rate: SendGrid vs SES
  - Latency: SendGrid vs SES
  - Error rate in application
- Document findings
**Output:** Go / No-Go decision to increase traffic percentage
**Reversible:** Yes (monitor only, no code change)

---

### Step 2.3 — Increase to 10% of emails via SES (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Set feature flag to route 10% to `aws_ses`
- Monitor for 48h–1 week (same metrics as Step 2.1)
**Reversible:** Yes (flip flag)
**Verify:** No significant deviation from SendGrid baseline metrics

---

### Step 2.4 — Increase to 50% of emails via SES (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Set feature flag to route 50% to `aws_ses`
- Monitor for 48h–1 week
**Reversible:** Yes (flip flag)
**Verify:** Same metrics healthy; no user-reported email issues

---

### Step 2.5 — Increase to 100% of emails via SES (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Set feature flag to route 100% to `aws_ses`
- Monitor closely for first 48h, then observe for 1-2 weeks
- SendGrid is still configured — instant rollback possible by flipping the flag
**Reversible:** Yes (flip flag instantly)
**Verify:** Zero emails going through SendGrid (confirm in SendGrid dashboard), SES metrics stable

---

### Phase 2 Checklist Before Moving to Phase 3

- [ ] Feature flag at 100% pointing to `aws_ses` for at least 1-2 weeks
- [ ] No errors or anomalies from SES in production logs
- [ ] SES delivery, bounce, and complaint rates are within acceptable thresholds
- [ ] SendGrid dashboard confirms 0 emails sent for the last 1-2 weeks
- [ ] No user reports of missing emails
- [ ] Team agrees it is safe to remove SendGrid

---

## Phase 3: CONTRACT — Remove SendGrid

**Goal:** Clean up by removing all SendGrid code, credentials, and dependencies. Only start after Phase 2 is verified stable for 1-2 weeks with 0 SendGrid usage.

---

### Step 3.1 — Remove SendGrid API key from config (EARNING)
**Type:** Earning
**Duration:** 30min
**What to do:**
- Remove `SENDGRID_API_KEY` from all environment configs, secrets manager, CI/CD pipelines
- Deploy (application should still work — only SES path used now)
**Reversible:** Can restore from secrets backup
**Verify:** Application starts correctly; no errors due to missing SendGrid key

---

### Step 3.2 — Remove SendGrid code from EmailService (EARNING)
**Type:** Earning
**Duration:** 1h
**What to do:**
- Delete `_send_via_sendgrid()` method
- Remove `provider` parameter from `EmailService.send()` — SES is now the only provider
- Simplify the class

Example after cleanup:
```python
class EmailService:
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name=AWS_REGION)

    def send(self, to, subject, body, html_body=None):
        return self.ses_client.send_email(...)
```

- Update all call sites that passed `provider=` argument
**Deployable:** Yes
**Reversible:** Git revert
**Verify:** All unit and integration tests pass; test email sends correctly

---

### Step 3.3 — Remove feature flag (EARNING)
**Type:** Earning
**Duration:** 30min
**What to do:**
- Delete the `email_provider` feature flag from feature flag system and code
- Remove all conditional logic referencing it
**Deployable:** Yes
**Reversible:** Git revert
**Verify:** No references to `email_provider` flag remain in codebase

---

### Step 3.4 — Uninstall SendGrid SDK (EARNING)
**Type:** Earning
**Duration:** 30min
**What to do:**
- Remove `sendgrid` from `requirements.txt` / `package.json` / `Gemfile` etc.
- Run dependency install to confirm no broken imports
- Deploy
**Deployable:** Yes
**Reversible:** Re-add package
**Verify:** `import sendgrid` (or equivalent) fails as expected; application still sends emails correctly

---

### Step 3.5 — Cancel SendGrid subscription (OPERATIONAL)
**Type:** Earning (cost reduction)
**Duration:** 30min
**What to do:**
- Log in to SendGrid and cancel or downgrade the subscription
- Export any historical email analytics you want to retain before cancellation
- Update internal documentation and runbooks to reference AWS SES instead of SendGrid
**Verify:** SendGrid account is cancelled or at free tier; no further billing

---

### Phase 3 Checklist

- [ ] SendGrid API key removed from all environments
- [ ] `_send_via_sendgrid` code deleted
- [ ] Feature flag removed
- [ ] SendGrid SDK uninstalled
- [ ] All tests pass
- [ ] No errors in production after deploy
- [ ] SendGrid subscription cancelled

---

## Summary

| Phase | Steps | Effort | Duration |
|-------|-------|--------|----------|
| Phase 1: EXPAND | 5 steps | ~6-7h | Week 1 |
| Phase 2: MIGRATE | 5 steps | ~5-6h active + passive monitoring | Weeks 2-4 |
| Phase 3: CONTRACT | 5 steps | ~3h | Week 5 (after 2 weeks stable at 100%) |
| **Total** | **15 steps** | **~12-15h** | **~1 month** |

---

## Rollback Procedures

| Phase | Rollback |
|-------|---------|
| Expand | Revert code deploy — no user impact, SES path was unused |
| Migrate | Flip feature flag back to `sendgrid` — instant, zero data loss |
| Contract | Git revert + restore SendGrid API key from secrets backup — harder, which is why we wait |

---

## Key Principles Applied

- **Expand before contracting:** SendGrid is never removed until AWS SES is proven stable at 100% for 1-2 weeks
- **Feature flag for gradual rollout:** 1% → 10% → 50% → 100% — no big bang
- **Learning before earning:** AWS SES is tested with internal emails before touching production traffic
- **Every step is deployable and reversible**
- **Zero downtime:** Users always receive emails throughout the migration

---

*Pattern: Expand-Contract | Author inspiration: Eduardo Ferro (eferro.net)*
