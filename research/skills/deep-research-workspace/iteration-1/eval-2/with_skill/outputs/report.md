---
title: Research on JWT Authentication and Common Security Pitfalls
date: 2026-04-26
query: How does JWT authentication work and what are common security pitfalls?
keywords: JWT, JSON Web Token, authentication, security, algorithm confusion, signature verification, HMAC, RSA, RFC 7519, RFC 8725
status: complete
agent_count: 2
source_count: 8
---

# Research on JWT Authentication and Common Security Pitfalls

## Executive Summary

JSON Web Tokens (JWTs) are a compact, URL-safe standard (RFC 7519) for transmitting cryptographically secured claims between parties. A JWT consists of three Base64URL-encoded parts — header, payload, and signature — enabling stateless authentication without server-side session storage. While widely adopted, JWTs are plagued by implementation pitfalls: the most critical include algorithm confusion attacks (e.g., switching RS256 to HS256 using the public key as a secret), accepting `"alg": "none"` tokens, weak signing secrets, and incomplete claim validation. RFC 8725 (JWT Best Current Practices) and OWASP provide authoritative guidance on avoiding these vulnerabilities.

## Detailed Findings

### JWT Structure and How It Works

A JWT is represented as three Base64URL-encoded segments joined by dots: `Header.Payload.Signature`.

**Header** — Contains metadata about the token: the type (`"typ": "JWT"`) and the signing algorithm (e.g., `"alg": "HS256"` or `"alg": "RS256"`). This tells the recipient how the token was secured.

**Payload** — A JSON object containing *claims*: statements about the entity (user) and additional data. RFC 7519 defines seven registered claims:
- `iss` (Issuer): identifies who issued the token
- `sub` (Subject): identifies the principal the token describes
- `aud` (Audience): specifies intended recipients
- `exp` (Expiration Time): token validity deadline (Unix timestamp)
- `nbf` (Not Before): earliest time the token is valid
- `iat` (Issued At): creation timestamp
- `jti` (JWT ID): unique identifier, useful for replay prevention

**Signature** — Created by signing the Base64URL-encoded header and payload (concatenated with a dot) using the algorithm and key specified in the header. For HMAC-SHA256: `HMACSHA256(base64url(header) + "." + base64url(payload), secret)`. For RSA: the signing key is a private key, and verification uses the corresponding public key.

Key points:
- The payload is encoded but NOT encrypted — anyone can decode it [1] [6]
- The signature makes the token tamper-evident: any modification to header or payload invalidates it [1] [2]
- RFC 7519 requires cryptographic protection via JWS (signing) or JWE (encryption) [4]

**Authentication Flow:**
1. User submits credentials to the authorization server
2. Server validates credentials and issues a JWT
3. Client stores the token and attaches it to subsequent requests: `Authorization: Bearer <token>`
4. Server validates the JWT signature and claims before granting access
5. No server-side session state is needed — the token is self-contained [1] [2]

**Signing Algorithms:**
- **Symmetric (HMAC):** HS256, HS384, HS512 — a single shared secret is used to both sign and verify. All parties must know the secret.
- **Asymmetric (RSA/ECDSA):** RS256, RS384, RS512, ES256, ES384 — a private key signs, and the public key verifies. The public key can be distributed openly via a JWKS endpoint. [7]

### Common Security Pitfalls

#### 1. The `"alg": "none"` Attack

Some JWT libraries historically accepted tokens with the algorithm header set to `"none"` and an empty signature as "validly verified." An attacker could:
1. Decode any JWT
2. Modify the payload claims (e.g., escalate privileges)
3. Re-encode with `"alg": "none"` and an empty signature

If the server trusts the token's `alg` header without enforcing an allowlist, this bypasses signature verification entirely, allowing arbitrary account access. [2] [8]

**Mitigation:** Explicitly specify and enforce the expected algorithm in your verification code. Never read the algorithm from the untrusted token header.

#### 2. Algorithm Confusion (RS256 → HS256) Attack

This is one of the most sophisticated JWT attacks. It exploits the difference between asymmetric and symmetric algorithms:
- A server configured for RS256 has a public RSA key (widely available)
- An attacker changes the token's `alg` header from `RS256` to `HS256`
- The server's JWT library, seeing `HS256`, uses the RSA **public key** as the HMAC secret
- The attacker signs a forged token using the public key as a MAC secret

Since the public key is not secret, the attacker can generate valid HMAC signatures the server will accept. [3] [8]

**Mitigation:** Validate the `alg` header against an explicit allowlist tied to the specific key type. Never allow callers to select the algorithm.

#### 3. Weak Signing Keys and Brute-Force Attacks

HS256 tokens signed with short, guessable, or default secrets (e.g., "secret", "password") are vulnerable to offline brute-force attacks. An attacker who obtains a valid token can attempt to crack the secret using wordlists (e.g., via hashcat). [2] [3]

RFC 8725 and OWASP both state:
- HMAC secrets must be at least 256 bits (32 bytes) of cryptographic randomness
- OWASP recommends 64+ characters for HMAC secrets
- Never use human-memorable passwords as JWT signing keys [5] [4]

**Mitigation:** Use cryptographically secure random key generation. Prefer asymmetric signing (RS256/ES256) for multi-party scenarios so the signing secret never needs to be shared.

#### 4. Header Parameter Injection (jwk, jku, kid)

The JWT header supports optional parameters that can be exploited:
- **`jwk` injection:** Attacker embeds their own public key directly in the token header; a vulnerable library uses it to verify the signature the attacker just created with the matching private key.
- **`jku` injection:** Attacker sets the JWK Set URL to a server they control, which returns their own public key.
- **`kid` path traversal:** Attacker manipulates the Key ID to a predictable file path (e.g., `/dev/null`), causing the library to sign/verify with a null/empty key. [3]

**Mitigation:** Never use key material embedded in or referenced from the token header. Maintain a server-side key registry and look up keys by `kid` only from trusted internal sources.

#### 5. Missing or Incomplete Claim Validation

Signature verification confirms authenticity but claim validation enforces authorization rules. Many implementations omit:
- **`exp` check:** Expired tokens are accepted indefinitely
- **`aud` check:** Tokens issued for Service A are accepted by Service B (token substitution)
- **`iss` check:** Tokens from untrusted issuers are accepted

RFC 8725 explicitly mandates validating `iss`, `sub`, `aud`, `exp`, `nbf`, and `iat`. [4] [7]

**Mitigation:** Implement a validation checklist: verify signature → check `exp` → check `nbf` → verify `iss` against a trusted list → verify `aud` matches the current service.

#### 6. Sensitive Data Exposure in Payload

Because the payload is only Base64URL-encoded (not encrypted), any party that intercepts or stores the token can read all claims. Including PII (email, SSN, medical data) in JWT payloads is a privacy violation. [5] [7]

**Mitigation:** Keep payloads minimal. Use JWE (JSON Web Encryption) if sensitive data must be included, or use opaque reference tokens (Phantom Token / Split Token pattern) and resolve them server-side.

#### 7. Token Storage and XSS/CSRF Risks

- **localStorage:** Persistent, accessible to JavaScript — vulnerable to XSS attacks stealing the token
- **sessionStorage:** Cleared on tab close, still accessible to XSS
- **HttpOnly cookies:** Not accessible to JavaScript, immune to XSS, but susceptible to CSRF

OWASP recommends using `sessionStorage` or JavaScript-closure-stored tokens combined with strict Content Security Policy (CSP) headers. If cookies are used, apply `HttpOnly`, `Secure`, and `SameSite=Strict` flags. [5]

#### 8. No Token Revocation Mechanism

JWTs are stateless by design — once issued, they remain valid until expiration. There is no built-in revocation. This is a significant limitation for high-security use cases (e.g., password change, account compromise).

**Mitigation:** Keep token lifetimes short (15–30 minutes for access tokens). Implement a server-side denylist (storing SHA-256 hashes of revoked JTIs) for critical operations. Use refresh token rotation with revocation tracking. [5] [7]

#### 9. Compression Oracle Attacks

RFC 8725 warns that compressing data before encryption leaks plaintext information through ciphertext length analysis. Even though the plaintext is encrypted, an attacker who can influence token content and observe ciphertext length can infer sensitive values. [4]

**Mitigation:** Do not compress JWT payloads before encryption.

### Cross-References and Contradictions

There is strong consensus across RFC 7519, RFC 8725, OWASP, Auth0, PortSwigger, and Curity on the core mitigations: explicit algorithm allowlisting, complete claim validation, strong key entropy, and short token lifetimes. All sources agree that trusting the `alg` header field is the root cause of the two most severe attack classes (alg:none and algorithm confusion).

A notable tension exists around **storage recommendations**: OWASP and many security guides warn against both cookie and localStorage storage, advocating JavaScript-closure-based storage — a solution that has limited adoption and adds implementation complexity. In practice, HttpOnly cookies with CSRF tokens remain the most widely deployed approach, and many practitioners consider this an acceptable trade-off.

RFC 8725 (2020) supersedes some advice in the original RFC 7519 (2015), particularly around algorithm agility. The BCP explicitly discourages algorithm agility (allowing multiple algorithms) in favor of explicit, per-use-case algorithm binding — a shift from the original spec's design philosophy.

There are gaps in current coverage around **distributed/federated JWT validation** (e.g., across microservices) and **post-quantum cryptography readiness** for JWT signing algorithms.

## Conclusions

- JWTs are three-part Base64URL-encoded tokens (header.payload.signature) enabling stateless authentication; the signature guarantees tamper-evidence but the payload is not secret
- The two most severe vulnerabilities — `"alg": "none"` bypass and algorithm confusion — both stem from trusting attacker-controlled data in the token header; the fix is to explicitly enforce algorithm choices server-side
- Weak HMAC keys are highly exploitable offline; use 256+ bit cryptographically random secrets or switch to asymmetric RS256/ES256
- Complete claim validation (`exp`, `aud`, `iss`, `sub`) is mandatory; missing any one claim can enable token reuse, substitution, or impersonation attacks
- Token revocation is structurally hard with JWTs; short lifetimes (15–30 min) plus a denylist for critical revocation events is the industry consensus

## Bibliography

[1] JWT Introduction - jwt.io — https://jwt.io/introduction
[2] JWT Best Practices (Auth0 Blog / RFC 8725 draft) — https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/
[3] JWT Vulnerabilities - PortSwigger Web Security Academy — https://portswigger.net/web-security/jwt
[4] RFC 8725: JSON Web Token Best Current Practices (IETF) — https://datatracker.ietf.org/doc/html/rfc8725
[5] OWASP JWT Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
[6] JWT Token Structure - Auth0 Docs — https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-token-structure
[7] JWT Best Practices - Curity — https://curity.io/resources/learn/jwt-best-practices/
[8] Critical Vulnerabilities in JWT Libraries - Auth0 Blog — https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
[9] RFC 7519: JSON Web Token (IETF) — https://datatracker.ietf.org/doc/html/rfc7519

---
*Research conducted by stepwise-research multi-agent system*
*Generated: 2026-04-26*
