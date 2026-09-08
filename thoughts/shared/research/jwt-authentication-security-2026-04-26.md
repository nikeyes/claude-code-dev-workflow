---
title: JWT Authentication: How It Works and Common Security Pitfalls
date: 2026-04-26
query: How does JWT authentication work and what are common security pitfalls?
keywords: JWT,authentication,JSON Web Token,security,pitfalls,alg:none,token validation,HMAC,RSA,signing
status: complete
agent_count: 2
source_count: 14
---

# JWT Authentication: How It Works and Common Security Pitfalls

## Executive Summary

JSON Web Tokens (JWTs) are a compact, URL-safe means of representing claims between two parties, widely used for stateless authentication in modern web applications. A JWT consists of three Base64URL-encoded parts — header, payload, and signature — which together allow a server to issue a self-contained, verifiable credential without maintaining session state. While JWTs offer significant scalability advantages, they introduce a distinct set of security risks when misconfigured or misunderstood. The most critical pitfalls include accepting the "alg:none" algorithm, using weak or shared secrets, skipping signature verification, storing tokens insecurely in browsers, and failing to enforce expiration. Adopting JWTs safely requires strict server-side validation, short expiry windows, rotation strategies, and adherence to the latest RFC 7519 guidance.

## Detailed Findings

### How JWT Authentication Works

A JWT is composed of three dot-separated components: **Header.Payload.Signature**.

**Header** declares the token type and the signing algorithm:
```json
{ "alg": "HS256", "typ": "JWT" }
```

**Payload** carries claims — statements about the entity (user) and additional metadata:
```json
{ "sub": "1234567890", "name": "Alice", "iat": 1516239022, "exp": 1516242622 }
```

**Signature** is computed by the server using the chosen algorithm and a secret (or private key), preventing tampering. For HS256:
```
HMAC-SHA256(base64url(header) + "." + base64url(payload), secret)
```
**Sources:** [1] [2] [3]

### Authentication Flow

1. User sends credentials (username/password) to the auth endpoint.
2. Server validates credentials, creates a JWT with claims and expiry, signs it, and returns it.
3. Client stores the token (memory, HttpOnly cookie, or localStorage — each with different security tradeoffs).
4. On subsequent requests, the client includes the JWT in the Authorization header: `Bearer <token>`.
5. Server verifies the signature, checks expiry (`exp`) and not-before (`nbf`) claims, then grants or denies access.

This stateless model eliminates server-side session storage, enabling horizontal scaling. **Sources:** [2] [4] [5]

### Signing Algorithms

JWT supports two families of algorithms:
- **HMAC (symmetric):** HS256, HS384, HS512 — same secret signs and verifies; simple but requires secure secret sharing.
- **RSA/ECDSA (asymmetric):** RS256, RS384, PS256, ES256 — private key signs, public key verifies; preferred for distributed systems where multiple services verify tokens without access to the signing secret.

The IETF recommends RS256 or ES256 for new systems. HS256 is acceptable only when the signing secret is long (≥256-bit), random, and never shared with resource servers. **Sources:** [3] [6] [7]

### Common JWT Security Pitfalls

**Pitfall 1: The "alg:none" Attack (CVE-2015-9235)**
The JWT spec originally allowed `"alg": "none"` to indicate an unsigned token. Vulnerable libraries accepted these tokens as valid, allowing attackers to forge arbitrary claims. Fix: explicitly whitelist accepted algorithms server-side; never accept "none". **Sources:** [8] [9]

**Pitfall 2: Algorithm Confusion (RS256 → HS256 Downgrade)**
If a server accepts both RS256 and HS256, an attacker can forge a HS256 token signed with the server's *public key* (which is not secret). The server, expecting HS256, verifies with the public key and accepts the forged token. Fix: pin the expected algorithm in server configuration, never derive it from the token header. **Sources:** [8] [10] [11]

**Pitfall 3: Weak or Guessable Secrets**
HS256 secrets shorter than 256 bits are vulnerable to brute-force and dictionary attacks. Real-world breaches have been caused by default secrets like "secret", "password", or demo credentials left in production. Tools like `jwt-tool` and `hashcat` can crack weak secrets. Fix: use a cryptographically random secret of at least 32 bytes. **Sources:** [9] [12]

**Pitfall 4: Missing or Ignored Signature Verification**
Some SDK versions and custom implementations have shipped with signature verification disabled or optional. Without verification, any forged token is accepted. Fix: always verify signatures; use well-maintained libraries (e.g., `python-jose`, `jsonwebtoken` for Node.js, `java-jwt` for Java). **Sources:** [8] [11]

**Pitfall 5: No Expiry or Overly Long Expiry**
Tokens without an `exp` claim never expire; stolen tokens remain valid indefinitely. Long-lived tokens (days/weeks) increase the window of opportunity for abuse. Fix: set short `exp` windows (15-60 minutes for access tokens), use refresh tokens for long sessions, implement token revocation via short-lived blacklists or rotating secrets. **Sources:** [4] [5] [13]

**Pitfall 6: Insecure Token Storage**
localStorage is accessible to JavaScript and therefore vulnerable to XSS attacks — a single injected script can exfiltrate all stored tokens. HttpOnly cookies prevent JavaScript access and are the recommended storage mechanism. Memory storage (React state) is safest but loses tokens on page reload. Fix: store JWTs in HttpOnly, Secure, SameSite=Strict cookies. **Sources:** [5] [13] [14]

**Pitfall 7: Sensitive Data in Payload**
The JWT payload is Base64URL-encoded, not encrypted. Any party with the token can decode the payload. Storing PII, roles, or secrets in unencrypted JWTs risks exposure. Fix: avoid sensitive claims in standard JWTs; use JWE (JSON Web Encryption, RFC 7516) when payload confidentiality is required. **Sources:** [2] [6]

## Cross-References and Contradictions

There is strong consensus across IETF RFCs, OWASP guidance, and security researchers on the core mechanics of JWT: all sources agree on the three-part structure, the role of the signature for integrity, and the stateless nature of JWT-based authentication. The OWASP Top 10 (2021), auth0 documentation, and academic treatments such as those published on PortSwigger Web Academy all converge on the same fundamental flow and the same critical recommendation: server-side algorithm pinning is non-negotiable. No credible source argues for accepting the "alg" field from a client-supplied token without server-side whitelisting.

A notable tension exists between convenience and security in token storage recommendations. Earlier guidance from JWT.io and some framework documentation (pre-2020) suggested localStorage as a simple default, whereas current OWASP guidance and the Mozilla Developer Network explicitly warn against it due to XSS risk, instead recommending HttpOnly cookies. This represents an evolution in community thinking rather than a genuine disagreement: the move from localStorage to HttpOnly cookies reflects accumulated real-world incident data. Some practitioners still advocate for in-memory storage as an alternative middle ground, but this approach lacks persistence across page reloads and is considered impractical for most user-facing applications.

There is genuine debate in the security community about refresh token strategies. Some sources (Auth0, Okta) recommend sliding-window refresh tokens with rotation to balance usability and security, while others (the OAuth Security BCP, RFC 9700) caution that refresh token rotation can itself introduce vulnerabilities if revocation infrastructure is not robust. The RFC 9700 Best Current Practice explicitly notes that refresh tokens must be sender-constrained or one-time-use to prevent replay attacks — a nuance absent from many tutorials and SDK default configurations. This gap between SDK defaults and the current security BCP is a meaningful source of residual risk in production systems.

## Conclusions

- JWT tokens use a signed Header.Payload.Signature structure that enables stateless, scalable authentication; the signature is the sole integrity guarantee and must always be verified server-side.
- Algorithm confusion and the alg:none attack are the highest-severity JWT vulnerabilities; mitigation requires pinning the expected algorithm in server configuration and never trusting the token header's alg field.
- HS256 is only safe with secrets of 32+ cryptographically random bytes; RS256 or ES256 are preferred for multi-service architectures where verifying services should not hold the signing secret.
- Access tokens should have short expiry windows (15-60 minutes); long-lived sessions require refresh token rotation with robust revocation, following RFC 9700 guidance rather than SDK defaults.
- Store JWTs in HttpOnly, Secure, SameSite=Strict cookies to prevent XSS exfiltration; never use localStorage for tokens in applications handling sensitive data.

## Bibliography

[1] RFC 7519 - JSON Web Token (JWT) - IETF - https://datatracker.ietf.org/doc/html/rfc7519
[2] Introduction to JSON Web Tokens - JWT.io - https://jwt.io/introduction
[3] RFC 7518 - JSON Web Algorithms (JWA) - IETF - https://datatracker.ietf.org/doc/html/rfc7518
[4] OAuth 2.0 Token Best Practices - IETF RFC 9700 - https://datatracker.ietf.org/doc/html/rfc9700
[5] OWASP Authentication Cheat Sheet - OWASP Foundation - https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
[6] OWASP JSON Web Token Cheat Sheet - OWASP Foundation - https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
[7] RFC 7517 - JSON Web Key (JWK) - IETF - https://datatracker.ietf.org/doc/html/rfc7517
[8] PortSwigger Web Security Academy - JWT Attacks - https://portswigger.net/web-security/jwt
[9] Critical vulnerabilities in JSON Web Token libraries - Auth0 Blog - https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
[10] JWT Algorithm Confusion Attacks - PortSwigger Research - https://portswigger.net/research/jwt-algorithm-confusion-attacks
[11] Common JWT Security Vulnerabilities - SANS Internet Storm Center - https://isc.sans.edu/diary/Common+JWT+Security+Vulnerabilities/29156
[12] JWT Security Best Practices - Okta Developer Blog - https://developer.okta.com/blog/2018/06/20/what-happens-if-your-jwt-is-stolen
[13] Where to Store JWTs - Cookies vs HTML5 Web Storage - Stormpath/Okta - https://developer.okta.com/blog/2022/07/08/spa-web-security-csrf-xss
[14] Using HTTP cookies - MDN Web Docs - Mozilla - https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies


---
*Research conducted by stepwise-research multi-agent system*
*Generated: 2026-04-26 21:00:31 CEST*
