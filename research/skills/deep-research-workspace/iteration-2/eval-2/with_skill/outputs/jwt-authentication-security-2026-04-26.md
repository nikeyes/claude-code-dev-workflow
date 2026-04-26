---
title: Research on JWT Authentication: How It Works and Common Security Pitfalls
date: 2026-04-26
query: How does JWT authentication work and what are common security pitfalls?
keywords: JWT,JSON Web Token,authentication,authorization,security,pitfalls,HMAC,RSA,alg none,secret key
status: complete
agent_count: 2
source_count: 14
---

# Research on JWT Authentication: How It Works and Common Security Pitfalls

## Executive Summary

JSON Web Tokens (JWTs) are a compact, URL-safe mechanism for representing claims securely between two parties, widely used for stateless authentication in modern web applications. A JWT consists of three Base64URL-encoded parts—header, payload, and signature—separated by dots, and is typically issued by an authorization server after credential verification. The server signs the token (using HMAC-SHA256 or RSA/ECDSA) so that any party with the secret or public key can verify its authenticity without storing session state. Despite their convenience, JWTs carry significant security risks when misconfigured: the most critical pitfalls include accepting the 'alg:none' attack, confusion between symmetric and asymmetric algorithms, weak or leaked secrets, missing expiration validation, and storing tokens in localStorage where XSS can steal them. Mitigating these risks requires strict algorithm whitelisting, short token lifetimes with refresh-token rotation, and storing JWTs in HttpOnly cookies.

## Detailed Findings

### 1. JWT Structure and Encoding

A JWT is composed of three dot-separated parts encoded in Base64URL:

- **Header**: Specifies the token type (`typ: JWT`) and signing algorithm (`alg: HS256`, `RS256`, etc.)
- **Payload**: Contains "claims" — registered (e.g., `iss`, `sub`, `exp`, `iat`), public, and private claims
- **Signature**: Computed over `base64(header) + '.' + base64(payload)` using the chosen algorithm and secret/private key

The signature prevents tampering: changing any byte in the header or payload invalidates the signature. However, JWTs are **not encrypted by default** — the payload is only encoded, not secret. Sensitive data should never be placed in a JWT unless using JWE (JSON Web Encryption).
**Sources:** [1] [2] [3]

### 2. Authentication Flow

The standard JWT authentication flow:

1. Client sends credentials (username/password) to the auth server
2. Server validates credentials and issues a signed JWT containing user identity and roles
3. Client stores the JWT (ideally in an HttpOnly cookie) and sends it with each subsequent request, typically in the `Authorization: Bearer <token>` header
4. Resource server validates the JWT signature and checks claims (`exp`, `iss`, `aud`) before granting access
5. No server-side session storage is required — the token is self-contained

This stateless model allows horizontal scaling without sticky sessions, making JWTs popular in microservices architectures.
**Sources:** [1] [4] [5]

### 3. Signing Algorithms

JWTs support several signing algorithms, each with different security tradeoffs:

- **HS256/HS384/HS512 (HMAC)**: Symmetric — same secret used to sign and verify. Fast, but the secret must be shared between issuer and verifier. A leaked secret compromises all tokens.
- **RS256/RS384/RS512 (RSA)**: Asymmetric — private key signs, public key verifies. Public key can be distributed freely; only the auth server holds the private key.
- **ES256/ES384/ES512 (ECDSA)**: Asymmetric with shorter keys than RSA. Preferred for high-performance scenarios.
- **PS256/PS384/PS512 (RSASSA-PSS)**: Probabilistic RSA variant with stronger security proofs.

RS256 or ES256 are recommended for production systems where the resource server is separate from the auth server.
**Sources:** [2] [6] [7]

### 4. Critical Security Pitfall: The alg:none Attack

The JWT specification allows `"alg": "none"` to indicate an unsecured token (no signature). Vulnerable libraries that trust the header's `alg` field will accept any token claiming `alg:none` as valid without verifying a signature. An attacker can:

1. Decode any legitimate JWT (Base64URL is trivially reversible)
2. Modify the payload (e.g., change `role: user` to `role: admin`)
3. Set `"alg": "none"` in the header and remove the signature
4. Submit the forged token

**Mitigation**: Always explicitly whitelist accepted algorithms in the library configuration. Never accept `alg:none` in production. Libraries like `jsonwebtoken` (Node.js) require passing `algorithms: ['RS256']` to the verify call.
**Sources:** [8] [9] [10]

### 5. Algorithm Confusion (RS256 → HS256) Attack

When a system supports both RSA (RS256) and HMAC (HS256), an attacker can exploit libraries that auto-select the algorithm from the token header:

1. The attacker takes the server's **public key** (often publicly available via JWKS endpoint)
2. Crafts a token with `"alg": "HS256"` in the header
3. Signs it with the public key as if it were an HMAC secret
4. The vulnerable server, seeing `alg:HS256`, uses the public key as the HMAC secret — and the signature verifies

**Mitigation**: Never allow callers to dictate the algorithm. Pin the algorithm server-side and reject tokens using any other algorithm.
**Sources:** [9] [10] [11]

### 6. Weak Secrets and Secret Management

For HS256, the security of the entire system depends on the HMAC secret. Common mistakes:

- Using short, guessable secrets (e.g., `secret`, `password`, `jwt_secret`)
- Hardcoding secrets in source code committed to version control
- Using the same secret across environments (dev/staging/prod)
- Never rotating secrets after a suspected compromise

NIST recommends HMAC-SHA256 secrets of at least 256 bits (32 bytes) of cryptographic randomness. Secrets should be stored in environment variables or secret management systems (HashiCorp Vault, AWS Secrets Manager) and rotated regularly.
**Sources:** [6] [12] [13]

### 7. Missing or Incorrect Claim Validation

JWTs contain claims that **must** be validated on every request:

- `exp` (expiration): Token is only valid until this timestamp. Failing to check `exp` means tokens remain valid forever after issuance, even for revoked users.
- `nbf` (not before): Token should not be accepted before this time.
- `iss` (issuer): Validates that the token was issued by the expected authority.
- `aud` (audience): Ensures the token was intended for this specific service, preventing token reuse across services.

A study of open-source JWT libraries found that many did not validate `aud` by default, enabling cross-service token reuse attacks.
**Sources:** [3] [4] [11]

### 8. Token Storage and XSS/CSRF

Where a JWT is stored determines its vulnerability surface:

- **localStorage**: Accessible to any JavaScript on the page. A single XSS vulnerability allows an attacker to steal the token and fully impersonate the user. **Not recommended for sensitive applications.**
- **sessionStorage**: Same XSS risk as localStorage; cleared on tab close but still vulnerable.
- **HttpOnly cookie**: Not accessible to JavaScript; immune to XSS token theft. Vulnerable to CSRF, but CSRF is mitigated with `SameSite=Strict` or `SameSite=Lax` cookie attribute and CSRF tokens.

The OWASP recommendation is to store JWTs in HttpOnly, Secure, SameSite cookies for browser-based applications.
**Sources:** [5] [13] [14]

### 9. Token Expiration and Revocation

JWTs are stateless and cannot be "revoked" server-side once issued (unlike opaque session tokens). Common approaches to handle revocation:

- **Short-lived access tokens** (5-15 minutes) combined with longer-lived refresh tokens stored server-side. Revoking a refresh token prevents new access tokens from being issued.
- **Token blacklisting/denylist**: Maintain a server-side list of revoked JTI (JWT ID) claims. Adds state but allows immediate revocation. Use Redis with TTL equal to token lifetime to limit storage growth.
- **Rotating refresh tokens**: Issue a new refresh token on every use. If an old refresh token is used, suspect token theft and revoke all refresh tokens for that user.

The tradeoff between statelessness and revocability is a fundamental JWT design tension.
**Sources:** [7] [12] [14]

## Conclusions

- JWT authentication is inherently stateless and scalable, but this statelessness makes revocation difficult; short-lived tokens (5-15 min) with refresh-token rotation are the recommended pattern to balance security and scalability.
- The three most critical implementation mistakes are: (1) not whitelisting the signing algorithm, enabling alg:none and algorithm confusion attacks; (2) using weak or improperly managed HMAC secrets; and (3) storing tokens in localStorage, exposing them to XSS.
- Always validate all relevant claims on every request: `exp`, `iss`, `aud`, and `nbf`. Missing `aud` validation is particularly common and enables cross-service token reuse.
- For new systems, prefer RS256 or ES256 over HS256 — asymmetric algorithms eliminate the need to share a secret between the auth server and resource servers, reducing the blast radius of a compromise.
- Use a well-maintained, up-to-date JWT library (e.g., `jsonwebtoken` for Node.js, `PyJWT` for Python, `java-jwt` for Java) and explicitly pass algorithm and audience options rather than relying on defaults.

## Bibliography

[1] RFC 7519 - JSON Web Token (JWT) - IETF - https://datatracker.ietf.org/doc/html/rfc7519
[2] RFC 7515 - JSON Web Signature (JWS) - IETF - https://datatracker.ietf.org/doc/html/rfc7515
[3] RFC 7518 - JSON Web Algorithms (JWA) - IETF - https://datatracker.ietf.org/doc/html/rfc7518
[4] Introduction to JSON Web Tokens - jwt.io - https://jwt.io/introduction
[5] OWASP Cheat Sheet: JSON Web Token Security - OWASP - https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
[6] JSON Web Token Best Current Practices - RFC 8725 - IETF - https://datatracker.ietf.org/doc/html/rfc8725
[7] Auth0 - Refresh Token Rotation - https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation
[8] Critical vulnerabilities in JSON Web Token libraries - Tim McLean (2015) - https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
[9] JWT Algorithm Confusion Attacks - PortSwigger Web Security Academy - https://portswigger.net/web-security/jwt/algorithm-confusion
[10] JWT Vulnerabilities - PortSwigger Web Security Academy - https://portswigger.net/web-security/jwt
[11] SoK: Playing with Fire – Revisiting JWT Security - IEEE S&P 2023 - https://ieeexplore.ieee.org/document/10179416
[12] NIST SP 800-63B: Digital Identity Guidelines - Authentication - https://pages.nist.gov/800-63-3/sp800-63b.html
[13] OWASP Top 10 - A07:2021 Identification and Authentication Failures - https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
[14] OAuth 2.0 Security Best Current Practice - RFC 9700 - IETF - https://datatracker.ietf.org/doc/html/rfc9700


---
*Research conducted by stepwise-research multi-agent system*
*Generated: 2026-04-26 20:45:03 CEST*
