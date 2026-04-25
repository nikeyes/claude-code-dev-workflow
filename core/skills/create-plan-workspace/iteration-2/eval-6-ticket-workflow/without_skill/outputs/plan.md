# Implementation Plan: ENG-1234 — Bulk Import Endpoint for Inventory Service

## Ticket Summary

Add a `bulk_import(csv_data: str) -> dict` method to `InventoryService` that:
- Parses a CSV string (header: `sku,name,quantity,price`)
- Creates new products or updates existing ones (additive quantity, replaced price)
- Returns `{"created": N, "updated": M, "errors": [...]}`
- Collects invalid rows in errors instead of aborting

---

## Codebase Analysis

### Relevant files
- `inventory.py` — contains `InventoryService`; this is the only file that needs to be changed
- `test_inventory.py` — existing tests pass via `make test` (pytest); new tests go here
- `auth.py` — unrelated to this ticket; no changes needed

### Existing API used by the new method
| Method | Purpose |
|---|---|
| `add_product(sku, name, quantity, price)` | Creates a new product (overwrites if SKU exists) |
| `get_product(sku)` | Returns product dict or `None` |
| `update_quantity(sku, delta)` | Adds `delta` to existing quantity |

The new method must internally use `get_product` to detect create vs. update, then call `add_product` (create path) or `update_quantity` + direct price update (update path).

---

## Implementation Steps

### Step 1: Write failing tests (Red)

Add a `TestBulkImport` class to `test_inventory.py` covering:

1. **Happy path — all new products**
   - Input: valid CSV with two new SKUs
   - Assert: `created == 2`, `updated == 0`, `errors == []`
   - Assert: both products exist in inventory with correct fields

2. **Happy path — all existing products (update)**
   - Pre-populate inventory with SKU001
   - Input: CSV row for SKU001 with different quantity and price
   - Assert: `created == 0`, `updated == 1`, `errors == []`
   - Assert: quantity is additive (old + new), price is replaced

3. **Mixed create and update**
   - Pre-populate one SKU, import CSV with that SKU plus a new one
   - Assert: `created == 1`, `updated == 1`, `errors == []`

4. **Invalid row — missing required field**
   - Input: CSV row missing the `name` column
   - Assert: `errors` contains one entry describing the problem
   - Assert: `created == 0` (no valid rows were processed)

5. **Invalid row — negative quantity**
   - Input: CSV row with `quantity == -5`
   - Assert: row goes to errors, import continues

6. **Invalid row — non-numeric price**
   - Input: CSV row with `price == "abc"`
   - Assert: row goes to errors, import continues

7. **Mixed valid and invalid rows**
   - Input: 3 rows: 1 valid new, 1 invalid, 1 valid new
   - Assert: `created == 2`, `errors` has 1 entry (partial success)

8. **Empty CSV (header only)**
   - Input: just the header line
   - Assert: `created == 0`, `updated == 0`, `errors == []`

### Step 2: Implement `bulk_import` (Green)

Add the method to `InventoryService` in `inventory.py`:

```python
import csv
import io

def bulk_import(self, csv_data: str) -> dict:
    created = 0
    updated = 0
    errors = []

    reader = csv.DictReader(io.StringIO(csv_data))
    for row_num, row in enumerate(reader, start=2):  # row 1 is the header
        error = self._validate_row(row, row_num)
        if error:
            errors.append(error)
            continue

        sku = row["sku"].strip()
        name = row["name"].strip()
        quantity = int(row["quantity"].strip())
        price = float(row["price"].strip())

        if self.get_product(sku) is None:
            self.add_product(sku, name, quantity, price)
            created += 1
        else:
            self.update_quantity(sku, quantity)
            self._products[sku]["price"] = price
            updated += 1

    return {"created": created, "updated": updated, "errors": errors}
```

Add a private validation helper:

```python
def _validate_row(self, row: dict, row_num: int) -> str | None:
    required = ["sku", "name", "quantity", "price"]
    for field in required:
        if field not in row or not str(row[field]).strip():
            return f"Row {row_num}: missing required field '{field}'"
    try:
        quantity = int(row["quantity"].strip())
    except ValueError:
        return f"Row {row_num}: quantity must be an integer, got '{row['quantity']}'"
    if quantity < 0:
        return f"Row {row_num}: quantity must be non-negative, got {quantity}"
    try:
        float(row["price"].strip())
    except ValueError:
        return f"Row {row_num}: price must be numeric, got '{row['price']}'"
    return None
```

Note: `csv` and `io` are stdlib modules; no new dependencies.

### Step 3: Refactor (if needed)

After tests pass, review for clarity:
- Extract CSV parsing logic to `_parse_csv_rows` if `bulk_import` grows too long
- Ensure error messages are consistent and descriptive
- Keep `_validate_row` private; it is an implementation detail

---

## Validation Checklist

- [ ] All existing tests still pass (`make test`)
- [ ] All 8 new tests pass
- [ ] `created`, `updated`, and `errors` counts are accurate in all test scenarios
- [ ] Update path: quantity is additive, price is replaced
- [ ] Partial failures do not abort the import
- [ ] No new dependencies added

---

## Out of Scope

- HTTP endpoint / REST API layer — the ticket specifies a service method only
- CSV file upload (the method accepts a string; callers handle file I/O)
- Authentication / permission checks — `auth.py` is not touched
- Persistent storage — the existing in-memory store is sufficient
