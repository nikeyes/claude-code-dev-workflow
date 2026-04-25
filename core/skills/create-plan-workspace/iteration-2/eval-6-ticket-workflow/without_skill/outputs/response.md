# ENG-1234: Bulk Import — Implementation Plan

## What I read

- `tickets/eng-1234.md` — the feature request
- `inventory.py` — `InventoryService` with `add_product`, `get_product`, `update_quantity`, `list_products`, `get_total_value`
- `test_inventory.py` — existing pytest tests for the service
- `auth.py` — `AuthService`; unrelated to this ticket
- `Makefile` — runs `pytest test_inventory.py -v`

## Key observations

1. The ticket requires one new public method: `bulk_import(csv_data: str) -> dict`.
2. Python's standard library `csv` + `io.StringIO` handle parsing — no new dependencies.
3. The existing `get_product` / `add_product` / `update_quantity` methods cover the create-vs-update logic; `bulk_import` orchestrates them.
4. `auth.py` is completely independent; no changes needed there.

## Plan

The full plan is saved to `plan.md` in this directory. Summary:

### TDD approach

**Red** — Add 8 failing tests in `test_inventory.py` covering:
- All-new products
- All-existing products (additive quantity, replaced price)
- Mixed create + update
- Invalid: missing field, negative quantity, non-numeric price
- Mixed valid + invalid rows (partial success)
- Empty CSV (header only)

**Green** — Implement `bulk_import` and `_validate_row` in `inventory.py`:
- Parse with `csv.DictReader`
- Validate each row; append error string and skip on failure
- `get_product` decides create vs. update path
- Return `{"created": N, "updated": M, "errors": [...]}`

**Refactor** — Extract `_parse_csv_rows` only if needed for clarity; keep validation private.

### Files changed
| File | Change |
|---|---|
| `inventory.py` | Add `bulk_import` + `_validate_row` methods; add `import csv, io` at top |
| `test_inventory.py` | Add `TestBulkImport` class with 8 test methods |

### Files not changed
- `auth.py` — out of scope
- `Makefile` — existing `make test` command covers new tests automatically
