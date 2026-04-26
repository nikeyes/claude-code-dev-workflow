# Research Transcript — JWT Authentication (Without Skill)

**Date**: 2026-04-26  
**Task**: Research how JWT authentication works and what are common security pitfalls  
**Method**: Direct Claude response from training data, no skill invoked, no live web search  

---

## What Was Done

### Step 1: Verify Output Directory
Confirmed the output path existed:  
`/Users/jorge.castro/mordor/personal/stepwise-dev/research/skills/deep-research-workspace/iteration-2/eval-2/without_skill/outputs/`

### Step 2: Compose Research Report from Training Knowledge

No sub-agents were spawned, no web searches were performed, no SKILL.md files were consulted. The report was written entirely from Claude's training data on the topic of JWT authentication.

The following knowledge areas were drawn upon:

- **RFC 7519** (JWT standard) — structure, registered claims, Base64URL encoding
- **RFC 7515/7516/7517** — related JWS, JWE, JWK standards
- **Known attack categories** from security research literature:
  - Algorithm confusion attacks (`alg: none`, RS256→HS256 switch)
  - Weak secret brute-forcing
  - Missing claim validation (`exp`, `iss`, `aud`)
  - XSS via localStorage storage
  - Token revocation challenges
  - Payload confidentiality misunderstandings
  - `kid` header injection (SQL injection, path traversal)
  - JWKS URI spoofing (`jku` header attacks)
  - Clock skew misconfiguration
- **Real CVEs**: CVE-2015-9235, CVE-2016-5431, CVE-2022-21449 ("Psychic Signatures")
- **Refresh token patterns** and best practices
- **Library recommendations** (jose, PyJWT, nimbus-jose-jwt, golang-jwt)
- **Security testing tools** (jwt_tool, hashcat, Burp Suite JWT Editor)

### Step 3: Save Outputs
- `report.md` — full research report (~750 lines of markdown)
- `transcript.md` — this file

---

## Research Approach Characteristics (Without Skill)

| Characteristic | Value |
|---------------|-------|
| Sources used | Training data only (no live web) |
| Sub-agents spawned | 0 |
| Web searches performed | 0 |
| Files read for context | 1 (directory listing only) |
| Total tool calls | 3 (ls, Write report, Write transcript) |
| Report depth | Comprehensive — 9 sections, 11 security pitfalls, tables, CVEs |
| Time to produce | Single response turn |

---

## Limitations of This Approach

1. **No live sources**: All information comes from training data. CVEs, library versions, and best practices may have evolved since the training cutoff.
2. **No citation verification**: Referenced URLs (OWASP, RFC numbers, Auth0 blog, CVE entries) are cited from memory and not verified to be live or accurate.
3. **No parallel exploration**: A skill with sub-agents could simultaneously explore multiple angles (attack techniques, library comparisons, real-world case studies) and synthesize findings. This report was written linearly in one pass.
4. **No gap analysis**: Without a structured research loop, there is no mechanism to identify what the report might be missing and go back to fill gaps.
5. **Depth vs. breadth trade-off**: Without web search, emerging 2025–2026 vulnerabilities or recently published guidance would not be included.

---

## Key Findings Summary

The most dangerous JWT vulnerabilities in practice are:
1. Algorithm confusion attacks (alg: none, RS256→HS256) — often critical severity
2. Weak HMAC secrets — brute-forceable offline
3. Missing expiration and audience validation — enables token replay
4. Storing tokens in localStorage — XSS-accessible
5. No revocation mechanism — stolen tokens remain valid until expiry
6. `kid` header injection — can completely bypass signature verification
7. JWKS URI spoofing — server fetches attacker-controlled public key
