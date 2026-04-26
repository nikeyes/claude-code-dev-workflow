# Test Desiderata Analysis: test_order_service.ts

**File analyzed:** `core/skills/test-desiderata-workspace/evals/files/test_order_service.ts`
**Framework:** Kent Beck's Test Desiderata (12 properties)
**Date:** 2026-04-26

---

## Summary

The `OrderService` test suite contains 4 tests (`test1`, `test2`, `test3`, `test4 behavioral violation`) across the `describe("OrderService")` block. The tests cover order creation, total calculation, cancellation, and a mocked total. Four violations are seeded in the file and confirmed by analysis; additional secondary issues were found during evaluation.

**Overall assessment:** The suite has significant issues in Readable, Fast, Behavioral, and Writable properties. The Isolated property is acceptable (a fresh `OrderService` instance is created in `beforeEach`). Several other properties are partially satisfied or not applicable to this unit-level suite.

---

## Property-by-Property Evaluation

### 1. Isolated — PASS (with minor note)

Each test gets a fresh `OrderService` instance via `beforeEach(() => { service = new OrderService(); })`. The in-memory `db` Map is therefore reset between tests, so execution order does not affect results.

**Minor note:** `test4` creates a `vi.spyOn` and calls `spy.mockRestore()` at the end. If the test threw before reaching `mockRestore`, the spy could leak into subsequent tests. Using `afterEach(() => vi.restoreAllMocks())` would be more robust.

**No critical violation.**

---

### 2. Composable — PARTIAL ISSUE

The tests do not decompose dimensions of variability (e.g., single-item vs. multi-item orders, integer vs. floating-point prices). `test2` combines order creation and total calculation in one test, which means a failure could originate from either `createOrder` or `getTotal` without isolating which is broken.

**Issue (secondary):**
```
Issue: test2 combines two operations in one test
Location: Lines 60-73
Impact: A failure in createOrder silently prevents getTotal from being tested, masking the actual broken behavior
Fix: Split into separate tests — one asserting createOrder succeeds, one asserting getTotal returns the correct value
Tradeoff: Slight increase in test count; payoff is clearer failure attribution
```

---

### 3. Deterministic — FAIL (via Fast violation)

`test3` uses a real `setTimeout(resolve, 500)` which introduces a wall-clock dependency. While the test itself always resolves (it is not truly flaky in this case), the delay is environmental: on an overloaded CI machine the 500 ms could be longer, and the test cannot be parallelized safely with time-sensitive global timers.

This is addressed in full under **Fast** below.

---

### 4. Fast — FAIL

**Issue:**
```
Issue: test3 uses a real 500 ms setTimeout
Location: Line 77 — await new Promise((resolve) => setTimeout(resolve, 500))
Impact: This single delay adds 500 ms to every test run. With dozens of tests, wall-clock delays accumulate into minutes, destroying fast feedback loops.
Fix: Remove the sleep entirely — the OrderService under test is purely in-memory and needs no delay. If simulating async behavior is the goal, use vi.useFakeTimers() to advance time without real waiting.
Tradeoff: None. The delay has no testing value here.
```

---

### 5. Writable — FAIL

**Issue:**
```
Issue: The same 10-line Order literal is copy-pasted verbatim across test1, test2, test3, and test4
Locations:
  - Lines 48-55 (test1)
  - Lines 62-69 (test2)
  - Lines 79-83 (test3)
  - Lines 92-97 (test4)
Impact: Adding a new field to the Order interface requires updating every test. The friction of writing new tests is high because authors must manually construct the object each time instead of calling a factory.
Fix: Introduce a test factory function, e.g.:
  function makeOrder(overrides: Partial<Order> & { id: string }): Order {
    return {
      customerId: "cust-123",
      items: [
        { sku: "SKU-A", qty: 2, price: 10.0 },
        { sku: "SKU-B", qty: 1, price: 5.0 },
      ],
      ...overrides,
    };
  }
  Each test then calls makeOrder({ id: "ord-001" }) and overrides only what matters for that scenario.
Tradeoff: Small upfront cost to define the factory; long-term it dramatically reduces boilerplate.
```

---

### 6. Readable — FAIL

**Issue:**
```
Issue: Test names (test1, test2, test3, test4 behavioral violation) convey no behavioral intent
Locations:
  - Line 46: it("test1", ...)
  - Line 60: it("test2", ...)
  - Line 75: it("test3", ...)
  - Line 89: it("test4 behavioral violation", ...)
Impact: When a test fails in CI, the only information available is "test1 failed". The reader must open the file and read the body to understand what behavior was expected. This slows debugging and removes the self-documenting value of tests.
Fix: Rename tests to describe the behavior and expected outcome, e.g.:
  - "should return the order id when creating a valid order"
  - "should calculate the total as sum of qty * price for all items"
  - "should succeed when cancelling an existing order"
  - "should throw when getting the total for an unknown order"  ← (currently not tested at all)
Tradeoff: None. Descriptive names cost nothing.
```

**Secondary readability issue:**

`test3` ends with `expect(true).toBe(true)` (line 86). This assertion is vacuous — it always passes and communicates nothing. It should be replaced by a meaningful assertion (e.g., confirming the order no longer exists by asserting that `service.cancelOrder` on the same ID throws).

---

### 7. Behavioral — FAIL

**Issue (primary — mocking the method under test):**
```
Issue: test4 spies on and replaces the very method it is asserting
Location: Lines 91, 98-99
  const spy = vi.spyOn(service, "getTotal").mockResolvedValue(999);
  ...
  expect(total).toBe(999); // tests the mock, not the implementation
Impact: The test does not exercise OrderService.getTotal at all. No matter how broken the implementation is, this test passes. It provides zero behavioral signal and gives false confidence.
Fix: Remove the spy entirely and assert the real computed value:
  await service.createOrder(makeOrder({ id: "ord-004", items: [{ sku: "SKU-D", qty: 1, price: 50.0 }] }));
  const total = await service.getTotal("ord-004");
  expect(total).toBe(50);
Tradeoff: None. The mock adds complexity without benefit.
```

**Issue (secondary — vacuous assertion in test3):**
```
Issue: expect(true).toBe(true) on line 86 is a no-op assertion
Location: Line 86
Impact: The cancelOrder operation could silently throw or fail and the test would still pass (assuming the error propagated through the async chain — but in this case the real issue is intent: the test claims to test cancelOrder but makes no behavioral assertion about it).
Fix: Assert that the cancelled order is no longer retrievable:
  await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
Tradeoff: None.
```

**Issue (missing error-path coverage):**

None of the 4 tests covers the error branches explicitly declared in the implementation:
- `createOrder` throws when `items` is empty
- `getTotal` throws when order is not found
- `cancelOrder` throws when order is not found

These are behavioral guarantees that are untested.

---

### 8. Structure-insensitive — FAIL (test4)

The `vi.spyOn(service, "getTotal")` in `test4` couples the test to the method name `getTotal` as an internal implementation detail on the `service` object. If `getTotal` is renamed or extracted, the spy breaks even if behavior is preserved.

This is a direct consequence of the Behavioral violation: mocking the SUT method also introduces a Structure-insensitive violation.

---

### 9. Automated — PASS

All tests are fully automated. No manual steps, console output requiring human inspection, or interactive prompts are present.

---

### 10. Specific — PARTIAL ISSUE

`test2` asserts `expect(total).toBe(25)` which is specific. However, because `test2` chains `createOrder` and `getTotal` in the same test body, a failure in either operation produces a single failure message that does not point clearly to which method broke.

The vacuous `expect(true).toBe(true)` in `test3` is the opposite extreme: the assertion always passes, so the test can never be specific about a failure.

---

### 11. Predictive — FAIL

The suite does not test:
- `createOrder` with an empty items array (the only validation the implementation has)
- `getTotal` for a non-existent order ID
- `cancelOrder` for a non-existent order ID
- Orders with zero-price or zero-quantity items
- Concurrent or repeated `createOrder` calls with the same ID

These are all production-relevant scenarios that, if broken, would not be caught by the current tests.

---

### 12. Inspiring — FAIL

`test3`'s vacuous `expect(true).toBe(true)` and `test4`'s mock-yourself pattern mean that two of the four tests do not verify any real behavior. A developer looking at this suite would not feel confident that the service is correct for its stated contracts.

---

## Prioritized Violations

| Priority | Property | Severity | Location |
|----------|----------|----------|----------|
| 1 | **Behavioral** | Critical | test4 (lines 91, 98-99): mocks the SUT method, making the test vacuous |
| 2 | **Behavioral** | High | test3 (line 86): vacuous `expect(true).toBe(true)` |
| 3 | **Fast** | High | test3 (line 77): real 500 ms `setTimeout` |
| 4 | **Readable** | High | All tests (lines 46, 60, 75, 89): non-descriptive test names |
| 5 | **Writable** | Medium | All tests: repeated 10-line Order literal boilerplate |
| 6 | **Predictive** | Medium | Entire suite: no error-path tests |
| 7 | **Structure-insensitive** | Medium | test4 (line 91): spy on method name |
| 8 | **Composable** | Low | test2: chains two operations in one test |
| 9 | **Isolated** | Low | test4: mockRestore not in afterEach |

---

## Tradeoff Analysis

- **Fast vs. Predictive:** Adding more tests (error paths, edge cases) will slightly increase run time, but since the suite is in-memory, this tradeoff is minimal.
- **Writable vs. Predictive:** A test factory (fixing Writable) simultaneously lowers the cost of writing the missing error-path tests (fixing Predictive). These properties support each other here.
- **Composable vs. Readable:** Splitting `test2` into two tests (Composable) makes the intent of each clearer (Readable). No conflict.

---

## Recommended Refactored Test Suite (excerpt)

```typescript
import { describe, it, expect, afterEach, vi } from "vitest";

function makeOrder(overrides: { id: string } & Partial<Order>): Order {
  return {
    customerId: "cust-123",
    items: [
      { sku: "SKU-A", qty: 2, price: 10.0 },
      { sku: "SKU-B", qty: 1, price: 5.0 },
    ],
    ...overrides,
  };
}

describe("OrderService", () => {
  let service: OrderService;

  beforeEach(() => { service = new OrderService(); });
  afterEach(() => { vi.restoreAllMocks(); });

  it("returns the order id when creating a valid order", async () => {
    const id = await service.createOrder(makeOrder({ id: "ord-001" }));
    expect(id).toBe("ord-001");
  });

  it("calculates the total as sum of qty * price across all items", async () => {
    await service.createOrder(makeOrder({ id: "ord-002" }));
    const total = await service.getTotal("ord-002");
    expect(total).toBe(25); // 2*10 + 1*5
  });

  it("removes the order so getTotal throws after cancellation", async () => {
    await service.createOrder(makeOrder({ id: "ord-003" }));
    await service.cancelOrder("ord-003");
    await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
  });

  it("computes the real total without mocking", async () => {
    await service.createOrder(makeOrder({ id: "ord-004", items: [{ sku: "SKU-D", qty: 1, price: 50.0 }] }));
    const total = await service.getTotal("ord-004");
    expect(total).toBe(50);
  });

  it("throws when creating an order with no items", async () => {
    await expect(service.createOrder(makeOrder({ id: "ord-005", items: [] }))).rejects.toThrow("Order must have items");
  });

  it("throws when getting the total for an unknown order", async () => {
    await expect(service.getTotal("does-not-exist")).rejects.toThrow("Order not found");
  });

  it("throws when cancelling an unknown order", async () => {
    await expect(service.cancelOrder("does-not-exist")).rejects.toThrow("Order not found");
  });
});
```

This refactored suite:
- Fixes all four seeded violations (Readable, Fast, Behavioral, Writable)
- Adds error-path coverage (Predictive, Inspiring)
- Separates combined operations (Composable)
- Uses `afterEach(vi.restoreAllMocks)` for safer isolation (Isolated)
