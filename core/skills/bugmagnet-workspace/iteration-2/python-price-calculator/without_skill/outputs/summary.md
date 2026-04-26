# Price Calculator — Test Coverage Analysis & Bug Report

## Original Test Coverage

The existing test file (`test_price_calculator.py`) contained **3 tests**:
- One basic discount test (10% off $100)
- One single-item total test (default 21% tax)
- One EUR format test

Coverage was essentially a happy-path smoke test with zero edge-case or boundary coverage. `apply_coupon` and `split_payment` had **zero tests**.

---

## Tests Added

**File**: `test_price_calculator_comprehensive.py`
**Total new tests**: 47

| Module | Tests added |
|---|---|
| `calculate_discount` | 10 |
| `calculate_total` | 13 |
| `format_price` | 8 |
| `apply_coupon` | 12 |
| `split_payment` | 11 |
| **Total** | **47** |

---

## Bugs Discovered

### Bug 1 — No input validation on `calculate_discount`
**Location**: `price_calculator.py`, line 6  
**Root cause**: No guard on `discount_percent` or `price`. Accepts negative discounts (silently increases the price) and discounts above 100 (produces negative prices).  
**Proposed fix**: Raise `ValueError` if `discount_percent < 0` or `discount_percent > 100`, or if `price < 0`.

### Bug 2 — No input validation on `calculate_total` quantities
**Location**: `price_calculator.py`, line 17  
**Root cause**: Negative `quantity` values are accepted and propagate to the subtotal. A cart could have a negative subtotal.  
**Proposed fix**: Raise `ValueError` if any item's `quantity < 0`.

### Bug 3 — `apply_coupon` silently ignores unknown coupon types
**Location**: `price_calculator.py`, line 46  
**Root cause**: The final `return total` acts as a catch-all for unknown coupon types (e.g., `"gift_card"`). The caller receives the original total with no indication that the coupon was not applied.  
**Proposed fix**: Raise `ValueError` for unsupported coupon types instead of silently returning the unchanged total.

### Bug 4 — `apply_coupon` produces negative totals
**Location**: `price_calculator.py`, lines 43–45  
**Root cause**: No guard on `coupon["value"]`. A `percent` coupon above 100 or a `fixed` coupon exceeding the total both produce negative totals.  
**Proposed fix**: Clamp result to 0 (`max(0.0, result)`) or raise `ValueError` when the coupon value is out of range.

### Bug 5 — `apply_coupon` accepts negative coupon values (adds to total)
**Location**: `price_calculator.py`, lines 43–45  
**Root cause**: A negative `value` in a percent or fixed coupon increases the total rather than reducing it. No validation exists.  
**Proposed fix**: Raise `ValueError` if `coupon["value"] < 0`.

### Bug 6 — `split_payment` crashes with `parts = 0`
**Location**: `price_calculator.py`, line 51  
**Root cause**: `total / parts` raises `ZeroDivisionError` when `parts = 0`. No guard exists.  
**Proposed fix**: Raise `ValueError("parts must be a positive integer")` before performing the division.

### Bug 7 — `split_payment` crashes with negative `parts`
**Location**: `price_calculator.py`, lines 51–54  
**Root cause**: With `parts < 0`, `[per_part] * parts` produces an empty list `[]`, and then `result[-1]` raises `IndexError` because there is no last element.  
**Proposed fix**: Same as Bug 6 — validate that `parts >= 1` before proceeding.

### Bug 8 — `format_price` accepts negative amounts without error
**Location**: `price_calculator.py`, line 34  
**Root cause**: Negative `amount` is formatted (e.g., `"€-5.00"`) with no guard. For an e-commerce context, negative displayed prices are almost certainly unintentional.  
**Proposed fix**: Raise `ValueError` if `amount < 0`, or document and test the intended behavior explicitly.

### Bug 9 — `format_price` with empty-string currency produces no symbol
**Location**: `price_calculator.py`, line 33  
**Root cause**: `symbols.get("", "")` returns `""` (the empty string itself), so `format_price(10.0, "")` returns `"10.00"` — a number with no currency indicator.  
**Proposed fix**: Raise `ValueError` for empty or `None` currency codes.

---

## Coverage Assessment

| Function | Happy path | Edge cases | Boundary | Error/exception |
|---|---|---|---|---|
| `calculate_discount` | covered | partial | zero/100% | not guarded |
| `calculate_total` | covered | partial | empty list, zero qty | missing keys |
| `format_price` | covered | unknown currency, negative | zero amount | empty currency |
| `apply_coupon` | covered | unknown type, negative value | 0%, 100%, exceeds total | missing keys |
| `split_payment` | covered | 1 part, fractional | zero total | zero/negative parts |

The new test suite raises coverage from a narrow 3-test smoke check to a full behavioural suite that exercises all five functions across normal, boundary, and error-inducing inputs. Nine distinct bugs (missing input guards and silent failure modes) were identified.
