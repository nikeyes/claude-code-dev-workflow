# Test Quality Analysis: test_order_service.ts

## Summary

The test file contains four deliberate quality violations spread across its four test cases. The violations span readability, speed, behavioral correctness, and writability. Below is a detailed analysis of each issue along with specific recommendations.

---

## Issues Found

### 1. Unreadable Test Names (Readable violation)

**Location**: `it("test1", ...)`, `it("test2", ...)`, `it("test3", ...)`

**Problem**: Three of the four tests have names that communicate nothing about the behavior under test. A reader cannot understand what each test verifies without reading the full implementation. The one exception — `"test4 behavioral violation"` — references the violation itself rather than the behavior.

**Impact**: When a test fails, the name is the first signal developers see in CI output. Names like `test1` force developers to open the file to understand what broke, slowing diagnosis.

**Recommendation**: Name each test as a sentence describing the expected behavior under a given condition:
- `"test1"` → `"createOrder returns the order id when given valid items"`
- `"test2"` → `"getTotal returns the sum of qty times price for all items"`
- `"test3"` → `"cancelOrder removes the order so it can no longer be retrieved"`
- `"test4 behavioral violation"` → `"getTotal calculates the correct total from actual item data"`

---

### 2. Real Timer in a Test (Fast violation)

**Location**: `it("test3", ...)` — line 77: `await new Promise((resolve) => setTimeout(resolve, 500));`

**Problem**: A real 500ms `setTimeout` is used inside the test body. This delay has no relationship to the logic under test (`createOrder` + `cancelOrder`), so it adds 500ms of wall-clock time to every test run with zero benefit.

**Impact**: Even at a small scale, artificial sleeps degrade the test suite's feedback loop. Teams start skipping tests or running subsets because the suite is "too slow." The problem compounds as the codebase grows.

**Recommendation**: Remove the `setTimeout` entirely. If the intent was to simulate some async behavior, `OrderService`'s methods are already async and `await`-ing them is sufficient. No artificial delay is needed.

```typescript
it("cancelOrder removes the order so it can no longer be retrieved", async () => {
  const order = buildOrder("ord-003", [{ sku: "SKU-C", qty: 3, price: 8.0 }]);
  await service.createOrder(order);
  await service.cancelOrder("ord-003");
  await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
});
```

---

### 3. Vacuous Assertion (Behavioral / Specificity violation)

**Location**: `it("test3", ...)` — line 86: `expect(true).toBe(true);`

**Problem**: The only assertion in `test3` is a tautology. It always passes regardless of what `cancelOrder` does — or whether it throws an exception. The test could be completely broken and still be green.

**Impact**: This test provides false confidence. A regression in `cancelOrder` (e.g., it no longer deletes the record) would go undetected.

**Recommendation**: Assert the actual post-cancellation behavior. The most meaningful assertion is that attempting to retrieve the cancelled order throws an error:

```typescript
await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
```

---

### 4. Mocking the Method Under Test (Behavioral violation)

**Location**: `it("test4 behavioral violation", ...)` — lines 91–99

**Problem**: `vi.spyOn(service, "getTotal").mockResolvedValue(999)` replaces the `getTotal` method with a stub that always returns `999`. The test then calls `service.getTotal(...)` and asserts `999`. This asserts the behavior of the mock, not the implementation.

**Impact**: The real `getTotal` logic — `reduce((sum, i) => sum + i.qty * i.price, 0)` — is never executed. A complete rewrite or deletion of that logic would leave this test green. The test provides no safety net for the code it claims to cover.

**Recommendation**: Remove the spy entirely and assert against the real computed value:

```typescript
it("getTotal calculates the correct total from actual item data", async () => {
  const order = buildOrder("ord-004", [{ sku: "SKU-D", qty: 1, price: 50.0 }]);
  await service.createOrder(order);
  const total = await service.getTotal("ord-004");
  expect(total).toBe(50.0);
});
```

---

### 5. Duplicated Setup Boilerplate (Writable violation)

**Location**: All four test bodies repeat the same `Order` object literal construction (~10–12 lines each).

**Problem**: Each test manually constructs an `Order` with `id`, `customerId`, and `items`. The structure is identical across tests; only the values differ. This is copy-paste boilerplate, not meaningful test logic.

**Impact**: If the `Order` interface changes (e.g., a new required field is added), every test must be updated individually. It also makes the test bodies harder to scan because the signal (the behavior being tested) is buried in the noise (data construction).

**Recommendation**: Extract a builder function that accepts only the values that matter for the specific test:

```typescript
function buildOrder(
  id: string,
  items: { sku: string; qty: number; price: number }[],
  customerId = "cust-default"
): Order {
  return { id, customerId, items };
}
```

Each test then reads as:

```typescript
const order = buildOrder("ord-001", [
  { sku: "SKU-A", qty: 2, price: 10.0 },
  { sku: "SKU-B", qty: 1, price: 5.0 },
]);
```

---

### 6. Missing Error Path Coverage

**Location**: No test in the suite exercises the error-throwing branches of `OrderService`.

**Problem**: `createOrder` throws when `items` is empty; `getTotal` and `cancelOrder` both throw when the `orderId` is not found. None of these paths are tested.

**Impact**: A regression in error handling would be invisible to the test suite.

**Recommendation**: Add at minimum:

```typescript
it("createOrder throws when the order has no items", async () => {
  const emptyOrder = buildOrder("ord-empty", []);
  await expect(service.createOrder(emptyOrder)).rejects.toThrow("Order must have items");
});

it("getTotal throws when the order does not exist", async () => {
  await expect(service.getTotal("nonexistent")).rejects.toThrow("Order not found");
});

it("cancelOrder throws when the order does not exist", async () => {
  await expect(service.cancelOrder("nonexistent")).rejects.toThrow("Order not found");
});
```

---

## Prioritized Recommendations

| Priority | Issue | Action |
|----------|-------|--------|
| 1 (Critical) | Mocking the method under test (test4) | Remove the spy; test real logic |
| 2 (Critical) | Vacuous assertion `expect(true).toBe(true)` (test3) | Assert the actual post-cancel state |
| 3 (High) | Unreadable test names (test1, test2, test3) | Rename to describe behavior |
| 4 (High) | Real 500ms timer (test3) | Remove `setTimeout` |
| 5 (Medium) | Duplicated boilerplate across all tests | Extract `buildOrder` helper |
| 6 (Medium) | No error path coverage | Add tests for each throwing branch |

---

## Revised Test Suite (Reference)

```typescript
import { describe, it, expect, beforeEach } from "vitest";

// ... (interfaces and OrderService unchanged)

function buildOrder(
  id: string,
  items: { sku: string; qty: number; price: number }[],
  customerId = "cust-default"
): Order {
  return { id, customerId, items };
}

describe("OrderService", () => {
  let service: OrderService;

  beforeEach(() => {
    service = new OrderService();
  });

  it("createOrder returns the order id when given valid items", async () => {
    const order = buildOrder("ord-001", [
      { sku: "SKU-A", qty: 2, price: 10.0 },
      { sku: "SKU-B", qty: 1, price: 5.0 },
    ]);
    const id = await service.createOrder(order);
    expect(id).toBe("ord-001");
  });

  it("getTotal returns the sum of qty times price for all items", async () => {
    const order = buildOrder("ord-002", [
      { sku: "SKU-A", qty: 2, price: 10.0 },
      { sku: "SKU-B", qty: 1, price: 5.0 },
    ]);
    await service.createOrder(order);
    const total = await service.getTotal("ord-002");
    expect(total).toBe(25);
  });

  it("cancelOrder removes the order so it can no longer be retrieved", async () => {
    const order = buildOrder("ord-003", [{ sku: "SKU-C", qty: 3, price: 8.0 }]);
    await service.createOrder(order);
    await service.cancelOrder("ord-003");
    await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
  });

  it("getTotal calculates the correct total from actual item data", async () => {
    const order = buildOrder("ord-004", [{ sku: "SKU-D", qty: 1, price: 50.0 }]);
    await service.createOrder(order);
    const total = await service.getTotal("ord-004");
    expect(total).toBe(50.0);
  });

  it("createOrder throws when the order has no items", async () => {
    const emptyOrder = buildOrder("ord-empty", []);
    await expect(service.createOrder(emptyOrder)).rejects.toThrow("Order must have items");
  });

  it("getTotal throws when the order does not exist", async () => {
    await expect(service.getTotal("nonexistent")).rejects.toThrow("Order not found");
  });

  it("cancelOrder throws when the order does not exist", async () => {
    await expect(service.cancelOrder("nonexistent")).rejects.toThrow("Order not found");
  });
});
```
