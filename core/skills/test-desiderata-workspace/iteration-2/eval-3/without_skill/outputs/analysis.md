# Test Quality Analysis: test_inventory.go

## File Reviewed

`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_inventory.go`

---

## Summary

The test file contains four deliberately planted quality issues that undermine test reliability, readability, and automation. Three of the four tests have problems. One test (`TestAddNegativeStock`) is acceptable as written.

---

## Issues Identified

### 1. Isolation Violation — Shared Global State

**Location**: Line 55, `TestFullInventoryFlow` (line 57), `TestReserveExceedsStock` (line 77)

```go
var globalInventory = NewInventory()
```

Both `TestFullInventoryFlow` and `TestReserveExceedsStock` mutate the same `globalInventory` variable. This means:

- Test results depend on execution order. Go does not guarantee test order within a package.
- `TestReserveExceedsStock` implicitly requires `TestFullInventoryFlow` to have run first and to have left `globalInventory` in a specific state (SKU-1 with some stock and reserved units). If tests run in isolation or in a different order, `TestReserveExceedsStock` will either fail spuriously or produce a false positive (if `globalInventory` has no stock for SKU-1 at all, reserving 100 will also fail — but for a different reason).
- Shared state makes test failures harder to diagnose and introduces hidden coupling.

**Recommendation**: Each test should create its own `Inventory` instance using `NewInventory()` and set it up to the exact precondition it needs. Remove the package-level `globalInventory` variable entirely.

---

### 2. Composability Violation — One Test Covering Multiple Behaviors

**Location**: `TestFullInventoryFlow` (lines 57–75)

The single test exercises `AddStock`, `Reserve`, `Release`, and `Available` in a sequential chain. Problems:

- If `AddStock` or `Reserve` fails, the test aborts (`t.Fatalf`) before reaching `Release` and `Available`, leaving those behaviors untested.
- A failure message like "unexpected error" does not tell you which operation failed.
- When this test fails, you cannot tell whether the bug is in `AddStock`, `Reserve`, `Release`, or `Available`.
- It is not possible to run just the `Release` behavior in isolation to diagnose a regression.

**Recommendation**: Split into focused, single-behavior tests:

- `TestAddStock_IncreasesAvailableQty`
- `TestReserve_DecreasesAvailableQty`
- `TestRelease_RestoresAvailableQty`
- `TestAvailable_ReflectsStockMinusReserved`

Each test should set up its own precondition, perform exactly one operation, and assert exactly one outcome.

---

### 3. Automation Violation — Manual Inspection via fmt.Println

**Location**: Line 70

```go
fmt.Printf("Available after release: %d\n", available)
```

This line prints the computed value to stdout, requiring a human to read the output and judge whether it looks correct. In an automated CI pipeline, this output is noise — it does not contribute to pass/fail. Actual verification does happen on line 72 (`if available != 8`), but the `fmt.Printf` call suggests the author did not trust the assertion alone and left a debug print in place.

**Recommendation**: Remove the `fmt.Printf` statement entirely. The assertion on line 72 is sufficient and machine-verifiable. Also remove the `"fmt"` import if it is not needed elsewhere.

---

### 4. Specificity Violation — Generic Error Messages in Production Code

**Location**: Lines 28 and 37

```go
return fmt.Errorf("operation failed")
```

Both `AddStock` (invalid qty) and `Reserve` (insufficient stock) return the same generic error string. Tests that check `err == nil` cannot distinguish between the two failure modes. This also means:

- `TestReserveExceedsStock` only checks `err != nil`, so it would pass even if `AddStock` returned the same error for a completely different reason.
- A caller receiving `"operation failed"` has no actionable information.

**Recommendation**: Return distinct, descriptive errors:

```go
// In AddStock
return fmt.Errorf("invalid quantity %d: must be greater than zero", qty)

// In Reserve
return fmt.Errorf("insufficient stock for SKU %q: requested %d, available %d", sku, qty, available)
```

Tests should then assert on the error content or use sentinel errors/error types, not just `err != nil`.

---

## What Is Already Correct

`TestAddNegativeStock` is the only test written in a healthy way:

- It creates its own local `Inventory` instance (`inv := NewInventory()`).
- It tests a single behavior (rejecting negative qty).
- It does not depend on any other test's state.
- It uses a simple, clear assertion.

This test serves as the template the other tests should follow.

---

## Recommended Rewrite (Sketch)

```go
func TestAddStock_IncreasesAvailableQty(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    if got := inv.Available("SKU-1"); got != 10 {
        t.Errorf("expected 10, got %d", got)
    }
}

func TestReserve_DecreasesAvailableQty(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    err := inv.Reserve("SKU-1", 3)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if got := inv.Available("SKU-1"); got != 7 {
        t.Errorf("expected 7, got %d", got)
    }
}

func TestReserve_FailsWhenExceedsStock(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 5)
    err := inv.Reserve("SKU-1", 10)
    if err == nil {
        t.Fatal("expected error when reserving more than available")
    }
}

func TestRelease_RestoresAvailableQty(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 10)
    inv.Reserve("SKU-1", 3)
    inv.Release("SKU-1", 1)
    if got := inv.Available("SKU-1"); got != 8 {
        t.Errorf("expected 8, got %d", got)
    }
}

func TestAddStock_RejectsNegativeQty(t *testing.T) {
    inv := NewInventory()
    err := inv.AddStock("SKU-X", -5)
    if err == nil {
        t.Fatal("expected error for negative qty")
    }
}
```

---

## Issue Summary Table

| Issue | Desideratum Violated | Severity | Location |
|---|---|---|---|
| Shared `globalInventory` across tests | Isolated | High | Lines 55, 59–79 |
| One test covers add + reserve + release + available | Composable | High | Lines 57–75 |
| `fmt.Printf` used to verify output | Automated | Medium | Line 70 |
| Generic `"operation failed"` error message | Specific | Medium | Lines 28, 37 |
