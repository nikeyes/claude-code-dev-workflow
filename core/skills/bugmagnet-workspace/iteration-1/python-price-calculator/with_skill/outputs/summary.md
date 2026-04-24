## Test Coverage Summary

**Tests Added: 45 total**
- TestCalculateDiscount (8 tests)
- TestCalculateTotal (9 tests)
- TestFormatPrice (8 tests)
- TestApplyCoupon (8 tests)
- TestSplitPayment (8 tests)
- TestFloatingPointEdgeCases (4 tests)

**Final Count:**
- 42 passing tests
- 3 skipped tests (bugs documented)
- Total: 45 tests

**Bugs Discovered:**
1. apply_coupon produces negative total when fixed coupon exceeds total - price_calculator.py:45
   - Root cause: No minimum-zero clamp in fixed coupon branch
   - Fix: `return max(round(total - coupon["value"], 2), 0)`
   - Minimal reproduction: `apply_coupon(50.0, {"type": "fixed", "value": 100})` returns -50.0

2. apply_coupon produces negative total when percent coupon > 100% - price_calculator.py:43
   - Root cause: No upper bound validation on coupon percent value
   - Fix: Cap value at 100 before calculation
   - Minimal reproduction: `apply_coupon(100.0, {"type": "percent", "value": 150})` returns -50.0

3. split_payment raises ZeroDivisionError for parts=0 - price_calculator.py:51
   - Root cause: No guard clause for parts <= 0
   - Fix: Add `if parts <= 0: raise ValueError("parts must be positive")`
   - Minimal reproduction: `split_payment(100.0, 0)` raises ZeroDivisionError
