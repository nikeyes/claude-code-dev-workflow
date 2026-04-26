# Test Coverage Summary — price_calculator.py

## Tests Added: 43 total

- `calculate_discount` boundary conditions (8 tests)
- `calculate_total` edge cases (10 tests, 1 skipped BUG)
- `format_price` edge cases (8 tests)
- `apply_coupon` edge cases (9 tests, 2 skipped BUGs)
- `split_payment` edge cases (8 tests, 2 skipped BUGs)

## Results: 38 passing, 5 skipped (bugs)

---

## Bugs Discovered

### 1. No floor at zero for `fixed` coupons — `price_calculator.py:45`
- **Root cause:** `apply_coupon` subtracts the fixed value from the total without clamping to 0. When `coupon["value"] > total` the customer receives a negative charge.
- **Proposed fix:** `return max(0.0, round(total - coupon["value"], 2))`

### 2. No ceiling at 100 for `percent` coupons — `price_calculator.py:43`
- **Root cause:** `apply_coupon` does not clamp `coupon["value"]` to 100; values above 100 produce a negative total (store owes the customer money).
- **Proposed fix:** `return max(0.0, round(total - (total * coupon["value"] / 100), 2))`

### 3. Item discount > 100 silently corrupts subtotal — `price_calculator.py:6`
- **Root cause:** `calculate_discount` does not clamp `discount_percent` to `[0, 100]`. When an item carries a discount > 100, `calculate_total` accumulates a negative item price, producing a subtotal lower than it should be.
- **Proposed fix:** In `calculate_discount`: `discount_percent = max(0.0, min(discount_percent, 100.0))`

### 4. `split_payment(total, 0)` raises `ZeroDivisionError` — `price_calculator.py:51`
- **Root cause:** No guard on `parts <= 0`; `total / parts` raises `ZeroDivisionError` instead of a descriptive `ValueError`.
- **Proposed fix:** `if parts <= 0: raise ValueError("parts must be a positive integer")`

### 5. `split_payment(total, -N)` raises `IndexError` — `price_calculator.py:53-54`
- **Root cause:** `[per_part] * -2` produces an empty list; the subsequent `result[-1] = ...` assignment raises `IndexError` on an empty list.
- **Proposed fix:** Same guard as bug #4: `if parts <= 0: raise ValueError(...)`

---

## Coverage Notes

The existing test suite covers three happy-path scenarios (one per function, none for `apply_coupon` or `split_payment`). The new tests cover:

- **Boundary values:** 0%, 100%, >100% discounts; 0 and 1 split parts
- **Empty / zero inputs:** empty item list, zero price, zero tax rate, zero coupon
- **Negative inputs:** negative quantity, negative coupon, negative price
- **Missing / unknown keys:** missing `price`, `quantity`, `type`, `value`; unknown currency codes and coupon types
- **Floating-point accumulation:** repeated 0.10 additions, uneven splits summing to exact total
- **Large inputs:** 1 million-unit quantities, 1000-way payment split
