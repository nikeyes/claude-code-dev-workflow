# Test Coverage Analysis: price_calculator.py

## Baseline Coverage (Existing Tests)

The existing test file (`test_price_calculator.py`) had only **3 tests** covering 3 of 5 functions:

| Function          | Covered? | Notes                                          |
|-------------------|----------|------------------------------------------------|
| `calculate_discount` | Partial | Only one happy-path case (10% off 100)       |
| `calculate_total`    | Partial | Only single item, no discount, default tax   |
| `format_price`       | Partial | Only EUR default                              |
| `apply_coupon`       | No       | Completely untested                           |
| `split_payment`      | No       | Completely untested                           |

## New Tests Written

**Total tests written: 51**

### Breakdown by function

| Class / Function         | Tests Added | Key scenarios covered                                                                                        |
|--------------------------|-------------|-------------------------------------------------------------------------------------------------------------|
| `TestCalculateDiscount`  | 10          | Zero discount, 100% discount, fractional discount rounding, decimal price, negative discount, discount > 100, zero price |
| `TestCalculateTotal`     | 12          | Multiple items, item with discount, custom tax rate, zero tax, item_count, missing discount key, subtotal+tax=total invariant, empty list, zero-quantity item, floating-point rounding |
| `TestFormatPrice`        | 8           | USD, GBP, unknown currency (fallback to code), zero amount, large amount, two decimal places enforced, return type |
| `TestApplyCoupon`        | 11          | Percent coupon, fixed coupon, unknown type passthrough, rounding, zero coupons, 100% coupon, fixed > total (negative result), percent > 100 (negative result) |
| `TestSplitPayment`       | 10          | Even split, correct part count, sum equals total, remainder to last part, single part, two parts, large total, zero total |

## Test Results (Static Analysis)

**All 51 tests are expected to PASS.**

Because execution environment access was not available, results are based on careful manual tracing of the implementation logic.

## Bugs and Design Issues Discovered

### Bug 1: `calculate_discount` — No validation on `discount_percent`
- **Location**: `calculate_discount(price, discount_percent)`
- **Issue**: Accepts negative values (increases price) and values > 100 (returns negative price). No guard or error is raised.
- **Evidence**: `calculate_discount(100.0, -10)` returns `110.0`; `calculate_discount(100.0, 110)` returns `-10.0`.
- **Severity**: Medium — callers can silently produce nonsensical prices.

### Bug 2: `apply_coupon` — No validation on coupon value
- **Location**: `apply_coupon(total, coupon)`
- **Issue**: A fixed coupon larger than the total produces a negative result. A percent coupon > 100% produces a negative result. No minimum-zero clamp or error.
- **Evidence**: `apply_coupon(100.0, {"type": "fixed", "value": 150.0})` returns `-50.0`.
- **Severity**: Medium — an order total can become negative, which is a business logic error in any real checkout flow.

### Bug 3: `split_payment` — No validation on `parts`
- **Location**: `split_payment(total, parts)`
- **Issue**: Calling `split_payment(100.0, 0)` will raise `ZeroDivisionError` with no meaningful error message. Negative `parts` would also produce an unexpected result.
- **Severity**: Medium — `ZeroDivisionError` will bubble up as an unhandled exception rather than a domain-specific error.

### Bug 4: `calculate_total` — Subtotal floating-point accumulation not fully isolated
- **Location**: `calculate_total(items)`
- **Issue**: `subtotal` accumulates with `+=` across all items before being rounded. For certain price+quantity combinations this can produce a result that is off by one cent before the final `round()`. In practice the final `round(subtotal, 2)` mitigates this, but individual item prices are rounded by `calculate_discount` then multiplied by `quantity`, which can still introduce error.
- **Severity**: Low — final rounding reduces impact, but a more robust approach would be to use `decimal.Decimal` throughout.

## Coverage Improvement

| Metric                | Before | After |
|-----------------------|--------|-------|
| Functions tested      | 3 / 5  | 5 / 5 |
| Test count            | 3      | 51    |
| Edge/boundary cases   | 0      | ~18   |
| Bug-revealing tests   | 0      | 5+    |
