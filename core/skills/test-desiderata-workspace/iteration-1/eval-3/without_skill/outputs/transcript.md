# Transcript: Test Desiderata Analysis (Baseline, No Skill)

**Date**: 2026-04-26  
**Mode**: Baseline — no skill file used  
**File analyzed**: `core/skills/test-desiderata-workspace/evals/files/test_inventory.go`

---

## Steps Taken

### Step 1: Read the test file

Used the Read tool to load the full content of `test_inventory.go`. The file is 92 lines and contains:
- A Go `inventory` package with production code (`Inventory` struct, `NewInventory`, `AddStock`, `Reserve`, `Release`, `Available`)
- A package-level shared variable `globalInventory`
- 3 test functions: `TestFullInventoryFlow`, `TestReserveExceedsStock`, `TestAddNegativeStock`
- Comments in the file explicitly annotating 4 seeded violations

### Step 2: Identify seeded violations from comments

The file comments identified these violations:
- **Isolated**: `globalInventory` shared across tests
- **Composable**: one giant test covering add, reserve, release, restock in sequence
- **Automated**: `fmt.Println` requiring human inspection
- **Specific**: generic `"operation failed"` error messages

### Step 3: Evaluate all 12 Test Desiderata properties

Went through each of the 12 properties systematically:

1. **Isolated** — VIOLATED (confirmed seeded violation)
2. **Composable** — VIOLATED (confirmed seeded violation)
3. **Deterministic** — LATENT RISK (emerges from Isolated violation; `go test -shuffle=on` would expose it)
4. **Fast** — PASS (pure in-memory operations)
5. **Writable** — PARTIAL PASS (Go testing is low-friction, but no setup helpers)
6. **Readable** — PARTIAL PASS (magic number 8, misleading test name)
7. **Behavioral** — PARTIAL PASS (public API tested, but failed-reserve invariant untested)
8. **Structure-insensitive** — PASS (no internal field access)
9. **Automated** — VIOLATED (confirmed seeded violation: `fmt.Printf` on line 70)
10. **Specific** — VIOLATED (confirmed seeded violation: generic errors; also weak assertion messages)
11. **Predictive** — PARTIAL PASS (missing edge cases: release-beyond-reserved, unknown SKU, zero qty)
12. **Inspiring** — PARTIAL PASS (shared state erodes confidence; `TestAddNegativeStock` is good)

### Step 4: Formulate recommendations

Prioritized 5 concrete recommendations ordered by impact:
1. Remove `globalInventory`, use local `inv` in each test
2. Remove `fmt.Printf` call
3. Use specific error messages in production code
4. Split `TestFullInventoryFlow` into focused tests
5. Add edge case tests

### Step 5: Write outputs

- Wrote full analysis to `analysis.md`
- Writing this transcript to `transcript.md`

---

## Key Observations

**Confirmed all 4 seeded violations.** Beyond those, identified:
- A latent non-determinism risk (Deterministic property) caused by the Isolated violation
- A missing invariant test: after a failed `Reserve`, `Available()` should be unchanged
- Edge cases not covered: release-beyond-reserved clamping (code clamps to 0 but no test verifies this), unknown SKU availability (should return 0), zero-quantity operations

**Strongest test in the file**: `TestAddNegativeStock` (line 85-91) — creates its own inventory, tests a single behavior, has no shared state.

**Weakest test**: `TestReserveExceedsStock` — entirely depends on state from a previous test. If run in isolation, it tests a different scenario than intended (empty inventory vs. fully-stocked inventory). It would still pass (empty inventory also can't satisfy a reserve of 100), but for the wrong reason.

---

## Approach Notes (Baseline)

This analysis was performed using direct knowledge of Kent Beck's Test Desiderata framework without invoking any skill file. The 12 properties were evaluated by reading the code directly and applying the framework manually. No sub-agents or specialized tools were used beyond file reading.
