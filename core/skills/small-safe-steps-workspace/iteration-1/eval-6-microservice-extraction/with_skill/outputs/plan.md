# Small Safe Steps Plan: Extract PaymentService Microservice from OrderService

## Goal

Extract the payment processing logic (`charge_order`, `refund_order`, `_call_payment_gateway`, `_call_payment_refund`) from `OrderService` into a separate `PaymentService` microservice, with zero downtime and full test coverage preserved at each step.

## Why This Is a Risky Change

This is an **architecture change** (monolith to microservice extraction), which is a breaking change by nature:

- `OrderService` currently owns the payment state (`payment_id`) and the payment lifecycle
- `charge_order` and `refund_order` are called directly by `process_order` (full lifecycle method)
- 5 existing tests exercise payment behavior through `OrderService` directly
- Moving to a separate service changes the call boundary (in-process → network/HTTP)
- Failure modes change (a local method call cannot time out; a network call can)

**Decision: Apply Expand-Contract Pattern.**

---

## Phases Overview

| Phase | Name | Goal | Duration |
|-------|------|------|----------|
| 1 | EXPAND | Build PaymentService alongside OrderService | ~2 weeks |
| 2 | MIGRATE | Route payment calls through PaymentService | ~1 week |
| 3 | CONTRACT | Remove payment logic from OrderService | ~1 week |

**Total estimated effort:** ~18-24 hours of active work spread over 3-5 weeks.

---

## Phase 1: EXPAND — Build PaymentService Alongside OrderService

**Goal:** A standalone `PaymentService` exists, is tested, and deployed — but `OrderService` still handles all payment calls. Zero users are affected.

### Step 1.1 — Learning: Audit all payment-related code and tests (1-2h)

**Type:** Learning step (time-boxed)

- Read `order_service.py` and identify every method touching payment logic:
  - `charge_order` (validates status, calls `_call_payment_gateway`, sets `payment_id` and `status`)
  - `refund_order` (validates `payment_id`, calls `_call_payment_refund`, sets `status`)
  - `_call_payment_gateway` (stub for HTTP POST to `https://payments.internal/v1`)
  - `_call_payment_refund` (stub for HTTP POST to `https://payments.internal/v1/refund`)
- Read `test_order_service.py` and catalog all tests that exercise payment:
  - `test_charge_order_success`
  - `test_charge_order_invalid_token`
  - `test_charge_already_paid_order`
  - `test_refund_order`
  - `test_process_order_full_lifecycle` (end-to-end, includes payment)
- Document: What data does `PaymentService` need? (`card_token`, `amount`, `payment_id`)
- Document: What does `OrderService` need back from `PaymentService`? (`payment_id`, `success: bool`)
- Output: Short decision document — interface contract for `PaymentService`

**Reversible:** Yes — no code written yet.
**Deployable:** Artifact (document).

---

### Step 1.2 — Create `PaymentService` class with identical logic (2-3h)

**Type:** Earning step

- Create `payment_service.py` in the same repository (not a separate repo yet — reduces coordination overhead)
- Implement `PaymentService` as an exact copy of the payment methods from `OrderService`:

```python
class PaymentService:
    def __init__(self, gateway_url: str = "https://payments.internal/v1"):
        self._payment_gateway_url = gateway_url

    def charge(self, order_id: str, card_token: str, amount: float) -> Optional[str]:
        """Returns payment_id on success, None on failure."""
        success = self._call_payment_gateway(card_token, amount)
        if success:
            return f"pay_{order_id[:8]}"
        return None

    def refund(self, payment_id: str, amount: float) -> bool:
        return self._call_payment_refund(payment_id, amount)

    def _call_payment_gateway(self, card_token: str, amount: float) -> bool:
        return bool(card_token) and amount > 0

    def _call_payment_refund(self, payment_id: str, amount: float) -> bool:
        return bool(payment_id) and amount > 0
```

- Note: The interface is slightly different from `OrderService` — `PaymentService` takes `amount` and `order_id` directly rather than looking them up. This is intentional: the service owns payment logic only, not order state.
- `OrderService` is **not changed at all** in this step.
- Verify: `OrderService` tests still pass unchanged.

**Reversible:** Yes — delete `payment_service.py`.
**Deployable:** Yes — `payment_service.py` is in the repo but unused.

---

### Step 1.3 — Write tests for `PaymentService` in isolation (1-2h)

**Type:** Earning step

- Create `test_payment_service.py`
- Cover all behaviors independently of `OrderService`:
  - `test_charge_returns_payment_id_on_success`
  - `test_charge_returns_none_for_empty_token`
  - `test_charge_returns_none_for_zero_amount`
  - `test_refund_returns_true_for_valid_payment_id`
  - `test_refund_returns_false_for_empty_payment_id`
- All tests must pass.
- Run the full suite: `pytest` — both `test_order_service.py` and `test_payment_service.py` must be green.

**Reversible:** Yes — delete `test_payment_service.py`.
**Deployable:** Yes — tests are additive.

---

### Step 1.4 — Add shadow dual-call inside `OrderService` (2-3h)

**Type:** Earning step (shadow mode — learning in production)

This is the key "expand" step: `OrderService` calls **both** its own payment logic and `PaymentService`, but still uses its own result. This lets us compare outputs in production with zero user impact.

- Modify `OrderService.__init__` to instantiate `PaymentService`:

```python
def __init__(self):
    self._orders: dict[str, Order] = {}
    self._payment_gateway_url = "https://payments.internal/v1"
    self._shipping_provider_url = "https://shipping.internal/v1"
    self._payment_service = PaymentService()  # shadow call
```

- Modify `charge_order` to dual-call and log discrepancies:

```python
def charge_order(self, order_id: str, card_token: str) -> bool:
    order = self._orders.get(order_id)
    if order is None or order.status != "pending":
        return False

    # Original path (still authoritative)
    payment_id = f"pay_{order_id[:8]}"
    success = self._call_payment_gateway(card_token, order.total)

    # Shadow call to PaymentService (compare but don't use result yet)
    shadow_payment_id = self._payment_service.charge(order_id, card_token, order.total)
    shadow_success = shadow_payment_id is not None
    if shadow_success != success:
        # Log discrepancy — in production this would go to observability/alerting
        print(f"[shadow] charge discrepancy: original={success}, shadow={shadow_success}, order={order_id}")

    if success:
        order.payment_id = payment_id
        order.status = "paid"
        self._orders[order_id] = order
    return success
```

- Modify `refund_order` similarly:

```python
def refund_order(self, order_id: str) -> bool:
    order = self._orders.get(order_id)
    if order is None or order.payment_id is None:
        return False

    # Original path (still authoritative)
    success = self._call_payment_refund(order.payment_id, order.total)

    # Shadow call
    shadow_success = self._payment_service.refund(order.payment_id, order.total)
    if shadow_success != success:
        print(f"[shadow] refund discrepancy: original={success}, shadow={shadow_success}, order={order_id}")

    if success:
        order.status = "refunded"
        self._orders[order_id] = order
    return success
```

- Run `pytest` — all existing tests must still pass (behavior unchanged).

**Reversible:** Yes — revert `OrderService` changes, shadow calls removed.
**Deployable:** Yes — behavior is identical to before; shadow logs are additive.

---

### Phase 1 Checklist

- [ ] `PaymentService` exists and has its own passing test suite
- [ ] `OrderService` dual-calls `PaymentService` in shadow mode
- [ ] All original `test_order_service.py` tests still pass
- [ ] No discrepancies observed in shadow logs (in a real system: monitor for 1 week)

---

## Phase 2: MIGRATE — Route Payment Calls Through PaymentService

**Goal:** `OrderService` delegates payment decisions to `PaymentService` and uses its result as the authoritative answer. Dual-call is still active as safety net.

### Step 2.1 — Switch `charge_order` to use `PaymentService` result (1-2h)

**Type:** Earning step

- Change `charge_order` so `PaymentService` is now authoritative; original logic is the shadow:

```python
def charge_order(self, order_id: str, card_token: str) -> bool:
    order = self._orders.get(order_id)
    if order is None or order.status != "pending":
        return False

    # New authoritative call
    new_payment_id = self._payment_service.charge(order_id, card_token, order.total)
    new_success = new_payment_id is not None

    # Old logic in shadow (still dual-calling for safety)
    old_success = self._call_payment_gateway(card_token, order.total)
    if old_success != new_success:
        print(f"[shadow] charge discrepancy: new={new_success}, old={old_success}, order={order_id}")

    if new_success:
        order.payment_id = new_payment_id
        order.status = "paid"
        self._orders[order_id] = order
    return new_success
```

- Run `pytest` — all tests must pass.

**Reversible:** Yes — flip which result is authoritative.
**Deployable:** Yes.

---

### Step 2.2 — Switch `refund_order` to use `PaymentService` result (1-2h)

**Type:** Earning step

- Same pattern as Step 2.1 for refunds:

```python
def refund_order(self, order_id: str) -> bool:
    order = self._orders.get(order_id)
    if order is None or order.payment_id is None:
        return False

    # New authoritative call
    new_success = self._payment_service.refund(order.payment_id, order.total)

    # Old logic in shadow
    old_success = self._call_payment_refund(order.payment_id, order.total)
    if old_success != new_success:
        print(f"[shadow] refund discrepancy: new={new_success}, old={old_success}, order={order_id}")

    if new_success:
        order.status = "refunded"
        self._orders[order_id] = order
    return new_success
```

- Run `pytest` — all tests must pass.
- Monitor shadow logs for 1 week (in production): confirm zero discrepancies.

**Reversible:** Yes — flip authoritative result.
**Deployable:** Yes.

---

### Phase 2 Checklist

- [ ] `charge_order` uses `PaymentService` as authoritative, old logic as shadow
- [ ] `refund_order` uses `PaymentService` as authoritative, old logic as shadow
- [ ] All tests pass
- [ ] Zero discrepancies in shadow logs for at least 1 week
- [ ] Rollback plan confirmed: flip feature flag / swap authoritative call

---

## Phase 3: CONTRACT — Remove Payment Logic from OrderService

**Goal:** `OrderService` contains no payment logic. `PaymentService` is the sole owner. Old code is deleted cleanly.

### Step 3.1 — Remove shadow (old) payment calls from `OrderService` (1h)

**Type:** Earning step

- Remove all calls to `_call_payment_gateway` and `_call_payment_refund` from `charge_order` and `refund_order`
- Remove the shadow logging
- Clean up: `charge_order` and `refund_order` now only call `self._payment_service.*`:

```python
def charge_order(self, order_id: str, card_token: str) -> bool:
    order = self._orders.get(order_id)
    if order is None or order.status != "pending":
        return False
    new_payment_id = self._payment_service.charge(order_id, card_token, order.total)
    if new_payment_id is not None:
        order.payment_id = new_payment_id
        order.status = "paid"
        self._orders[order_id] = order
    return new_payment_id is not None

def refund_order(self, order_id: str) -> bool:
    order = self._orders.get(order_id)
    if order is None or order.payment_id is None:
        return False
    success = self._payment_service.refund(order.payment_id, order.total)
    if success:
        order.status = "refunded"
        self._orders[order_id] = order
    return success
```

- Run `pytest` — all tests must pass.

**Reversible:** Still easy — `_call_payment_gateway` not yet deleted.
**Deployable:** Yes.

---

### Step 3.2 — Delete `_call_payment_gateway` and `_call_payment_refund` from `OrderService` (30min)

**Type:** Earning step

- Delete the two private methods from `OrderService`:
  - `_call_payment_gateway`
  - `_call_payment_refund`
- Delete `self._payment_gateway_url` from `__init__` (no longer needed by `OrderService`)
- Run `pytest` — all tests must pass.

**Reversible:** Recoverable from git history.
**Deployable:** Yes.

---

### Step 3.3 — Update `test_order_service.py` to inject `PaymentService` for isolation (1-2h)

**Type:** Earning step

- `OrderService` now depends on `PaymentService`. For tests that only care about order management, inject a test double to avoid payment coupling:

```python
@pytest.fixture
def svc():
    service = OrderService()
    return service  # PaymentService injected by default, no change needed for most tests
```

- Optionally, add a constructor parameter to allow injection:

```python
class OrderService:
    def __init__(self, payment_service: Optional[PaymentService] = None):
        self._payment_service = payment_service or PaymentService()
        ...
```

- This makes tests more resilient and the dependency explicit.
- Run `pytest` — all tests must pass.

**Reversible:** Yes.
**Deployable:** Yes.

---

### Step 3.4 — Final cleanup and documentation (30min-1h)

**Type:** Earning step

- Remove shadow logging code if any remains
- Ensure `OrderService` docstring reflects the new architecture (delegates payment to `PaymentService`)
- Verify no references to old payment methods exist in `order_service.py`:

```bash
grep -n "_call_payment" order_service.py  # Should return nothing
grep -n "payment_gateway_url" order_service.py  # Should return nothing
```

- Final `pytest` run — full suite green.

**Reversible:** N/A — documentation only.
**Deployable:** Yes.

---

### Phase 3 Checklist

- [ ] `_call_payment_gateway` and `_call_payment_refund` deleted from `OrderService`
- [ ] `self._payment_gateway_url` removed from `OrderService.__init__`
- [ ] `OrderService` only calls `self._payment_service.charge(...)` and `self._payment_service.refund(...)`
- [ ] All original tests still pass
- [ ] `PaymentService` has its own independent test suite
- [ ] No payment logic in `order_service.py`

---

## Final Self-Check

- [x] Every step takes 1-3 hours (no step exceeds this)
- [x] Every step is deployable to production (or creates verifiable artifact)
- [x] Every step is reversible at every phase
- [x] Risky change uses expand-contract pattern (Expand → Migrate → Contract)
- [x] Learning steps are separated from earning steps (Step 1.1 is time-boxed research)
- [x] Dual-call is active during the entire migrate phase (Steps 2.1 and 2.2)
- [x] Contract phase only starts after shadow monitoring confirms zero discrepancies
- [x] Each phase is independently valuable

---

## Summary Timeline

| Step | Description | Type | Time |
|------|-------------|------|------|
| 1.1 | Audit payment code and define interface | Learning | 1-2h |
| 1.2 | Create `PaymentService` with identical logic | Earning | 2-3h |
| 1.3 | Write isolated tests for `PaymentService` | Earning | 1-2h |
| 1.4 | Add shadow dual-call in `OrderService` | Earning | 2-3h |
| — | Monitor shadow logs in production | Passive | 1 week |
| 2.1 | Switch `charge_order` to `PaymentService` | Earning | 1-2h |
| 2.2 | Switch `refund_order` to `PaymentService` | Earning | 1-2h |
| — | Monitor for discrepancies | Passive | 1 week |
| 3.1 | Remove shadow calls from `OrderService` | Earning | 1h |
| 3.2 | Delete `_call_payment_gateway/_refund` | Earning | 30min |
| 3.3 | Make `PaymentService` injectable in `OrderService` | Earning | 1-2h |
| 3.4 | Final cleanup and documentation | Earning | 30min-1h |

**Total active work:** ~15-20 hours
**Total calendar time:** ~3-5 weeks (due to monitoring periods)
