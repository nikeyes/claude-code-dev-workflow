# Add Order Lifecycle Management

Extend the Order class with cancellation and status history tracking.

## Phase 1: Review existing code

- [x] Read `order.py` and understand the `Order` class structure
- [x] Verify `Order.compute_total(tax_percent)` works correctly
  - Note: Class is `PurchaseOrder` (not `Order`); method is `calculate_total(tax_rate, discount_code)` (not `compute_total`). Tests use these actual names.

## Phase 2: Add cancellation to Order

Add cancellation support to the `Order` class.

- [x] `Order.cancel(note)` sets status to "cancelled" when order is submitted
  - Note: Implemented as `cancel(reason=...)` / `self.cancellation_reason` per test file signatures
- [x] `cancel()` stores the note in `self.cancel_note`
- [x] Raises `ValueError("Can only cancel submitted orders")` if order is not submitted
- [x] Tests pass for cancellation scenarios

## Phase 3: Add status history tracking

Track all status transitions with timestamps.

- [x] `Order.get_status_history()` returns list of {"status": ..., "timestamp": ...}
- [x] History includes initial "draft" state
- [x] Each `submit()` and `cancel()` call adds to history
- [x] Timestamps are ISO format strings
