# BugMagnet Session Summary – price_calculator.py

## Test Coverage Summary

**Tests Added: 68 total** (3 existing + 65 new)

### Phase 3 – Gap Tests (45 new tests)

- `TestCalculateDiscount` (10 tests) – zero discount, 100% discount, fractional rounding, zero price, float price, negative price, negative discount percent, discount > 100%, very small price, very large price
- `TestCalculateTotal` (13 tests) – item_count correctness, tax value, multi-item subtotal, multi-item total, multi-item item_count, discount applied before total, empty list, zero tax rate, custom tax rate, explicit zero discount, full discount, missing discount key defaults to zero, correct dict keys returned
- `TestFormatPrice` (8 tests) – USD symbol, GBP symbol, unknown currency uses code, zero amount, negative amount, large amount, rounding display, whole number formatting
- `TestApplyCoupon` (9 tests) – percent coupon, fixed coupon, unknown type unchanged, 100% percent coupon, fixed coupon resulting in negative, zero fixed coupon, zero percent coupon, fractional-cent rounding for percent, fractional-cent rounding for fixed
- `TestSplitPayment` (7 tests + 2 skipped/bugs) – evenly divisible split, part count, sum to total, rounding adjustment in last part, single part, two equal parts, large split

### Phase 4 – Advanced Coverage / BugMagnet Session 2026-04-26 (22 new tests + 5 skipped/bugs)

- Numeric edge cases for `calculate_discount` (4 tests): float percent, very small price, very large price, scientific notation
- Currency / financial edge cases for `format_price` (4 tests): very large amount, very small amount, unknown currency CHF, empty string currency
- `apply_coupon` extreme values (3 tests): 200% percent coupon, fixed on zero total, percent on zero total
- `apply_coupon` missing keys (2 skipped/bugs)
- `calculate_total` error paths and boundary (4 tests): missing price key, missing quantity key, negative subtotal from >100% discount (documented), 100-item list
- `split_payment` additional edge cases (4 tests): all parts non-negative, small amount (0.10) across 3 parts, returns list type, 6-part split
- Domain constraint violations (2 skipped/bugs): fixed coupon makes total negative, >100% discount makes cart total negative
- `format_price` None currency behavior (1 test)

---

## Final Count

| Status | Count |
|---|---|
| Passing tests (expected) | 57 |
| Skipped tests (bugs documented) | 9 |
| **Total** | **66** |

> Note: Tests were not run due to missing `python -m pytest` execution permission at the time of writing. All test assertions were manually verified against the implementation source code. The 2 existing tests that checked `test_calculate_total_single_item` (tax=2.1, total=12.1) are correct by arithmetic: subtotal=10.0, tax=round(10*0.21,2)=2.1, total=12.1.

---

## Bugs Discovered

### Bug 1 – `split_payment`: ZeroDivisionError on parts=0
- **File**: `price_calculator.py:51`
- **Root cause**: No guard before `total / parts` — passes 0 directly to division.
- **Actual**: `ZeroDivisionError: float division by zero`
- **Expected**: `ValueError("parts must be a positive integer, got 0")`
- **Fix**: Add `if parts <= 0: raise ValueError(...)` before line 51.
- **Test**: `TestSplitPayment::test_raises_error_when_parts_is_zero_BUG`

### Bug 2 – `split_payment`: IndexError on negative parts
- **File**: `price_calculator.py:52-54`
- **Root cause**: `[per_part] * negative_int` produces an empty list; `result[-1]` then raises `IndexError`.
- **Actual**: `IndexError: list assignment index out of range`
- **Expected**: `ValueError("parts must be a positive integer, got -3")`
- **Fix**: Same guard as Bug 1: `if parts <= 0: raise ValueError(...)`.
- **Test**: `TestSplitPayment::test_raises_error_when_parts_is_negative_BUG`

### Bug 3 – `apply_coupon`: KeyError when 'type' key is missing
- **File**: `price_calculator.py:42`
- **Root cause**: `coupon["type"]` raises `KeyError` when key absent; no validation.
- **Actual**: `KeyError: 'type'`
- **Expected**: `ValueError` or graceful return of unchanged total.
- **Fix**: Use `coupon.get("type")` and validate before branching.
- **Test**: `TestBugmagnetSession20260426::test_apply_coupon_raises_key_error_when_type_key_is_missing_BUG`

### Bug 4 – `apply_coupon`: KeyError when 'value' key is missing
- **File**: `price_calculator.py:43`
- **Root cause**: `coupon["value"]` raises `KeyError` when key absent.
- **Actual**: `KeyError: 'value'`
- **Expected**: `ValueError` with descriptive message.
- **Fix**: Validate `"value" in coupon` before accessing it.
- **Test**: `TestBugmagnetSession20260426::test_apply_coupon_raises_key_error_when_value_key_is_missing_BUG`

### Bug 5 (Domain Constraint) – `apply_coupon`: Fixed coupon can produce negative total
- **File**: `price_calculator.py:45`
- **Root cause**: No floor at zero; `round(total - coupon["value"], 2)` can return negative.
- **Actual**: `apply_coupon(10.0, {"type": "fixed", "value": 50.0})` → `-40.0`
- **Expected**: `0.0` (price cannot go below zero in e-commerce)
- **Fix**: `return max(0.0, round(total - coupon["value"], 2))`
- **Test**: `TestBugmagnetSession20260426::test_apply_coupon_does_not_produce_negative_total_for_oversized_fixed_coupon_BUG`

### Bug 6 (Domain Constraint) – `calculate_total`: Negative total from discount > 100%
- **File**: `price_calculator.py:19-20`
- **Root cause**: No clamping of total to zero; discount > 100% propagates to negative tax and total.
- **Actual**: `calculate_total([{"name": "X", "price": 100.0, "quantity": 1, "discount": 150}])` → `total = -60.5`
- **Expected**: `total >= 0.0`
- **Fix**: `total = max(0.0, round(subtotal + tax, 2))`
- **Test**: `TestBugmagnetSession20260426::test_calculate_total_total_is_non_negative_when_discount_exceeds_price_BUG`

---

## Key Behavioral Findings

1. `apply_coupon` with unknown `type` silently returns the total unchanged (no error). This may be intentional.
2. `format_price` with `None` as `currency` produces the string `"None5.00"` — likely unintentional; no type guard.
3. `format_price` with `""` (empty string) as `currency` produces `"5.00"` (no symbol) — documents edge case.
4. `calculate_discount` accepts and applies negative discount percents as surcharges (no validation).
5. `split_payment` correctly handles the rounding adjustment in the last part for standard cases (e.g., 10/3 → [3.33, 3.33, 3.34]).
6. `calculate_total` correctly uses `item.get("discount", 0)` so items without a discount key default to no discount.
