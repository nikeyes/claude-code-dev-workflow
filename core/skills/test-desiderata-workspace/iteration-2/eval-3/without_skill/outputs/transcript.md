# Transcript: Test Quality Analysis of test_inventory.go

## Task

Analyze the test file at:
`/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_inventory.go`

Identify quality problems and produce concrete improvement recommendations.

---

## Steps Taken

### Step 1: Read the target file

Used the Read tool to load the full contents of `test_inventory.go`.

The file contained:
- Package declaration and imports (`fmt`, `testing`)
- Production code: `Inventory` struct, `NewInventory`, `AddStock`, `Reserve`, `Release`, `Available`
- A package-level variable: `var globalInventory = NewInventory()`
- Three test functions: `TestFullInventoryFlow`, `TestReserveExceedsStock`, `TestAddNegativeStock`
- Comments inside the file explicitly labelling the intended violations (the file is an eval fixture)

### Step 2: Check output directory existence

Used Bash to confirm:
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/iteration-2/eval-3/without_skill/outputs/` exists and is empty.

### Step 3: Analyze the code

Reviewed each test and the production code against standard test quality criteria (Kent Beck's Test Desiderata framework):

**Isolated**: Does each test stand alone, independent of other tests?
- Found: `globalInventory` shared between `TestFullInventoryFlow` and `TestReserveExceedsStock`. The second test depends on state left by the first.

**Composable**: Does each test cover exactly one behavior?
- Found: `TestFullInventoryFlow` chains four operations (AddStock, Reserve, Release, Available) into a single test. A single failure masks which behavior is broken.

**Automated**: Is the pass/fail determined by the machine, not a human reading stdout?
- Found: `fmt.Printf("Available after release: %d\n", available)` on line 70 outputs a value to stdout requiring human inspection.

**Specific**: When a test fails, does the failure message point precisely to what went wrong?
- Found: Both `AddStock` and `Reserve` return `fmt.Errorf("operation failed")`. Tests cannot distinguish between error types, and callers get no actionable information.

**Clean (not violated)**: `TestAddNegativeStock` uses a local `inv`, tests one behavior, makes no side effects, and asserts clearly. This is the positive example in the file.

### Step 4: Drafted recommendations

For each issue:
- Described the root cause
- Explained the consequence (what goes wrong in practice)
- Provided a concrete fix with code examples

Also drafted a full recommended rewrite of the test suite showing all issues resolved.

### Step 5: Wrote output files

- Wrote `analysis.md` with structured issue descriptions, severity ratings, and a rewrite sketch.
- Wrote this `transcript.md` summarizing the steps taken.

---

## Key Findings

| Finding | Violated Property | Severity |
|---|---|---|
| `globalInventory` shared across tests | Isolated | High |
| `TestFullInventoryFlow` tests four behaviors | Composable | High |
| `fmt.Printf` used to inspect computed value | Automated | Medium |
| Generic `"operation failed"` errors | Specific | Medium |

One test (`TestAddNegativeStock`) is already correctly written and serves as a model.

---

## Time

Analysis completed in a single pass. No external resources consulted. No framework beyond standard Go testing patterns and Kent Beck's Test Desiderata applied.
