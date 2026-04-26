# Hamburger Method: User Authentication with SSO, MFA, Social Login & Session Management

Let's apply the Hamburger Method to slice this feature into vertical, deliverable pieces.

---

## Layers Identified

This feature involves several distinct technical and business steps:

1. **Credential collection** — how the user provides identity proof
2. **Identity verification** — how the system validates who the user is
3. **MFA challenge** — second factor enforcement
4. **Session creation** — how the system represents an authenticated user
5. **Session lifecycle management** — how sessions are maintained and terminated

---

## Options per Layer

### Layer 1 — Credential Collection

How the user provides their identity to the system.

- **1.1**: Single username/password form, no external providers, no social login
- **1.2**: Username/password form + Google OAuth button (redirect flow, no SDK)
- **1.3**: Username/password + Google OAuth + GitHub OAuth (two social providers)
- **1.4**: Username/password + Google + GitHub + SAML SSO (enterprise IdP via SP-initiated flow)
- **1.5**: All of the above + IdP-initiated SAML, OIDC discovery, and extensible provider registry

---

### Layer 2 — Identity Verification

How the system validates the identity claim.

- **2.1**: Compare password hash against a local users table (bcrypt, no external service)
- **2.2**: Local password check + delegate social login to provider's callback (verify OAuth token with provider API)
- **2.3**: Local password + social login + SAML assertion validation (signature check via xmldsig)
- **2.4**: All of the above + integration with an identity provider library (e.g., Passport.js, NextAuth, Auth0 SDK)
- **2.5**: Fully managed identity platform (Auth0, Okta, Cognito) handling all provider verification centrally

---

### Layer 3 — MFA Challenge

Enforcing a second factor after primary authentication.

- **3.1**: No MFA — skip entirely for first slice
- **3.2**: TOTP (time-based one-time password) via authenticator app; hardcoded secret for one test user
- **3.3**: TOTP with per-user secret stored in DB; enrollment flow for real users
- **3.4**: TOTP + email OTP as fallback; user can choose preferred method
- **3.5**: TOTP + email OTP + SMS OTP + WebAuthn (hardware keys/biometrics); admin-enforced MFA policies per role/tenant

---

### Layer 4 — Session Creation

How the system represents the authenticated user after successful login.

- **4.1**: Server-side session stored in memory (single-process, no Redis); session ID in a cookie
- **4.2**: Server-side session stored in a database table (survives restarts, single server)
- **4.3**: Stateless JWT (access token + refresh token) stored in httpOnly cookies; no external store
- **4.4**: JWT + Redis session store for revocation support; refresh token rotation
- **4.5**: JWT with centralized session registry, distributed revocation (Redis Cluster/Pub-Sub), and SSO single-logout propagation across multiple apps

---

### Layer 5 — Session Lifecycle Management

How sessions are maintained, refreshed, and terminated.

- **5.1**: Fixed expiry cookie; user must re-login when it expires; no logout endpoint
- **5.2**: Logout endpoint that clears the cookie; fixed expiry still used
- **5.3**: Sliding session expiry (activity extends lifetime); logout clears server-side record
- **5.4**: Refresh token rotation; silent re-authentication in background; explicit logout invalidates all tokens
- **5.5**: Full session management: concurrent session limits, device list UI, remote session revocation, SSO single-logout (SLO), audit log of all session events

---

## Force Radical Slicing

**"If you had to ship something by tomorrow, what would you build?"**

The answer: ship a login form that works for one real user. No social login, no MFA, no complex session management. Prove the auth path is wired end to end.

---

## Smallest Vertical Slice (Ship by Tomorrow)

Select one option from each layer to form a complete, deployable slice:

| Layer | Choice | Description |
|-------|--------|-------------|
| 1 - Credential collection | **1.1** | Username + password form only |
| 2 - Identity verification | **2.1** | Local bcrypt password check against users table |
| 3 - MFA challenge | **3.1** | No MFA (skip entirely) |
| 4 - Session creation | **4.1** | In-memory server-side session, session ID cookie |
| 5 - Session lifecycle | **5.2** | Logout endpoint clears cookie; fixed expiry |

**What this delivers:**
- A real user can register, log in, and log out
- Session persists across page loads until expiry or explicit logout
- No external dependencies (no Redis, no OAuth providers, no SAML)
- Can be deployed on a single server in hours
- Validates the session middleware, route guards, and DB wiring are correct

**This slice does NOT include:** social login, MFA, SSO, or session revocation — all intentionally deferred.

---

## Follow-up Slices

### Slice 2: Add Google social login (1-2 days)
- Layer 1: **1.2** — Add Google OAuth button to the login form
- Layer 2: **2.2** — Verify OAuth callback token with Google API
- Layers 3, 4, 5: unchanged from Slice 1
- Value: Users with Google accounts can log in without a password; validates the OAuth redirect flow

### Slice 3: Add GitHub social login + basic session durability (1 day)
- Layer 1: **1.3** — Add GitHub OAuth alongside Google
- Layer 2: **2.2** — Same callback verification pattern, now for two providers
- Layer 4: **4.2** — Move session store to DB (survives deploys without logging users out)
- Layers 3, 5: unchanged
- Value: Covers the two most-requested social providers; sessions survive server restarts

### Slice 4: Add TOTP-based MFA (2-3 days)
- Layer 3: **3.3** — TOTP with per-user secret in DB + enrollment flow
- Layer 4: **4.3** — Upgrade to JWT + httpOnly cookies (stateless, scales horizontally)
- Layer 5: **4.4** — Refresh token rotation + full logout invalidation
- Layer 1, 2: unchanged
- Value: Security-conscious users can enable MFA; JWTs prepare for multi-service architecture

### Slice 5: Add enterprise SSO (SAML) (3-5 days)
- Layer 1: **1.4** — SAML SP-initiated login alongside existing providers
- Layer 2: **2.3** — SAML assertion signature validation
- Layer 5: **5.5** — SSO single-logout propagation
- Value: Enterprise customers can use their corporate IdP (Okta, Azure AD, etc.)

---

## Self-Check

- [x] Identified 5 clear functional layers (not just frontend/backend/DB)
- [x] Generated 5 options per layer following manual → scripted → automated → scalable → enterprise gradient
- [x] Forced radical slicing ("ship by tomorrow") — answered concretely
- [x] Smallest slice uses level 1-2 options from each layer
- [x] Smallest slice delivers value to at least one real user (can register + login + logout)
- [x] Smallest slice deployable in less than 1 day (no Redis, no OAuth, no MFA)
- [x] Proposed 4 follow-up slices showing clear, incremental improvement
- [x] No slice requires more than 3-5 days; each is reversible or expandable

---

## Key Insight

The feature as stated ("SSO + MFA + social login + session management") is at least 4-5 independent vertical slices, not one story. Attempting to deliver all of it at once means:
- No feedback until everything is done (weeks of dark work)
- No ability to test individual parts in production
- High risk of over-engineering early decisions (e.g., choosing a full identity platform before validating basic login works)

The Hamburger Method reveals that you can have a working, production-ready login system running **tomorrow**, and incrementally add SSO, MFA, and social login over the following sprints — each slice independently testable and deployable.
