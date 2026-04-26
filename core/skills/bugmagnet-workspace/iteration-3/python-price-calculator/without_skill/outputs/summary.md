# Bug Discovery Summary — price_calculator.py

## Existing Test Coverage

The existing suite (`test_price_calculator.py`) has only 3 tests covering the happy path of 3 out of 5 functions:

| Function | Existing tests | Status |
|---|---|---|
| `calculate_discount` | 1 (basic 10% off) | Minimal |
| `calculate_total` | 1 (single item, default tax) | Minimal |
| `format_price` | 1 (EUR symbol) | Minimal |
| `apply_coupon` | 0 | **Completely untested** |
| `split_payment` | 0 | **Completely untested** |

---

## Bugs Found

### BUG-1 — `calculate_discount`: No guard on discount > 100%
**Severity**: Medium  
**Behaviour**: `calculate_discount(100, 150)` returns `-50.0`. A negative price is nonsensical in an e-commerce context.  
**Fix suggestion**: Clamp or raise `ValueError` when `discount_percent` > 100 or < 0.

### BUG-2 — `calculate_discount`: Negative discount silently raises the price
**Severity**: Low-Medium  
**Behaviour**: `calculate_discount(100, -10)` returns `110.0`. No error is raised; a data-entry mistake or a malicious coupon could inflate prices.

### BUG-3 — `calculate_total`: Negative `quantity` accepted silently
**Severity**: Medium  
**Behaviour**: `calculate_total([{"name": "X", "price": 10, "quantity": -1}])` returns a negative subtotal. A return/refund flow should be explicit, not a side-effect of unvalidated input.

### BUG-4 — `calculate_total`: Explicit `None` discount causes `TypeError`
**Severity**: Medium  
**Behaviour**: If a caller sets `"discount": None` on an item (e.g., from a nullable DB column), `item.get("discount", 0)` returns `None` (the default is only used when the key is absent) and `calculate_discount` receives `None`, raising `TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'`.  
**Fix suggestion**: `item.get("discount") or 0` (treats both absent and `None` as zero).

### BUG-5 — `calculate_total`: Missing `"price"` or `"quantity"` key raises bare `KeyError`
**Severity**: Medium  
**Behaviour**: No input validation; a malformed item dict produces an unhandled `KeyError` with no diagnostic message.

### BUG-6 — `calculate_total`: Negative `tax_rate` silently reduces total below subtotal
**Severity**: Low  
**Behaviour**: `calculate_total(items, tax_rate=-0.1)` is accepted without error and produces a total that is less than the subtotal.

### BUG-7 — `apply_coupon`: Completely untested; coupon can make total negative
**Severity**: High  
**Behaviour**: Both `percent` (> 100%) and `fixed` (value > total) coupons produce a negative total with no error or clamp.

### BUG-8 — `apply_coupon`: Negative coupon value silently acts as a surcharge
**Severity**: Medium  
**Behaviour**: `apply_coupon(100, {"type": "percent", "value": -10})` returns `110.0`. A data-entry error inflates the customer's bill invisibly.

### BUG-9 — `apply_coupon`: Missing `"type"` or `"value"` key raises bare `KeyError`
**Severity**: Medium  
**Behaviour**: No validation on the coupon dict; malformed input propagates as an unhandled `KeyError`.

### BUG-10 — `split_payment`: `parts=0` raises unhandled `ZeroDivisionError`
**Severity**: High  
**Behaviour**: `split_payment(100, 0)` raises `ZeroDivisionError` instead of a clear `ValueError`.

### BUG-11 — `split_payment`: Negative `parts` crashes with `IndexError`
**Severity**: High  
**Behaviour**: `split_payment(100, -2)` calls `[per_part] * -2` which produces an empty list, then `result[-1] = ...` raises `IndexError: list assignment index out of range`.

---

## Coverage Gaps (beyond the bugs)

| Area | Gap |
|---|---|
| `format_price` | USD, GBP, unknown currency code, zero amount, negative amount, very large amount |
| `calculate_discount` | Zero discount, 100% discount, zero price, fractional rounding |
| `calculate_total` | Empty list, zero-quantity item, multiple items, custom tax rate, item_count accuracy, large quantities, floating-point accumulation |
| `apply_coupon` | All cases — function never imported or referenced in existing tests |
| `split_payment` | All cases — function never imported or referenced in existing tests |

---

## Test File

`test_edge_cases.py` — 57 new tests organised by function and scenario class, covering:
- Boundary values (0%, 100%, negative, very large)
- Missing/invalid input keys
- Silent numeric bugs (negative total, negative price, price inflation)
- Floating-point rounding behaviour (documented with assertions)
- All untested functions (`apply_coupon`, `split_payment`)

Each test that documents a bug includes a comment explaining the root cause and what the expected safe behaviour should be.
