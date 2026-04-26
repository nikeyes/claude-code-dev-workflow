# Evaluation Transcript — test_inventory.go

## Skill Used
`test-desiderata` (Kent Beck's Test Desiderata framework, 12 properties)

## Steps Taken

### Step 1: Read the Skill File
Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

Key takeaways from the skill:
- 12 properties to evaluate: Isolated, Composable, Deterministic, Fast, Writable, Readable, Behavioral, Structure-insensitive, Automated, Specific, Predictive, Inspiring.
- Analysis workflow: Read code → Evaluate against principles → Identify tradeoffs → Prioritize → Suggest specific changes.
- Output format: Issue / Location / Impact / Fix / Tradeoff per violation.
- Priority order: Safety (Isolated, Deterministic) → Feedback loop (Fast) → Maintainability (Readable, Structure-insensitive) → Confidence (Predictive, Inspiring).

### Step 2: Read the Test File
Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_inventory.go`.

**File structure observed:**
- Lines 1–7: Package header with embedded violation comments (confirming seeded bugs: Isolated, Composable, Automated, Specific).
- Lines 9–12: Imports (`fmt`, `testing`).
- Lines 14–23: `Inventory` struct definition with `stock` and `reserved` maps.
- Lines 19–23: `NewInventory()` constructor.
- Lines 26–32: `AddStock` method — generic error `"operation failed"` for qty <= 0.
- Lines 34–40: `Reserve` method — generic error `"operation failed"` for insufficient stock.
- Lines 43–48: `Release` method — silently clamps to 0 if over-released.
- Lines 50–52: `Available` method — returns 0 for unknown SKUs (Go zero-value).
- Line 55: `var globalInventory = NewInventory()` — package-level mutable state (Isolated violation).
- Lines 57–75: `TestFullInventoryFlow` — monolithic test: add, reserve, release, check available + `fmt.Printf` (Composable + Automated violations).
- Lines 77–83: `TestReserveExceedsStock` — depends on `globalInventory` modified by prior test (Isolated violation).
- Lines 85–91: `TestAddNegativeStock` — uses local `inv`, good isolation here.

### Step 3: Evaluate Against Each Property

**1. Isolated:** VIOLATED
- `globalInventory` at line 55 shared across tests.
- `TestReserveExceedsStock` relies on state set by `TestFullInventoryFlow`.
- Only `TestAddNegativeStock` is properly isolated (uses local `inv`).

**2. Composable:** VIOLATED
- `TestFullInventoryFlow` chains AddStock → Reserve → Release → Available in a single test.
- Cannot test each dimension independently.
- Failure in Reserve hides whether Release behavior is correct.

**3. Deterministic:** PASS
- No randomness, no time dependency, no external calls.
- All inputs are hardcoded constants.
- Note: execution-order sensitivity from Isolated violation creates order-dependent results, but this is a secondary effect.

**4. Fast:** PASS
- Pure in-memory operations. No I/O, sleep, or network calls.

**5. Writable:** ACCEPTABLE (low concern)
- `NewInventory()` is trivial to call.
- The `globalInventory` pattern is a bad example that could lead new contributors astray.

**6. Readable:** VIOLATED
- Test name "TestFullInventoryFlow" does not communicate expected outcome.
- Magic number `8` at line 73 without explaining the arithmetic.
- `fmt.Printf` at line 70 adds noise without clarifying intent.
- Error message "expected 8, got %d" missing context.

**7. Behavioral:** PARTIAL CONCERN
- Tests check return values and errors.
- Missing: state-integrity assertions after errors (does stock stay unchanged after a failed AddStock or Reserve?).

**8. Structure-insensitive:** PASS
- Tests call only public API methods.
- Internal `stock`/`reserved` maps not accessed directly in tests.

**9. Automated:** VIOLATED
- `fmt.Printf` at line 70 writes to stdout.
- Humans running `go test` see printed output and may incorrectly treat it as verification.
- The assertion at lines 72–74 handles actual verification, making the print redundant and misleading.

**10. Specific:** VIOLATED
- `AddStock` and `Reserve` both return `"operation failed"` — identical, generic strings.
- Impossible to distinguish which operation or what condition caused the failure.
- `TestFullInventoryFlow` covers multiple operations; failure location is unclear.

**11. Predictive:** VIOLATED
- Untested: zero-quantity AddStock, Release-more-than-reserved clamping, Available on unknown SKU, multiple SKUs, error-state integrity.
- These are all plausible production failure points.

**12. Inspiring:** PARTIAL CONCERN
- Minimal suite (3 tests) for a component with 4 operations and multiple edge cases.
- Test passing does not inspire confidence that Inventory is production-ready.

### Step 4: Identify Tradeoffs

- Composable vs. Readable: splitting tests makes each test simpler and more readable, no real conflict.
- Predictive vs. Fast: adding more tests adds minimal time since all operations are in-memory.
- Isolated vs. Writable: one line of setup per test is a trivial cost for isolation guarantee.

### Step 5: Prioritize Improvements

Priority 1 (Safety): Remove `globalInventory`, use local instances per test. Remove `fmt.Printf`.
Priority 2 (Feedback): Specific error messages. Split and rename `TestFullInventoryFlow`.
Priority 3 (Confidence): Add missing edge-case tests, add state-integrity assertions after errors.

### Step 6: Output

Wrote full analysis to:
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-1/eval-3/with_skill/outputs/analysis.md`

## Summary of Findings

| Violation Count | Properties |
|---|---|
| 5 definite violations | Isolated, Composable, Readable, Automated, Specific, Predictive |
| 3 partial concerns | Writable, Behavioral, Inspiring |
| 4 passing | Deterministic, Fast, Structure-insensitive (+ Automated passing except for the print) |

The most impactful single change: remove `globalInventory` and replace with per-test `NewInventory()` calls. This fixes the most serious reliability issue with minimal effort.
