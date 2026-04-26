# HTTP 404: Not Found

## Definition

HTTP 404 is a standard HTTP response status code indicating that the server could not find the requested resource. It belongs to the 4xx class of client error responses.

## What It Means

When a client (browser, API consumer, etc.) makes a request to a server, and the server cannot locate the resource at the specified URL, it returns a 404 status code. The resource may:

- Never have existed at that URL
- Have been deleted or moved without a redirect
- Have a URL that was typed or constructed incorrectly

## Common Causes

- **Broken or mistyped URL** — the path contains a typo or incorrect segment
- **Deleted content** — a page or resource was removed from the server
- **Moved content without redirect** — the resource was relocated but no 301/302 redirect was set up
- **Case sensitivity** — on case-sensitive servers (e.g., Linux), `/Page.html` and `/page.html` are different URLs

## 404 vs. Related Codes

| Code | Meaning |
|------|---------|
| 404 | Resource not found (server cannot locate it) |
| 410 | Gone — resource existed but was permanently removed |
| 403 | Forbidden — resource exists but access is denied |
| 301 | Moved Permanently — resource has a new URL |

## Summary

HTTP 404 means "the thing you asked for doesn't exist here." It is one of the most common HTTP errors encountered in web browsing and API development.
