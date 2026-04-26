# Evaluation Transcript: test-desiderata skill on test_data_pipeline.py

## Session Info

- **Date:** 2026-04-26
- **Skill:** `stepwise-core:test-desiderata`
- **Input file:** `core/skills/test-desiderata-workspace/evals/files/test_data_pipeline.py`
- **Model:** Claude (via stepwise-dev agent)

---

## Step 1: Read the Skill File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

Key takeaways:
- Analysis workflow: Read → Evaluate → Identify tradeoffs → Prioritize → Suggest changes
- 12 properties: Isolated, Composable, Deterministic, Fast, Writable, Readable, Behavioral, Structure-insensitive, Automated, Specific, Predictive, Inspiring
- Output format per issue: Issue / Location / Impact / Fix / Tradeoff
- Priority order: Safety (Isolated + Deterministic) → Feedback Loop (Fast) → Maintainability (Readable + Structure-insensitive) → Confidence (Predictive + Inspiring)

---

## Step 2: Read the Test File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_data_pipeline.py`.

The file is 91 lines. It contains:
- A `DataPipeline` class (production code embedded in the test file) with `extract`, `transform`, `load`, and `run` methods
- A `TestDataPipeline` class with 4 test methods
- A module-level constant `SHARED_OUTPUT = "/tmp/pipeline_output.csv"`
- Embedded comments in the docstring flagging intentional violations

### Key observations from reading:

1. **Line 21:** `self.batch_size = int(os.getenv("BATCH_SIZE", "10"))` — reads env var at construction
2. **Line 30:** `time.sleep(0.001)` inside `transform` — artificial sleep per record
3. **Line 56:** `SHARED_OUTPUT = "/tmp/pipeline_output.csv"` — shared path across all tests
4. **Lines 63–68:** `test_pipeline_runs_all_steps` — asserts on `result["steps"]` (step name list), not output data
5. **Lines 70–78:** `test_transform_uppercases_category` — name claims to test uppercasing, but assertion is `records_processed == 2` (count only)
6. **Lines 84–90:** `test_large_batch` — 50 records × 0.001s = 50ms artificial sleep; no assertion on transformed content
7. **No tests for error paths:** no malformed input, no None values, no type errors

The docstring at the top confirms all violations are intentional for evaluation purposes:
- Deterministic: env dependency (BATCH_SIZE)
- Isolated + Deterministic: shared /tmp file
- Behavioral: checks step count not correctness
- Predictive: no malformed input tests
- Fast: sleep(0.001) per record
- Specific: aggregate stats assertions

---

## Step 3: Evaluate Against Each Property

Went through all 12 properties systematically:

### Isolated — VIOLATED
All tests share `/tmp/pipeline_output.csv`. Parallel execution causes race conditions. Serial execution leaves stale artifacts. `test_large_batch` even comments on this explicitly.

### Composable — OK
Each test covers a distinct scenario. Minor concern: `test_pipeline_runs_all_steps` conflates step-sequence verification with record-count verification, but overall composability is acceptable.

### Deterministic — VIOLATED
Two sub-issues:
- `os.getenv("BATCH_SIZE")` makes pipeline initialization dependent on environment state not controlled by tests
- Shared filesystem path means test results can depend on what files already exist

### Fast — VIOLATED
`time.sleep(0.001)` per record in `transform`. Small per-test, but scales badly with record count and test suite size.

### Writable — OK
`setup_method` is simple. Test structure is low-boilerplate. The shared path constant was probably introduced to reduce writable friction (one constant vs. per-test path management).

### Readable — Partial concern
Test names are mostly clear, but `test_transform_uppercases_category` does not test what its name says. This is a readability + behavioral issue combined.

### Behavioral — VIOLATED
- `test_pipeline_runs_all_steps`: asserts on `result["steps"]` (internal tracking list), not actual output behavior
- `test_transform_uppercases_category`: name says "uppercases category" but assertion is `records_processed == 2` — zero behavioral coverage of the uppercasing

### Structure-insensitive — Partial concern
`result["steps"] == ["extract", "transform", "load"]` couples the test to the implementation detail of how `run` populates `_steps_executed`. If the implementation is refactored to not use this internal list, the test would break even though behavior is unchanged.

### Automated — OK
All four tests run without human intervention. No print-and-inspect patterns.

### Specific — VIOLATED
`test_transform_uppercases_category` asserts `records_processed == 2`. When this fails (e.g., count is 1), the failure message tells you nothing about which record was dropped or what the transformation produced.

### Predictive — VIOLATED
No tests for:
- Non-numeric `value` fields (e.g., `"N/A"`, `""`, `None`) — `float()` will raise
- `None` category — `.upper()` will raise `AttributeError`
- Completely empty records `{}`
- Records with extra unknown fields

### Inspiring — Low (derived)
Consequence of Behavioral and Predictive failures. The suite passes with confidence that is not warranted — it does not verify the actual transformation logic or error resilience.

---

## Step 4: Identify Tradeoffs

### Fast vs Predictive
The sleep was presumably added to simulate real latency (making the test more "realistic"/Predictive), but it directly penalizes Fast. In unit tests this is the wrong tradeoff — latency simulation belongs in integration tests.

### Isolated vs Writable
Using a single shared constant path reduces per-test path management friction (Writable), but breaks Isolated. Resolution: pytest's `tmp_path` fixture gives both Isolated and Writable with zero extra effort.

### Specific vs Predictive vs Writable
Aggregate-count assertions are easy to write (Writable) but sacrifice both Specific (failures not diagnostic) and Predictive (edge cases not covered). Using `@pytest.mark.parametrize` can resolve all three simultaneously.

---

## Step 5: Prioritize

Following the skill's priority order:

1. **Safety first:** Fix Isolated (shared path) and Deterministic (env var) — these cause flaky failures
2. **Feedback loop:** Remove `time.sleep` — fast tests run often
3. **Maintainability:** Fix Behavioral violations — tests should assert on what they claim to test
4. **Confidence:** Add Predictive error-path tests — define the contract for malformed input

---

## Step 6: Write Output

Produced `analysis.md` with:
- 6 violations documented with Issue / Location / Impact / Fix / Tradeoff format
- Properties without violations listed
- Tradeoff analysis section
- Prioritized recommendations table
- Summary table

Total violations identified: 6 (Isolated, Deterministic, Fast, Behavioral, Specific, Predictive)
Total properties assessed: 12
Critical priority: 2 (Isolated, Deterministic)
High priority: 2 (Behavioral, Predictive)
Moderate priority: 2 (Fast, Specific)
