# Hamburger Method: User Authentication with SSO, MFA, Social Login, and Session Management

## Feature Description

Implement user authentication for a SaaS application covering:
- Single Sign-On (SSO) via SAML 2.0 / OIDC
- Multi-Factor Authentication (MFA) — TOTP, SMS, hardware keys
- Social login via Google and GitHub (OAuth 2.0 / OIDC)
- Session management — creation, validation, refresh, revocation

---

## Step 1: Identify the Layers (The Burger Stack)

The Hamburger Method decomposes the feature into horizontal layers — from data persistence at the bottom to user-facing UI at the top. Every layer must be traversed to deliver a working vertical slice.

| # | Layer | Responsibility |
|---|-------|---------------|
| 1 | **Data / Persistence** | Store users, credentials, sessions, MFA secrets, OAuth tokens, SSO configs |
| 2 | **Domain / Business Logic** | Auth rules, MFA verification, token validation, session lifecycle policies |
| 3 | **External Integrations** | OAuth2 providers (Google, GitHub), SAML/OIDC IdPs, SMS/TOTP libraries |
| 4 | **API / Transport** | HTTP endpoints, JWT issuance, CSRF tokens, rate limiting |
| 5 | **Security / Cross-Cutting** | Password hashing, secrets management, audit logging, HTTPS enforcement |
| 6 | **Frontend / UI** | Login forms, OAuth redirect flows, MFA challenge screens, session expiry UX |

---

## Step 2: Generate Implementation Options Per Layer

### Layer 1 — Data / Persistence

**Option A — Single users table with JSON columns**
All auth data (OAuth tokens, MFA secrets, session data) stored in JSON columns on the users table. Simple schema, poor queryability for complex lookups.

**Option B — Normalized relational schema (users + sessions + mfa_credentials + oauth_accounts)**
Separate tables per concern. Fully relational, supports indexing and foreign-key integrity. Higher migration complexity but best long-term maintainability.

**Option C — Users table + Redis for sessions only**
Relational DB for persistent identity data; Redis for short-lived session tokens. Offloads session lookup latency, adds an infrastructure dependency.

**Option D — Third-party identity store (Auth0, Cognito, Firebase Auth)**
Delegate all user storage to a managed service. Zero schema to maintain, vendor lock-in risk, cost at scale.

**Option E — Append-only event log (event sourcing)**
All auth events stored as immutable events; current state derived by projection. Excellent audit trail, significant implementation overhead.

---

### Layer 2 — Domain / Business Logic

**Option A — Inline logic in route handlers**
Auth rules written directly inside API controllers. Fast to prototype, becomes unmaintainable at scale.

**Option B — Service layer with pure functions**
Dedicated AuthService, MfaService, SessionService classes with no framework coupling. Testable, portable, clear ownership.

**Option C — State machine for auth flow**
Each authentication attempt modeled as a finite state machine (unauthenticated → password-verified → mfa-pending → authenticated). Explicit transitions, easy to reason about complex MFA flows.

**Option D — Policy objects / strategy pattern**
Pluggable auth strategies (password, TOTP, hardware key, OAuth). Each strategy is a standalone class implementing a common interface. Easy to add new factors without changing core logic.

**Option E — Rules engine (e.g., Open Policy Agent)**
Externalized policy evaluation. Powerful for complex role/tenant-based rules, overkill for standard auth flows.

---

### Layer 3 — External Integrations

**Option A — Direct OAuth2 HTTP calls**
Implement the OAuth2 authorization code flow manually using raw HTTP. Full control, maintenance burden for spec changes.

**Option B — Passport.js / Authlib / similar SDK**
Use a battle-tested library with pre-built strategies for Google, GitHub, SAML, OIDC. Fastest path, good community support.

**Option C — Hosted OAuth proxy (e.g., Dex, Keycloak)**
Run an internal identity broker that federates Google, GitHub, SAML. Uniform OIDC interface internally; adds infrastructure.

**Option D — Managed identity provider (Auth0, Okta)**
Fully managed external integrations. Zero code for provider-specific quirks; vendor dependency.

**Option E — Direct SAML library (e.g., node-saml, python3-saml)**
Parse SAML assertions in-app, handle IdP metadata. Full control over SSO, non-trivial XML/crypto handling.

---

### Layer 4 — API / Transport

**Option A — REST endpoints with JWT (stateless)**
POST /auth/login returns a signed JWT. No server-side session state; horizontal scaling is trivial. Token revocation requires a blocklist.

**Option B — REST endpoints with opaque session tokens (stateful)**
Server issues an opaque token stored in the DB / Redis. Easy revocation, server must validate every request.

**Option C — REST + refresh token rotation**
Short-lived access token (15 min) + long-lived refresh token with rotation on use. Balances statelessness with revocation capability.

**Option D — GraphQL mutations**
Auth operations exposed as GraphQL mutations. Consistent with a GraphQL-first API; adds complexity to CSRF handling.

**Option E — BFF (Backend for Frontend) pattern**
A thin server-side layer issues HttpOnly cookies; the SPA never touches tokens. Best security posture for browser clients, requires a dedicated BFF service.

---

### Layer 5 — Security / Cross-Cutting

**Option A — bcrypt password hashing + manual audit log table**
Standard bcrypt (cost 12), write auth events to an audit_logs table manually. Simple, well-understood.

**Option B — Argon2id + structured logging to SIEM**
Argon2id for password hashing (OWASP recommended), structured JSON logs shipped to a SIEM (e.g., Datadog, Splunk). Better security, more infrastructure.

**Option C — Passkeys / WebAuthn only (passwordless)**
Eliminate passwords entirely. Gold standard for phishing resistance; significant UX change, not backward-compatible.

**Option D — Centralized secrets manager (Vault, AWS Secrets Manager)**
All signing keys, OAuth secrets, MFA seeds stored in a secrets manager with rotation support. Production-grade, adds operational complexity.

**Option E — Rate limiting + CAPTCHA as security controls**
IP-based and account-based rate limiting; CAPTCHA on failed attempts. Brute-force mitigation layer, orthogonal to storage/hashing choice.

---

### Layer 6 — Frontend / UI

**Option A — Server-rendered HTML forms (no JS framework)**
Plain HTML login form, redirect-based OAuth flow, TOTP input page. Works everywhere, no SPA complexity.

**Option B — React / Vue SPA with API-driven auth**
Client-side form validation, token storage in memory (not localStorage), interceptors for token refresh. Modern UX, requires careful token handling.

**Option C — Headless UI library (e.g., Radix UI, shadcn/ui)**
Pre-built accessible components for login, MFA, OAuth buttons. Accelerates UI build, consistent accessibility.

**Option D — Auth UI kit from provider (e.g., Auth0 Lock, Firebase UI)**
Drop-in hosted or embeddable login widget. Fastest delivery, limited customization.

**Option E — Progressive enhancement**
Server-rendered baseline + JS enhancement for inline validation and token refresh. Best compatibility, more complex frontend build.

---

## Step 3: Compose the Smallest Vertical Slice

A vertical slice must:
1. Be independently deployable
2. Deliver real end-to-end user value
3. Touch all necessary layers with the simplest possible option at each layer
4. Be completable in 1–3 days by one developer

### Recommended Smallest Vertical Slice

**"Email + Password login that returns a session token and works end-to-end"**

This slice validates the entire authentication pipeline — data, domain logic, API, security controls, and UI — before layering on OAuth, MFA, or SSO complexity.

| Layer | Chosen Option | Rationale |
|-------|--------------|-----------|
| **Data** | Option B — Normalized schema: `users` + `sessions` tables | Establishes the relational foundation that all future features extend. Only two tables needed for this slice. |
| **Domain Logic** | Option B — Service layer with pure functions (`AuthService`) | `AuthService.login(email, password)` → validates credentials, issues session. Pure function = easily testable. |
| **External Integrations** | None for this slice | No OAuth or SSO in slice 1. |
| **API** | Option C — REST + refresh token rotation (simplified: just access token for slice 1) | `POST /api/auth/login` returns `{ accessToken, expiresAt }`. One endpoint, no refresh token rotation yet. |
| **Security** | Option A — bcrypt (cost 12) + manual audit log | Hash password on registration. Log login attempts to `audit_logs`. Rate limit login endpoint (5 req/min per IP). |
| **Frontend** | Option A — Server-rendered HTML form (or minimal React form) | Single login page: email input, password input, submit button. Redirect to dashboard on success. |

### Slice 1 Scope (what is included)

- User registration: `POST /api/auth/register` — accepts email + password, hashes with bcrypt, inserts into `users` table
- User login: `POST /api/auth/login` — verifies password hash, creates a row in `sessions` table, returns an opaque session token in an HttpOnly cookie
- Protected route check: middleware reads cookie, validates session row exists and is not expired
- Logout: `POST /api/auth/logout` — deletes the session row, clears the cookie
- Login UI: a simple HTML or React form with email + password fields
- Basic audit log: every login attempt (success/failure) written to `audit_logs`
- Rate limiting: 5 login attempts per IP per minute (in-memory or Redis)

### Slice 1 Scope (what is explicitly excluded)

- Google OAuth
- GitHub OAuth
- SSO (SAML / OIDC)
- MFA (TOTP, SMS, hardware key)
- Refresh token rotation
- Password reset / forgot password
- Account lockout policy
- Email verification

### Why This Slice First?

- Validates the core session contract that OAuth and MFA will reuse
- Proves the data schema and service layer before complicating them
- Gives the team a working, deployable login feature from day one
- All future slices (social login, MFA, SSO) layer on top of this foundation without changing it

---

## Step 4: Subsequent Slices (Roadmap)

| Slice | Feature Added | Builds On |
|-------|--------------|-----------|
| **Slice 2** | Google OAuth login | Slice 1: adds `oauth_accounts` table, Passport.js Google strategy, `/auth/google` redirect flow |
| **Slice 3** | GitHub OAuth login | Slice 2: adds GitHub strategy, reuses `oauth_accounts` table |
| **Slice 4** | TOTP-based MFA | Slice 1: adds `mfa_credentials` table, `speakeasy` TOTP library, MFA challenge step after password |
| **Slice 5** | SMS-based MFA | Slice 4: adds SMS provider (Twilio), alternate MFA verification path |
| **Slice 6** | Refresh token rotation | Slice 1: extends `sessions` table with `refresh_token`, implements rotation logic |
| **Slice 7** | SSO via OIDC | Slices 2–3: adds OIDC IdP configuration table, discovery document parsing, OIDC flow |
| **Slice 8** | SSO via SAML 2.0 | Slice 7: adds SAML metadata, assertion consumer service endpoint, `node-saml` |
| **Slice 9** | Hardware key MFA (WebAuthn) | Slice 4: adds WebAuthn registration/assertion, passkey credential storage |
| **Slice 10** | Admin session management UI | Slice 6: lists active sessions, allows remote revocation |

---

## Summary

The Hamburger Method applied to this authentication feature reveals six horizontal layers. Each layer has 5 viable implementation options ranging from minimal to production-grade. The smallest deliverable vertical slice is **email + password login with session tokens**, which traverses all layers end-to-end using the simplest viable option at each layer. This slice can be delivered in 1–2 days, validated in production, and extended incrementally toward SSO, MFA, and social login without architectural rewrites.
