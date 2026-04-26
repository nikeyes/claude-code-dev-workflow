# Test Quality Analysis: test_inventory.go

## Summary

The file `test_inventory.go` contains three test functions for an `Inventory` manager. The code has several deliberate quality violations planted in it, along with issues in both the production code and the test code. Below is a systematic analysis organized by quality dimension.

---

## Issues Found

### 1. Isolation — Shared Global State

**Location**: Line 55, used in `TestFullInventoryFlow` (line 57) and `TestReserveExceedsStock` (line 77).

```go
var globalInventory = NewInventory()
```

Both `TestFullInventoryFlow` and `TestReserveExceedsStock` operate on the same `globalInventory` instance. This means:

- Tests are **order-dependent**: `TestReserveExceedsStock` implicitly depends on the state left by `TestFullInventoryFlow`. After the first test, `globalInventory` has `SKU-1` with stock=10 and a net reservation of 2 units (3 reserved, 1 released). The second test attempts to reserve 100 units and expects failure — which works only because the first test ran first and populated that state.
- If Go's test runner executes them in a different order, or if `TestFullInventoryFlow` is skipped, `TestReserveExceedsStock` may behave unexpectedly (reserving 100 units against an empty inventory will still fail, but for the wrong reason — zero available rather than insufficient stock).
- Running tests in parallel with `t.Parallel()` would produce race conditions and non-deterministic results.

**Recommendation**: Each test should create its own `Inventory` instance via `NewInventory()`. Remove `globalInventory` entirely.

---

### 2. Composability — One Test Covers Multiple Behaviors

**Location**: `TestFullInventoryFlow` (lines 57–75).

This single test exercises four distinct behaviors in sequence:
1. Adding stock (`AddStock`)
2. Reserving units (`Reserve`)
3. Releasing a reservation (`Release`)
4. Checking available quantity (`Available`)

Each of these behaviors deserves its own focused test. A failure in `TestFullInventoryFlow` tells you "something went wrong in the flow" but not which specific behavior is broken. You would have to read through the test body and reason about state transitions to diagnose the failure.

**Recommendation**: Split into focused tests such as:
- `TestAddStock_IncreasesAvailable`
- `TestReserve_DecreasesAvailable`
- `TestRelease_RestoresAvailable`
- `TestAvailable_ReflectsNetStock`

---

### 3. Automated Verification — Manual Inspection via fmt.Println

**Location**: Line 70.

```go
fmt.Printf("Available after release: %d\n", available)
```

This `Printf` statement writes to stdout during test execution. It requires a human to read the test output and manually verify the printed value is reasonable. An automated test run (CI, `go test ./...`) will show this output but nothing will fail if the value is wrong — only the subsequent assertion at line 72 guards correctness.

The `fmt` import itself is a code smell in a test file: its only use is for this debug print. If the assertion on line 72 is sufficient (it is), the `Printf` adds noise without value.

**Recommendation**: Remove the `fmt.Printf` line and the `fmt` import entirely. The assertion `if available != 8` is the correct automated verification mechanism.

---

### 4. Specificity — Generic Error Messages in Production Code

**Location**: Lines 28 and 37.

```go
return fmt.Errorf("operation failed") // AddStock with qty <= 0
return fmt.Errorf("operation failed") // Reserve exceeding available
```

Both `AddStock` and `Reserve` return the identical, undescriptive error string `"operation failed"`. This has two consequences for tests:

- Tests that check for errors (lines 80–83, 88–91) can only assert `err != nil`. They cannot assert the error message to confirm the *right* error was returned for the *right* reason.
- In production usage, a caller receiving `"operation failed"` cannot distinguish between "you passed a negative quantity" and "there is insufficient stock". Debugging becomes significantly harder.

**Recommendation**: Return descriptive, contextual errors:
```go
// AddStock
return fmt.Errorf("quantity must be positive, got %d", qty)

// Reserve
return fmt.Errorf("insufficient stock for SKU %q: requested %d, available %d", sku, qty, available)
```

And in tests, assert the error message:
```go
if !strings.Contains(err.Error(), "quantity must be positive") {
    t.Errorf("expected quantity error, got: %v", err)
}
```

---

### 5. Readability — Assertion Messages Lack Context

**Location**: Line 73.

```go
t.Errorf("expected 8, got %d", available)
```

The error message does not explain *why* 8 is the expected value. A reader seeing this failure message needs to re-read the entire test body to reconstruct that: stock=10, reserved=3, released=1, therefore available = 10 - (3-1) = 8.

**Recommendation**: Make the assertion message self-explanatory:
```go
t.Errorf("after adding 10, reserving 3, releasing 1: expected available=8, got %d", available)
```

This issue is compounded by the composable violation — splitting the test would naturally produce shorter, more readable assertion messages.

---

### 6. Readability — Test Names Do Not Describe Expected Behavior

`TestFullInventoryFlow` describes the mechanism (a flow), not the behavior under test. Good test names follow the pattern `Test<Subject>_<Condition>_<ExpectedOutcome>` or similar conventions that let the test name serve as documentation.

**Examples of improved names**:
- `TestRelease_AfterPartialReservation_CorrectlyRestoresAvailable`
- `TestReserve_WhenExceedingStock_ReturnsError`
- `TestAddStock_WithNegativeQuantity_ReturnsError`

---

### 7. Missing Edge Cases

The current test suite has gaps that the existing test functions do not cover:

- `TestAddStock` for a valid positive quantity (happy path with assertion on `Available`)
- `TestReserve_ExactlyAvailableStock` — reserving the entire available quantity (boundary condition)
- `TestRelease_BeyondReserved` — the production code clamps to zero (line 45–47), but this behavior is never tested
- `TestAddStock_ZeroQuantity` — the guard is `qty <= 0`, so zero should also fail, but is not tested
- `TestAvailable_UnknownSKU` — returns 0 for unknown SKUs due to Go map zero-values; this implicit contract is untested

---

## Summary Table

| Dimension       | Issue                                        | Severity |
|-----------------|----------------------------------------------|----------|
| Isolation       | Shared `globalInventory` across tests        | High     |
| Composability   | `TestFullInventoryFlow` tests 4 behaviors    | High     |
| Automated       | `fmt.Printf` requires human inspection       | Medium   |
| Specific        | Generic `"operation failed"` error messages  | Medium   |
| Readability     | Assertion messages lack context              | Low      |
| Readability     | Test names describe mechanism not behavior   | Low      |
| Coverage        | Several boundary cases untested              | Medium   |

---

## Recommended Refactored Structure

```go
package inventory

import (
    "strings"
    "testing"
)

func TestAddStock_WithPositiveQuantity_IncreasesAvailable(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    if inv.Available("SKU-1") != 10 {
        t.Errorf("expected available=10, got %d", inv.Available("SKU-1"))
    }
}

func TestAddStock_WithNegativeQuantity_ReturnsError(t *testing.T) {
    inv := NewInventory()
    err := inv.AddStock("SKU-X", -5)
    if err == nil {
        t.Fatal("expected error for negative quantity")
    }
    if !strings.Contains(err.Error(), "quantity must be positive") {
        t.Errorf("expected descriptive error, got: %v", err)
    }
}

func TestReserve_WithSufficientStock_DecreasesAvailable(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    if err := inv.Reserve("SKU-1", 3); err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if inv.Available("SKU-1") != 7 {
        t.Errorf("expected available=7 after reserving 3 of 10, got %d", inv.Available("SKU-1"))
    }
}

func TestReserve_WhenExceedingStock_ReturnsError(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    err := inv.Reserve("SKU-1", 100)
    if err == nil {
        t.Fatal("expected error when reserving more than available")
    }
    if !strings.Contains(err.Error(), "insufficient stock") {
        t.Errorf("expected descriptive error, got: %v", err)
    }
}

func TestRelease_AfterPartialReservation_RestoresAvailable(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    inv.Reserve("SKU-1", 3)
    inv.Release("SKU-1", 1)
    if inv.Available("SKU-1") != 8 {
        t.Errorf("after reserving 3 and releasing 1 from stock of 10: expected available=8, got %d", inv.Available("SKU-1"))
    }
}

func TestRelease_BeyondReserved_ClampsToZero(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    inv.Reserve("SKU-1", 2)
    inv.Release("SKU-1", 5) // release more than reserved
    if inv.Available("SKU-1") != 10 {
        t.Errorf("releasing beyond reserved should clamp to 0 reserved: expected available=10, got %d", inv.Available("SKU-1"))
    }
}
```

This refactored structure: creates fresh state in each test, names each test after a single verifiable behavior, asserts error messages specifically, and removes the debug print entirely.
