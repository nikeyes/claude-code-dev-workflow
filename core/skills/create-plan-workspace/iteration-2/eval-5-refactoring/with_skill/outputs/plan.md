# Refactor data_processor to Strategy Pattern Implementation Plan

## Overview

Refactor `data_processor.py` to replace the monolithic `process()` function's `if/elif` chain (5 branches) with the Strategy pattern. Each format type becomes an independent strategy class, making it easy to add new formats and test each parser in isolation.

## Current State Analysis

The current implementation lives in a single file `data_processor.py` (118 lines) with one `process()` function containing 5 `if/elif` branches:

- `json` (lines 8-19): parses JSON, normalises dict→list, annotates with `source`, `fields`, `field_count`
- `csv` (lines 21-30): uses `csv.DictReader`, strips whitespace, same annotation structure
- `key_value` (lines 33-44): splits on `\n` then `=`, skips invalid lines, same annotation
- `xml_simple` (lines 46-84): hand-rolled XML tag parser, accumulates `fields` per `<record>`, same annotation
- `fixed_width` (lines 86-110): derives column positions from header line, same annotation
- `else` (lines 112-113): raises `ValueError("Unsupported format: ...")`

A companion `get_supported_formats()` function (lines 116-117) returns a hardcoded list.

All 5 parsers produce records with the same structure: `{"source": str, "fields": dict, "field_count": int}`.

The test suite (`test_data_processor.py`) covers all 5 format classes plus the unsupported-format error; tests only use the public API (`process`, `get_supported_formats`) — no implementation details are tested. The `Makefile` runs `pytest test_data_processor.py -v`.

## Desired End State

After the refactor:

1. A `FormatStrategy` abstract base class (or `Protocol`) defines `parse(data: str) -> list[dict]`.
2. Five concrete strategy classes (`JsonStrategy`, `CsvStrategy`, `KeyValueStrategy`, `XmlSimpleStrategy`, `FixedWidthStrategy`) each implement `parse`.
3. A registry (`dict[str, FormatStrategy]`) maps format names to strategy instances.
4. `process(data, format_type)` delegates to the registry; raises `ValueError` for unknown formats.
5. `get_supported_formats()` derives its list from the registry keys.
6. All existing tests pass without modification.
7. Adding a new format requires only: write a new strategy class + register it — no changes to `process`.

### Key Discoveries

- `data_processor.py:7-113` — entire logic is one function; no existing abstractions to preserve
- `data_processor.py:116-117` — `get_supported_formats` is a hardcoded list; after refactor it should derive from the registry
- `test_data_processor.py:1` — imports only `process` and `get_supported_formats`; public API must remain stable
- `Makefile:2` — single test command: `make test` (runs `pytest test_data_processor.py -v`)
- All 5 parsers share the identical output schema — a clean fit for Strategy

## What We're NOT Doing

- No new format parsers beyond the existing 5
- No async or streaming support
- No changes to the test file
- No persistence, serialisation, or CLI interface
- No plugin-loading mechanism (strategies are registered in-module)
- No performance optimisation of the parsers themselves

## Implementation Approach

Introduce the Strategy pattern incrementally in 3 phases:

1. **Define the abstraction** — `FormatStrategy` base class/protocol and a registry, with `process` and `get_supported_formats` delegating to it. Tests must stay green throughout.
2. **Migrate strategies one by one** — move each parser branch into its own class and register it, removing the corresponding `elif` branch after each migration.
3. **Cleanup** — remove the now-empty `if/elif` skeleton, verify the final shape, run full test suite.

Each phase ends with a green `make test` run before moving on.

---

## Phase 1: Introduce Abstraction and Registry

### Overview

Define `FormatStrategy`, create an empty registry, and wire `process` and `get_supported_formats` to the registry — while keeping all 5 `elif` branches intact as a fallback. This proves the scaffolding works before any migration.

### Changes Required

#### 1. Add `FormatStrategy` ABC and empty registry

**File**: `data_processor.py`

Add at the top (after imports):

```python
from abc import ABC, abstractmethod

class FormatStrategy(ABC):
    @abstractmethod
    def parse(self, data: str) -> list[dict]:
        ...

_REGISTRY: dict[str, FormatStrategy] = {}
```

#### 2. Update `process` to try registry first, fall through to elif chain

**File**: `data_processor.py`

```python
def process(data: str, format_type: str) -> list[dict[str, Any]]:
    if format_type in _REGISTRY:
        return _REGISTRY[format_type].parse(data)
    if format_type == "json":
        ...  # existing branch unchanged
    elif format_type == "csv":
        ...
    # ... remaining branches unchanged
    else:
        raise ValueError(f"Unsupported format: {format_type}")
```

#### 3. Update `get_supported_formats` to include registry keys

**File**: `data_processor.py`

```python
def get_supported_formats() -> list[str]:
    legacy = ["json", "csv", "key_value", "xml_simple", "fixed_width"]
    return list(_REGISTRY.keys()) or legacy
```

Note: once all strategies are registered, the legacy list is removed.

### Success Criteria

- [ ] All tests pass: `make test`

---

## Phase 2: Migrate Each Format to a Strategy Class

### Overview

For each of the 5 formats, extract the parsing logic into a dedicated class, register the instance, and remove the corresponding `elif` branch. Migrate in order: `json` → `csv` → `key_value` → `xml_simple` → `fixed_width`. Run `make test` after each migration.

### Changes Required

#### Step 2a: JsonStrategy

**File**: `data_processor.py`

```python
class JsonStrategy(FormatStrategy):
    def parse(self, data: str) -> list[dict]:
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            parsed = [parsed]
        result = []
        for item in parsed:
            result.append({
                "source": "json",
                "fields": item,
                "field_count": len(item),
            })
        return result

_REGISTRY["json"] = JsonStrategy()
```

Remove the `if format_type == "json":` branch from `process`. Run `make test`.

#### Step 2b: CsvStrategy

**File**: `data_processor.py`

```python
class CsvStrategy(FormatStrategy):
    def parse(self, data: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(data))
        result = []
        for row in reader:
            cleaned = {k: v.strip() for k, v in row.items()}
            result.append({
                "source": "csv",
                "fields": cleaned,
                "field_count": len(cleaned),
            })
        return result

_REGISTRY["csv"] = CsvStrategy()
```

Remove the `elif format_type == "csv":` branch. Run `make test`.

#### Step 2c: KeyValueStrategy

**File**: `data_processor.py`

```python
class KeyValueStrategy(FormatStrategy):
    def parse(self, data: str) -> list[dict]:
        result = []
        for line in data.strip().split("\n"):
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            result.append({
                "source": "key_value",
                "fields": {key.strip(): value.strip()},
                "field_count": 1,
            })
        return result

_REGISTRY["key_value"] = KeyValueStrategy()
```

Remove the `elif format_type == "key_value":` branch. Run `make test`.

#### Step 2d: XmlSimpleStrategy

**File**: `data_processor.py`

```python
class XmlSimpleStrategy(FormatStrategy):
    def parse(self, data: str) -> list[dict]:
        result = []
        current_tag = None
        current_value = []
        fields = {}
        for line in data.strip().split("\n"):
            line = line.strip()
            if line.startswith("</") and line.endswith(">"):
                tag = line[2:-1]
                if tag == current_tag:
                    fields[tag] = "".join(current_value)
                    current_tag = None
                    current_value = []
                elif tag == "record":
                    if fields:
                        result.append({
                            "source": "xml_simple",
                            "fields": dict(fields),
                            "field_count": len(fields),
                        })
                        fields = {}
            elif line.startswith("<") and line.endswith(">"):
                tag = line[1:-1]
                if tag == "record":
                    fields = {}
                else:
                    current_tag = tag
                    current_value = []
            else:
                if current_tag:
                    current_value.append(line)
        if fields:
            result.append({
                "source": "xml_simple",
                "fields": dict(fields),
                "field_count": len(fields),
            })
        return result

_REGISTRY["xml_simple"] = XmlSimpleStrategy()
```

Remove the `elif format_type == "xml_simple":` branch. Run `make test`.

#### Step 2e: FixedWidthStrategy

**File**: `data_processor.py`

```python
class FixedWidthStrategy(FormatStrategy):
    def parse(self, data: str) -> list[dict]:
        field_spec = None
        result = []
        for line in data.strip().split("\n"):
            if field_spec is None:
                field_spec = []
                pos = 0
                for name in line.split():
                    start = line.index(name, pos)
                    field_spec.append((name, start))
                    pos = start + len(name)
                continue
            fields = {}
            for i, (name, start) in enumerate(field_spec):
                end = field_spec[i + 1][1] if i + 1 < len(field_spec) else len(line)
                fields[name] = line[start:end].strip()
            result.append({
                "source": "fixed_width",
                "fields": fields,
                "field_count": len(fields),
            })
        return result

_REGISTRY["fixed_width"] = FixedWidthStrategy()
```

Remove the `elif format_type == "fixed_width":` branch. Run `make test`.

### Success Criteria (after each step)

- [ ] All tests pass: `make test`

---

## Phase 3: Final Cleanup

### Overview

After all 5 strategies are registered, the `process` function's `if/elif` skeleton is empty. Clean up the dead code, simplify `get_supported_formats`, and verify the final structure.

### Changes Required

#### 1. Simplify `process`

**File**: `data_processor.py`

```python
def process(data: str, format_type: str) -> list[dict[str, Any]]:
    if format_type not in _REGISTRY:
        raise ValueError(f"Unsupported format: {format_type}")
    return _REGISTRY[format_type].parse(data)
```

#### 2. Simplify `get_supported_formats`

**File**: `data_processor.py`

```python
def get_supported_formats() -> list[str]:
    return list(_REGISTRY.keys())
```

#### 3. Remove unused imports (if any)

Verify that all imports (`json`, `csv`, `io`, `Any`, `ABC`, `abstractmethod`) are still required. The `ABC`/`abstractmethod` imports are new; `json`, `csv`, `io` are now used by strategy classes.

### Success Criteria

- [ ] All tests pass: `make test`
- [ ] `process` function body is 3 lines or fewer (no `if/elif` chain)
- [ ] `get_supported_formats` derives its list from `_REGISTRY` — no hardcoded strings

---

## Testing Strategy

### Unit Tests

All existing tests in `test_data_processor.py` cover the full public API and must pass unchanged at every phase:

- `TestProcessJSON` — single object, array, field_count
- `TestProcessCSV` — basic parsing, whitespace stripping
- `TestProcessKeyValue` — basic parsing, invalid line skipping
- `TestProcessXMLSimple` — single record with multi-line values
- `TestProcessFixedWidth` — header-derived columns
- `TestSupportedFormats` — lists all 5 formats, raises for unsupported

### No new tests required

The refactor is purely structural; behaviour is unchanged. The existing test suite provides full regression coverage for each incremental migration step.

---

## Performance Considerations

No performance impact. The registry lookup is O(1) dict access. Parsing logic is identical to the original.

## Migration Notes

- No data migration required (in-memory transformation only)
- The public API (`process`, `get_supported_formats`) is preserved exactly
- Each phase step can be independently code-reviewed
- Rolling back any step is trivial: restore the removed `elif` branch

## References

- Source file: `data_processor.py:7-117`
- Test file: `test_data_processor.py`
- Makefile target: `Makefile:1-2` (`make test`)
