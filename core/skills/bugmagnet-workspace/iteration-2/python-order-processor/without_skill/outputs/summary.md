# Order Processor — Test Coverage Analysis & Bug Report

## Summary

| Metric | Value |
|---|---|
| Tests in original file | 3 |
| Tests added (new file) | 79 |
| Total tests | 82 |
| Confirmed bugs | 6 |
| Potential concerns (not bugs per se) | 2 |

---

## Bugs Discovered

### BUG-1: Tax calculated on pre-discount subtotal

**Severity:** High  
**File:** `order_processor.py`, line 237  
**Root cause:** In `OrderProcessor.process()`, `calculate_tax` is called with `subtotal` (the raw item total before order-level discounts), not with the post-discount amount (`discounted`). This causes customers to pay more tax than they should whenever a discount code is applied.

**Reproducing scenario:**
- Subtotal = $100.00, 10% discount code applied → discounted = $90.00  
- US-CA tax rate 7.25%  
- Correct tax: $90.00 × 0.0725 = **$6.53**  
- Actual (buggy) tax: $100.00 × 0.0725 = **$7.25** (+$0.72 overcharge)

**Proposed fix:** Change line 237 to pass `discounted` instead of `subtotal`:
```python
# Before (buggy)
tax = self.pricing.calculate_tax(subtotal, order.shipping_address)

# After (fixed)
tax = self.pricing.calculate_tax(discounted, order.shipping_address)
```

**Covered by:** `TestOrderProcessorProcess::test_tax_calculated_on_pre_discount_subtotal`

---

### BUG-2: Quantity break threshold is exclusive (off-by-one)

**Severity:** Medium  
**File:** `order_processor.py`, line 125  
**Root cause:** The bulk-discount condition is `item.quantity > QUANTITY_BREAK_THRESHOLD` where `QUANTITY_BREAK_THRESHOLD = 10`. Ordering exactly 10 units does **not** qualify for the 5% bulk discount — you need 11+. The semantically correct boundary should almost certainly be `>=`.

**Reproducing scenario:**
- `unit_price=10.0`, `quantity=10` → expected with bulk discount: $95.00, actual: $100.00

**Proposed fix:**
```python
# Before (buggy)
if item.quantity > QUANTITY_BREAK_THRESHOLD:

# After (fixed)
if item.quantity >= QUANTITY_BREAK_THRESHOLD:
```

**Covered by:** `TestPricingEngineLineTotals::test_quantity_break_exactly_at_threshold_does_not_discount`

---

### BUG-3: Fixed order-level discount can produce a negative post-discount total

**Severity:** Medium  
**File:** `order_processor.py`, line 171  
**Root cause:** `apply_discounts` applies a `FIXED` discount by simple subtraction with no floor guard. A discount code with `value > subtotal` makes `discounted` negative, which propagates into the final order total. No `max(0.0, discounted)` guard exists.

**Reproducing scenario:**
- Subtotal = $50.00, FIXED discount code with `value=200.0`  
- Result: discounted = **-$150.00**

**Proposed fix:**
```python
elif discount.discount_type == DiscountType.FIXED:
    discounted = max(0.0, discounted - discount.value)
    applied.append(f"{discount.code}: -{discount.value:.2f}")
```

**Covered by:** `TestPricingEngineDiscounts::test_fixed_discount_exceeding_subtotal_produces_negative_total`

---

### BUG-4: Minimum-order eligibility uses original subtotal, enabling double-stacking below minimum

**Severity:** Low-Medium  
**File:** `order_processor.py`, line 163  
**Root cause:** In `apply_discounts`, the guard `if subtotal < discount.minimum_order` checks against the original `subtotal` parameter (captured at call entry), not against the running `discounted` value. When a first discount reduces the price below a second discount's `minimum_order`, the second discount still applies because the check uses the original total.

**Reproducing scenario:**
- Subtotal = $100, Discount 1 (FIXED $50) → running total = $50  
- Discount 2 has `minimum_order=$60`  
- Check: `$100 >= $60` → True → discount 2 applied even though running total ($50) is below minimum

**Proposed fix:** Change the guard to use the running total:
```python
if discounted < discount.minimum_order:   # was: subtotal
    continue
```

**Covered by:** `TestPricingEngineDiscounts::test_minimum_order_check_uses_original_subtotal_not_running_total`

---

### BUG-5: Loyalty points — truncation happens before member doubling

**Severity:** Low  
**File:** `order_processor.py`, lines 274–277  
**Root cause:** `calculate_loyalty_points` calls `int(total)` first, then doubles for members. The truncation step discards fractional cents before the multiplication, so members can silently lose up to 1 point per transaction.

**Reproducing scenario:**
- `total=99.9`, `is_member=True`  
- Current: `int(99.9) * 2 = 99 * 2 = 198`  
- Expected: `int(99.9 * 2) = int(199.8) = 199`

**Proposed fix:**
```python
def calculate_loyalty_points(self, total: float, is_member: bool = False) -> int:
    multiplied = total * 2 if is_member else total
    return int(multiplied)
```

**Covered by:** `TestLoyaltyPoints::test_member_truncation_order_discards_value`

---

### BUG-6: apply_refund does not restore inventory

**Severity:** High  
**File:** `order_processor.py`, lines 313–357  
**Root cause:** `apply_refund()` recalculates financial totals for the remaining items, but never calls `self.inventory.release()` for the returned items. Stock is permanently consumed even after a complete refund, causing inventory counts to drift lower over time.

**Reproducing scenario:**
- Initial stock P1: 10 → process order (qty=1) → stock = 9  
- Call `apply_refund(processed, ["P1"], ...)` → stock remains **9**, should be **10**

**Proposed fix:** Add a release call at the start of `apply_refund`:
```python
refund_order_items = [
    OrderItem(product_id=item["product_id"], name=item["name"],
              unit_price=item["unit_price"], quantity=item["quantity"])
    for item in refund_items
]
self.inventory.release(refund_order_items)
```

**Covered by:** `TestApplyRefund::test_refund_does_not_restore_inventory`

---

## Additional Concerns (Not Confirmed Bugs)

### CONCERN-1: Zero unit_price items accepted silently
Validation allows `unit_price=0.0`. This may be intentional (free promotional items) but could also indicate missing validation if zero-price items should never appear in paid orders.

### CONCERN-2: Negative loyalty points not guarded
`calculate_loyalty_points` returns a negative integer when `total < 0.0` (which can happen due to BUG-3). No floor at 0 exists.

---

## Coverage Assessment

| Area | Original Tests | New Tests | Coverage Notes |
|---|---|---|---|
| `Inventory` | 0 | 10 | Full CRUD coverage including edge cases |
| `PricingEngine.calculate_line_total` | 0 | 9 | All branches: no discount, %, fixed, qty break boundaries |
| `PricingEngine.calculate_subtotal` | 0 | 4 | Empty list, single, multi, key fields |
| `PricingEngine.apply_discounts` | 1 (via process) | 10 | Stacking, minimum_order, negative total, 100% |
| `PricingEngine.calculate_tax` | 0 | 5 | All known regions, unknown, zero rate |
| `PricingEngine.calculate_shipping` | 0 | 6 | Threshold exact/above/below, unknown country |
| `OrderProcessor.validate` | 1 | 9 | All error paths, multiple errors |
| `OrderProcessor.process` | 1 | 9 | Happy path, error path, tax/shipping bugs |
| `OrderProcessor.process_batch` | 0 | 6 | Full success, partial failure, empty batch |
| `OrderProcessor.calculate_loyalty_points` | 0 | 5 | Member/non-member, truncation order bug |
| `OrderProcessor.generate_invoice` | 0 | 8 | All conditional sections |
| `OrderProcessor.apply_refund` | 0 | 8 | Partial/full refund, inventory bug, proportional discount |
| Boundary/Integration | 1 | 8 | Threshold boundaries, cross-component flows |
