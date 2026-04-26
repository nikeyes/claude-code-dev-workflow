# Bug Discovery Summary — order_processor.py

## Scope

- **Implementation**: `order_processor.py` — e-commerce order processing pipeline
- **Existing tests**: `test_order_processor.py` — 3 happy-path tests only
- **New test file**: `test_order_processor_edge_cases.py`

---

## Confirmed Bugs

### BUG-1 — Tax calculated on pre-discount subtotal (incorrect taxable base)
**Location**: `OrderProcessor.process()` line 237
**Severity**: High — customers are always overtaxed when discounts are applied

In `process()`, tax is calculated using `self.pricing.calculate_tax(subtotal, ...)` instead of `self.pricing.calculate_tax(discounted, ...)`. The `discounted` variable (post-discount amount) is computed just before the tax call, but the raw `subtotal` is passed instead. This means a 50% discount on a $100 order still results in tax being levied on $100 rather than $50.

**Test**: `TestProcessTaxBug::test_tax_is_calculated_on_subtotal_not_discounted_amount`

---

### BUG-2 — Fixed item discount can make a line total negative
**Location**: `PricingEngine.calculate_line_total()` lines 130–131
**Severity**: Medium — an invalid negative line total corrupts every downstream calculation

When `discount_type == DiscountType.FIXED` and `discount_value` exceeds the base price, `base -= item.discount_value` returns a negative number. There is no floor at `0.0`.

**Test**: `TestCalculateLineTotal::test_fixed_item_discount_larger_than_line_total_produces_negative`

---

### BUG-3 — Percentage item discount > 100% makes line total negative
**Location**: `PricingEngine.calculate_line_total()` line 129
**Severity**: Medium — same downstream corruption as BUG-2

`base *= 1 - item.discount_value / 100` with a `discount_value` of 150 yields `base *= -0.5`, producing a negative line total. No validation prevents this.

**Test**: `TestCalculateLineTotal::test_percentage_discount_over_100_percent_gives_negative`

---

### BUG-4 — Order-level fixed discount can drive total below zero
**Location**: `PricingEngine.apply_discounts()` line 171
**Severity**: Medium — negative order totals could corrupt payment processing

When `discount_type == DiscountType.FIXED` and `discount.value` exceeds the current `discounted` running total, the result is negative. No floor at `0.0` is applied.

**Test**: `TestApplyDiscounts::test_fixed_discount_larger_than_subtotal_produces_negative_total`

---

### BUG-5 — `minimum_order` check compares against original subtotal, not running total
**Location**: `PricingEngine.apply_discounts()` line 163
**Severity**: Medium — later discounts with a minimum can apply even after prior discounts pushed the running total below the minimum

`if subtotal < discount.minimum_order` uses the captured `subtotal` parameter, not `discounted` (the running total). A second discount whose minimum is, say, $60 will still be applied if the original subtotal was $80, even after the first discount dropped the running total to $40.

**Test**: `TestApplyDiscounts::test_minimum_order_check_uses_original_subtotal_not_running_total`

---

### BUG-6 — Quantity break threshold uses strict `>` instead of `>=`
**Location**: `PricingEngine.calculate_line_total()` line 125
**Severity**: Low — off-by-one boundary; customers ordering exactly 10 units do not receive the bulk discount

`if item.quantity > QUANTITY_BREAK_THRESHOLD` skips items with exactly 10 units (the threshold value). Depending on intent, the threshold is likely inclusive (`>=`).

**Test**: `TestCalculateLineTotal::test_quantity_exactly_at_break_threshold_does_not_get_discount`

---

### BUG-7 — Whitespace-only customer ID passes validation
**Location**: `OrderProcessor.validate()` line 214
**Severity**: Low — `if not order.customer_id` evaluates to `False` for `"   "`, allowing a technically empty identity through

**Test**: `TestValidate::test_whitespace_only_customer_id_passes_validation`

---

### BUG-8 — `calculate_loyalty_points` returns negative points for negative totals
**Location**: `OrderProcessor.calculate_loyalty_points()` line 274
**Severity**: Low — if a negative total somehow reaches this method (possible given BUG-2/4), points become negative

`int(total)` where `total < 0` yields a negative integer with no floor at 0.

**Test**: `TestCalculateLoyaltyPoints::test_negative_total_gives_negative_points`

---

## Coverage Gaps in Existing Tests

| Area | Gap |
|---|---|
| `calculate_line_total` | No tests for quantity break threshold (boundary, below, above) |
| `calculate_line_total` | No tests for item-level discounts (percentage or fixed) |
| `apply_discounts` | No tests for minimum_order enforcement |
| `apply_discounts` | No tests for multiple discounts compounding |
| `calculate_tax` | No tests at all — unknown region, zero amount, EU rates |
| `calculate_shipping` | No tests at all — free-shipping boundary, unknown country fallback |
| `validate` | No tests for zero/negative quantity, negative price, missing customer ID |
| `validate` | No tests for out-of-stock or unknown product |
| `Inventory` | No tests for `reserve`, `release`, `get_stock`, or concurrent checks |
| `process_batch` | No tests at all |
| `calculate_loyalty_points` | No tests at all |
| `generate_invoice` | No tests at all |
| `apply_refund` | No tests at all |

---

## Test File Overview

**File**: `test_order_processor_edge_cases.py`
**Test classes**: 13
**Test count**: 57

| Class | Focus |
|---|---|
| `TestCalculateLineTotal` | Item-level pricing boundaries and discount math |
| `TestApplyDiscounts` | Order-level discount application and minimum_order logic |
| `TestCalculateTax` | Tax rate lookup including unknowns and zero amounts |
| `TestCalculateShipping` | Free-shipping boundary and unknown country fallback |
| `TestValidate` | All validation error branches |
| `TestProcessTaxBug` | Documents the pre-discount taxable-base bug |
| `TestProcessOrderId` | Sequential order ID counter and inventory side-effects |
| `TestInventory` | Stock reservation, release, and edge cases |
| `TestProcessBatch` | Batch processing including empty input and mixed results |
| `TestCalculateLoyaltyPoints` | Point calculation including zero and negative totals |
| `TestGenerateInvoice` | Invoice formatting for all conditional sections |
| `TestApplyRefund` | Partial/full refunds, missing products, zero-subtotal guard |

---

## Testing Notes

Tests that document current **buggy** behavior are annotated with a comment explaining what the correct behavior should be. They are written to pass against the current implementation, serving as characterisation tests that will fail when the bugs are fixed — acting as regression guards during repair.
