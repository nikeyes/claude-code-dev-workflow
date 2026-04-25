# Response: Refactor data_processor to Strategy Pattern

## Analysis of the Current Code

`data_processor.py` has two public functions:

- `process(data, format_type)` — a 110-line function with a five-branch `if/elif` chain (json, csv, key_value, xml_simple, fixed_width). All format-specific logic is inlined here.
- `get_supported_formats()` — returns a hard-coded list of the five format names.

The test suite covers all five formats and the unsupported-format error path. The public contract that must be preserved is:
- `process(data: str, format_type: str) -> list[dict[str, Any]]`
- `get_supported_formats() -> list[str]`
- Each result dict has keys `source`, `fields`, and `field_count`.

## Proposed Design

**Strategy interface**: an abstract base class `FormatStrategy` with a `source` class attribute (the format name) and an abstract `parse(data)` method.

**Five concrete strategies**: `JsonStrategy`, `CsvStrategy`, `KeyValueStrategy`, `XmlSimpleStrategy`, `FixedWidthStrategy` — each encapsulating exactly the logic currently inside one `if/elif` branch.

**Registry**: a module-level dict `_STRATEGIES` built from instantiated strategy objects, keyed by `strategy.source`.

**Simplified public functions**:
```python
def process(data: str, format_type: str) -> list[dict[str, Any]]:
    if format_type not in _STRATEGIES:
        raise ValueError(f"Unsupported format: {format_type}")
    return _STRATEGIES[format_type].parse(data)

def get_supported_formats() -> list[str]:
    return list(_STRATEGIES.keys())
```

Adding a new format in future requires only: write a new strategy class and add it to the registry list — no changes to `process` or `get_supported_formats`.

## Implementation Plan

The refactoring is done in small, test-verified steps:

| Step | Action | Test check |
|------|--------|------------|
| 1 | Run baseline (`make test`) — confirm 11 green | Baseline |
| 2 | Add `FormatStrategy` ABC | No behavior change |
| 3 | Extract `JsonStrategy` class | `make test` passes |
| 4 | Extract `CsvStrategy` class | `make test` passes |
| 5 | Extract `KeyValueStrategy` class | `make test` passes |
| 6 | Extract `XmlSimpleStrategy` class | `make test` passes |
| 7 | Extract `FixedWidthStrategy` class | `make test` passes |
| 8 | Build `_STRATEGIES` registry; replace `if/elif` in `process`; update `get_supported_formats` | All 11 tests pass |
| 9 | Final cleanup — remove dead code | `make test` passes |

Steps 3–7 extract each strategy class while leaving the `if/elif` chain intact, so there is always a working fallback until step 8 cuts over.

The test file requires **zero changes**: the public API is preserved exactly.

See `plan.md` in this directory for the full detailed plan with complete code snippets for each step.
