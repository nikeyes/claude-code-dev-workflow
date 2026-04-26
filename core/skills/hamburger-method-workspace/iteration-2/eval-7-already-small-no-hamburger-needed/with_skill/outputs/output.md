# Hamburger Method Assessment: Copy to Clipboard Button

## Task

> Add a 'copy to clipboard' button to the API key display on the settings page

## Assessment: Hamburger Method NOT Applicable

This task does **not** qualify for the Hamburger Method.

The skill's own criteria states:

> **Do NOT use when:**
> - Feature is already small (< 1 day work)

Adding a "copy to clipboard" button is a single, self-contained UI change. It involves:

1. Rendering a button next to the API key field
2. Wiring a click handler that calls `navigator.clipboard.writeText(apiKey)`
3. Optionally showing brief feedback (e.g. "Copied!")

This is a straightforward front-end task estimable at 1–3 hours, well under the 1-day threshold. Applying the Hamburger Method would produce artificial layers and options for something that has no meaningful decomposition.

## Recommendation

Implement directly without slicing. A simple, complete implementation:

- Render a "Copy" button adjacent to the API key display
- On click, copy the key value to the clipboard using the Clipboard API
- Show a transient "Copied!" confirmation for ~2 seconds
- Handle the case where Clipboard API is not available (fallback: `document.execCommand('copy')` or a tooltip instructing manual copy)

No incremental delivery is needed — the feature is either present or not, and the full version is buildable in a single session.

## Self-Check Outcome

- [ ] Feature is large (3+ days) — **FAIL**: this is ~1–3 hours
- Because the "feature is already small" condition is met, the skill correctly does not apply here.

**Conclusion: Use the Hamburger Method only for features that genuinely require layered decomposition. This task does not.**
