# Migration Plan: SendGrid to AWS SES

## Overview

Migrate the application's email sending infrastructure from SendGrid to AWS Simple Email Service (SES). The migration aims for zero downtime by running both providers in parallel during the transition, then cutting over fully to SES once validated.

---

## Phase 1: Preparation and AWS Setup

### Step 1.1 — Audit current email usage
- Inventory every place in the codebase that calls SendGrid (search for `@sendgrid/mail`, `sendgrid`, `SG.` API keys, etc.)
- Document all email types sent: transactional (welcome, password reset, receipts), marketing, notifications
- Record volume, sender addresses, reply-to addresses, and any dynamic templates used
- Note any SendGrid-specific features in use: templates, unsubscribe groups, click/open tracking settings, suppression lists

### Step 1.2 — Set up AWS account access
- Ensure the application has (or create) an IAM user/role with the `ses:SendEmail` and `ses:SendRawEmail` permissions
- Prefer an IAM role (EC2 instance profile, ECS task role, Lambda execution role) over long-lived access keys
- Store the IAM credentials or role ARN in the secrets manager / environment variable system already in use

### Step 1.3 — Verify sender identities in SES
- Request production access (SES starts in sandbox mode; sandbox only allows verified recipients)
- Verify every sender domain and/or email address that currently sends via SendGrid:
  - Add the SES DNS records (DKIM CNAME, optional MAIL FROM MX/TXT) to your DNS provider
  - Confirm verification status in the AWS console
- Request SES sending limit increase if current SendGrid volume exceeds default SES limits

### Step 1.4 — Configure SES sending options
- Enable DKIM signing for each verified domain
- Optionally enable a custom MAIL FROM domain to avoid the `via amazonses.com` header
- Set up an SNS topic for bounce and complaint notifications; route those notifications to a handler that updates your suppression list (this replaces SendGrid's event webhooks)
- Decide on a configuration set and enable tracking (opens, clicks) if needed

---

## Phase 2: Code Abstraction (Expand)

### Step 2.1 — Introduce an email-provider abstraction
- Create an interface/abstract class `EmailProvider` with a single `sendEmail(message)` method (or equivalent in your language)
- Wrap the existing SendGrid calls behind a concrete `SendGridEmailProvider` that implements this interface
- Replace all direct SendGrid calls in the codebase with calls through the abstraction
- Run all existing tests; nothing should change in behavior

### Step 2.2 — Implement the SES provider
- Add the AWS SDK for SES (`@aws-sdk/client-ses` for Node, `boto3` for Python, `software.amazon.awssdk:ses` for Java, etc.)
- Create `SesEmailProvider` implementing the same interface
- Map all fields: `to`, `from`, `subject`, `html body`, `text body`, `reply-to`, `cc`, `bcc`, attachments
- Handle SES-specific error codes and translate them to the same error types the rest of the app already catches
- Write unit tests for the new provider using the AWS SDK's mock/test utilities

### Step 2.3 — Add a feature flag to select the active provider
- Introduce a config value (e.g. `EMAIL_PROVIDER=sendgrid|ses|both`) read at startup
- Wire the factory so `sendgrid` returns `SendGridEmailProvider`, `ses` returns `SesEmailProvider`
- `both` (or `shadow`) routes every send to SES but keeps SendGrid as a fallback — useful in the next phase

---

## Phase 3: Parallel Running / Shadow Mode (Validate)

### Step 3.1 — Enable shadow mode in a non-production environment
- Set `EMAIL_PROVIDER=both` in staging
- Verify real emails arrive correctly: formatting, links, attachments, encoding
- Compare SES delivery logs against SendGrid activity feed

### Step 3.2 — Migrate suppression / unsubscribe lists
- Export SendGrid's global unsubscribe, bounce, and spam report lists
- Import them into SES's account-level suppression list via the AWS console or `ses:PutSuppressedDestination` API
- Confirm the suppression list is honored by the new provider before proceeding

### Step 3.3 — Update event webhook handlers
- SendGrid pushes delivery events (bounces, opens, clicks) to a webhook endpoint
- Replace or augment this handler to also process SNS notifications from SES
- Ensure bounce/complaint handling logic (marking users as unsubscribable, alerting ops) works with the SES event format

---

## Phase 4: Cutover (Contract)

### Step 4.1 — Roll out SES to production gradually
- Deploy with `EMAIL_PROVIDER=ses` to a small percentage of traffic (canary/feature-flag rollout) if your infrastructure supports it
- Monitor SES CloudWatch metrics: `Send`, `Bounce`, `Complaint`, `Reject`, delivery rate
- Keep SendGrid credentials active as a rollback option

### Step 4.2 — Full production cutover
- Once confidence is high (24–48 hours of clean metrics), set `EMAIL_PROVIDER=ses` for 100% of traffic
- Monitor for 48–72 hours: bounce rate should stay below 5%, complaint rate below 0.1% (SES thresholds)

### Step 4.3 — Remove SendGrid (Contract phase)
- Delete or archive `SendGridEmailProvider` and its dependencies
- Remove the SendGrid SDK from package dependencies
- Revoke the SendGrid API key and remove it from secrets management
- Remove the `both` / shadow mode branch from the factory if no longer needed

---

## Phase 5: Post-Migration Cleanup and Hardening

### Step 5.1 — Update documentation and runbooks
- Update infrastructure diagrams to show SES
- Document how to rotate SES credentials / IAM role
- Update on-call runbooks: how to investigate bounces, complaints, and SES sending quota issues

### Step 5.2 — Tighten IAM permissions
- Apply least-privilege: scope the IAM policy to only the verified SES identities and configuration sets actually used
- Enable SES account-level sending pause in IAM policy (optional but useful for incident response)

### Step 5.3 — Set up ongoing monitoring
- CloudWatch alarm: bounce rate > 2% in any 15-minute window
- CloudWatch alarm: complaint rate > 0.05% in any 15-minute window
- CloudWatch alarm: `Reject` count > 0 (indicates malformed requests)
- Review SES Reputation Dashboard monthly

---

## Rollback Plan

| Phase | Rollback action |
|-------|----------------|
| Phase 2 | Delete the SES provider class; no production change has been made |
| Phase 3 | Switch `EMAIL_PROVIDER=sendgrid` in staging; no production impact |
| Phase 4 (canary) | Route canary traffic back to `sendgrid` via feature flag |
| Phase 4 (full cutover) | Set `EMAIL_PROVIDER=sendgrid`; redeploy; SendGrid key is still active |

---

## Dependencies and Prerequisites

- AWS account with SES available in the target region (SES is not available in all regions)
- DNS access to add DKIM and MAIL FROM records
- AWS SDK added to the project's dependencies
- Secrets/config management system that can hold the new IAM credentials or role configuration
- CI/CD pipeline updated to run the new SES provider tests
- Stakeholder sign-off on the 24–72 hour parallel-run window

---

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1 — AWS Setup | 0.5–1 day |
| Phase 2 — Code abstraction + SES provider | 1–2 days |
| Phase 3 — Shadow mode validation | 1–3 days (mostly waiting/monitoring) |
| Phase 4 — Cutover | 0.5 day + monitoring window |
| Phase 5 — Cleanup | 0.5 day |
| **Total** | **3.5–7 days** |

Effort varies significantly based on the number of email types, the complexity of existing SendGrid template usage, and whether a proper abstraction layer already exists in the codebase.
