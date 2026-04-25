# create-plan execution — ENG-1234: Bulk Import for Inventory Service

## Step 1: Context Gathering & Initial Analysis

### Files Read

- `tickets/eng-1234.md` — ticket fully read
- `inventory.py` — fully read
- `test_inventory.py` — fully read
- `auth.py` — fully read
- `Makefile` — fully read

### Ticket Summary

ENG-1234 requests a new `bulk_import(csv_data: str) -> dict` method on `InventoryService` that:
- Parses a CSV with columns `sku,name,quantity,price`
- Creates new products or updates existing ones (quantity: additive; price: replace)
- Returns `{"created": N, "updated": M, "errors": [...]}`
- Collects row-level errors without aborting the import

### Codebase Findings

**`inventory.py`**
- `InventoryService` uses an in-memory `dict[str, dict]` keyed by SKU
- `add_product` (line 8) **overwrites** existing SKUs entirely — cannot be reused for the additive-quantity / replace-price semantics required by the ticket
- `update_quantity` (line 20) applies a delta to an existing product's quantity — the additive-quantity pattern for bulk import mirrors this
- No `bulk_import` method exists yet

**`auth.py`**
- `AuthService` tracks per-user permissions; new users default to `["read"]`
- `has_permission(username, permission) -> bool` (line 44) is the natural gate for the bulk import operation
- `grant_permission(username, permission) -> bool` (line 50) allows ops to enable `"import"` for specific users
- The ticket does not mention auth, but bulk import is a write/destructive batch operation — the existing permission model should gate it

**`test_inventory.py`**
- Class-based pytest, `setup_method` pattern, no mocks
- `make test` runs `pytest test_inventory.py -v`

### Key Design Decision: Auth Integration

The ticket does not explicitly require auth, but `auth.py` exists in the same service and the operation is high-impact (up to hundreds of products modified in one call). The implementation will add an **optional** `auth_service` + `username` parameter pair so that:
- Existing tests continue to pass without modification (no auth service = no check)
- Callers with an `AuthService` context can enforce the `"import"` permission

---

## Step 2: Design Options Considered

### Option A: Reuse `add_product` for create, custom logic for update
Simpler but requires calling `get_product` to decide path, then separate methods. Slightly more coupling to existing API.

### Option B: Inline all logic in `bulk_import` (selected)
Cleaner encapsulation — the create/update semantics are distinct from the existing `add_product` contract (which always overwrites). Direct dict manipulation is consistent with how `update_quantity` works. No risk of accidentally re-using `add_product`'s overwrite semantics.

### Option C: Separate `BulkImportService` class
Over-engineered for this scope — the service is small and in-memory. No need for a separate class.

**Selected: Option B** — inline logic with direct `_products` manipulation.

---

## Step 3: Plan Structure (approved)

1. **Phase 1: Core Bulk Import Logic** — implement `bulk_import`, add unit tests covering create, update, error collection, edge cases
2. **Phase 2: Permission Gate** — wire in optional `AuthService` check, add auth tests

---

## Step 4: Implementation Plan

Plan saved to: `outputs/plan.md`

### Summary of Plan Contents

#### Phase 1 — Core Bulk Import Logic

**`inventory.py` changes:**
- Add `import csv, io` at top
- Add `bulk_import(self, csv_data: str) -> dict` method
- Parse with `csv.DictReader`
- Validate: all four fields present and non-empty, quantity is non-negative int, price is non-negative float
- For valid rows: create new SKU or increment quantity + replace price for existing SKU
- Return `{"created": N, "updated": M, "errors": [...]}`

**`test_inventory.py` additions — `TestBulkImport` class:**
- `test_bulk_import_creates_new_products`
- `test_bulk_import_updates_existing_sku_quantity_additive`
- `test_bulk_import_collects_errors_without_aborting`
- `test_bulk_import_rejects_negative_quantity`
- `test_bulk_import_rejects_non_numeric_price`
- `test_bulk_import_rejects_missing_required_field`
- `test_bulk_import_empty_csv_returns_zero_counts`
- `test_bulk_import_mixed_create_and_update`

**Success criteria:** `make test` green

#### Phase 2 — Permission Gate

**`inventory.py` changes:**
- Add `from auth import AuthService`
- Update `bulk_import` signature: `bulk_import(self, csv_data: str, auth_service: Optional[AuthService] = None, username: Optional[str] = None) -> dict`
- At method entry: if both `auth_service` and `username` provided, call `has_permission(username, "import")`; raise `PermissionError` if denied

**`test_inventory.py` additions — `TestBulkImportAuth` class:**
- `test_bulk_import_allowed_with_import_permission`
- `test_bulk_import_denied_without_import_permission`
- `test_bulk_import_no_auth_service_skips_permission_check`

**Success criteria:** `make test` green

---

## Step 5: Plan Location

Implementation plan complete: `outputs/plan.md`

Next steps in the workflow:
- Review and approve the plan
- Use `/stepwise-core:implement-plan outputs/plan.md` to execute it
- Or use `/stepwise-core:iterate-plan outputs/plan.md [changes]` to refine further

Tip: Use `/clear` to free up context before starting implementation.

---

## Open Questions Resolved During Planning

| Question | Resolution |
|---|---|
| Should bulk import gate on auth? | Yes — `AuthService.has_permission` already exists; use optional parameters to avoid breaking existing tests |
| Should `add_product` be reused? | No — its overwrite semantics conflict with the additive-quantity requirement; inline logic is cleaner |
| Should a `PermissionError` abort the whole import or be collected in errors? | Abort (raise) — a permission denial is a caller-level error, not a row-level data error |
| What is the `"import"` permission name? | `"import"` — descriptive and distinct from `"read"` and `"write"` |
