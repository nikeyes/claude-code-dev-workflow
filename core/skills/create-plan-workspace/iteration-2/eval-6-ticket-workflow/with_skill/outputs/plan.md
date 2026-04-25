# Bulk Import Endpoint for Inventory Service — Implementation Plan

## Overview

Add a `bulk_import(csv_data: str) -> dict` method to `InventoryService` that parses a CSV of products, creates new SKUs or updates existing ones (additive quantity, replaced price), collects row-level errors without aborting the whole import, and requires the caller to hold an `"import"` permission checked via `AuthService`. This replaces the warehouse team's ~200-product manual entry process for quarterly restocking.

## Current State Analysis

**`inventory.py`** — `InventoryService` stores products in `self._products: dict[str, dict]`. The `add_product` method **overwrites** existing SKUs entirely; it does not implement the additive-quantity / replace-price semantics required by the ticket. No bulk import method exists.

**`auth.py`** — `AuthService` tracks per-user permissions (default `["read"]`), exposes `has_permission(username, permission) -> bool` and `grant_permission(username, permission) -> bool`. New users cannot write to the inventory without an explicit permission grant. Bulk import is a multi-write operation and must be gated.

**`test_inventory.py`** — Class-based pytest suite, one test class `TestInventoryService` with `setup_method`. All tests are unit-level with no external dependencies.

**`Makefile`** — `make test` runs `pytest test_inventory.py -v` from the project directory.

### Key Discoveries

- `inventory.py:8-15` — `add_product` replaces the full product record; bulk import for existing SKUs cannot reuse it as-is.
- `inventory.py:20-25` — `update_quantity` adds a delta to existing quantity; the additive-quantity logic for bulk import can follow this pattern.
- `auth.py:44-48` — `has_permission` is straightforward to call; the natural permission name for bulk import is `"import"`.
- `test_inventory.py:4-35` — Tests follow a simple arrange/act/assert pattern with no fixtures or mocks; new tests should follow the same style.

## Desired End State

After this plan is complete:

1. `InventoryService.bulk_import(csv_data: str) -> dict` exists and returns `{"created": N, "updated": M, "errors": [...]}`.
2. New SKUs are created; existing SKUs get quantity incremented and price replaced.
3. Rows with missing required fields, negative quantity, or non-numeric price are appended to `errors` and processing continues.
4. The method accepts a `username: str` parameter and raises `PermissionError` (or returns an error) if `AuthService.has_permission(username, "import")` is `False`.
5. `make test` passes with no failures.

### Verification

```
make test   # all existing + new tests green
```

## What We're NOT Doing

- No HTTP/REST endpoint — the ticket asks only for a service-layer method.
- No persistent storage — `_products` remains an in-memory dict.
- No CSV file I/O — the method accepts an already-read `str`, matching the ticket signature.
- No rollback / transactions — the ticket explicitly says errors should be collected, not abort.
- No changes to `AuthService` itself — we only call `has_permission`; `grant_permission` for `"import"` is an ops concern outside this ticket.
- No changes to the `Makefile` — `make test` already covers `test_inventory.py`.

## Implementation Approach

Implement in two phases:

1. **Core bulk import logic** — parse CSV, apply create/update rules, collect errors. No auth yet so we can test the logic independently.
2. **Permission gate** — wire in `AuthService.has_permission` check and add auth-related tests.

This keeps each phase independently verifiable and allows the warehouse team to test the import logic before the auth integration is complete.

---

## Phase 1: Core Bulk Import Logic

### Overview

Add `bulk_import(csv_data: str) -> dict` to `InventoryService` and cover it with unit tests. No auth dependency in this phase.

### Changes Required

#### 1. `InventoryService.bulk_import` method

**File**: `inventory.py`

**Changes**: Add the method after `list_products`. Use `csv.reader` from the standard library. Validate each row: all four columns present, quantity is a non-negative integer, price is a positive float. For a valid row — create product if SKU absent, otherwise add to quantity and replace price. Collect error strings for invalid rows.

```python
import csv
import io

# Inside InventoryService:

def bulk_import(self, csv_data: str) -> dict:
    created = 0
    updated = 0
    errors = []

    reader = csv.DictReader(io.StringIO(csv_data))
    required_fields = {"sku", "name", "quantity", "price"}

    for line_num, row in enumerate(reader, start=2):  # start=2: row 1 is header
        missing = required_fields - set(row.keys())
        if missing or not all(row.get(f, "").strip() for f in required_fields):
            errors.append(f"Row {line_num}: missing required fields")
            continue

        try:
            quantity = int(row["quantity"].strip())
            if quantity < 0:
                raise ValueError("negative quantity")
        except ValueError:
            errors.append(f"Row {line_num}: invalid quantity '{row['quantity'].strip()}'")
            continue

        try:
            price = float(row["price"].strip())
            if price < 0:
                raise ValueError("negative price")
        except ValueError:
            errors.append(f"Row {line_num}: invalid price '{row['price'].strip()}'")
            continue

        sku = row["sku"].strip()
        name = row["name"].strip()

        if sku in self._products:
            self._products[sku]["quantity"] += quantity
            self._products[sku]["price"] = price
            updated += 1
        else:
            self._products[sku] = {
                "sku": sku,
                "name": name,
                "quantity": quantity,
                "price": price,
            }
            created += 1

    return {"created": created, "updated": updated, "errors": errors}
```

#### 2. New tests for bulk import logic

**File**: `test_inventory.py`

**Changes**: Add a `TestBulkImport` test class after `TestInventoryService`.

```python
class TestBulkImport:
    def setup_method(self):
        self.service = InventoryService()

    def test_bulk_import_creates_new_products(self):
        csv_data = "sku,name,quantity,price\nSKU001,Widget,100,9.99\nSKU002,Gadget,50,19.99"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 2
        assert result["updated"] == 0
        assert result["errors"] == []

    def test_bulk_import_updates_existing_sku_quantity_additive(self):
        self.service.add_product("SKU001", "Widget", 10, 9.99)
        csv_data = "sku,name,quantity,price\nSKU001,Widget,100,12.99"
        result = self.service.bulk_import(csv_data)
        assert result["updated"] == 1
        assert self.service.get_product("SKU001")["quantity"] == 110  # 10 + 100
        assert self.service.get_product("SKU001")["price"] == 12.99

    def test_bulk_import_collects_errors_without_aborting(self):
        csv_data = "sku,name,quantity,price\nBAD,,,-1\nSKU002,Gadget,50,19.99"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 1
        assert len(result["errors"]) == 1

    def test_bulk_import_rejects_negative_quantity(self):
        csv_data = "sku,name,quantity,price\nSKU001,Widget,-5,9.99"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert "quantity" in result["errors"][0]

    def test_bulk_import_rejects_non_numeric_price(self):
        csv_data = "sku,name,quantity,price\nSKU001,Widget,10,abc"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 0
        assert "price" in result["errors"][0]

    def test_bulk_import_rejects_missing_required_field(self):
        csv_data = "sku,name,quantity,price\nSKU001,,10,9.99"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 0
        assert len(result["errors"]) == 1

    def test_bulk_import_empty_csv_returns_zero_counts(self):
        csv_data = "sku,name,quantity,price\n"
        result = self.service.bulk_import(csv_data)
        assert result == {"created": 0, "updated": 0, "errors": []}

    def test_bulk_import_mixed_create_and_update(self):
        self.service.add_product("EXISTING", "Old", 5, 1.00)
        csv_data = "sku,name,quantity,price\nEXISTING,Old,20,2.00\nNEW,New Product,10,5.00"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 1
        assert result["updated"] == 1
        assert result["errors"] == []
```

### Success Criteria

- [ ] All tests pass: `make test`
- [ ] No linting errors (if linter configured)

---

## Phase 2: Permission Gate via AuthService

### Overview

Extend `bulk_import` to accept an optional `username: str` parameter and check `AuthService.has_permission(username, "import")`. If the user lacks the permission, raise `PermissionError`. Add corresponding tests.

### Changes Required

#### 1. Update `bulk_import` signature

**File**: `inventory.py`

**Changes**: Import `AuthService` and update `bulk_import` to accept `auth_service` and `username` parameters (both optional to keep backwards compatibility with existing tests).

```python
from auth import AuthService

# Updated signature:
def bulk_import(
    self,
    csv_data: str,
    auth_service: Optional[AuthService] = None,
    username: Optional[str] = None,
) -> dict:
    if auth_service is not None and username is not None:
        if not auth_service.has_permission(username, "import"):
            raise PermissionError(
                f"User '{username}' does not have 'import' permission"
            )
    # ... rest of existing logic unchanged
```

#### 2. Auth-related tests

**File**: `test_inventory.py`

**Changes**: Add an `TestBulkImportAuth` class.

```python
from auth import AuthService

class TestBulkImportAuth:
    def setup_method(self):
        self.service = InventoryService()
        self.auth = AuthService()
        self.auth.register("warehouse_user", "password")
        self.auth.register("readonly_user", "password")
        self.auth.grant_permission("warehouse_user", "import")

    def test_bulk_import_allowed_with_import_permission(self):
        csv_data = "sku,name,quantity,price\nSKU001,Widget,10,9.99"
        result = self.service.bulk_import(csv_data, self.auth, "warehouse_user")
        assert result["created"] == 1

    def test_bulk_import_denied_without_import_permission(self):
        csv_data = "sku,name,quantity,price\nSKU001,Widget,10,9.99"
        with pytest.raises(PermissionError):
            self.service.bulk_import(csv_data, self.auth, "readonly_user")

    def test_bulk_import_no_auth_service_skips_permission_check(self):
        csv_data = "sku,name,quantity,price\nSKU001,Widget,10,9.99"
        result = self.service.bulk_import(csv_data)
        assert result["created"] == 1
```

### Success Criteria

- [ ] All tests pass: `make test`

---

## Testing Strategy

### Unit Tests

- Happy path: clean CSV creates and updates correct counts
- Update semantics: quantity is additive, price is replaced
- Error collection: invalid rows collected, valid rows still processed
- Edge cases: empty CSV, all-invalid CSV, mixed valid/invalid rows
- Auth: permission granted allows import, permission absent raises `PermissionError`, no auth service skips check

### Integration Tests

Not applicable — `InventoryService` and `AuthService` are pure in-memory; the unit tests with both collaborators constitute integration coverage.

### Manual Testing Steps

Not applicable — all acceptance criteria are machine-verifiable via `make test`.

---

## Performance Considerations

The method processes rows sequentially with O(n) time and O(n) space relative to CSV rows. For the described use case (~200 products per restock), this is negligible. If future scale requires it, the CSV parsing and validation could be parallelised, but that is out of scope for this ticket.

## Migration Notes

No persistent storage exists; no data migration is required.

## References

- Original ticket: `tickets/eng-1234.md`
- `inventory.py` — `add_product` (line 8), `update_quantity` (line 20)
- `auth.py` — `has_permission` (line 44), `grant_permission` (line 50)
- `test_inventory.py` — existing test patterns (line 4–35)
