# Test Desiderata Analysis: test_inventory.go

## Summary

Analyzed file: `core/skills/test-desiderata-workspace/evals/files/test_inventory.go`

Four Test Desiderata properties are violated: **Isolated**, **Composable**, **Automated**, and **Specific**. The remaining eight properties are either satisfied or not applicable given the scope of the file.

---

## Violations

### Issue 1: Isolated

**Issue:** Tests share a package-level mutable variable `globalInventory`

**Location:** Line 55 — `var globalInventory = NewInventory()` — shared by `TestFullInventoryFlow` (line 57) and `TestReserveExceedsStock` (line 77)

**Impact:** `TestReserveExceedsStock` passes only because `TestFullInventoryFlow` has already added 10 units of `SKU-1` to `globalInventory`. If the tests run in a different order (e.g., via `go test -shuffle=on`), or if `TestReserveExceedsStock` runs in isolation, `globalInventory` starts empty and `Reserve("SKU-1", 100)` returns an error for a different reason (zero available), making the test accidentally pass for the wrong reason — or it could begin silently passing when it should fail. Any future test that mutates `globalInventory` will corrupt later tests. The suite is not safe to parallelize (`t.Parallel()`).

**Fix:** Give each test its own `*Inventory` instance created with `NewInventory()`:

```go
func TestReserveExceedsStock(t *testing.T) {
    inv := NewInventory()
    inv.AddStock("SKU-1", 5)
    err := inv.Reserve("SKU-1", 100)
    if err == nil {
        t.Fatal("expected error reserving more than available")
    }
}
```

Remove the package-level `globalInventory` variable entirely. Each test constructs its own state.

---

### Issue 2: Composable

**Issue:** `TestFullInventoryFlow` tests four distinct behaviors — AddStock, Reserve, Release, and Available — in a single sequential scenario

**Location:** Lines 57–75 — `TestFullInventoryFlow` chains `AddStock`, `Reserve`, `Release`, and `Available` in one test body

**Impact:** When `TestFullInventoryFlow` fails, the failure message points to one line in a chain of operations. There is no way to know whether the failure originates in `AddStock`, `Reserve`, `Release`, or `Available` without mentally re-running the sequence. The test cannot be reused to verify individual operations in new scenarios. New behaviors (e.g., releasing more than was reserved) must be bolted onto the existing chain rather than composed independently.

**Fix:** Split into focused tests, one per behavior:

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
    inv.Reserve("SKU-1", 3)
    if got := inv.Available("SKU-1"); got != 7 {
        t.Errorf("expected 7, got %d", got)
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
```

Each test now sets up its own minimal state and verifies exactly one outcome.

---

### Issue 3: Automated

**Issue:** `fmt.Printf` on line 70 emits `"Available after release: %d\n"` to stdout, requiring a human to read the output to confirm correctness

**Location:** Line 70 — `fmt.Printf("Available after release: %d\n", available)`

**Impact:** The printed value is not part of any assertion — the test passes or fails on line 72–74 regardless of what was printed. A CI pipeline silently swallows the output, making it invisible. A developer reading the log has no automated confirmation that the printed number matches expectations. The print statement signals that the author was not confident the assertion alone was sufficient, which hints at missing trust in the test framework.

**Fix:** Remove the `fmt.Printf` statement. The assertion on lines 72–74 already captures the correctness check. If the value needs to be visible on failure, use `t.Logf` (which only prints on failure):

```go
available := inv.Available("SKU-1")
t.Logf("Available after release: %d", available) // only shown on failure
if available != 8 {
    t.Errorf("expected 8, got %d", available)
}
```

Or, use `testify/assert` with a descriptive message that is only printed when the assertion fails.

---

### Issue 4: Specific

**Issue:** Both `AddStock` and `Reserve` return the same generic error message `"operation failed"` regardless of what went wrong

**Location:** Line 28 — `return fmt.Errorf("operation failed")` (negative qty in `AddStock`); line 37 — `return fmt.Errorf("operation failed")` (over-reservation in `Reserve`)

**Impact:** When a test fails after receiving an error, the error message gives no indication of which operation failed or why. `TestAddNegativeStock` and `TestReserveExceedsStock` both check `err == nil`, but if a test ever needs to distinguish between "invalid quantity" and "insufficient stock" (e.g., to test error message content or error types), the identical messages make it impossible. Debugging production failures is also harder when the log contains only `"operation failed"`. The Specific property requires that test failures point directly to the problem; generic errors force manual tracing.

**Fix:** Return distinct, descriptive errors:

```go
// In AddStock:
return fmt.Errorf("AddStock: quantity must be positive, got %d", qty)

// In Reserve:
return fmt.Errorf("Reserve: insufficient stock for SKU %q: requested %d, available %d", sku, qty, available)
```

Tests that check error content can then assert on the message or use `errors.Is`/`errors.As` with sentinel errors or custom error types:

```go
var ErrInvalidQuantity = errors.New("invalid quantity")
var ErrInsufficientStock = errors.New("insufficient stock")
```

---

## Tradeoffs

### Tradeoff 1: Isolated ↔ Composable (only seeming to interfere)

The `Isolated` violation and the `Composable` violation are tightly linked. `TestFullInventoryFlow` tests the entire sequence (add, reserve, release, available) in one function, and it does so using `globalInventory`. The monolithic structure exists partly *because* state accumulates across operations — the test author relies on the shared instance to carry state from one operation to the next rather than setting up each scenario independently.

This looks like a tension: splitting into smaller tests (fixing Composable) seems to require even more setup code, which could make each test more complex. But this is only a seeming interference. The design fix is to introduce a small helper — or simply call `NewInventory()` in each test — so that each focused test sets up its own minimal state in two or three lines. Once every test owns its state, there is no reason for `globalInventory` to exist, and splitting becomes trivially safe.

**Priority:** Fix `Isolated` first. Shared mutable state causes intermittent failures that erode trust in the entire suite. Once `globalInventory` is gone, splitting `TestFullInventoryFlow` follows naturally and costs almost nothing.

---

### Tradeoff 2: Automated ↔ Specific (supporting)

The `Automated` violation (the `fmt.Printf` on line 70) and the `Specific` violation (generic `"operation failed"` messages) both push in the same direction: they make failures harder to diagnose. Removing `fmt.Printf` and replacing it with `t.Logf` (shown only on failure) makes the output meaningful and machine-visible. Replacing generic errors with descriptive ones makes the assertion output informative when a test fails. Fixing either one improves diagnosability; fixing both together delivers a suite where a failing test tells you exactly what went wrong without any manual inspection.

**Priority:** These two fixes are low-effort and independent. Apply both together; neither conflicts with the other.

---

### Tradeoff 3: Composable ↔ Specific (supporting)

A monolithic test (`Composable` violation) amplifies the `Specific` violation. When `TestFullInventoryFlow` fails, the failure could originate in `AddStock`, `Reserve`, `Release`, or `Available`. The generic `"operation failed"` error makes it even harder to localize. Splitting the test into focused cases (fixing `Composable`) means each failure is already narrowed to one operation; adding descriptive errors (fixing `Specific`) then pinpoints the exact condition within that operation. The two fixes compound each other's benefit.

**Priority:** Fix `Composable` (split the test) before adding descriptive errors — a focused test with a generic error is already far more debuggable than a monolithic test with descriptive errors.

---

### Tradeoff 4: Isolated ↔ Writable (only seeming to interfere)

Removing `globalInventory` and requiring each test to call `NewInventory()` might appear to increase boilerplate (violating `Writable`). In a larger suite this concern would be real. Here the setup is a single line: `inv := NewInventory()`. The three remaining tests each need at most two or three lines of setup. There is no actual writable cost. If the inventory setup were significantly heavier, a table-driven test or a `newInventoryWithStock` helper would give both isolation and writability simultaneously.

**Priority:** Not a real conflict at this scale. Remove `globalInventory` without hesitation.
