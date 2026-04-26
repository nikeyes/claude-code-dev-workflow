# Test Quality Analysis: test_order_service.ts

## File Analyzed
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_order_service.ts`

## Framework Applied
Kent Beck's Test Desiderata (12 properties)

---

## Summary

The test file covers an `OrderService` class with four tests. It contains intentional violations across four of the twelve desiderata properties. Below is a full evaluation of all 12 properties.

---

## Property-by-Property Evaluation

### 1. Isolated
**Status: PASS (mostly)**

Each test creates a fresh `OrderService` instance via `beforeEach`, so tests do not share state through the `db` map. Tests are isolated from each other in terms of data. The shared `service` variable is reset before each test, which is the correct pattern.

Minor note: `test4` calls `spy.mockRestore()` inside the test body rather than in `afterEach`, which could leave the service in a mocked state if the test throws before reaching that line. This is a minor isolation risk.

### 2. Composable
**Status: PASS (with caveats)**

Tests can be run individually or together without dependencies between them. There is no shared mutable state leaking between tests. However, the boilerplate duplication (see Writable) makes it harder to compose new tests quickly—you must copy-paste the full order fixture each time.

### 3. Deterministic
**Status: FAIL**

`test3` introduces a real `setTimeout` of 500ms:

```typescript
await new Promise((resolve) => setTimeout(resolve, 500));
```

This delay is not controlled by a fake timer or injectable clock. While in this specific case the delay is unconditional and will always resolve the same way, relying on real wall-clock time makes the test's execution profile non-deterministic across environments (e.g., slow CI machines could theoretically experience issues). The intent to test time-dependent behavior should use fake timers (`vi.useFakeTimers()`).

More critically, the assertion at the end of `test3` is `expect(true).toBe(true)`, which is vacuous and will always pass regardless of what the code does—making the test's pass/fail non-meaningful.

### 4. Fast
**Status: FAIL**

`test3` unconditionally waits 500ms via `setTimeout`:

```typescript
await new Promise((resolve) => setTimeout(resolve, 500));
```

This is a real wall-clock delay with no relation to the behavior being tested (order creation and cancellation). It slows the test suite by at least 500ms with zero diagnostic value. Fast tests should run in milliseconds. This violation should be fixed by either removing the unnecessary delay entirely or using `vi.useFakeTimers()` if timing behavior is actually relevant.

### 5. Writable
**Status: FAIL**

The same `Order` fixture is manually constructed in every test (`test1`, `test2`, `test3`, `test4`), each time with 6–8 lines of boilerplate:

```typescript
const order: Order = {
  id: "ord-001",
  customerId: "cust-123",
  items: [
    { sku: "SKU-A", qty: 2, price: 10.0 },
    { sku: "SKU-B", qty: 1, price: 5.0 },
  ],
};
```

This pattern is repeated four times with minor variations (different `id` and `customerId`). Writing a new test requires copying this boilerplate. The fix is to extract a factory helper:

```typescript
function makeOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: "ord-001",
    customerId: "cust-123",
    items: [{ sku: "SKU-A", qty: 2, price: 10.0 }],
    ...overrides,
  };
}
```

### 6. Readable
**Status: FAIL**

Tests are named `test1`, `test2`, `test3`, `test4 behavioral violation`. These names communicate nothing about what behavior is being verified. A reader cannot understand what the test covers without reading the full body.

Good test names describe the behavior under test and the expected outcome:

- `test1` → `"createOrder returns the order id"`
- `test2` → `"getTotal returns the sum of qty times price for each item"`
- `test3` → `"cancelOrder removes the order so it can no longer be retrieved"`
- `test4` → `"getTotal calculates from stored order items"` (after fixing the behavioral violation)

### 7. Behavioral
**Status: FAIL**

`test4` mocks the very method it is testing:

```typescript
const spy = vi.spyOn(service, "getTotal").mockResolvedValue(999);
// ...
const total = await service.getTotal("ord-004");
expect(total).toBe(999); // tests the mock, not the implementation
```

This test does not exercise the `getTotal` implementation at all. It verifies that the mock returns `999`—which is tautologically true. If `getTotal` had a bug, this test would still pass. A behavioral test should call the real implementation and assert on observable output.

Additionally, `test3` ends with:
```typescript
expect(true).toBe(true); // vacuous assertion
```
This passes regardless of what `createOrder` or `cancelOrder` do. A behavioral test should assert something meaningful, such as verifying that `getTotal` throws after cancellation.

### 8. Structure-insensitive
**Status: PASS**

The tests interact with the `OrderService` through its public API (`createOrder`, `getTotal`, `cancelOrder`) and do not inspect internal state (the private `db` map). Internal refactoring of the `db` storage mechanism would not break the tests.

Exception: `test4` uses `vi.spyOn` on a public method, which couples the test to the method name, but this is a behavioral problem (see above) more than a structure-sensitivity problem.

### 9. Automated
**Status: PASS**

All four tests are written using the `vitest` framework (`describe`, `it`, `expect`). They require no manual steps, no human-in-the-loop assertions, and can be executed with a standard `vitest` command.

### 10. Specific
**Status: FAIL (partial)**

`test3`'s vacuous assertion `expect(true).toBe(true)` provides zero specificity—it cannot fail under any circumstances and points to no particular behavior when it does pass. If `cancelOrder` threw an exception the test would fail on the `await` line, not on the assertion, providing a misleading diagnostic signal.

`test4`'s assertion `expect(total).toBe(999)` is specific only about the mock's return value, not about the system under test. It gives a false sense of precision.

`test1` and `test2` have specific and meaningful assertions.

### 11. Predictive
**Status: FAIL (partial)**

A test suite is predictive when passing tests give confidence that the code works and failing tests reliably indicate real bugs.

- `test3` and `test4` are not predictive: they pass even when the implementation is broken.
- The absence of tests for error paths (`createOrder` with empty items, `getTotal` for a non-existent order, `cancelOrder` for a non-existent order) means the suite gives false confidence about edge-case behavior.

### 12. Inspiring
**Status: FAIL**

The suite does not inspire developers to write more tests. The issues compound:
- Opaque names (`test1`, `test2`) make it hard to understand what's missing.
- Boilerplate duplication makes writing new tests tedious.
- A vacuous test (`expect(true).toBe(true)`) and a mock-testing-a-mock test (`test4`) teach bad habits to anyone reading the file.
- No negative/error-path tests exist, so there is no example of how to test error conditions.

A well-structured test suite should serve as documentation and a model for adding new tests.

---

## Violations Summary Table

| Property           | Status | Severity | Location         |
|--------------------|--------|----------|------------------|
| Isolated           | PASS*  | Low      | test4 (minor)    |
| Composable         | PASS   | -        | -                |
| Deterministic      | FAIL   | Medium   | test3            |
| Fast               | FAIL   | High     | test3            |
| Writable           | FAIL   | High     | all tests        |
| Readable           | FAIL   | High     | all tests        |
| Behavioral         | FAIL   | Critical | test3, test4     |
| Structure-insensitive | PASS | -       | -                |
| Automated          | PASS   | -        | -                |
| Specific           | FAIL   | High     | test3, test4     |
| Predictive         | FAIL   | High     | test3, test4     |
| Inspiring          | FAIL   | Medium   | overall          |

**Violations detected: 7 out of 12 properties**

---

## Concrete Recommendations

### 1. Fix test names (Readable)
Replace generic names with behavior-describing names:
```typescript
it("createOrder stores the order and returns its id")
it("getTotal returns sum of qty times price across all items")
it("cancelOrder removes the order from the service")
it("getTotal calculates from actual stored data") // after fixing behavioral issue
```

### 2. Extract an order factory (Writable)
```typescript
function makeOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: "ord-001",
    customerId: "cust-123",
    items: [{ sku: "SKU-A", qty: 2, price: 10.0 }],
    ...overrides,
  };
}
```

### 3. Remove the fake delay and add a real assertion (Fast, Deterministic, Behavioral, Specific)
Replace `test3` body with:
```typescript
it("cancelOrder removes the order so getTotal throws", async () => {
  const order = makeOrder({ id: "ord-003" });
  await service.createOrder(order);
  await service.cancelOrder("ord-003");
  await expect(service.getTotal("ord-003")).rejects.toThrow("Order not found");
});
```

### 4. Remove the mock from test4 and test real behavior (Behavioral, Specific, Predictive)
```typescript
it("getTotal calculates from actual stored data", async () => {
  const order = makeOrder({ id: "ord-004", items: [{ sku: "SKU-D", qty: 1, price: 50.0 }] });
  await service.createOrder(order);
  const total = await service.getTotal("ord-004");
  expect(total).toBe(50);
});
```

### 5. Add error-path tests (Predictive, Inspiring)
```typescript
it("createOrder throws when order has no items", async () => {
  const order = makeOrder({ items: [] });
  await expect(service.createOrder(order)).rejects.toThrow("Order must have items");
});

it("getTotal throws when order does not exist", async () => {
  await expect(service.getTotal("nonexistent")).rejects.toThrow("Order not found");
});

it("cancelOrder throws when order does not exist", async () => {
  await expect(service.cancelOrder("nonexistent")).rejects.toThrow("Order not found");
});
```

### 6. Move spy cleanup to afterEach (Isolated)
If mocks are ever needed, restore them in `afterEach` rather than at the end of the test body to prevent leakage on test failure.

---

## Conclusion

The file has 7 active violations across the 12 Test Desiderata properties. The most critical issues are the **Behavioral** violations: one test mocks the method it is supposed to test, and another test has a vacuous assertion that can never fail. These tests provide false confidence and would not catch bugs in the implementation. The **Readable** and **Writable** violations increase maintenance friction. Addressing all recommendations above would produce a test suite that is fast, honest, clear, and confidence-inspiring.
