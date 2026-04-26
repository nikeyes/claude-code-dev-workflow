# Hamburger Method: User Authentication with SSO, MFA, Social Login & Session Management

## Feature Description

Implement user authentication with SSO, MFA, social login (Google and GitHub), and session management for a SaaS application.

---

## Step 1: Identify Layers

This feature involves the following functional layers:

1. **Identity verification** — How does the system know who the user is?
2. **Authentication method** — How does the user prove their identity?
3. **Second factor (MFA)** — How does the system add an extra verification step?
4. **Session creation & management** — How does the system maintain authenticated state?
5. **Token/credential storage** — How are tokens, sessions, and secrets stored and protected?
6. **User feedback & error handling** — How does the system communicate auth state to the user?

---

## Step 2: Generate 4-5 Options per Layer

### Layer 1 — Identity Verification (Who is the user?)

- **1.1** Hardcoded list of allowed email addresses in a config file
- **1.2** Single identity provider: username/password stored in a local DB table
- **1.3** Social login via one provider only (e.g., Google OAuth2 with a library like Passport.js or NextAuth)
- **1.4** Multiple social login providers (Google + GitHub) with account linking by email
- **1.5** Enterprise SSO via SAML 2.0 / OIDC with an IdP (Okta, Azure AD, Auth0) plus social login and local accounts federated under a single identity

### Layer 2 — Authentication Method (How does the user prove identity?)

- **2.1** Shared password stored in `.env`, same for all internal test users
- **2.2** Username/password with bcrypt hashing and a `users` table
- **2.3** Magic link sent to verified email (no password at all)
- **2.4** OAuth2 PKCE flow with one social provider (Google); no local passwords
- **2.5** Full federated auth: local passwords + OAuth2 (Google, GitHub) + SAML SSO, all unified in one auth flow via a managed provider (Auth0, Clerk, Cognito)

### Layer 3 — Second Factor / MFA (Extra verification step)

- **3.1** No MFA — rely on provider's own security
- **3.2** Email OTP: send a 6-digit code to the user's email after password check
- **3.3** TOTP (Time-based OTP) via authenticator app (Google Authenticator, Authy) using `otplib` or similar
- **3.4** SMS OTP via Twilio or AWS SNS
- **3.5** Adaptive MFA: step-up only on risky signals (new device, unusual location, high-privilege actions), with recovery codes and multiple factor fallbacks

### Layer 4 — Session Creation & Management (Maintaining authenticated state)

- **4.1** Single hardcoded session token in memory (restart clears all sessions)
- **4.2** Server-side sessions stored in a DB table (`sessions`) with a cookie containing session ID
- **4.3** Stateless JWT access token (short-lived, 15 min) with no refresh token
- **4.4** JWT access token + refresh token stored in an HTTP-only cookie; refresh endpoint rotates tokens
- **4.5** Full session management: JWT + rotating refresh tokens + device tracking + concurrent session limits + forced logout + session activity audit log

### Layer 5 — Token/Credential Storage (How tokens and secrets are stored securely)

- **5.1** Tokens in `localStorage` (easy, insecure — for dev only)
- **5.2** Tokens in memory (React state/context) — lost on page refresh
- **5.3** HTTP-only cookies for refresh token; memory for access token
- **5.4** HTTP-only + Secure + SameSite=Strict cookies; CSRF protection via double-submit cookie pattern
- **5.5** Dedicated secrets manager (AWS Secrets Manager / HashiCorp Vault) for OAuth client secrets; HTTP-only cookies for user tokens; encryption at rest for stored credentials

### Layer 6 — User Feedback & Error Handling (Auth state communicated to user)

- **6.1** No error messages — generic "Something went wrong"
- **6.2** Basic error states: invalid credentials, account not found
- **6.3** Specific, actionable errors: expired session, wrong MFA code, account locked after N attempts
- **6.4** UX flows: loading states, redirect after login, remember-me checkbox, logout from all devices
- **6.5** Full auth UX: progressive disclosure, contextual help for MFA setup, account recovery flow, trusted device management, real-time session activity page

---

## Step 3: Force Radical Slicing

> **"If you had to ship something by tomorrow, what would you build?"**

**Minimum viable auth slice:**

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Identity verification | **1.3** Google OAuth2 only (NextAuth/Passport) | Covers the most common social login; zero password management |
| Authentication method | **2.4** OAuth2 PKCE with Google only | No local DB users to manage; Google handles identity |
| MFA | **3.1** No MFA | Rely on Google's own 2FA; don't build new infrastructure |
| Session management | **4.3** Stateless JWT (short-lived, 15 min) | No session DB needed; simple to deploy |
| Token storage | **5.3** HTTP-only cookie for token | Secure enough for early users; prevents XSS |
| User feedback | **6.2** Basic error states | Cover the most common failure paths only |

**This slice:**
- Can be built in 4-8 hours using NextAuth.js (Next.js) or Passport.js + `jsonwebtoken`
- Delivers working Google login to real users with zero password infrastructure
- Is secure enough for a closed beta (HTTP-only cookie, HTTPS required)
- Answers the question: "Can users log into our SaaS with their Google account today?"

---

## Step 4: Filter & Prioritize Options

**Eliminated for slice 1:**
- SAML/SSO (1.5): Requires enterprise IdP setup — weeks of work, no early users need it
- SMS OTP (3.4): Requires Twilio account, phone number handling, international compliance — costly for no current user demand
- Refresh token rotation (4.4/4.5): Adds complexity; short-lived JWT is sufficient for initial validation
- Secrets Manager (5.5): Over-engineered for a handful of OAuth client secrets; use env vars securely

**Fast-delivery options kept:**
- Google OAuth (1.3/2.4): Pre-built libraries handle the hard parts
- No MFA (3.1): Leverage Google's built-in 2FA rather than building our own
- Short JWT (4.3): Stateless, no infrastructure needed
- HTTP-only cookie (5.3): One line of config in most frameworks

---

## Step 5: Compose Vertical Slices

### Slice 1 — "Log in with Google" (Ship tomorrow)

**Options chosen:** 1.3 + 2.4 + 3.1 + 4.3 + 5.3 + 6.2

**What it delivers:**
- Users can sign in using their Google account
- A short-lived JWT is issued and stored in an HTTP-only cookie
- Basic error messages shown for auth failures
- Value to: any early SaaS user who already has a Google account (the majority)
- Answers: "Can real users log in and reach the dashboard securely?"

**Build time:** 4-8 hours

**Stack example:**
```
NextAuth.js with Google provider → JWT strategy → HTTP-only cookie
```

---

### Slice 2 — Add GitHub login + account linking (2-3 days after Slice 1)

**Changes from Slice 1:**
- Add GitHub as a second OAuth provider (1.4)
- Link accounts by email so Google and GitHub users with the same email share one account

**Value added:** Developers (a key SaaS segment) prefer GitHub login. No new infrastructure — just a second OAuth app registration.

---

### Slice 3 — Add MFA with TOTP (3-5 days after Slice 2)

**Changes from Slice 2:**
- Add optional TOTP MFA during login (3.3)
- Enroll flow: show QR code, verify first code, store TOTP secret encrypted in DB
- Recovery codes generated and shown once at enrollment

**Value added:** Users with sensitive data can opt into stronger security. Supports compliance requirements (SOC 2, GDPR).

---

### Slice 4 — Add JWT refresh token + proper session management (2-3 days after Slice 3)

**Changes from Slice 3:**
- Replace short-lived JWT-only approach with refresh token rotation (4.4)
- Store refresh token in HTTP-only + Secure + SameSite=Strict cookie
- Add logout (invalidate refresh token) and "logout from all devices" endpoint
- Token storage upgraded to (5.4)

**Value added:** Users stay logged in without re-authenticating every 15 minutes. Security posture improved with token rotation and revocation.

---

### Slice 5 — Enterprise SSO via SAML/OIDC (1-2 weeks after Slice 4)

**Changes from Slice 4:**
- Integrate Auth0 or Clerk as the auth layer (1.5 / 2.5)
- Support SAML 2.0 / OIDC for enterprise customers (Okta, Azure AD)
- Adaptive MFA (3.5) via Auth0 rules or Clerk policies
- Full session audit log and device management (4.5)

**Value added:** Unlocks enterprise deals. Compliance with security teams that require SSO.

---

## Self-Check

- [x] I identified 6 clear layers (within the 3-6 range), all functional not just technical
- [x] I generated 5 options per layer following the quality gradient
- [x] Options follow manual → scripted → automated → scalable → enterprise
- [x] I forced radical slicing by asking "ship by tomorrow" and answered it explicitly
- [x] The smallest vertical slice uses level 1-3 options from each layer
- [x] The smallest slice delivers value to real beta users (Google login to dashboard)
- [x] The smallest slice can be deployed in less than 1 day
- [x] I proposed 4 follow-up slices showing clear incremental improvement

---

## Key Insight

The instinct with authentication is to build everything at once (SSO + MFA + social + sessions) because "security must be complete." The Hamburger Method exposes that Google OAuth alone is already secure and valuable for early users. You can add MFA, GitHub, refresh tokens, and enterprise SSO incrementally — each slice improves security or reach without blocking the previous one from shipping.

> "Can we avoid doing it?" — Yes, we can avoid building a password system entirely by starting with OAuth only. The first slice has zero password infrastructure to maintain.
