# JWT Authentication: How It Works and Common Security Pitfalls

**Date**: 2026-04-26
**Research method**: Training data synthesis (no external sources consulted)

---

## Executive Summary

JSON Web Tokens (JWTs) are a compact, URL-safe means of representing claims between two parties. They are widely used for authentication and authorization in modern web applications and APIs. While JWTs offer real advantages—statelessness, portability, and self-contained claims—they also introduce a broad attack surface when misused. This report explains the mechanics of JWT authentication, then catalogues the most common and consequential security pitfalls encountered in production systems.

---

## 1. What Is a JWT?

A JSON Web Token is defined by RFC 7519. It is a base64url-encoded string composed of three dot-separated parts:

```
header.payload.signature
```

### 1.1 Header

The header is a JSON object that declares the token type and the signing algorithm:

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### 1.2 Payload

The payload carries **claims**—statements about the subject and additional metadata:

```json
{
  "sub": "user_42",
  "iss": "https://auth.example.com",
  "aud": "https://api.example.com",
  "iat": 1714089600,
  "exp": 1714093200,
  "roles": ["admin"]
}
```

Standard (registered) claims include:

| Claim | Meaning |
|-------|---------|
| `sub` | Subject – who the token refers to |
| `iss` | Issuer – who created the token |
| `aud` | Audience – who the token is intended for |
| `iat` | Issued-at timestamp |
| `exp` | Expiry timestamp |
| `nbf` | Not-before timestamp |
| `jti` | JWT ID – unique token identifier |

### 1.3 Signature

The signature proves the token has not been tampered with. For HMAC-based algorithms (e.g., HS256):

```
HMAC-SHA256(
  base64url(header) + "." + base64url(payload),
  secret
)
```

For RSA/EC-based algorithms (e.g., RS256, ES256), an asymmetric key pair is used: the private key signs, the public key verifies.

---

## 2. How JWT Authentication Works

### 2.1 The Basic Flow

1. **Login**: The client sends credentials (username/password, OAuth code, etc.) to the authentication server.
2. **Token issuance**: The server validates credentials, creates a JWT signed with its secret or private key, and returns it to the client.
3. **Subsequent requests**: The client attaches the JWT—typically in the `Authorization: Bearer <token>` header—on every request to protected resources.
4. **Token verification**: The resource server (or API gateway) verifies the JWT's signature, checks the expiry and other claims, and grants or denies access.

### 2.2 Stateless vs. Stateful Authentication

The key architectural difference from session-based auth is **statelessness**. The server does not store session state; all necessary information is embedded in the token itself. This makes JWTs attractive for:

- Horizontally scaled APIs (no shared session store needed)
- Microservices (a service can verify a token without calling back to an auth server)
- Cross-domain scenarios (tokens work across origins)

### 2.3 Token Refresh Pattern

Because JWTs cannot be invalidated once issued (until they expire), a common pattern pairs short-lived **access tokens** with longer-lived **refresh tokens**:

- Access token: expires in minutes (e.g., 15 min)
- Refresh token: expires in days/weeks, stored securely server-side

When the access token expires, the client uses the refresh token to obtain a new access token. The refresh token can be revoked (stored in a database), restoring some invalidation capability.

---

## 3. Common Security Pitfalls

### 3.1 The `alg: none` Attack

**Severity**: Critical

The JWT specification allows `"alg": "none"` to indicate an unsigned token. Some early library implementations accepted this at face value, skipping signature verification entirely. An attacker could forge any payload by:

1. Crafting a header with `"alg": "none"`
2. Writing an arbitrary payload (e.g., `"roles": ["superadmin"]`)
3. Omitting the signature

**Mitigation**: Always explicitly specify which algorithms are accepted. Never allow `none`. Most modern libraries have patched this, but explicit allowlisting remains best practice:

```python
# Python example (PyJWT)
jwt.decode(token, key, algorithms=["HS256"])  # explicit allowlist
```

---

### 3.2 Algorithm Confusion (RS256 → HS256 Confusion Attack)

**Severity**: Critical

When a server uses RS256 (asymmetric), the public key is—by definition—public. A vulnerable library that accepts both RS256 and HS256 can be exploited: an attacker signs a token with HS256 using the *server's public key* as the HMAC secret. If the server naively uses the key material to verify whatever algorithm the header claims, it will successfully verify the forged token.

**Mitigation**:
- Restrict accepted algorithms server-side; never let the client dictate the algorithm.
- Use separate key management objects per algorithm.

---

### 3.3 Weak or Hardcoded Secrets

**Severity**: High

HS256 security depends entirely on the entropy and secrecy of the HMAC secret. Common failures:

- Using a short or guessable secret (`"secret"`, `"password"`, the app name)
- Hardcoding the secret in source code (it ends up in version control)
- Reusing the same secret across environments

An attacker who obtains the secret can mint arbitrary valid tokens.

**Mitigation**:
- Use at least 256 bits of cryptographically random secret material for HS256.
- Store secrets in environment variables or a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.).
- Rotate secrets periodically and have a rotation plan.
- Prefer RS256/ES256 for multi-audience scenarios—compromise of one service's private key does not affect others.

---

### 3.4 Missing or Improper Claims Validation

**Severity**: High

Generating a properly signed JWT is only half the job; the receiver must validate all relevant claims. Common omissions:

| Missing check | Consequence |
|--------------|-------------|
| `exp` not checked | Expired tokens remain valid indefinitely |
| `iss` not checked | Tokens from foreign issuers accepted |
| `aud` not checked | Token intended for service A accepted by service B |
| `nbf` not checked | Tokens used before their intended start time |

**Mitigation**: Validate every claim that matters for your threat model. Most JWT libraries provide options to enforce these checks.

---

### 3.5 Token Storage on the Client

**Severity**: Medium–High

Where the client stores the JWT determines its exposure to theft:

| Storage location | XSS risk | CSRF risk | Notes |
|-----------------|----------|-----------|-------|
| `localStorage` | High | None | XSS can steal the token directly |
| `sessionStorage` | High | None | Same as localStorage, clears on tab close |
| Memory (JS variable) | Low | None | Lost on page refresh; complex to implement |
| HttpOnly cookie | None | Medium | Immune to XSS; CSRF protection required |

**Mitigation**: Store tokens in HttpOnly, Secure, SameSite=Strict/Lax cookies to prevent XSS-based token theft. Combine with CSRF tokens or SameSite cookies to prevent CSRF.

---

### 3.6 Lack of Token Revocation

**Severity**: Medium–High

Because JWTs are stateless, there is no built-in way to revoke a token before it expires. This becomes a problem when:

- A user logs out but their token remains valid
- An account is compromised and the token must be invalidated immediately
- Permissions change (e.g., a user is demoted) but the token still carries old roles

**Mitigation strategies**:

1. **Short expiry** (15 minutes or less) limits the window of abuse.
2. **Token blocklist** (denylist): Store revoked `jti` values in Redis or a database; check on every request. Sacrifices full statelessness.
3. **Refresh token rotation**: Issue single-use refresh tokens; revoke on suspicious reuse (refresh token reuse detection).
4. **Version claims**: Store a `tokenVersion` counter per user; increment on logout/compromise; reject tokens with outdated versions.

---

### 3.7 Sensitive Data in the Payload

**Severity**: Medium

The payload is base64url-encoded, not encrypted. Anyone who possesses the token can decode it and read all claims.

**Mitigation**:
- Do not include PII, passwords, API keys, or other secrets in the payload.
- If sensitive claims are unavoidable, use JSON Web Encryption (JWE) instead of plain JWTs.

---

### 3.8 Insufficient Token Expiry

**Severity**: Medium

Long-lived tokens (hours, days) extend the window during which a stolen token can be abused.

**Mitigation**: Use short access token lifetimes (15 minutes is a common recommendation) paired with a secure refresh token mechanism.

---

### 3.9 JWT Header Injection / `kid` Manipulation

**Severity**: High

The `kid` (key ID) header parameter is used to hint which key to use for verification. Vulnerable implementations may:

- **SQL injection via `kid`**: If the server constructs a database query from the `kid` value to retrieve the key, an attacker can inject SQL.
- **Path traversal via `kid`**: If the server reads a key from the filesystem using the `kid` value, an attacker might supply `kid: "../../dev/null"`, causing the server to use an empty string as the key—then sign a token with an empty string.
- **JWKS URI injection**: Some systems fetch the public key from a URL embedded in the token header (`jku` or `x5u` parameter). An attacker can point this to a controlled server hosting a malicious public key.

**Mitigation**:
- Treat `kid` and any URL-based header parameters as untrusted input; validate against an allowlist.
- Fetch JWKs only from a pre-configured, trusted endpoint, never from the token itself.

---

### 3.10 Replay Attacks

**Severity**: Medium

A stolen token can be replayed until it expires.

**Mitigation**:
- Use short expiry.
- For high-value operations, include a `jti` (JWT ID) and track used IDs server-side to prevent reuse.
- Bind tokens to TLS channel (token binding, experimental) or IP/device fingerprint (with trade-offs for mobile clients).

---

### 3.11 Library Vulnerabilities and Outdated Implementations

**Severity**: Varies

JWT library bugs have historically been severe (the `alg: none` and algorithm confusion issues were library-level flaws). Using unmaintained or outdated libraries exposes applications to known CVEs.

**Mitigation**:
- Use well-maintained, widely-audited libraries.
- Keep dependencies updated.
- Review library changelogs for security-relevant releases.
- Prefer libraries with explicit algorithm allowlisting APIs.

---

## 4. Best Practices Summary

| Category | Recommendation |
|----------|---------------|
| Algorithm | Use RS256 or ES256 for multi-party systems; HS256 only when you fully control both issuer and verifier. Allowlist algorithms explicitly. |
| Secret management | 256-bit+ random secrets; stored in secrets manager; rotated regularly. |
| Claims validation | Always validate `exp`, `iss`, `aud`. Set appropriate `nbf` and short `exp`. |
| Token lifetime | Access tokens: 15 minutes. Refresh tokens: days, stored securely server-side. |
| Storage | HttpOnly, Secure, SameSite cookies preferred over localStorage. |
| Revocation | Blocklist for immediate revocation needs; refresh token rotation. |
| Payload content | No PII or secrets; use JWE if encryption needed. |
| Header parameters | Ignore or strictly validate `kid`, `jku`, `x5u`, `jwk` header parameters. |
| Libraries | Use audited, actively maintained libraries; pin versions; monitor CVEs. |
| Transport | Always use TLS; never transmit JWTs over plain HTTP. |

---

## 5. JWT vs. Alternatives

| Mechanism | Stateless | Revocable | Complexity | Best for |
|-----------|-----------|-----------|------------|----------|
| Session cookies | No | Yes | Low | Traditional web apps |
| JWT | Yes | Hard | Medium | APIs, microservices |
| Opaque tokens | No | Yes | Medium | When revocation is critical |
| PASETO | Yes | Hard | Medium | JWT replacement with safer defaults |

PASETO (Platform-Agnostic Security Tokens) is worth noting as a JWT alternative designed to eliminate many of the footguns described above by removing algorithm agility—each version has one fixed algorithm.

---

## 6. Conclusion

JWT authentication is a powerful and widely-adopted pattern, but its flexibility is also its primary hazard. The most dangerous pitfalls—`alg: none`, algorithm confusion, and key confusion attacks—arise directly from the specification's permissiveness around algorithm selection. The statelessness that makes JWTs attractive also makes revocation inherently difficult.

Secure JWT usage requires disciplined implementation: explicit algorithm allowlisting, proper claims validation, short token lifetimes, secure storage, and regular library updates. For applications where immediate revocation or high-assurance identity is critical, supplementing JWTs with server-side state (blocklists, token versioning) or switching to opaque tokens may be the right trade-off.

---

## References

The following are authoritative sources on the topics covered. No live web searches were performed; these references are drawn from training knowledge.

- RFC 7519 – JSON Web Token (JWT): https://datatracker.ietf.org/doc/html/rfc7519
- RFC 7518 – JSON Web Algorithms (JWA): https://datatracker.ietf.org/doc/html/rfc7518
- RFC 7517 – JSON Web Key (JWK): https://datatracker.ietf.org/doc/html/rfc7517
- RFC 8725 – JSON Web Token Best Current Practices: https://datatracker.ietf.org/doc/html/rfc8725
- OWASP – JSON Web Token Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- PortSwigger Web Security Academy – JWT attacks: https://portswigger.net/web-security/jwt
- Auth0 Blog – Critical vulnerabilities in JWT libraries (2015): https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
- PASETO specification: https://paseto.io/
