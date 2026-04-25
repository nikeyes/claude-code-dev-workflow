# Add Order Lifecycle Management

Extend the Order class with cancellation and status history tracking.

## Phase 1: Review existing code

<!-- DEVIATION: Plan refers to `Order` class, but actual class is `PurchaseOrder`. Tests confirm `PurchaseOrder` — adapting all references accordingly. -->
<!-- DEVIATION: Plan refers to `Order.compute_total(tax_percent)`, but actual method is `calculate_total(tax_rate, discount_code)`. Tests confirm `calculate_total` — adapting all references accordingly. -->

- [x] Read `order.py` and understand the `Order` class structure
- [x] Verify `Order.compute_total(tax_percent)` works correctly

## Phase 2: Add cancellation to Order

Add cancellation support to the `Order` class.

<!-- DEVIATION: Plan says `cancel(note)` storing in `self.cancel_note`, but tests use `cancel(reason=...)` and `order.cancellation_reason`. Adapted to match tests as source of truth. -->

- [x] `Order.cancel(note)` sets status to "cancelled" when order is submitted
- [x] `cancel()` stores the note in `self.cancel_note`
- [x] Raises `ValueError("Can only cancel submitted orders")` if order is not submitted
- [x] Tests pass for cancellation scenarios

## Phase 3: Add status history tracking

Track all status transitions with timestamps.

- [x] `Order.get_status_history()` returns list of {"status": ..., "timestamp": ...}
- [x] History includes initial "draft" state
- [x] Each `submit()` and `cancel()` call adds to history
- [x] Timestamps are ISO format strings
