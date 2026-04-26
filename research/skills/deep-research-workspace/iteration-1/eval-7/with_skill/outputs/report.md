---
title: Research on HTTP 404
date: 2026-04-26
query: What does HTTP 404 mean?
keywords: HTTP, 404, Not Found, status code, client error, 4xx, broken link
status: complete
agent_count: 1
source_count: 2
---

# Research on HTTP 404

## Executive Summary

HTTP 404 ("Not Found") is a client error response status code indicating that the server cannot find the requested resource. It is part of the 4xx class of HTTP responses, which signal that the client has made a request that cannot be fulfilled. The 404 status does not distinguish between a resource being temporarily or permanently unavailable; for permanent removal, the 410 Gone status is preferred.

## Detailed Findings

### Definition and Meaning

HTTP 404 Not Found is a standard response code defined in RFC 9110 (HTTP Semantics). When a server returns this code, it means the resource at the requested URL cannot be located. The server understood the request but simply has no matching resource to serve.

Key points:
- 404 is a **client error** (4xx range), meaning the problem originates from the client's request (usually a wrong or outdated URL) [1]
- The status does not indicate whether the absence is temporary or permanent [1]
- For resources that have been permanently removed, servers should use **410 Gone** instead [1]

### Common Causes

- Mistyped URLs entered by the user
- Pages moved or deleted without setting up a redirect
- Broken internal or external links (sometimes called "dead links") [1]

### Best Practices

- Minimize broken links to avoid poor user experience
- Create custom, helpful 404 pages that guide users back to working content
- Use HTTP redirects (301/302) when content has moved rather than returning 404s [1]

## Cross-References and Contradictions

Both MDN Web Docs and RFC 9110 agree on the core definition: 404 signals a missing resource at a client-requested URL. There are no contradictions across sources. The only nuance is the recommendation to use 410 for permanently removed resources, which is a refinement rather than a contradiction.

## Conclusions

- HTTP 404 means the server cannot find the requested resource.
- It is a client-side error in the 4xx range.
- It does not specify whether the absence is temporary or permanent.
- 410 Gone is the more precise status for permanently deleted resources.
- Good practice is to redirect moved content and provide helpful custom 404 pages.

## Bibliography

[1] MDN Web Docs - HTTP 404 Not Found - https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
[2] RFC 9110 - HTTP Semantics, Section 15.5.5 - https://www.rfc-editor.org/rfc/rfc9110#section-15.5.5

---
*Research conducted by stepwise-research multi-agent system*
*Generated: 2026-04-26*
