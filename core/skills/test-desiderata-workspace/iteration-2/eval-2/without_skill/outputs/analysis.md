# Test Quality Analysis: test_order_service.ts

## Overview

The file under review is `/evals/files/test_order_service.ts`, a Vitest test suite for an `OrderService` class. The file itself contains comment annotations calling out intentional violations. This analysis independently identifies and expands on each problem and provides concrete recommendations.

---

## Issues Found

### 1. Unreadable Test Names (Readable violation)

**Location**: `it("test1", ...)`, `it("test2", ...)`, `it("test3", ...)`

**Problem**: Three of the four test names (`test1`, `test2`, `test3`) communicate nothing about the behavior being verified. A developer reading a test failure sees only `OrderService > test1`, with no indication of what broke or what was expected.

**Recommendation**: Rename each test to describe the scenario and expected outcome in plain language. Use the pattern "given [context], [subject] [expected outcome]" or the simpler "should [behavior] when [condition]".

Examples:
```typescript
it("returns the order id when a valid order is created")
it("calculates the correct total by summing qty * price across all items")
it("removes the order from the store when cancelled")
it("returns the real computed total, not a stubbed value")
```

---

### 2. Real `setTimeout` Delay in a Unit Test (Fast violation)

**Location**: `test3`, line 77

**Problem**:
```typescript
await new Promise((resolve) => setTimeout(resolve, 500));
```
This introduces a real 500 ms wall-clock wait with no purpose — it does not simulate any production behavior nor is it needed for the `OrderService` logic. Unit tests should run in milliseconds. A suite with many tests like this would become prohibitively slow.

**Recommendation**: Remove the delay entirely. If the intent is to test async behavior, `OrderService` methods already return real Promises and no artificial pause is needed. If a delay were meaningful (e.g., testing a timeout mechanism), use Vitest's fake timers (`vi.useFakeTimers()`) instead of real `setTimeout`.

---

### 3. Mocking the Method Under Test (Behavioral violation)

**Location**: `test4 behavioral violation`, lines 91–101

**Problem**:
```typescript
const spy = vi.spyOn(service, "getTotal").mockResolvedValue(999);
// ...
const total = await service.getTotal("ord-004");
expect(total).toBe(999);
```
The test mocks `getTotal` — the exact method it claims to test — and then asserts that the mock returns the value it was configured to return. This is tautological: the test exercises only the mocking framework, not the production code. If the real `getTotal` were completely broken, this test would still pass.

**Recommendation**: Remove the spy and assert against the real computed value. If the goal is to verify that `getTotal` correctly computes `qty * price` for a single item:
```typescript
it("calculates total as qty * price for a single-item order", async () => {
  const order: Order = {
    id: "ord-004",
    customerId: "cust-001",
    items: [{ sku: "SKU-D", qty: 1, price: 50.0 }],
  };
  await service.createOrder(order);
  const total = await service.getTotal("ord-004");
  expect(total).toBe(50.0);
});
```

---

### 4. Vacuous Assertion (Behavioral violation)

**Location**: `test3`, line 86

**Problem**:
```typescript
expect(true).toBe(true);
```
This assertion always passes regardless of any production behavior. It provides zero signal. Even if `cancelOrder` threw an exception before reaching this line, the test would fail for the wrong reason (unhandled rejection rather than an assertion).

**Recommendation**: Assert the actual post-condition. After cancelling an order, verify the order no longer exists by asserting that a subsequent `getTotal` call throws:
```typescript
await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
```

---

### 5. Duplicated Order-Construction Boilerplate (Writable violation)

**Location**: `test1` (lines 48–55), `test2` (lines 62–69), `test3` (lines 79–83), `test4` (lines 92–96)

**Problem**: Each test independently constructs a near-identical `Order` object with the same shape and similar values. This is mechanical repetition that makes tests harder to read and maintain — changing the `Order` interface requires updating four sites.

**Recommendation**: Extract a factory function or helper into the test file:
```typescript
function buildOrder(overrides: Partial<Order> & { id: string }): Order {
  return {
    customerId: "cust-123",
    items: [
      { sku: "SKU-A", qty: 2, price: 10.0 },
      { sku: "SKU-B", qty: 1, price: 5.0 },
    ],
    ...overrides,
  };
}
```
Each test then calls `buildOrder({ id: "ord-001" })` or overrides only what is relevant to that scenario, making the unique aspects of each test stand out clearly.

---

### 6. Missing Error-Path Tests (Behavioral gap)

**Problem**: The `OrderService` has three guard clauses that throw errors:
- `createOrder` throws when `items` is empty
- `getTotal` throws when the order does not exist
- `cancelOrder` throws when the order does not exist

None of these paths are tested. A future refactor that silently swallows errors, changes the error message, or returns a fallback value instead of throwing would go undetected.

**Recommendation**: Add tests for each error path:
```typescript
it("throws when creating an order with no items", async () => {
  await expect(
    service.createOrder({ id: "ord-x", customerId: "c", items: [] })
  ).rejects.toThrow("Order must have items");
});

it("throws when getting total for a non-existent order", async () => {
  await expect(service.getTotal("missing")).rejects.toThrow("Order not found");
});

it("throws when cancelling a non-existent order", async () => {
  await expect(service.cancelOrder("missing")).rejects.toThrow("Order not found");
});
```

---

## Summary Table

| # | Violation | Affected Tests | Severity |
|---|-----------|----------------|----------|
| 1 | Unreadable names | test1, test2, test3 | High |
| 2 | Real 500ms delay | test3 | High |
| 3 | Mocking the method under test | test4 | Critical |
| 4 | Vacuous `expect(true).toBe(true)` | test3 | High |
| 5 | Duplicated boilerplate | all tests | Medium |
| 6 | Missing error-path coverage | none | Medium |

---

## Recommended Refactored Test File

```typescript
import { describe, it, expect, beforeEach } from "vitest";

interface Order {
  id: string;
  items: { sku: string; qty: number; price: number }[];
  customerId: string;
}

class OrderService {
  private db: Map<string, Order> = new Map();

  async createOrder(order: Order): Promise<string> {
    if (!order.items.length) throw new Error("Order must have items");
    this.db.set(order.id, order);
    return order.id;
  }

  async getTotal(orderId: string): Promise<number> {
    const order = this.db.get(orderId);
    if (!order) throw new Error("Order not found");
    return order.items.reduce((sum, i) => sum + i.qty * i.price, 0);
  }

  async cancelOrder(orderId: string): Promise<void> {
    if (!this.db.has(orderId)) throw new Error("Order not found");
    this.db.delete(orderId);
  }
}

function buildOrder(overrides: Partial<Order> & { id: string }): Order {
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

  beforeEach(() => {
    service = new OrderService();
  });

  it("returns the order id when a valid order is created", async () => {
    const id = await service.createOrder(buildOrder({ id: "ord-001" }));
    expect(id).toBe("ord-001");
  });

  it("calculates total as sum of qty * price across all items", async () => {
    await service.createOrder(buildOrder({ id: "ord-002" }));
    const total = await service.getTotal("ord-002");
    expect(total).toBe(25); // (2 * 10) + (1 * 5)
  });

  it("makes the order unretrievable after cancellation", async () => {
    await service.createOrder(buildOrder({ id: "ord-003" }));
    await service.cancelOrder("ord-003");
    await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
  });

  it("throws when creating an order with no items", async () => {
    await expect(
      service.createOrder({ id: "ord-x", customerId: "cust-123", items: [] })
    ).rejects.toThrow("Order must have items");
  });

  it("throws when getting total for a non-existent order", async () => {
    await expect(service.getTotal("missing")).rejects.toThrow("Order not found");
  });

  it("throws when cancelling a non-existent order", async () => {
    await expect(service.cancelOrder("missing")).rejects.toThrow("Order not found");
  });
});
```
