# Hamburger Method: Add "Copy to Clipboard" Button to API Key Display

## Feature Description

Add a "copy to clipboard" button to the API key display on the settings page, so users can copy their API key with one click instead of manually selecting and copying the text.

---

## Step 1: Identify Layers

Applying the Hamburger Method means slicing the feature horizontally across technical layers, then composing vertical slices that cut through all layers end-to-end.

### Layer Identification

| # | Layer | Description |
|---|-------|-------------|
| 1 | UI Component | The button element itself (icon, label, placement, styling) |
| 2 | Interaction / UX | Click behavior, feedback state (visual confirmation) |
| 3 | Clipboard API | Mechanism to write text to the system clipboard |
| 4 | State / Logic | What text to copy, masking logic (show full key vs. masked), where key is sourced from |
| 5 | Accessibility | Keyboard support, ARIA labels, screen reader announcements |
| 6 | Testing | Unit tests for copy logic, integration/E2E tests for the button |

---

## Step 2: Generate Implementation Options Per Layer

### Layer 1 — UI Component (Button)

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Icon-only button (clipboard SVG icon, no text label) | Minimal space, requires tooltip or ARIA label for clarity |
| B | Icon + text label ("Copy" beside the icon) | Clear intent, takes more space |
| C | Inline text link ("Copy to clipboard") | Familiar pattern, no icon dependency |
| D | Button appended after masked key display (e.g., `sk-••••••••  [Copy]`) | Standard placement next to input/display field |
| E | Context menu option (right-click "Copy API Key") | Less discoverable, not mobile-friendly |

**Recommended**: Option D (or A with tooltip) — icon-only button next to the key display is the established pattern (e.g., GitHub tokens, AWS secrets).

---

### Layer 2 — Interaction / UX (Feedback)

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | No feedback — silent copy | Simple, but user is not sure it worked |
| B | Button text/icon toggles to "Copied!" for 2 seconds, then reverts | Clear, lightweight, common pattern |
| C | Toast/snackbar notification at bottom of screen | More visible, but adds toast infrastructure if not already present |
| D | Tooltip that appears and fades ("Copied!") | Clean, self-contained, no extra infrastructure |
| E | Success border/color flash on the key display field | Subtle, low-noise |

**Recommended**: Option B — button state toggles to "Copied!" and reverts. Zero additional infrastructure, universally understood.

---

### Layer 3 — Clipboard API

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | `navigator.clipboard.writeText()` (async, modern) | Works in all modern browsers; requires HTTPS or localhost; returns a Promise |
| B | `document.execCommand('copy')` (legacy, synchronous) | Deprecated; works in older browsers; requires a selected text range |
| C | Clipboard API with fallback to execCommand | Maximum compatibility; adds complexity |
| D | Third-party library (e.g., `clipboard.js`) | Handles edge cases; adds a dependency |
| E | Copy via hidden `<input>` element + execCommand | Legacy pattern; verbose but reliable in older environments |

**Recommended**: Option A — `navigator.clipboard.writeText()`. Modern applications can safely assume HTTPS and modern browser support. If compatibility is a concern, add Option C as a thin wrapper.

---

### Layer 4 — State / Logic (What to Copy)

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Copy the full, unmasked API key from component state (key is already loaded) | Simplest; requires key to be in memory |
| B | Copy the masked display value (e.g., `sk-••••••1234`) | Useless; user cannot authenticate with a masked key — avoid |
| C | Re-fetch the API key from the server on button click, then copy | Adds a network call; only valid if key is never stored client-side for security reasons |
| D | Copy from a hidden, unmasked `<input value={apiKey}>` element already in the DOM | Avoids re-fetch; clipboard write is decoupled from display masking |
| E | Derive copy value from existing prop/context that holds the full key | Clean; same as A but via context API |

**Recommended**: Option A — copy from existing component state. The API key is already loaded to display it (even if masked), so the full value should be accessible in the component.

---

### Layer 5 — Accessibility

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | `aria-label="Copy API key to clipboard"` on the button | Minimal; screen readers announce the action |
| B | `aria-label` + `aria-live` region to announce "Copied!" to screen readers | Full experience for screen reader users |
| C | Keyboard focusable button (default for `<button>`) + visible focus ring | Required baseline; `<button>` handles this by default |
| D | `role="button"` on a `<div>` with manual keyboard handler | Avoid; use a native `<button>` instead |
| E | `title` attribute as tooltip (hover text) | Accessible but inconsistent across browsers; supplement with `aria-label` |

**Recommended**: Option B — `aria-label` on the button plus an `aria-live` region for the feedback announcement. This covers both interaction and confirmation for assistive technologies.

---

### Layer 6 — Testing

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Unit test: mock `navigator.clipboard.writeText`, simulate click, assert mock called with full key | Fast, isolated, reliable |
| B | Unit test for feedback state: after click, assert button shows "Copied!", after timeout assert reverted | Tests UX transition |
| C | Integration test: render settings page, click button, verify clipboard API called | Realistic; may require mocking clipboard in JSDOM |
| D | E2E test (Cypress/Playwright): navigate to settings, click button, verify clipboard content | Most realistic; clipboard E2E testing can be flaky across browsers |
| E | Snapshot test of the button component | Low value; brittle; avoid |

**Recommended**: Options A + B — two focused unit tests covering the copy logic and the feedback state. Add Option D only if E2E tests are already established in the project.

---

## Step 3: Compose Vertical Slices

A vertical slice must include something from every layer that is necessary to make the feature work end-to-end.

### Slice 1 — Minimal Viable Copy Button (Recommended Smallest Slice)

**Goal**: A working button that copies the API key and confirms success. No polish, no edge cases, no accessibility beyond baseline.

| Layer | Choice | What is implemented |
|-------|--------|---------------------|
| UI Component | Icon-only `<button>` next to API key display | One `<button>` element with a clipboard icon |
| Interaction / UX | Button text toggles to "Copied!" for 2 seconds | `useState` for `copied` flag, `setTimeout` to reset |
| Clipboard API | `navigator.clipboard.writeText(apiKey)` | Single async call |
| State / Logic | Copy from existing `apiKey` prop/state | No new data fetching |
| Accessibility | `aria-label="Copy API key"` on button | Minimum viable screen reader support |
| Testing | One unit test: click triggers clipboard write with correct value | Single `it()` block |

**Effort estimate**: 1–2 hours.
**Value delivered**: Full end-to-end feature. Users can click the button and get the API key in their clipboard immediately.

---

### Slice 2 — Polished Copy Button

**Adds on top of Slice 1:**
- Tooltip on hover ("Copy API key to clipboard")
- Toast notification instead of button-state feedback (if toast infrastructure exists)
- Full `aria-live` announcement for screen readers
- Unit test for the 2-second feedback reset

**Effort estimate**: 2–3 hours additional.

---

### Slice 3 — Hardened Copy Button

**Adds on top of Slice 2:**
- Fallback to `execCommand('copy')` for older browsers
- Error handling: if clipboard write fails, show an error state
- E2E test covering the full flow in a real browser

**Effort estimate**: 2–3 hours additional.

---

## Step 4: Proposed Smallest Vertical Slice

### Recommendation: Implement Slice 1 Only

**Rationale:**

The feature "add a copy to clipboard button to the API key display" is inherently a small, self-contained piece of UI. Applying the full Hamburger Method reveals that even the most complete version (Slice 3) is modest in scope. However, the smallest slice (Slice 1) already delivers 100% of the core user value:

- The user sees a button next to the API key.
- The user clicks it.
- The API key is copied to their clipboard.
- The button confirms success visually.

All additional polish (tooltips, toasts, fallback APIs, E2E tests) is optional enhancement, not necessary for the feature to work.

### Minimal Slice Implementation Plan

1. **Locate the API key display component** in the settings page (e.g., `ApiKeyDisplay.tsx` or `SettingsPage.tsx`).
2. **Add state**: `const [copied, setCopied] = useState(false)`.
3. **Add handler**:
   ```js
   const handleCopy = async () => {
     await navigator.clipboard.writeText(apiKey);
     setCopied(true);
     setTimeout(() => setCopied(false), 2000);
   };
   ```
4. **Add button** next to the key display:
   ```jsx
   <button onClick={handleCopy} aria-label="Copy API key">
     {copied ? 'Copied!' : <ClipboardIcon />}
   </button>
   ```
5. **Add one unit test**:
   ```js
   it('copies the API key to the clipboard when the button is clicked', async () => {
     const mockWriteText = jest.fn().mockResolvedValue(undefined);
     Object.assign(navigator, { clipboard: { writeText: mockWriteText } });
     render(<ApiKeyDisplay apiKey="sk-test-123" />);
     await userEvent.click(screen.getByRole('button', { name: /copy api key/i }));
     expect(mockWriteText).toHaveBeenCalledWith('sk-test-123');
   });
   ```

### Observation: Is the Hamburger Method Necessary Here?

The Hamburger Method is most valuable for features that span multiple subsystems or have genuinely uncertain scope. For this feature — a copy button on a single settings page component — the full slicing exercise reveals that the "smallest slice" is essentially the entire feature. The layers exist, but they are all trivially small.

**Conclusion**: This feature does not benefit meaningfully from hamburger slicing. It should be implemented directly as a single, small task. The Hamburger Method would add more overhead than value here.

---

## Summary

| Slice | Description | Effort | User Value |
|-------|-------------|--------|------------|
| Slice 1 (Minimal) | Working copy button with visual feedback | 1–2 h | Full core value |
| Slice 2 (Polished) | Tooltip, toast, full a11y, feedback test | +2–3 h | Improved UX |
| Slice 3 (Hardened) | Browser fallback, error handling, E2E tests | +2–3 h | Production robustness |

**Start with Slice 1.** It is the smallest unit that delivers complete end-to-end value to the user. Given the inherent simplicity of this feature, deeper hamburger slicing is not needed — ship the whole thing in one iteration.
