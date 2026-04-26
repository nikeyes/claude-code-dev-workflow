# Test Desiderata Analysis: test_order_service.ts

## Summary

File analyzed: `core/skills/test-desiderata-workspace/evals/files/test_order_service.ts`
Framework: Kent Beck's Test Desiderata (12 properties)
Violations found: 4 properties violated across 4 tests

---

## Violations

### Issue 1: Readable — test names describe nothing

**Location:** Lines 46, 60, 75, 89 — test names `test1`, `test2`, `test3`, `test4 behavioral violation`

**Impact:** A reader cannot understand what behavior is being verified without reading the entire test body. When a test fails in CI the name `test1` gives zero diagnostic signal — you must open the file and read the code to discover what broke. The intent (the "why") is completely hidden.

**Fix:** Rename each test to describe the specific behavior and outcome under test:

```typescript
it("createOrder returns the order id when items are present", ...)
it("getTotal sums qty * price across all items", ...)
it("cancelOrder removes the order so it can no longer be retrieved", ...)
it("getTotal returns the calculated total for an existing order", ...)
```

---

### Issue 2: Writable — order fixture boilerplate duplicated in every test

**Location:** Lines 48-55 (`test1`), 62-69 (`test2`), 79-83 (`test3`), 93-97 (`test4`) — identical or near-identical `Order` object construction repeated four times

**Impact:** Adding a field to `Order` (e.g., `status`, `createdAt`) requires touching every test. The friction of writing new tests is high because each new test must reconstruct the full object from scratch. This discourages adding tests, directly lowering coverage over time.

**Fix:** Extract a shared factory function (or `beforeEach` helper) that returns a default `Order` and allow per-test overrides:

```typescript
function makeOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: "ord-001",
    customerId: "cust-123",
    items: [
      { sku: "SKU-A", qty: 2, price: 10.0 },
      { sku: "SKU-B", qty: 1, price: 5.0 },
    ],
    ...overrides,
  };
}
```

Each test then calls `makeOrder({ id: "ord-002" })` and only specifies what is relevant to that scenario.

---

### Issue 3: Fast — real 500 ms `setTimeout` inside a test

**Location:** Line 77 — `await new Promise((resolve) => setTimeout(resolve, 500));`

**Impact:** This single test adds 500 ms to every test run. In a suite of hundreds of tests a handful of similar delays compound into minutes of wall-clock wait time, slowing down the development feedback loop. The delay appears to serve no purpose: `OrderService` has no time-dependent logic, so the pause contributes nothing to the assertion (which is itself vacuous — see Issue 4).

**Fix:** Remove the `setTimeout` entirely. If the intent was to simulate async behavior, `OrderService` methods are already `async` and `await`-ing them is sufficient. If the intent was to test a future time-based feature, use `vi.useFakeTimers()` so time can be advanced programmatically without wall-clock delay:

```typescript
// Remove the setTimeout line entirely — no async delay is needed here
await service.createOrder(order);
await service.cancelOrder("ord-003");
expect(service.db.has("ord-003")).toBe(false); // verify the cancellation
```

---

### Issue 4: Behavioral — mock replaces the method under test; assertion verifies nothing real

**Location:** Lines 91-100 (`test4`) — `vi.spyOn(service, "getTotal").mockResolvedValue(999)` then `expect(total).toBe(999)`

**Impact:** The spy completely replaces `getTotal` with a function that always returns `999`. The assertion `expect(total).toBe(999)` cannot possibly fail regardless of what the real `getTotal` implementation does. The test would still pass if `getTotal` were deleted, threw an exception, or returned the wrong value. No behavioral change to `OrderService` can break this test, making it worthless as a safety net.

**Fix:** Remove the mock entirely and assert against the real computed total. The actual behavior under test is that `getTotal` sums `qty * price`:

```typescript
it("getTotal returns the calculated total for an existing order", async () => {
  const order = makeOrder({
    id: "ord-004",
    items: [{ sku: "SKU-D", qty: 1, price: 50.0 }],
  });
  await service.createOrder(order);
  const total = await service.getTotal("ord-004");
  expect(total).toBe(50.0);
});
```

**Note:** Line 86 in `test3` also contains a vacuous assertion (`expect(true).toBe(true)`). This is a secondary Behavioral violation: after `cancelOrder` no assertion verifies the cancellation occurred. The fix is to assert that the order is gone, for example by checking that a subsequent `getTotal` call throws `"Order not found"`.

---

## Tradeoffs

### Tradeoff 1: Writable ↔ Readable (only seeming to interfere)

Both are violated and both stem from the same missing abstraction: there is no named fixture.

A naive reading suggests a tension — making tests more readable (longer, more descriptive setup) conflicts with keeping them easy to write (short, minimal code). In practice, these violations reinforce each other. Because there is no shared `makeOrder` factory, each test contains a large anonymous block of data that obscures what is relevant to that specific scenario. A reader must scan 8-10 lines of item arrays to find the one detail that matters (e.g., the specific `id`).

Extracting a well-named factory (`makeOrder`) resolves both simultaneously:
- **Writable improves** because new tests need only specify the fields they care about (one line instead of ten).
- **Readable improves** because each test body becomes compact and the meaningful variation (the override) stands out immediately.

This is a pure design win: there is no real tension between these two properties here. The root cause is the missing fixture abstraction, not a genuine conflict.

**Priority:** Fix Writable first (extract `makeOrder`) — the Readable improvement follows automatically.

---

### Tradeoff 2: Fast ↔ Behavioral (only seeming to interfere)

`test3` violates both Fast (real `setTimeout`) and Behavioral (vacuous `expect(true).toBe(true)`). A surface reading suggests improving Behavioral (adding real assertions) might slow the test further because more assertions imply more setup or waiting. In reality the opposite is true.

The `setTimeout` is present precisely because the author had no real assertion to write. Once the behavioral gap is addressed (asserting that `cancelOrder` actually removes the order), the delay becomes obviously unnecessary and can be deleted without reducing test value. Fixing Behavioral enables fixing Fast — they only seem to conflict.

**Priority:** Fix Behavioral first (replace vacuous assertion with a meaningful one). The Fast fix (removing the `setTimeout`) then becomes a trivial cleanup with zero risk.

---

### Tradeoff 3: Readable ↔ Specific (supporting relationship)

These two properties support each other and both degrade together in this file. When test names are opaque (`test1`, `test2`) and assertions are vacuous (`expect(true).toBe(true)`), a failing test provides no useful signal about what broke or where to look.

Fixing Readable (descriptive test names) and Behavioral/Specific (meaningful assertions with clear expected values) together ensures that a failure in CI immediately communicates both which behavior broke and what the expected versus actual values were.

**Priority:** Address both together when renaming tests — a well-named test and a well-formed assertion are a single unit of work.

---

### Tradeoff 4: Behavioral ↔ Writable (real tension, manageable)

Adding thorough behavioral coverage (testing error paths, boundary values, order-not-found scenarios) will increase the number of tests and therefore the amount of setup code. This is a genuine tension: more Behavioral coverage means more tests, and without a fixture helper each test is expensive to write.

However, this tension is substantially reduced by fixing the Writable violation first. Once `makeOrder` exists, adding a new behavioral test (e.g., `createOrder throws when items array is empty`) costs only 3-4 lines instead of 15. The tension does not disappear entirely — edge-case tests still require thought — but the friction drops from "painful" to "acceptable."

**Priority:** Fix Writable (extract `makeOrder`) before expanding behavioral coverage. Adding tests before the fixture exists will compound the boilerplate debt.
