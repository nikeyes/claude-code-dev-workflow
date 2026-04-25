# Add Order Lifecycle Management

Extend the Order class with cancellation and status history tracking.

## Phase 1: Review existing code

- [ ] Read `order.py` and understand the `Order` class structure
- [ ] Verify `Order.compute_total(tax_percent)` works correctly

## Phase 2: Add cancellation to Order

Add cancellation support to the `Order` class.

- [ ] `Order.cancel(note)` sets status to "cancelled" when order is submitted
- [ ] `cancel()` stores the note in `self.cancel_note`
- [ ] Raises `ValueError("Can only cancel submitted orders")` if order is not submitted
- [ ] Tests pass for cancellation scenarios

## Phase 3: Add status history tracking

Track all status transitions with timestamps.

- [ ] `Order.get_status_history()` returns list of {"status": ..., "timestamp": ...}
- [ ] History includes initial "draft" state
- [ ] Each `submit()` and `cancel()` call adds to history
- [ ] Timestamps are ISO format strings
