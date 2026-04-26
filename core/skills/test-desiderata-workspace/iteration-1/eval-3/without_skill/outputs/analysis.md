# Test Quality Analysis: test_inventory.go

**Framework**: Kent Beck's Test Desiderata (12 properties)  
**File analyzed**: `core/skills/test-desiderata-workspace/evals/files/test_inventory.go`  
**Date**: 2026-04-26

---

## Summary

The test file contains 3 test functions covering an `Inventory` struct with stock management operations. Several deliberate violations are embedded in the code (noted in comments). This analysis evaluates all 12 Test Desiderata properties and provides concrete recommendations.

---

## Property-by-Property Evaluation

### 1. Isolated — VIOLATED

**What it means**: Tests should not affect each other. Each test should set up its own state.

**Violation**: A package-level variable `globalInventory` is declared at line 55 and shared across `TestFullInventoryFlow` and `TestReserveExceedsStock`. `TestReserveExceedsStock` implicitly depends on `globalInventory` having been populated with `SKU-1` stock by the previous test.

```go
// Line 55 — shared mutable state
var globalInventory = NewInventory()

// TestReserveExceedsStock uses it without setup
err := globalInventory.Reserve("SKU-1", 100)
```

If `TestReserveExceedsStock` runs in isolation or before `TestFullInventoryFlow`, the assertion changes meaning: an empty inventory would also return an error, but for different reasons.

**Recommendation**: Each test should create its own `inv := NewInventory()` and populate it with the minimal stock required for that scenario. Remove `globalInventory`.

---

### 2. Composable — VIOLATED

**What it means**: Tests should be combinable without side effects. Small, focused tests are easier to compose into suites.

**Violation**: `TestFullInventoryFlow` exercises four distinct behaviors in sequence: `AddStock`, `Reserve`, `Release`, and `Available`. This is a scenario test, not a unit test. If any step fails, the failure message does not pinpoint which behavior broke.

**Recommendation**: Split into focused tests:
- `TestAddStock_IncreasesAvailableQuantity`
- `TestReserve_DecreasesAvailableQuantity`
- `TestRelease_RestoresAvailableQuantity`
- `TestAvailable_ReflectsStockMinusReserved`

---

### 3. Deterministic — PASS (with caveat)

**What it means**: Tests should always produce the same result given the same code.

**Observation**: The tests themselves are deterministic in logic. However, because `TestReserveExceedsStock` depends on state from `TestFullInventoryFlow`, running tests in a different order (e.g., via `go test -shuffle=on`) could produce different outcomes. This is an emergent non-determinism caused by the Isolated violation.

**Recommendation**: Fixing the Isolated violation resolves this latent non-determinism.

---

### 4. Fast — PASS

**What it means**: Tests should run quickly to encourage frequent execution.

**Observation**: All tests are pure in-memory operations with no I/O, sleep, or network calls. They will run in microseconds.

---

### 5. Writable — PARTIAL PASS

**What it means**: Tests should be easy to write. The test framework should not create friction.

**Observation**: The Go `testing` package is low-friction. However, the absence of a test helper for setup (like a `setupInventory(sku string, qty int)` helper) means each new test requires repetitive boilerplate. `TestAddNegativeStock` is the cleanest example — isolated and focused. The others are harder to replicate correctly due to shared state.

**Recommendation**: Introduce a helper function to construct a pre-loaded inventory for common scenarios.

---

### 6. Readable — PARTIAL PASS

**What it means**: Tests should read like documentation of the behavior.

**Observation**: `TestAddNegativeStock` and `TestReserveExceedsStock` have clear names. `TestFullInventoryFlow` is named like a scenario rather than a behavior. The assertion `if available != 8` requires the reader to mentally trace the arithmetic (10 added, 3 reserved, 1 released = 8 available) rather than having it explained.

**Recommendation**:
- Rename `TestFullInventoryFlow` to descriptive per-behavior names.
- Add inline comments or use named constants to explain expected values (e.g., `expectedAvailable := 8 // 10 added - 3 reserved + 1 released`).

---

### 7. Behavioral — PARTIAL PASS

**What it means**: Tests should verify observable behavior, not implementation details.

**Observation**: Tests check return values and error presence, which are correct behavioral signals. `TestFullInventoryFlow` checks `Available()`, which is the right public interface. No private fields are accessed directly.

**Minor concern**: `TestReserveExceedsStock` only checks `err == nil` — it does not verify the inventory state remained unchanged after a failed reservation. A failed reservation should not modify `reserved`, and that invariant is untested.

**Recommendation**: After a failed `Reserve`, assert that `Available()` still returns the pre-attempt value to confirm the state was not corrupted.

---

### 8. Structure-insensitive — PASS

**What it means**: Tests should not break when the internal structure of the code changes, only when behavior changes.

**Observation**: Tests use the public API (`AddStock`, `Reserve`, `Release`, `Available`) and do not reference `stock` or `reserved` map internals. A refactoring of the internal data structure would not break these tests.

---

### 9. Automated — VIOLATED

**What it means**: Tests should run without human intervention and results should be machine-readable.

**Violation**: Line 70 uses `fmt.Printf` to print the available quantity to stdout:

```go
fmt.Printf("Available after release: %d\n", available)
```

This output requires a human to inspect the terminal to verify the value. It is not part of the automated assertion and produces noise in CI output.

**Recommendation**: Remove the `fmt.Printf` call entirely. The assertion on line 72 (`if available != 8`) already provides automated verification. The `fmt` import can also be removed from the test file once the `Printf` is gone (it is only used for `Printf` in the test; the production code uses `fmt.Errorf` which is in the same file here).

---

### 10. Specific — VIOLATED

**What it means**: When a test fails, it should clearly identify what went wrong.

**Violation 1 (production code)**: Both `AddStock` and `Reserve` return the same generic error message `"operation failed"`:

```go
return fmt.Errorf("operation failed") // line 28
return fmt.Errorf("operation failed") // line 37
```

When a test catches one of these errors, it cannot distinguish which failure condition triggered — invalid quantity vs. insufficient stock.

**Violation 2 (test assertions)**: `TestFullInventoryFlow` uses:
```go
t.Errorf("expected 8, got %d", available)
```
This is acceptable but does not name the operation being tested. A more specific message like `"Available() after AddStock(10)/Reserve(3)/Release(1): expected 8, got %d"` would be immediately actionable.

**Recommendation**:
- Change production errors to specific messages:
  - `fmt.Errorf("AddStock: quantity must be positive, got %d", qty)`
  - `fmt.Errorf("Reserve: insufficient stock for SKU %q: requested %d, available %d", sku, qty, available)`
- Improve assertion messages to include context about the operation sequence.

---

### 11. Predictive — PARTIAL PASS

**What it means**: A passing test suite should give confidence the system works in production.

**Observation**: The three tests cover the main happy path and two error paths. However, several important scenarios are untested:
- Releasing more than reserved (the code clamps to 0, but this is unverified by tests)
- Reserving zero quantity
- Adding stock to a SKU that already has stock
- Calling `Available` on an unknown SKU (should return 0 — untested)
- Thread safety (not required for predictive purposes at unit level, but worth noting for production use)

The `globalInventory` coupling also means the test suite could pass even if `TestReserveExceedsStock` is accidentally testing a pre-loaded state rather than a fresh one, masking bugs.

**Recommendation**: Add targeted tests for the edge cases above, especially the release-beyond-reserved clamping behavior.

---

### 12. Inspiring — PARTIAL PASS

**What it means**: A good test suite should inspire confidence and make developers want to keep it green.

**Observation**: `TestAddNegativeStock` is a clean, well-scoped test and sets a good example. The other two tests undermine confidence because of shared state, console output noise, and the monolithic flow test. A developer encountering a failure in `TestReserveExceedsStock` would have to check whether `TestFullInventoryFlow` ran first to understand the failure context — this erodes trust.

**Recommendation**: Apply the isolation and composability fixes. A suite of 6-8 small, independent, well-named tests would be far more inspiring than 3 entangled ones.

---

## Violation Summary

| Property | Status | Severity |
|---|---|---|
| Isolated | VIOLATED | High — causes order-dependent failures |
| Composable | VIOLATED | Medium — monolithic test, hard to maintain |
| Deterministic | LATENT RISK | Medium — emerges from Isolated violation |
| Fast | PASS | — |
| Writable | PARTIAL | Low — setup boilerplate friction |
| Readable | PARTIAL | Low — magic numbers, misleading test name |
| Behavioral | PARTIAL | Low — missing invariant on failed reserve |
| Structure-insensitive | PASS | — |
| Automated | VIOLATED | High — fmt.Printf requires human inspection |
| Specific | VIOLATED | High — generic error messages, weak assertions |
| Predictive | PARTIAL | Medium — missing edge case coverage |
| Inspiring | PARTIAL | Medium — shared state erodes confidence |

---

## Priority Recommendations

1. **Remove `globalInventory`** and add `inv := NewInventory()` inside each test function. This fixes Isolated, resolves the latent Determinism issue, and improves Inspiring.

2. **Remove `fmt.Printf`** from `TestFullInventoryFlow`. This fixes Automated and removes CI noise.

3. **Use specific error messages** in `AddStock` and `Reserve`. This fixes Specific and makes debugging faster.

4. **Split `TestFullInventoryFlow`** into 3-4 focused tests. This fixes Composable and improves Readable and Predictive.

5. **Add edge case tests** for release-beyond-reserved clamping and unknown SKU availability. This improves Predictive.
