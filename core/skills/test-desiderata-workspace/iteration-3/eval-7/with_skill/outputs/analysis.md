# Test Desiderata Analysis: test_data_pipeline.py

## Summary

File analyzed: `test_data_pipeline.py`
Framework: Kent Beck's Test Desiderata (12 properties)
Violations found: 6 properties violated across 4 test methods

---

## Violations

### 1. Isolated — Shared Filesystem Artifact

**Issue:** All four tests write to the same hardcoded path `SHARED_OUTPUT = "/tmp/pipeline_output.csv"`. Any test that writes to this path leaves state on disk that the next test may read or overwrite, making results dependent on execution order and parallel-run safety impossible.

**Location:**
- Line 56: `SHARED_OUTPUT = "/tmp/pipeline_output.csv"`
- Lines 65, 76, 82, 87: every `self.pipeline.run(source, SHARED_OUTPUT)` call

**Impact:** If tests run in parallel or a previous run left a stale file, test behavior becomes unpredictable. A partially written file from a crashed test would cause subsequent tests to fail or silently read corrupted data.

**Fix:** Use a temporary file unique to each test invocation, cleaned up afterwards:

```python
import tempfile

def test_pipeline_runs_all_steps(self, tmp_path):
    output = tmp_path / "output.csv"
    source = [{"id": 1, "value": "10.5", "category": "sales"}]
    result = self.pipeline.run(source, str(output))
    ...
```

pytest's built-in `tmp_path` fixture creates a unique directory per test and cleans it up automatically.

---

### 2. Deterministic — Environment Variable Dependency

**Issue:** `DataPipeline.__init__` reads `os.getenv("BATCH_SIZE", "10")` at construction time. The `setup_method` creates a fresh `DataPipeline()` for every test, so any `BATCH_SIZE` set in the environment at the moment the test runs silently changes pipeline behavior. Two developers running the same tests on different machines (or CI vs local) may get different results.

**Location:**
- Line 21 (production code): `self.batch_size = int(os.getenv("BATCH_SIZE", "10"))`
- Line 61 (test setup): `self.pipeline = DataPipeline()` — no control over the env var

**Impact:** Tests are non-repeatable across environments. The violation is invisible in normal output; it only surfaces as a hard-to-diagnose discrepancy between environments.

**Fix:** Inject `batch_size` as a constructor parameter with a default, making the env-var read an application-level concern separate from the pipeline logic:

```python
# In production code
class DataPipeline:
    def __init__(self, batch_size: int = None):
        self.batch_size = batch_size if batch_size is not None else int(os.getenv("BATCH_SIZE", "10"))

# In tests — explicit control, no env dependency
self.pipeline = DataPipeline(batch_size=10)
```

---

### 3. Fast — Unnecessary `time.sleep` in `transform`

**Issue:** `transform` calls `time.sleep(0.001)` on every record to simulate "network latency". For `test_large_batch` (50 records) this adds at least 50 ms. At scale (thousands of tests, hundreds of records each) the cumulative cost is significant.

**Location:**
- Line 30: `time.sleep(0.001)  # Fast violation: unnecessary sleep per record`
- Line 85–89: `test_large_batch` — 50 records * 0.001 s = 0.05 s minimum per run

**Impact:** Slows the feedback loop. If this sleep represents real I/O that needs to be exercised, the correct fix is to make the I/O injectable and use a no-op stub in unit tests.

**Fix:** Remove the sleep from production code or make the delay injectable so tests can pass a zero-delay stub:

```python
class DataPipeline:
    def __init__(self, batch_size=None, record_delay=0.0):
        self.record_delay = record_delay
        ...

    def transform(self, records):
        for record in records:
            time.sleep(self.record_delay)   # 0.0 in tests
            yield ...

# Test setup
self.pipeline = DataPipeline(batch_size=10, record_delay=0.0)
```

---

### 4. Behavioral — `test_pipeline_runs_all_steps` checks step names, not behavior

**Issue:** `test_pipeline_runs_all_steps` asserts on `result["steps"] == ["extract", "transform", "load"]`. This list is assigned unconditionally in `run()` before any actual work happens (line 49: `self._steps_executed = ["extract", "transform", "load"]`). Even if `transform` were completely broken, the assertion would still pass.

**Location:**
- Lines 63–67: `test_pipeline_runs_all_steps`
- Line 49: `self._steps_executed = ["extract", "transform", "load"]` — hardcoded, not derived from execution

**Impact:** The test provides false confidence. It confirms that the `run` method exists and returns a dict with a `steps` key — not that the pipeline actually does anything useful with the data.

**Fix:** Assert on the actual output content instead of (or in addition to) internal step tracking:

```python
def test_pipeline_runs_all_steps(self, tmp_path):
    output = tmp_path / "output.csv"
    source = [{"id": 1, "value": "10.5", "category": "sales"}]
    self.pipeline.run(source, str(output))

    rows = list(csv.DictReader(output.open()))
    assert len(rows) == 1
    assert rows[0]["id"] == "1"
    assert rows[0]["value"] == "10.5"
    assert rows[0]["category"] == "SALES"
```

---

### 5. Specific — `test_transform_uppercases_category` asserts aggregate count, not transformation

**Issue:** The test name promises it verifies that categories are uppercased, but the only assertion is `result["records_processed"] == 2`. The actual uppercased values are never checked. If `transform` stopped uppercasing categories, this test would still pass.

**Location:**
- Lines 70–78: `test_transform_uppercases_category`
- Line 78: `assert result["records_processed"] == 2` — only assertion, irrelevant to the test name

**Impact:** When this test fails it only tells you the count changed; it says nothing about uppercasing. When it passes it tells you nothing about uppercasing either. It is a mislabeled count test.

**Fix:** Read the output file and assert on the transformed values directly:

```python
def test_transform_uppercases_category(self, tmp_path):
    output = tmp_path / "output.csv"
    source = [
        {"id": 1, "value": "5.0", "category": "sales"},
        {"id": 2, "value": "3.0", "category": "marketing"},
    ]
    self.pipeline.run(source, str(output))

    rows = list(csv.DictReader(output.open()))
    assert rows[0]["category"] == "SALES"
    assert rows[1]["category"] == "MARKETING"
```

---

### 6. Predictive — No coverage for malformed input or type coercion errors

**Issue:** `transform` does `float(record.get("value", 0))` and `str(record.get("id", ""))`. There are no tests for what happens when `value` is non-numeric (e.g. `"abc"`), when `id` is missing, or when `category` is `None`. These are real inputs in any data pipeline and will raise `ValueError` or `AttributeError` at runtime.

**Location:**
- Lines 84–89: `test_large_batch` comment "no assertion that all 50 records are correctly transformed"
- Lines 28–35: `transform` — no error handling for bad input

**Impact:** The pipeline will crash in production on the first malformed row, and the test suite would not have caught it. Error handling paths are completely untested.

**Fix:** Add tests for error scenarios and define expected behavior:

```python
def test_transform_raises_on_non_numeric_value(self, tmp_path):
    output = tmp_path / "output.csv"
    source = [{"id": 1, "value": "not_a_number", "category": "sales"}]
    with pytest.raises(ValueError, match="could not convert"):
        self.pipeline.run(source, str(output))

def test_transform_handles_missing_category(self, tmp_path):
    output = tmp_path / "output.csv"
    source = [{"id": 1, "value": "5.0"}]   # no category key
    self.pipeline.run(source, str(output))
    rows = list(csv.DictReader(output.open()))
    assert rows[0]["category"] == "UNKNOWN"
```

---

## Tradeoffs

### Tradeoff 1: Isolated ↔ Writable (only seeming to interfere)

The shared `SHARED_OUTPUT` constant exists because writing the output path in every test call is boilerplate — a writable convenience. Adding a unique path per test feels like more work. This makes the Isolated violation and the Writable concern look like a genuine tension.

It is not. pytest's `tmp_path` fixture resolves both at once: tests gain isolation without writing any extra path-management code. The fixture is injected automatically, is one word, and handles cleanup. Fixing Isolated here does not cost Writable at all — it is a design opportunity.

**Priority:** Fix Isolated first (flaky tests erode trust faster than any ergonomic concern), and the Writable improvement comes for free.

---

### Tradeoff 2: Behavioral ↔ Specific (supporting — fixing one enables the other)

`test_pipeline_runs_all_steps` violates Behavioral (checks step list, not output) and `test_transform_uppercases_category` violates Specific (name promises category assertion, body delivers count assertion). Both failures have the same root cause: the tests assert on the `run()` return dict instead of on the actual file output.

Once the output file is read and its rows are asserted (the Behavioral fix), every test automatically becomes more Specific — a failure message will name exactly which field was wrong on which record. Fixing Behavioral is the higher-leverage action; Specific quality follows directly.

**Priority:** Fix Behavioral first by asserting on output rows. Specificity improves as a side effect.

---

### Tradeoff 3: Deterministic ↔ Fast (interfering — real tension, manageable)

Controlling `BATCH_SIZE` means either setting and unsetting the environment variable in test setup/teardown (fragile, affects other tests running in the same process) or refactoring the constructor to accept the value as a parameter. The refactoring is the right move, but it does add a small amount of extra code at the call site — a real but tiny cost.

This is a genuine interfering relationship: making the pipeline fully deterministic requires a small amount of additional setup ceremony. However, the cost is low and the benefit (reproducible results across all environments) is high.

**Priority:** Fix Deterministic. The extra setup cost is negligible compared to the debugging cost of environment-dependent test failures on CI.

---

### Tradeoff 4: Fast ↔ Predictive (interfering — real tension)

Removing `time.sleep` in unit tests is the right call, but if that sleep represents real downstream I/O (a network call, a database write), removing it from the production code path requires an integration test that exercises the real path — and that test will be slower. More predictive coverage of I/O behavior means at least some tests must actually do I/O.

The standard resolution is a two-layer strategy: fast unit tests with injectable zero-delay stubs, plus a separate integration suite that runs the real code path (possibly less frequently). This gives both Fast unit tests and Predictive integration coverage without forcing a compromise in either layer.

**Priority:** Fix Fast first in the unit test layer by making the delay injectable. Schedule integration tests separately to preserve Predictive coverage.
