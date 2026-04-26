# Hamburger Method: Add a Search Feature to E-Commerce Site

Let's apply the Hamburger Method to slice this feature into deliverable vertical pieces.

---

## Layers Identified

The "search feature so users can find products" involves these functional layers:

1. **Accept search input** — how the user enters their query
2. **Match products** — how we find products that match the query
3. **Rank/filter results** — how results are ordered or narrowed
4. **Display results** — how matching products are shown to the user
5. **Handle no-results / errors** — what happens when nothing matches

---

## Options per Layer

### Layer 1 — Accept Search Input

- 1.1: Add a plain HTML text input on an existing page (no JS, form POST)
- 1.2: Text input with a submit button, basic browser form submission
- 1.3: Search bar with real-time input (onChange triggers fetch)
- 1.4: Search bar with debounce and URL-based state (shareable links)
- 1.5: Full search experience with autocomplete suggestions, filters, and keyboard navigation

### Layer 2 — Match Products

- 2.1: Hardcode a list of 5-10 products; filter by `includes()` on the name string
- 2.2: Query the existing products table with `WHERE name LIKE '%query%'`
- 2.3: Full-text search using database built-in (e.g., PostgreSQL `tsvector`, MySQL `FULLTEXT`)
- 2.4: Dedicated search index (e.g., Elasticsearch, Typesense, Algolia)
- 2.5: AI/semantic search (vector embeddings + similarity matching)

### Layer 3 — Rank / Filter Results

- 3.1: No ranking — return results in DB insertion order
- 3.2: Sort alphabetically by product name
- 3.3: Sort by relevance score (basic: exact match first, then partial)
- 3.4: Sort by relevance + business rules (stock, margin, promotions)
- 3.5: Personalized ranking based on user history and behavior

### Layer 4 — Display Results

- 4.1: Plain unordered list of product names with links
- 4.2: Simple product cards (name, price, thumbnail)
- 4.3: Paginated results grid with product cards
- 4.4: Infinite scroll or "load more" with skeleton loading states
- 4.5: Rich results with filters sidebar, facets, sorting controls, highlighted match terms

### Layer 5 — Handle No-Results / Errors

- 5.1: Show nothing (empty list, no message)
- 5.2: Display a plain text "No products found" message
- 5.3: Show "No results for X" with a suggestion to try different terms
- 5.4: No-results page with curated suggestions or popular products
- 5.5: Smart fallback: fuzzy matching, spelling corrections, or "did you mean?" suggestions

---

## Radical Slicing: Ship by Tomorrow

> **"If you had to ship something by tomorrow, what would you build?"**

**Smallest vertical slice:**

| Layer | Choice | Rationale |
|-------|--------|-----------|
| 1 — Input | **1.1**: Plain HTML text input, form POST | Zero JS, zero new infrastructure |
| 2 — Match | **2.2**: `WHERE name LIKE '%query%'` on existing products table | Uses existing DB, no new services |
| 3 — Rank | **3.1**: No ranking, return in DB order | No logic needed |
| 4 — Display | **4.1**: Plain list of product names + links | Renders in minutes |
| 5 — No-results | **5.2**: "No products found" plain text | Trivial to add |

**What this delivers:** A user types a word in a text box, submits the form, and sees a list of products whose names contain that word — or a "no products found" message. No JavaScript, no new infrastructure, no indexing service. Can be built and deployed in a few hours.

**Deployment risk:** Near zero. It's a new page/route, doesn't touch existing product pages. Fully reversible.

---

## Follow-up Slices

### Slice 2: Better UX input (no new backend work)
- Replace form POST with a fetch-based input (1.3)
- Keep everything else the same (2.2, 3.1, 4.1, 5.2)
- Goal: faster feedback loop for the user without page reload

### Slice 3: Useful results display
- Upgrade display to product cards with name, price, and thumbnail (4.2)
- Add "No results for X, try a different term" message (5.3)
- Keep matching and ranking the same (2.2, 3.1)
- Goal: results feel like a real shopping experience

### Slice 4: Smarter matching
- Upgrade to full-text search with DB built-in (2.3)
- Add basic relevance sorting — exact match first (3.3)
- Goal: better result quality without introducing external services

### Slice 5: Scale if needed
- Introduce Typesense or Algolia (2.4) when DB full-text search becomes a bottleneck
- Add filters sidebar (4.5) when catalog grows large enough to need narrowing
- This slice only makes sense after real user data shows the need

---

## Self-Check

- [x] Identified 5 clear functional layers (not "frontend/backend/DB")
- [x] Generated 5 options per layer following quality gradient (manual → enterprise)
- [x] Forced radical slicing ("ship by tomorrow" question applied)
- [x] Smallest slice uses level 1-2 options from each layer
- [x] Smallest slice delivers value to real users (they can actually search)
- [x] Smallest slice is deployable in hours, not days
- [x] Proposed 4 follow-up slices showing clear incremental improvement
- [x] No slice requires Redis, Kafka, Elasticsearch, or new infrastructure until Slice 5
