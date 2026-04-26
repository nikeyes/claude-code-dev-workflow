# JWT Authentication: How It Works and Common Security Pitfalls

**Date**: 2026-04-26  
**Topic**: JWT Authentication — Mechanisms and Security Vulnerabilities  
**Method**: Training data synthesis (no live web search)

---

## Executive Summary

JSON Web Tokens (JWTs) are a compact, URL-safe means of representing claims between two parties. They are widely used for stateless authentication and authorization in modern web applications. While JWTs offer real advantages in distributed systems, their flexibility introduces a class of implementation mistakes that frequently result in critical security vulnerabilities. This report covers the full lifecycle of JWT authentication and catalogs the most consequential security pitfalls known in the field.

---

## 1. What Is a JWT?

A JWT (pronounced "jot") is defined by RFC 7519. It encodes a set of **claims** — assertions about a subject — as a JSON object that is digitally signed (and optionally encrypted).

### 1.1 Structure

A JWT consists of three Base64URL-encoded parts separated by dots:

```
HEADER.PAYLOAD.SIGNATURE
```

**Example (decoded):**

```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "1234567890",
  "name": "Alice",
  "iat": 1516239022,
  "exp": 1516242622
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

### 1.2 Claim Types

| Claim | Type | Meaning |
|-------|------|---------|
| `iss` | Registered | Issuer |
| `sub` | Registered | Subject (user identifier) |
| `aud` | Registered | Audience (intended recipient) |
| `exp` | Registered | Expiration time (Unix timestamp) |
| `nbf` | Registered | Not before (token not valid before this time) |
| `iat` | Registered | Issued at |
| `jti` | Registered | JWT ID (unique identifier) |
| Custom fields | Public/Private | Application-specific data |

---

## 2. How JWT Authentication Works

### 2.1 Authentication Flow

```
1. User submits credentials (username + password) to /login
2. Server validates credentials against the database
3. Server generates a JWT signed with a secret (or private key)
4. Server returns the JWT to the client
5. Client stores the JWT (localStorage, sessionStorage, or a cookie)
6. Client includes the JWT in the Authorization header for subsequent requests:
   Authorization: Bearer <token>
7. Server validates the JWT signature and claims on each request
8. If valid, the server processes the request; otherwise it returns 401
```

### 2.2 Signature Verification

For **symmetric** algorithms (e.g., HS256):
- The server signs the token with a shared secret.
- Verification uses the same secret.
- Suitable for single-service architectures.

For **asymmetric** algorithms (e.g., RS256, ES256):
- The server signs with a **private key**.
- Any party with the corresponding **public key** can verify the token.
- Suitable for microservices and multi-party scenarios (the issuer can be separate from the verifier).

### 2.3 Why JWTs Are Popular

- **Stateless**: The server does not need to store session state; all needed information is in the token.
- **Scalable**: Horizontally scalable services can verify tokens independently without a shared session store.
- **Interoperable**: The open standard works across languages and platforms.
- **Self-contained**: Tokens carry claims, reducing database lookups per request.

---

## 3. Common Security Pitfalls

### 3.1 Algorithm Confusion: The "alg: none" Attack

**Severity: Critical**

Early JWT libraries honored the `alg` field from the token header itself. An attacker could:
1. Take a valid token.
2. Change the header to `{"alg": "none", "typ": "JWT"}`.
3. Strip the signature.
4. Submit the unsigned token.

If the server naively accepted `alg: none`, it would treat the token as valid without any signature check.

**Mitigation**: Always specify the expected algorithm explicitly on the server side. Never accept `alg: none` from untrusted input.

---

### 3.2 RS256 to HS256 Algorithm Switching Attack

**Severity: Critical**

Some libraries support both asymmetric (RS256) and symmetric (HS256) algorithms. An attacker who knows the server's **public key** (often publicly available) can:
1. Craft a token signed with HS256 using the public key as the HMAC secret.
2. Change the header's `alg` from `RS256` to `HS256`.

A naive library that picks the verification method from the token header will verify the HMAC using the public key — which the attacker already knows — and accept the forged token.

**Mitigation**: Always configure the expected algorithm on the server side, independent of what the token header claims.

---

### 3.3 Weak or Predictable Secrets (HS256)

**Severity: High**

When using HMAC-based algorithms, the security of the signature depends entirely on the entropy of the secret key. Common mistakes:
- Using short secrets (e.g., `"secret"`, `"password"`, `"12345"`).
- Using well-known strings or application names.
- Reusing secrets across environments (dev/staging/production).

An attacker who obtains tokens can perform offline brute-force attacks (tools like `hashcat` have dedicated JWT modes).

**Mitigation**:
- Use a cryptographically random secret of at least 256 bits.
- Use separate secrets per environment.
- Rotate secrets periodically using key versioning.

---

### 3.4 Missing or Incorrect Expiration (`exp`) Validation

**Severity: High**

JWTs with no expiration or very long-lived tokens create a large window for exploitation. If a token is stolen (via XSS, man-in-the-middle, or log exposure), the attacker can use it indefinitely.

**Mitigation**:
- Always set a reasonable `exp` claim (e.g., 15 minutes for access tokens).
- Validate `exp` strictly on the server side.
- Use short-lived access tokens combined with refresh tokens for better UX.

---

### 3.5 Missing Audience (`aud`) and Issuer (`iss`) Validation

**Severity: Medium–High**

If a service validates the signature but ignores `aud` and `iss` claims, a token issued for one service can be replayed against another service that shares the same signing key.

**Example**: A JWT meant for `api.payments.example.com` could be accepted by `api.admin.example.com` if both use the same secret and neither checks `aud`.

**Mitigation**:
- Always validate `iss` to ensure the token was issued by the expected authority.
- Always validate `aud` to ensure the token was intended for this service.

---

### 3.6 Storing JWTs in localStorage (XSS Exposure)

**Severity: High**

`localStorage` is accessible via JavaScript. Any XSS vulnerability in the application can allow an attacker to steal tokens stored there.

**Comparison of storage options:**

| Storage | XSS Risk | CSRF Risk | Notes |
|---------|----------|-----------|-------|
| `localStorage` | High | Low | Accessible via JS |
| `sessionStorage` | High | Low | Accessible via JS, cleared on tab close |
| `HttpOnly` cookie | Low | Medium | Not accessible via JS, needs CSRF protection |
| `SameSite=Strict` cookie | Low | Very Low | Best for same-origin flows |

**Mitigation**: Store JWTs in `HttpOnly`, `Secure`, `SameSite=Strict` cookies to prevent JavaScript access. Implement CSRF tokens if cookies are used.

---

### 3.7 No Token Revocation Mechanism

**Severity: Medium–High**

Because JWTs are stateless, there is no built-in revocation mechanism. If a token is compromised (or a user logs out), the token remains valid until it expires.

**Mitigation strategies**:
- **Blocklist (denylist)**: Maintain a server-side set of revoked `jti` values. Check on each request. This re-introduces state but only for the small set of revoked tokens.
- **Short expiration + refresh tokens**: Use short-lived access tokens (minutes) and a longer-lived refresh token stored securely. Refresh tokens can be revoked in a database.
- **Token rotation**: Issue a new refresh token on every use and invalidate the old one (sliding session).

---

### 3.8 Sensitive Data in Payload (No Encryption)

**Severity: Medium**

JWT payloads are Base64URL-encoded, not encrypted. Anyone who obtains the token can decode the payload and read its contents. Developers sometimes store sensitive data (PII, internal roles, database IDs) in the payload without realizing it is visible.

**Mitigation**:
- Avoid storing sensitive data in JWT payloads unless the token is encrypted (JWE — JSON Web Encryption, RFC 7516).
- Store only the minimal claims necessary for authorization.

---

### 3.9 JWT Injection via `kid` (Key ID) Header Parameter

**Severity: High**

Some JWT implementations use the `kid` (Key ID) header to look up the signing key dynamically from a database or file. If user input is not sanitized:
- **SQL Injection via `kid`**: `kid: "' UNION SELECT 'attacker-controlled-secret' --"` can cause the server to use an attacker-chosen key for verification.
- **Path Traversal via `kid`**: `kid: "../../dev/null"` can force the server to use an empty key, effectively bypassing signature verification.

**Mitigation**:
- Validate and whitelist the `kid` value before any lookup.
- Never use `kid` directly in SQL queries without parameterization.
- Restrict `kid` to known, enumerable key identifiers.

---

### 3.10 Accepting Expired Tokens Due to Clock Skew Misconfiguration

**Severity: Low–Medium**

Some libraries allow a configurable clock skew tolerance (e.g., accepting tokens expired up to 5 minutes ago). If this tolerance is set too high, it significantly extends the effective validity window of stolen tokens.

**Mitigation**: Keep clock skew tolerance minimal (typically ≤ 30 seconds). Ensure server clocks are synchronized via NTP.

---

### 3.11 JWT Confusion with JWK Sets (JWKS URI Spoofing)

**Severity: High**

Some OAuth/OIDC implementations automatically fetch the public key from a URL specified in the JWT header (`jku` — JWK Set URL, or `x5u`). If the library trusts this URL without validation, an attacker can:
1. Host their own JWKS endpoint.
2. Sign a token with their own private key.
3. Set `jku` in the token header to their endpoint.

The server fetches the attacker's public key and validates the forged token successfully.

**Mitigation**:
- Never automatically trust URLs from token headers.
- Pin the JWKS URI to a known, server-configured value.
- Most modern libraries have fixed this, but verify library settings.

---

## 4. JWT vs. Session Tokens: When to Use Which

| Consideration | JWT | Server-Side Sessions |
|---------------|-----|---------------------|
| Scalability | Excellent (stateless) | Requires shared session store |
| Revocation | Difficult | Easy (delete session record) |
| Token size | Larger (carries data) | Compact (just an ID) |
| Database lookups per request | Fewer (claims in token) | Required |
| Security model | Complex (many pitfalls) | Simpler |
| Best fit | Distributed/microservices, APIs | Traditional monolith, web apps |

---

## 5. Refresh Token Patterns

Access tokens should be short-lived. Refresh tokens manage session longevity:

```
1. Login → server returns:
   - access_token (exp: 15 minutes)
   - refresh_token (exp: 7 days, stored in HttpOnly cookie)

2. Client uses access_token for API calls.

3. When access_token expires (401 response):
   - Client calls /refresh with the refresh_token
   - Server validates refresh_token, issues new access_token
   - (With rotation) Server also issues new refresh_token and invalidates old one

4. On logout:
   - Server invalidates the refresh_token in the database
   - Client discards both tokens
```

---

## 6. Security Best Practices Summary

| Practice | Rationale |
|----------|-----------|
| Always specify algorithm server-side | Prevents alg confusion attacks |
| Use RS256/ES256 for distributed systems | Allows verification without sharing secrets |
| Set short `exp` (15 min for access tokens) | Limits blast radius of token theft |
| Validate `iss`, `aud`, `exp`, `nbf` | Prevents replay and cross-service attacks |
| Use `HttpOnly`, `Secure`, `SameSite` cookies | Prevents XSS-based token theft |
| Use high-entropy secrets (≥256 bits) for HS256 | Prevents brute-force |
| Implement refresh token rotation | Enables revocation without pure statelessness |
| Maintain a small revocation list (`jti`) | Supports immediate revocation when needed |
| Sanitize `kid` header before key lookup | Prevents SQL injection / path traversal |
| Never put sensitive data in payload | Payload is readable by anyone with the token |
| Pin JWKS URI server-side | Prevents JKU spoofing attacks |

---

## 7. Known CVEs and Real-World Incidents

- **CVE-2015-9235** — `jsonwebtoken` (Node.js): The library accepted `alg: none`, allowing signature bypass. Fixed in v4.2.2.
- **CVE-2016-5431** — `python-jwt`: RS256/HS256 algorithm confusion vulnerability.
- **CVE-2022-21449** ("Psychic Signatures" — Java 15-17): A flaw in Java's ECDSA signature verification allowed empty/zeroed signatures to pass for any EC-signed JWT, completely bypassing verification.
- **Auth0 2017 disclosure**: Multiple JWT libraries were vulnerable to the `alg: none` and RS256→HS256 confusion attacks.

---

## 8. Recommended Libraries and Tools

### Libraries with Strong JWT Security Defaults
- **Node.js**: `jose` (Panva) — strict algorithm enforcement by default
- **Python**: `PyJWT` (>= 2.0) — breaks on `alg: none` by default
- **Java**: `nimbus-jose-jwt` — comprehensive, well-audited
- **Go**: `golang-jwt/jwt` — community fork of dgrijalva/jwt-go after it was abandoned

### Security Testing Tools
- **jwt_tool** — JWT testing and exploitation toolkit
- **hashcat** — Offline HMAC secret brute-forcing (`--hash-type 16500` for HS256)
- **Burp Suite** — JWT Editor extension for intercepting and modifying tokens
- **jwt.io** — Online JWT debugger (do not paste production tokens)

---

## 9. Conclusion

JWT authentication is a powerful and widely adopted pattern, but it comes with a non-trivial attack surface. The most dangerous vulnerabilities — algorithm confusion, weak secrets, and missing claim validation — stem from incorrect implementation rather than flaws in the JWT standard itself. Developers should:

1. Use a well-maintained library with secure defaults.
2. Always specify and enforce the expected algorithm server-side.
3. Validate all relevant claims (`exp`, `iss`, `aud`, `nbf`).
4. Store tokens in `HttpOnly` cookies, not `localStorage`.
5. Pair short-lived access tokens with a refresh token rotation strategy.
6. Treat the JWT payload as readable (not confidential) unless using JWE.

Following these practices eliminates the majority of known JWT security vulnerabilities in production systems.

---

## References

- RFC 7519 — JSON Web Token (JWT): https://datatracker.ietf.org/doc/html/rfc7519
- RFC 7515 — JSON Web Signature (JWS): https://datatracker.ietf.org/doc/html/rfc7515
- RFC 7516 — JSON Web Encryption (JWE): https://datatracker.ietf.org/doc/html/rfc7516
- RFC 7517 — JSON Web Key (JWK): https://datatracker.ietf.org/doc/html/rfc7517
- OWASP: JSON Web Token Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- PortSwigger: JWT Attacks — https://portswigger.net/web-security/jwt
- Auth0 Blog: Critical Vulnerabilities in JWT libraries (2015) — https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
- CVE-2022-21449 (Psychic Signatures) — https://neilmadden.blog/2022/04/19/psychic-signatures-in-java/
