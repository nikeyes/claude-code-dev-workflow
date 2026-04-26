# Hamburger Method: Add Search Feature to E-Commerce Site

**Task:** Add a search feature to our e-commerce site so users can find products

---

## Step 1: Identify Layers

The complete flow for a product search feature involves these functional layers:

1. **Accept search input** — how the user enters a query
2. **Find matching products** — how the system locates relevant products
3. **Rank / filter results** — how results are ordered and refined
4. **Display results** — how matches are presented to the user
5. **Handle no results** — what happens when nothing matches

---

## Step 2: Options per Layer (4-5 each, manual → enterprise)

---

### Layer 1 — Accept search input

- **1.1** A plain HTML text input with a submit button (no JS, full page reload)
- **1.2** A styled search bar with a magnifying glass icon, still submits on Enter/click
- **1.3** Search bar with client-side debounce, submits after user stops typing (300 ms)
- **1.4** Autocomplete dropdown showing product name suggestions as user types
- **1.5** Voice/image search + autocomplete + recent/saved searches

---

### Layer 2 — Find matching products

- **2.1** Hardcoded list of 5 products returned for any query (fixture data)
- **2.2** SQL `LIKE '%query%'` on product name column only
- **2.3** SQL full-text search across name, description, and category fields
- **2.4** Dedicated search service (e.g., Elasticsearch / Typesense) with indexing
- **2.5** ML-powered semantic search (vector embeddings, intent understanding)

---

### Layer 3 — Rank / filter results

- **3.1** No ranking — return results in DB insertion order
- **3.2** Sort by relevance score (exact match first, then partial)
- **3.3** Sort by relevance + apply basic filters (category, price range)
- **3.4** Faceted filtering (multiple attributes) + configurable sort options
- **3.5** Personalized ranking based on user history and purchase behavior

---

### Layer 4 — Display results

- **4.1** Plain HTML list: product name + price only
- **4.2** Simple grid/list with product name, price, and thumbnail image
- **4.3** Card layout with name, image, price, rating, and "Add to Cart" button
- **4.4** Paginated results with infinite scroll option and highlighted query terms
- **4.5** Rich results with sponsored items, banners, A/B-tested layouts

---

### Layer 5 — Handle no results

- **5.1** Show a blank page (nothing rendered)
- **5.2** Show a static "No results found" text message
- **5.3** Show "No results found" + suggestions (e.g., "Try: shoes, bags")
- **5.4** Show "No results found" + recommended/popular products as fallback
- **5.5** Auto-correct typos, fuzzy match, and show intent-based alternatives

---

## Step 3: Force Radical Slicing

> **"If you had to ship something by tomorrow, what would you build?"**

Pick the lowest viable option from each layer:

| Layer | Pick | Description |
|---|---|---|
| 1 — Input | **1.1** | Plain HTML text input, full page reload on submit |
| 2 — Find products | **2.2** | SQL `LIKE '%query%'` on product name |
| 3 — Rank | **3.1** | No ranking, return in DB order |
| 4 — Display | **4.1** | Plain HTML list: name + price |
| 5 — No results | **5.2** | Static "No results found" message |

**This slice can be built and deployed in a few hours.** It requires no new infrastructure, no new services, and no JavaScript. A real user can type a query and see matching products. That is the entire value proposition validated.

---

## Step 4: Filter & Prioritize

Options eliminated for the first slice:
- Autocomplete (1.3–1.5): requires JS and additional API endpoints
- Full-text / search engine (2.3–2.5): requires schema changes or new services
- Faceted filtering (3.3–3.5): needs significant UI and query complexity
- Rich card layout (4.3–4.5): needs design work and extra data (images, ratings)
- Fuzzy matching / recommendations (5.3–5.5): needs extra logic and data

Options kept (fast, reversible, testable with real users):
- 1.1, 2.2, 3.1, 4.1, 5.2

---

## Step 5: Smallest Vertical Slice

**Slice 1 — "Type and Find" (ship tomorrow)**

- **Who benefits:** Any shopper who knows (roughly) the name of a product they want
- **Decision it answers:** "Does our product catalog have what I'm looking for?"
- **What it delivers:** A search bar on the product listing page; submitting the form runs a `LIKE '%query%'` SQL query on the product name field and renders a plain list of matching products (name + price); if nothing matches, shows "No results found"
- **Time to build:** 2–4 hours
- **Infrastructure needed:** None — reuses existing DB and server-side rendering
- **Stability risk:** Zero downtime; feature is additive, does not touch existing pages

---

## Step 6: Follow-Up Slices

**Slice 2 — "Better Results" (next sprint)**
- Upgrade 2.2 → 2.3: Extend SQL search to cover description and category fields
- Upgrade 4.1 → 4.2: Show product thumbnails alongside name and price
- Everything else stays the same

**Slice 3 — "Useful When Empty" (sprint after)**
- Upgrade 5.2 → 5.4: When no results found, show 4–6 popular/featured products
- Upgrade 3.1 → 3.2: Sort results so exact-name matches appear first

**Slice 4 — "Fast and Filtered" (backlog)**
- Upgrade 1.1 → 1.3: Add debounced submit and basic category filter checkbox
- Upgrade 2.3 → 2.4: Introduce Typesense or Elasticsearch for full-text indexing
- Upgrade 4.2 → 4.3: Add "Add to Cart" button directly on search result cards

---

## Self-Check

- [x] 3–6 functional layers identified (5 layers)
- [x] At least 4–5 options generated per layer
- [x] Options follow quality gradient (manual → enterprise)
- [x] Radical slicing question asked and answered explicitly
- [x] Smallest slice uses level 1–2 options from each layer
- [x] Smallest slice delivers value to at least one real user (any shopper)
- [x] Smallest slice deployable in less than 1 day (2–4 hours)
- [x] 3 follow-up slices proposed with clear incremental improvements
