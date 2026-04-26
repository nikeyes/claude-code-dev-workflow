# JWT Authentication: How It Works and Common Security Pitfalls

## How JWT Works

JSON Web Tokens (JWT) are a compact, URL-safe means of representing claims to be transferred between two parties. They are defined in RFC 7519 and widely used for authentication and authorization in web applications.

### Structure

A JWT consists of three Base64URL-encoded parts separated by dots:

```
header.payload.signature
```

**Header**

The header is a JSON object that typically declares the token type (`typ: "JWT"`) and the signing algorithm (`alg`), such as `HS256` (HMAC-SHA256) or `RS256` (RSA-SHA256):

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload**

The payload contains *claims* — statements about an entity (typically the user) and additional metadata. Standard registered claims include:

- `iss` (issuer): who issued the token
- `sub` (subject): the principal the token refers to (e.g., user ID)
- `aud` (audience): the intended recipients
- `exp` (expiration time): when the token expires (Unix timestamp)
- `iat` (issued at): when the token was issued
- `nbf` (not before): earliest time the token is valid

Applications can also include custom (private) claims:

```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "role": "admin",
  "iat": 1516239022,
  "exp": 1516242622
}
```

**Signature**

The signature is computed over the encoded header and payload using a secret (symmetric) or private key (asymmetric):

```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

The signature ensures the token has not been tampered with. It does NOT encrypt the payload — claims are readable by anyone who holds the token. Sensitive data should never be placed in JWT payloads without additional encryption (JWE).

### Authentication Flow

1. The client sends credentials (e.g., username + password) to the authentication server.
2. The server validates the credentials, creates a JWT signed with its secret or private key, and returns it to the client.
3. The client stores the token (typically in memory, `localStorage`, or a cookie) and includes it in subsequent requests, usually in the `Authorization` header: `Authorization: Bearer <token>`.
4. The resource server receives the request, validates the JWT signature and claims (`exp`, `iss`, `aud`), and grants or denies access based on the token's contents.
5. No server-side session state is required — the token is self-contained.

### Symmetric vs. Asymmetric Signing

- **Symmetric (HS256, HS384, HS512):** Both issuer and verifier share the same secret. Simple but requires the secret to be known to every service that needs to verify tokens.
- **Asymmetric (RS256, RS384, RS512, ES256, etc.):** The issuer signs with a private key; verifiers use the corresponding public key. Allows tokens to be verified without sharing secrets — better for distributed systems.

---

## Common Security Pitfalls

### 1. Algorithm Confusion / "alg: none" Attack

Early JWT libraries accepted the `"alg": "none"` header value, meaning no signature was required. An attacker could strip the signature, set `alg` to `none`, and forge arbitrary claims. Libraries must explicitly reject `none` as an algorithm and must enforce a whitelist of accepted algorithms.

**RS256 → HS256 Confusion:** If a server accepts both RSA and HMAC algorithms and a library uses the public RSA key as the HMAC secret when `alg` is switched to HS256, an attacker who knows the public key (which is public) can forge tokens. Always pin the expected algorithm server-side.

### 2. Weak or Exposed Secrets

For HS256 tokens, a short or guessable secret allows offline brute-force attacks. A captured JWT can be cracked with tools such as `hashcat` or `jwt_tool` without any interaction with the server. Secrets must be cryptographically random and sufficiently long (at least 256 bits for HS256).

### 3. Missing or Incorrect Claim Validation

Servers must validate:

- **`exp`:** Reject expired tokens. Failing to check expiry means stolen tokens remain valid indefinitely.
- **`iss`:** Ensure the token was issued by a trusted issuer. Cross-service token replay becomes possible otherwise.
- **`aud`:** Verify the token is intended for this service. A token issued for Service A can be replayed against Service B if audience is not checked.
- **`nbf`:** Respect the "not before" constraint.

Omitting any of these checks can allow token replay, cross-service abuse, or use of stale credentials.

### 4. Storing JWTs in localStorage

Tokens stored in `localStorage` or `sessionStorage` are accessible to JavaScript, making them vulnerable to Cross-Site Scripting (XSS) attacks. A single XSS vulnerability on the page can drain all stored tokens. Storing access tokens in memory and refresh tokens in `HttpOnly`, `Secure`, `SameSite=Strict` cookies is a safer pattern.

### 5. No Token Revocation / Logout Strategy

JWTs are stateless and valid until they expire. If a user logs out, their token cannot be "invalidated" unless the server maintains a denylist (blocklist) or uses short-lived tokens with a refresh token rotation strategy. Long-lived JWTs without a revocation mechanism pose a significant risk if tokens are stolen.

### 6. Long Token Lifetimes

Setting `exp` far in the future (e.g., 30 days) gives attackers a wide window to exploit a stolen token. Short-lived access tokens (5–15 minutes) combined with refresh tokens reduce exposure. Refresh tokens themselves should be rotated and stored securely.

### 7. Sensitive Data in Payload

Because the payload is only Base64URL-encoded (not encrypted), it is trivially readable by anyone who holds the token. PII, passwords, financial data, or any confidential information must not be placed in a JWT payload. Use JWE (JSON Web Encryption, RFC 7516) if confidentiality of claims is required.

### 8. Cross-Site Request Forgery (CSRF) with Cookie-Stored JWTs

If a JWT is stored in a cookie, CSRF attacks may be possible unless `SameSite` cookie attributes are set appropriately (`SameSite=Strict` or `SameSite=Lax`) and/or a CSRF token is used.

### 9. Key Management and Rotation

Failure to rotate signing keys means a compromised key permanently undermines trust in all tokens. Systems should support key rotation with a JWKS (JSON Web Key Set) endpoint, allowing verifiers to fetch current public keys by `kid` (key ID) from the token header.

### 10. JWT Header Injection (kid, jku, x5u)

Some JWT implementations honor header parameters like `kid` (key ID), `jku` (JWK Set URL), or `x5u` (X.509 URL) to dynamically fetch the verification key. An attacker can manipulate these to point to an attacker-controlled key source. Implementations must:

- Validate `jku`/`x5u` against a strict allowlist of trusted URLs.
- Sanitize `kid` values to prevent SQL/command injection if they are used to look up keys from a database.

---

## Summary Table

| Pitfall | Risk | Mitigation |
|---|---|---|
| `alg: none` | Signature bypass | Whitelist accepted algorithms |
| Algorithm confusion (RS256→HS256) | Token forgery | Pin expected algorithm server-side |
| Weak secret | Offline brute force | Use 256-bit+ random secrets |
| Missing claim validation | Token replay, cross-service abuse | Always validate `exp`, `iss`, `aud` |
| localStorage storage | XSS token theft | Use `HttpOnly` cookies or memory |
| No revocation | Stolen tokens remain valid | Short-lived tokens + refresh rotation |
| Sensitive data in payload | PII exposure | Never put secrets/PII in payload |
| CSRF with cookies | Unauthorized requests | `SameSite` cookies + CSRF tokens |
| Poor key management | Permanent compromise | JWKS endpoint + key rotation |
| Header injection (kid, jku) | Key substitution | Strict allowlists + input sanitization |

---

## Bibliography

The following sources informed this report (drawn from training knowledge):

1. **RFC 7519 — JSON Web Token (JWT)**. Jones, M., Bradley, J., Sakimura, N. (2015). Internet Engineering Task Force. https://datatracker.ietf.org/doc/html/rfc7519

2. **RFC 7515 — JSON Web Signature (JWS)**. Jones, M., Bradley, J., Sakimura, N. (2015). Internet Engineering Task Force. https://datatracker.ietf.org/doc/html/rfc7515

3. **RFC 7516 — JSON Web Encryption (JWE)**. Jones, M., Hildebrand, J. (2015). Internet Engineering Task Force. https://datatracker.ietf.org/doc/html/rfc7516

4. **RFC 7517 — JSON Web Key (JWK)**. Jones, M. (2015). Internet Engineering Task Force. https://datatracker.ietf.org/doc/html/rfc7517

5. **"Critical vulnerabilities in JSON Web Token libraries"**. Tim McLean (2015). Auth0 Security Blog. Describes the `alg: none` and RS256/HS256 confusion vulnerabilities. https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/

6. **OWASP JSON Web Token Cheat Sheet**. OWASP Foundation. https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html

7. **"JWT Security Best Practices"**. Curity Identity Server Documentation. https://curity.io/resources/learn/jwt-best-practices/

8. **"Stop using JWT for sessions"**. Jochen Mader / various authors. Describes statelessness pitfalls and revocation challenges. Referenced widely in web security communities.

9. **NIST SP 800-63B — Digital Identity Guidelines: Authentication and Lifecycle Management**. National Institute of Standards and Technology (2017). https://pages.nist.gov/800-63-3/sp800-63b.html

10. **PortSwigger Web Security Academy — JWT Attacks**. PortSwigger. Practical attack demonstrations including `alg: none`, algorithm confusion, and `kid` injection. https://portswigger.net/web-security/jwt
