# Hamburger Method: E-Commerce Product Search Feature

## Feature Description

Add a search feature to our e-commerce site so users can find products by typing a query and seeing a list of matching results.

---

## Step 1: Identify the Layers

The Hamburger Method starts by decomposing a feature into its architectural and functional layers — from the outermost user-facing presentation down to the innermost data layer. Each layer represents a dimension of variability where different implementation choices can be made independently.

### Layer Stack (Top to Bottom)

| # | Layer | Description |
|---|-------|-------------|
| 1 | UI / Entry Point | How the user initiates a search (input mechanism) |
| 2 | Results Presentation | How matching products are shown to the user |
| 3 | API / Communication | How the frontend talks to the backend |
| 4 | Search Logic / Matching | How the backend determines which products match |
| 5 | Data Access | How the backend retrieves candidate products |
| 6 | Data Storage / Index | How products are stored and indexed for search |

---

## Step 2: Generate Implementation Options Per Layer

For each layer, we generate 4–5 concrete implementation options, ranging from the simplest possible approach to progressively more capable alternatives.

---

### Layer 1: UI / Entry Point — How the user triggers a search

| Option | Description | Complexity |
|--------|-------------|------------|
| A | An existing HTML `<form>` with a text input and a submit button; submits a GET request to a new `/search` page | Minimal — no JavaScript needed |
| B | A text input in the navbar with a search icon button; JavaScript submits asynchronously and updates the page without a full reload | Low |
| C | A search input with real-time "search as you type" that fires a request after each keystroke (debounced) | Medium |
| D | A command-palette style overlay (Cmd+K) that provides keyboard-accessible fuzzy search | High |
| E | A conversational / AI-powered chat input that interprets natural language queries | Very High |

---

### Layer 2: Results Presentation — How matching products are displayed

| Option | Description | Complexity |
|--------|-------------|------------|
| A | A plain HTML list of product names with a link to each product detail page | Minimal |
| B | A grid of product cards (image, name, price) rendered server-side as a full page | Low |
| C | An inline dropdown/popover showing top N results beneath the search box, rendered client-side | Medium |
| D | A dedicated full-page search results page with faceted filters (category, price range, rating) | High |
| E | An infinite-scroll results page with relevance score badges, sponsored slots, and personalisation | Very High |

---

### Layer 3: API / Communication — How frontend and backend exchange data

| Option | Description | Complexity |
|--------|-------------|------------|
| A | Standard HTML form GET — browser sends `GET /search?q=shoes` and server returns a full HTML page | Minimal |
| B | REST endpoint `GET /api/products/search?q=shoes` returning JSON; frontend fetches and renders | Low |
| C | GraphQL query `{ products(query: "shoes") { id name price } }` over a single endpoint | Medium |
| D | WebSocket or Server-Sent Events stream that pushes partial results as they are found | High |
| E | Federated API gateway that aggregates results from multiple microservices (products, inventory, pricing) | Very High |

---

### Layer 4: Search Logic / Matching — How the server finds relevant products

| Option | Description | Complexity |
|--------|-------------|------------|
| A | SQL `LIKE '%query%'` on the product name column — exact substring match | Minimal |
| B | SQL `ILIKE` (case-insensitive) with `OR` across name and description columns | Low |
| C | Full-text search using the database engine's built-in FTS (PostgreSQL `tsvector`, MySQL `FULLTEXT`) | Medium |
| D | Dedicated search engine (Elasticsearch, OpenSearch, Typesense, Meilisearch) with ranking, stemming, and synonyms | High |
| E | Semantic / vector search using product embeddings and approximate nearest-neighbour lookup | Very High |

---

### Layer 5: Data Access — How the application retrieves products from storage

| Option | Description | Complexity |
|--------|-------------|------------|
| A | Direct SQL query from the route handler / controller using raw SQL or a query builder | Minimal |
| B | ORM method call (e.g., `Product.where(name: LIKE ?)`) — abstracts the query behind the model layer | Low |
| C | Repository/DAO pattern — a dedicated `ProductSearchRepository` class that isolates data access | Medium |
| D | Caching layer (Redis, Memcached) — cache popular queries so repeated searches skip the DB | High |
| E | CQRS read model — a separate, denormalised read database optimised purely for search queries | Very High |

---

### Layer 6: Data Storage / Index — How products are persisted and indexed

| Option | Description | Complexity |
|--------|-------------|------------|
| A | Existing products table with no changes — search queries run directly against the main table | Minimal |
| B | Add a database index on the `name` column to speed up LIKE queries | Minimal/Low |
| C | Add a composite index covering the columns most used in search (name, category, status) | Low |
| D | Maintain a separate `products_search_index` table / materialised view with pre-processed, normalised text | Medium |
| E | External search index (Elasticsearch, Algolia, Typesense) kept in sync via event streams or periodic jobs | High |

---

## Step 3: Compose the Smallest Vertical Slice

A vertical slice cuts through every layer and delivers a complete, working, user-visible behaviour end to end. The smallest useful slice picks the simplest option from each layer while still being genuinely valuable to a real user.

### Selection — Minimum Viable Search Slice

| Layer | Chosen Option | Rationale |
|-------|--------------|-----------|
| UI / Entry Point | **A — HTML form with text input + submit button** | Zero JavaScript, works on any browser, immediately testable |
| Results Presentation | **A — Plain HTML list of product names with links** | No styling effort; proves the full path is working |
| API / Communication | **A — HTML form GET, full-page server response** | No JSON, no AJAX, no CORS — the simplest possible round trip |
| Search Logic | **A — SQL `LIKE '%query%'` on the name column** | No new dependencies; proves end-to-end matching works |
| Data Access | **A — Direct SQL query from the route handler** | No abstraction overhead; easy to refactor once the path is proven |
| Data Storage | **A — Existing products table, no schema changes** | Nothing to migrate; slice is deployable immediately |

---

### Slice Description: "Basic Name Search"

**User story:**
> As a shopper, I can type a word into a search box and press Enter to see a list of products whose names contain that word, so that I can find what I am looking for without browsing every category.

**What it does:**
1. A search box (HTML `<input type="text">` inside a `<form method="GET" action="/search">`) is rendered on any page — initially the homepage or a dedicated `/search` page.
2. The user types a query (e.g., "sneakers") and presses Enter or clicks "Search".
3. The browser sends `GET /search?q=sneakers` to the server.
4. The server runs: `SELECT id, name FROM products WHERE name LIKE '%sneakers%' LIMIT 50`
5. The server renders an HTML page listing matching product names, each a hyperlink to the product detail page.
6. If there are no matches, the page shows "No products found for 'sneakers'."

**What it explicitly does NOT include:**
- Images, prices, or ratings in results
- Filters, facets, or sorting
- Autocomplete or real-time suggestions
- Pagination (capped at 50 results for now)
- Any JavaScript
- Any new database tables, indexes, or external services

**Why this slice is valuable despite its simplicity:**
- It proves the entire request-response cycle works: UI → server route → database → rendered HTML → browser.
- It is shippable to production and genuinely useful (users can find products by name).
- Every subsequent improvement (add images, add filters, switch to full-text search, add autocomplete) is an incremental enhancement on top of this proven foundation.
- It provides immediate feedback on correctness: if the wrong products appear, the bug is in the LIKE query — there is nowhere else to look.

---

## Step 4: Incremental Enhancement Path

Once the smallest slice is live, subsequent slices add value without rewriting what exists:

| Slice # | Enhancement | Layers Touched |
|---------|-------------|---------------|
| 2 | Add product image and price to results | Layer 2 only |
| 3 | Add a database index on `products.name` | Layer 6 only |
| 4 | Extend LIKE to also match the `description` column | Layer 4 only |
| 5 | Move search logic to a `ProductSearchRepository` class | Layer 5 only |
| 6 | Add JSON API endpoint + AJAX results rendering | Layers 2 + 3 |
| 7 | Switch to PostgreSQL full-text search (`tsvector`) | Layers 4 + 6 |
| 8 | Add category and price range filters to the results page | Layers 2 + 4 |
| 9 | Add autocomplete/typeahead dropdown | Layers 1 + 2 + 3 |
| 10 | Introduce Typesense or Meilisearch for advanced relevance | Layers 4 + 5 + 6 |

Each slice in this path delivers independent, releasable value and is testable on its own. No slice requires undoing work from a previous slice.

---

## Summary

The Hamburger Method reveals that "add search" is not a single task — it spans six independent layers, each with multiple implementation options ranging from trivial to enterprise-grade. By selecting the simplest option at every layer, we arrive at a **Basic Name Search** slice that:

- Is fully vertical (touches all layers end to end)
- Delivers real user value (products are findable)
- Can be built, tested, and deployed in a matter of hours
- Creates zero technical debt that blocks future enhancements
- Provides a stable foundation for every subsequent improvement on the enhancement path
