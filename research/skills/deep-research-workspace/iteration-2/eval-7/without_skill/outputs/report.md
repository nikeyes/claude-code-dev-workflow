# HTTP 404: Not Found

HTTP 404 is an HTTP status code meaning **"Not Found"**. It is returned by a web server when the requested resource does not exist at the specified URL.

## What It Means

When a client (browser, API consumer, etc.) sends a request to a server for a specific URL, and the server cannot find anything at that location, it responds with a 404 status code. This is part of the HTTP/1.1 standard (RFC 7231).

- **4xx range**: Client-side errors — the problem is with the request, not the server.
- **404 specifically**: The resource was not found. The server is reachable and understood the request; it simply has nothing at that path.

## Common Causes

- Mistyped URL
- Page or resource has been deleted
- Broken or outdated link
- Content moved without a redirect in place
- The resource never existed

## 404 vs Related Codes

| Code | Meaning |
|------|---------|
| 404  | Not Found — resource doesn't exist at this URL |
| 410  | Gone — resource existed but was permanently removed |
| 403  | Forbidden — resource exists but access is denied |
| 401  | Unauthorized — authentication required |
| 301/302 | Redirect — resource has moved |

## For Developers

- Return 404 when a resource genuinely doesn't exist (e.g., `/users/9999` where user 9999 is not in the database).
- Distinguish from 410 (Gone) when the resource previously existed and will not return.
- Avoid returning 200 with an error body ("soft 404") — this confuses clients and search engines.

## Summary

HTTP 404 is one of the most common and well-understood HTTP responses. It simply means: "I looked, and there's nothing here." No research report is warranted — this is stable, well-documented knowledge in the HTTP specification.
