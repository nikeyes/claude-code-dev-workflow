# Plan: Extract PaymentService from OrderService

## Goal

Extract the payment processing logic from `OrderService` into a standalone `PaymentService` class,
without breaking existing tests or changing observable behavior.

## Context

`OrderService` currently owns three concerns:
- Order management (`create_order`, `get_order`, `list_orders_for_customer`)
- Payment processing (`charge_order`, `refund_order`, `_call_payment_gateway`, `_call_payment_refund`)
- Shipping (`ship_order`, `_call_shipping_provider`)

Only payment is extracted in this plan. Shipping is a separate future concern.

---

## Step 1 — Write a failing test for PaymentService in isolation

Create `test_payment_service.py` with tests that target a `PaymentService` class that does not exist yet.

Tests to write:
- `test_charge_succeeds_with_valid_token` — `charge(amount, card_token)` returns a payment id string
- `test_charge_fails_with_empty_token` — returns `None`
- `test_charge_fails_with_zero_amount` — returns `None`
- `test_refund_succeeds` — `refund(payment_id, amount)` returns `True`
- `test_refund_fails_with_empty_payment_id` — returns `False`

These tests must fail before any new code exists (red phase).

---

## Step 2 — Create PaymentService to make the new tests pass

Create `payment_service.py` with a `PaymentService` class that owns the gateway logic.

```
class PaymentService:
    def __init__(self, gateway_url: str = "https://payments.internal/v1"):
        self._gateway_url = gateway_url

    def charge(self, amount: float, card_token: str) -> Optional[str]:
        """Returns a payment_id on success, None on failure."""
        if not card_token or amount <= 0:
            return None
        # simulate: same rule as _call_payment_gateway
        return f"pay_{uuid.uuid4().hex[:8]}"

    def refund(self, payment_id: str, amount: float) -> bool:
        """Returns True on success, False on failure."""
        return bool(payment_id) and amount > 0
```

Run `test_payment_service.py` — all tests must pass (green phase).
Run `test_order_service.py` — all tests must still pass (no regression).

---

## Step 3 — Inject PaymentService into OrderService (keeping old behavior)

Change `OrderService.__init__` to accept an optional `PaymentService` parameter:

```python
def __init__(self, payment_service: Optional[PaymentService] = None):
    self._payment_service = payment_service or PaymentService()
    self._orders: dict[str, Order] = {}
    self._shipping_provider_url = "https://shipping.internal/v1"
    # _payment_gateway_url no longer needed here
```

This is a backwards-compatible change: existing callers `OrderService()` continue to work.

Run both test files — all tests must still pass.

---

## Step 4 — Delegate charge_order to PaymentService

Replace the body of `charge_order` to call `self._payment_service.charge(...)` instead of
`self._call_payment_gateway(...)`.

Before:
```python
payment_id = f"pay_{order_id[:8]}"
success = self._call_payment_gateway(card_token, order.total)
```

After:
```python
payment_id = self._payment_service.charge(order.total, card_token)
success = payment_id is not None
```

Run both test files — all tests must still pass.

---

## Step 5 — Delegate refund_order to PaymentService

Replace the body of `refund_order` to call `self._payment_service.refund(...)` instead of
`self._call_payment_refund(...)`.

Before:
```python
success = self._call_payment_refund(order.payment_id, order.total)
```

After:
```python
success = self._payment_service.refund(order.payment_id, order.total)
```

Run both test files — all tests must still pass.

---

## Step 6 — Delete the now-dead private methods from OrderService

Remove `_call_payment_gateway` and `_call_payment_refund` from `OrderService`.
Also remove the `_payment_gateway_url` attribute if it is no longer referenced.

Run both test files — all tests must still pass.

---

## Step 7 — Refactor and cleanup (optional, while tests stay green)

- Add a `PaymentServiceProtocol` (or ABC) if other implementations are anticipated.
- Move `PaymentService` to its own module/package boundary if deploying as a separate process.
- Update `process_order` docstring to reflect the delegation.
- Remove the `# Simplified:` comments inside `PaymentService` and replace with proper docstrings.

---

## Acceptance Criteria

- `test_order_service.py` — all 11 existing tests pass without modification.
- `test_payment_service.py` — all new payment-specific tests pass.
- `OrderService` contains no direct payment gateway logic (no `_call_payment_gateway`, no `_call_payment_refund`).
- `PaymentService` has no knowledge of `Order` objects or order state.
- No test file is deleted or altered to make tests pass.

---

## Risk Notes

- `charge_order` currently derives `payment_id` from `order_id[:8]`. The new `PaymentService.charge`
  generates its own id. Existing tests only check `payment_id is not None`, so this is safe. If
  deterministic ids are required downstream, pass `order_id` as a hint to `charge()`.
- `OrderService` and `PaymentService` share in-process memory in this plan. True microservice
  extraction (HTTP boundary, separate deployment) is a follow-on step beyond this plan.
