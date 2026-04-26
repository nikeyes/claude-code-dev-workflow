# Test Desiderata Analysis: test_inventory.go

## Overview

**File analyzed:** `core/skills/test-desiderata-workspace/evals/files/test_inventory.go`
**Package:** `inventory`
**Tests found:**
- `TestFullInventoryFlow` (line 57)
- `TestReserveExceedsStock` (line 77)
- `TestAddNegativeStock` (line 85)

The file implements an `Inventory` struct with `AddStock`, `Reserve`, `Release`, and `Available` operations alongside their tests in the same file.

---

## Evaluation Against the 12 Test Desiderata Properties

### 1. Isolated — VIOLATED

**Assessment:** Fail

**Evidence:**
- Line 55: `var globalInventory = NewInventory()` — a package-level mutable variable shared across all tests.
- `TestFullInventoryFlow` (line 59) calls `globalInventory.AddStock("SKU-1", 10)` and modifies the shared inventory.
- `TestReserveExceedsStock` (line 79) calls `globalInventory.Reserve("SKU-1", 100)` and implicitly depends on the state left by `TestFullInventoryFlow` (it expects SKU-1 to exist and have limited available stock). If `TestReserveExceedsStock` ran first on an empty inventory, the assertion would pass but for the wrong reason (stock of 0 is less than 100 — wait, 100 > 0 so it would also fail). However, the available amount after the first test is 8, so the assertion logic depends on previous execution.

**Issue:**
```
Issue: TestReserveExceedsStock violates Isolated property
Location: Line 79 — uses globalInventory modified by TestFullInventoryFlow
Impact: Test results depend on execution order. Running tests in isolation or
        in a different order produces different results.
Fix: Each test should create its own local Inventory instance using NewInventory()
     and set up only the state it needs.
Tradeoff: Slightly more setup code per test, but much more reliable.
```

---

### 2. Composable — VIOLATED

**Assessment:** Fail

**Evidence:**
- `TestFullInventoryFlow` (lines 57–75) covers four distinct operations in sequence: AddStock → Reserve → Release → Available. Each operation is a separate concern that could be tested independently.
- Combining them into a single test means a failure in `Reserve` prevents testing `Release` behavior.
- There is no ability to reuse setup or compose smaller tests for edge-case combinations.

**Issue:**
```
Issue: TestFullInventoryFlow violates Composable property
Location: Lines 57–75 — single test covers add, reserve, release, and available
Impact: Cannot test dimensions independently. A bug in Reserve hides whether
        Release works. Cannot combine partial scenarios.
Fix: Break into focused tests:
     - TestAddStock_IncreasesAvailable
     - TestReserve_DecreasesAvailable
     - TestRelease_RestoresAvailability
     - TestAvailable_ReflectsNetPosition
Tradeoff: More test functions, but each is independently runnable and composable.
```

---

### 3. Deterministic — PASS

**Assessment:** Pass (with a note)

No random data generation, time dependencies, or external service calls are present. All test data is hardcoded (`"SKU-1"`, quantities 10, 3, 1, 100, etc.). The tests are deterministic in isolation, though the Isolated violation means results vary by execution order — a secondary effect, not a primary Deterministic failure.

---

### 4. Fast — PASS

**Assessment:** Pass

No I/O, sleep calls, network requests, or heavy operations. All operations are in-memory map manipulations. Tests should run in microseconds.

---

### 5. Writable — PARTIAL CONCERN

**Assessment:** Acceptable, with a note

Adding new tests for `AddStock` or `Release` requires either:
- Creating a new local `Inventory` instance (easy, `NewInventory()` is simple), or
- Relying on `globalInventory` (perpetuating the isolation problem).

The API is straightforward, and `NewInventory()` has no complex dependencies. Boilerplate is low. However, the presence of `globalInventory` as the "default" pattern in the existing tests creates a path-of-least-resistance anti-pattern for new tests.

---

### 6. Readable — VIOLATED

**Assessment:** Fail

**Evidence:**
- `TestFullInventoryFlow` (line 57): The name says "flow" but does not communicate what specific behavior is expected. A reader must parse the entire body to understand what is being validated.
- Line 73: The assertion `if available != 8` uses a magic number `8` without explaining the arithmetic (started with 10, reserved 3, released 1 → 10 - 3 + 1 = 8). The reasoning is not self-evident.
- Line 70: `fmt.Printf("Available after release: %d\n", available)` — print statement instead of a named intermediate variable or explanatory comment.
- Line 72: The assertion error message `"expected 8, got %d"` lacks context about *why* 8 is the expected value.

**Issue:**
```
Issue: TestFullInventoryFlow violates Readable property
Location: Lines 57–75
Impact: Reader must mentally simulate the full sequence to understand what
        value is expected and why. Intent is obscured.
Fix: Use descriptive test names that state the scenario and expected outcome,
     e.g. TestAvailableAfterReserveAndRelease_ReturnsCorrectCount.
     Use named constants or variables: const initialStock = 10, reserved = 3,
     released = 1, expectedAvailable = initialStock - reserved + released.
     Replace fmt.Printf with a proper assertion or remove it entirely.
```

---

### 7. Behavioral — PARTIAL CONCERN

**Assessment:** Mostly pass, with gaps

The tests do check observable behavior (return values and errors). However:
- `TestAddNegativeStock` only checks that *some* error is returned — it does not verify that stock was NOT modified when the error occurred. If `AddStock` erroneously partially updated state before returning the error, the test would still pass.
- `TestReserveExceedsStock` verifies an error is returned but does not check that `Reserved` state was not modified (no phantom reservation).

**Issue:**
```
Issue: TestAddNegativeStock and TestReserveExceedsStock have incomplete behavioral
       assertions (partial Behavioral violation)
Location: Lines 85–91 and 77–83
Impact: A buggy implementation that partially mutates state before returning
        an error would not be caught.
Fix: After expecting an error, assert that Available() is unchanged:
     e.g., if inv.Available("SKU-X") != 0 { t.Error("stock should not change on error") }
```

---

### 8. Structure-insensitive — PASS

**Assessment:** Pass

Tests call the public API (`AddStock`, `Reserve`, `Release`, `Available`) and do not inspect internal fields (`stock`, `reserved` maps directly). Refactoring the internal implementation (e.g., changing map key structure or adding caching) would not break the tests.

---

### 9. Automated — VIOLATED

**Assessment:** Fail

**Evidence:**
- Line 70: `fmt.Printf("Available after release: %d\n", available)` — this prints to stdout and requires a human to read and interpret the output to confirm correctness. The value is subsequently checked by a `t.Errorf` assertion (line 72–74), making the print redundant and misleading. A human running `go test` would see the output and might assume it is the verification, not realizing the actual assertion follows.

**Issue:**
```
Issue: TestFullInventoryFlow violates Automated property
Location: Line 70 — fmt.Printf writes to stdout requiring human inspection
Impact: Test output is noisy; humans may incorrectly trust the printed output
        as the verification mechanism rather than the actual t.Errorf assertion.
Fix: Remove the fmt.Printf entirely. The assertion on line 72–74 is sufficient.
     If debugging context is needed, use t.Logf (only shown on failure).
Tradeoff: None — the assertion already covers the check mechanically.
```

---

### 10. Specific — VIOLATED

**Assessment:** Fail

**Evidence:**
- `AddStock` returns `fmt.Errorf("operation failed")` (line 28) for invalid quantity.
- `Reserve` returns `fmt.Errorf("operation failed")` (line 37) for insufficient stock.
- Both return the same error string, making it impossible to distinguish which operation failed or why. Tests that check `err == nil` cannot distinguish error types.
- `TestFullInventoryFlow` uses `t.Fatalf` after `Reserve` fails with the message `"unexpected error: %v"` — if the error message is generic, diagnosing the failure in CI requires reading source code.

**Issue:**
```
Issue: AddStock and Reserve return identical generic errors, violating Specific property
Location: Lines 28, 37 — "operation failed" error message
Impact: When a test fails involving an error, the output gives no indication of
        what went wrong or where. Debugging requires source inspection.
Fix: Use specific error messages:
     - Line 28: fmt.Errorf("AddStock: quantity must be positive, got %d", qty)
     - Line 37: fmt.Errorf("Reserve: requested %d but only %d available for SKU %q", qty, available, sku)
Tradeoff: Slightly more verbose error messages, but dramatically faster diagnosis.
```

**Additional Specificity issue:**
- `TestFullInventoryFlow` covers multiple behaviors in one test. When it fails, it is not immediately obvious *which* operation caused the failure (AddStock? Reserve? Release? Available calculation?).

---

### 11. Predictive — VIOLATED

**Assessment:** Fail

**Evidence:**
Several important behaviors are not tested at all:

- **Zero-quantity stock add:** What happens with `AddStock("SKU", 0)`? The guard is `qty <= 0`, so 0 should fail — untested.
- **Release more than reserved:** `Release` silently clamps to 0 (line 44–47). This behavior (no error on over-release) is untested and may be surprising.
- **Release on non-existent SKU:** `Release("UNKNOWN", 5)` — would set `reserved["UNKNOWN"]` to -5, then clamp to 0. Behavior is not tested.
- **Available on unknown SKU:** `Available("UNKNOWN")` returns 0 (Go's zero-value for missing map key). This may or may not be desired — untested.
- **Concurrent access:** Not required at this level, but absent from consideration.
- **Multiple SKUs:** No test exercises interactions between different SKUs.

**Issue:**
```
Issue: Missing test coverage for edge cases, violating Predictive property
Location: Release function (lines 43–48) — over-release clamping untested
          Available function (lines 50–52) — unknown SKU behavior untested
          AddStock (lines 26–32) — zero-quantity boundary untested
Impact: Bugs in these paths would reach production undetected.
Fix: Add tests:
     - TestRelease_MoreThanReserved_ClampsToZero
     - TestAvailable_UnknownSKU_ReturnsZero
     - TestAddStock_ZeroQuantity_ReturnsError
```

---

### 12. Inspiring — PARTIAL CONCERN

**Assessment:** Partial fail

The three existing tests cover happy path, one error path (negative stock), and one capacity-exceeded path. This provides minimal confidence. A developer looking at this test suite could not confidently say "if these pass, the inventory system works correctly." Key scenarios (Release behavior, boundary conditions, error state integrity) are absent.

**Issue:**
```
Issue: Test suite lacks coverage of important behaviors, limiting Inspiring quality
Impact: Tests passing does not inspire confidence that the system is production-ready.
Fix: Add tests for Release behavior, boundary conditions on all operations,
     and error-state integrity (state unchanged after error). The suite should
     tell the story of what the Inventory guarantees.
```

---

## Summary of Violations

| Property             | Status   | Severity |
|----------------------|----------|----------|
| 1. Isolated          | VIOLATED | High     |
| 2. Composable        | VIOLATED | High     |
| 3. Deterministic     | Pass     | —        |
| 4. Fast              | Pass     | —        |
| 5. Writable          | Concern  | Low      |
| 6. Readable          | VIOLATED | Medium   |
| 7. Behavioral        | Concern  | Medium   |
| 8. Structure-insensitive | Pass | —        |
| 9. Automated         | VIOLATED | High     |
| 10. Specific         | VIOLATED | High     |
| 11. Predictive       | VIOLATED | Medium   |
| 12. Inspiring        | Concern  | Medium   |

**Violations found: 5 definite violations, 3 partial concerns**

---

## Prioritized Improvement Plan

### Priority 1 — Safety (fix flaky/unreliable tests)

1. **Remove `globalInventory`** — Replace all uses with local `NewInventory()` in each test. Fixes Isolated, and indirectly improves Deterministic reliability.

2. **Remove `fmt.Printf`** — Delete line 70. The assertion on line 72 is the actual check. Fixes Automated.

### Priority 2 — Feedback loop (make failures faster to diagnose)

3. **Use specific error messages** — Replace both `"operation failed"` strings with messages naming the operation and including the bad values. Fixes Specific.

4. **Rename and split `TestFullInventoryFlow`** — Create `TestReserve_DecreasesAvailableStock`, `TestRelease_IncreasesAvailableStock`, etc. Fixes Composable and Readable.

### Priority 3 — Confidence (strengthen production readiness)

5. **Add missing edge-case tests:**
   - `TestAddStock_ZeroQuantity_ReturnsError`
   - `TestRelease_MoreThanReserved_ClampsToZero`
   - `TestAvailable_UnknownSKU_ReturnsZero`
   - `TestAddStock_ErrorDoesNotMutateState`
   - `TestReserve_ErrorDoesNotMutateReservation`

   Fixes Predictive and Inspiring.

6. **Add post-error state assertions** in `TestAddNegativeStock` and `TestReserveExceedsStock`. Fixes partial Behavioral concern.

---

## Tradeoffs to Consider

- **Composable vs. Readable:** Splitting `TestFullInventoryFlow` into smaller tests makes each test more focused (Composable, Specific) but requires more test functions. The tradeoff is clearly worth it here.
- **Predictive vs. Fast:** Adding more edge-case tests slightly increases test count but since all tests are in-memory, the Fast property is not at risk.
- **Isolated vs. Writable:** Per-test `NewInventory()` instances add a one-line setup per test — negligible writable overhead for a significant isolation gain.

---

## Recommended Refactored Example

```go
func TestAddStock_IncreasesAvailableStock(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-A", 10)
    if got := inv.Available("SKU-A"); got != 10 {
        t.Errorf("expected available=10 after adding 10, got %d", got)
    }
}

func TestReserve_DecreasesAvailableStock(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-A", 10)
    if err := inv.Reserve("SKU-A", 3); err != nil {
        t.Fatalf("unexpected error reserving 3: %v", err)
    }
    if got := inv.Available("SKU-A"); got != 7 {
        t.Errorf("expected available=7 after reserving 3 from 10, got %d", got)
    }
}

func TestRelease_RestoresAvailability(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-A", 10)
    inv.Reserve("SKU-A", 3)
    inv.Release("SKU-A", 1)
    const expected = 8 // 10 - 3 + 1
    if got := inv.Available("SKU-A"); got != expected {
        t.Errorf("expected available=%d after reserve 3 and release 1 from 10, got %d", expected, got)
    }
}

func TestReserve_ExceedsAvailable_ReturnsError(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-A", 5)
    err := inv.Reserve("SKU-A", 10)
    if err == nil {
        t.Fatal("expected error when reserving more than available")
    }
    if got := inv.Available("SKU-A"); got != 5 {
        t.Errorf("expected state unchanged after failed reserve, got available=%d", got)
    }
}

func TestAddStock_NegativeQuantity_ReturnsError(t *testing.T) {
    inv := NewInventory()
    err := inv.AddStock("SKU-X", -5)
    if err == nil {
        t.Fatal("expected error for negative quantity")
    }
    if got := inv.Available("SKU-X"); got != 0 {
        t.Errorf("expected stock unchanged after failed add, got available=%d", got)
    }
}
```
