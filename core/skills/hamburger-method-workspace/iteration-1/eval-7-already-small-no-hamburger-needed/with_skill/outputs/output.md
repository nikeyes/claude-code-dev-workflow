# Hamburger Method Analysis: Add a 'copy to clipboard' button to the API key display on the settings page

## Skill Decision: Hamburger Method Not Applicable

The hamburger method is the wrong tool for this task.

**Reason:** This feature is already small — well under 1 day of work.

The skill explicitly states:

> **Do NOT use when:**
> - Feature is already small (< 1 day work)

---

## Why This Feature Is Already Small

Adding a "copy to clipboard" button to an existing API key display involves:

1. Adding a button element next to the existing API key field
2. Attaching a click handler that calls `navigator.clipboard.writeText(apiKey)`
3. Optionally showing a brief "Copied!" confirmation (tooltip or text swap)

This is a single-concern, single-location UI change. It touches:
- One component/template file (the settings page)
- Zero backend changes
- Zero new infrastructure
- Zero new dependencies (Clipboard API is native to all modern browsers)

Estimated effort: **1–3 hours**, including writing and testing.

---

## Recommendation

Do not apply the hamburger method. Implement this directly.

**Suggested implementation approach (straightforward, no slicing needed):**

1. Locate the settings page component where the API key is displayed
2. Add a "Copy" button (or icon button) adjacent to the API key field
3. On click, call `navigator.clipboard.writeText(apiKey)`
4. Show a brief visual confirmation ("Copied!" label or checkmark icon) that disappears after ~2 seconds
5. Handle the edge case where the Clipboard API is unavailable (fallback to `document.execCommand('copy')` or show a manual-copy prompt)

That's the complete implementation. It does not need layered analysis or incremental delivery planning.

---

## What to Use Instead

If you need help breaking this into safe implementation micro-steps (e.g., TDD-style), use the **small-safe-steps** skill instead.

If you want to explore test coverage for the button once built, use the **bugmagnet** skill.
