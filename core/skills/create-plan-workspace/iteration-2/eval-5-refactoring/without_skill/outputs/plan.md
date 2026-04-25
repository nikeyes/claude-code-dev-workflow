# Implementation Plan: Refactor data_processor to Strategy Pattern

## Context

The `data_processor.py` module exposes two public functions:
- `process(data, format_type)` — parses a string into a list of dicts using a long `if/elif` chain (5 branches: json, csv, key_value, xml_simple, fixed_width).
- `get_supported_formats()` — returns a hard-coded list of format names.

The test suite in `test_data_processor.py` covers all five formats plus the unsupported-format error, and the public API is `process` + `get_supported_formats`.

**Goal**: Replace the `if/elif` chain with the Strategy pattern so that:
1. Each format is an isolated, independently-testable unit.
2. Adding a new format requires no changes to existing code (open/closed principle).
3. The public API (`process`, `get_supported_formats`) stays unchanged so all existing tests continue to pass without modification.

---

## Design Decisions

### Strategy interface

Each strategy is a class that implements two methods:

```python
class FormatStrategy:
    source: str                           # format name / "source" label

    def parse(self, data: str) -> list[dict[str, Any]]:
        ...
```

`source` doubles as the format key, eliminating the separate name-to-strategy mapping.

### Registry

A module-level dict maps format name → strategy instance:

```python
_STRATEGIES: dict[str, FormatStrategy] = {
    s.source: s for s in [
        JsonStrategy(),
        CsvStrategy(),
        KeyValueStrategy(),
        XmlSimpleStrategy(),
        FixedWidthStrategy(),
    ]
}
```

`get_supported_formats()` becomes `list(_STRATEGIES.keys())`.

`process()` becomes a one-liner lookup + dispatch:

```python
def process(data: str, format_type: str) -> list[dict[str, Any]]:
    if format_type not in _STRATEGIES:
        raise ValueError(f"Unsupported format: {format_type}")
    return _STRATEGIES[format_type].parse(data)
```

---

## Step-by-Step Plan

### Step 1 — Run the test suite (baseline)

Verify all tests pass before touching any production code.

```bash
make test
```

Expected: all 11 tests green.

---

### Step 2 — Define the base Strategy class

Add an abstract base class at the top of `data_processor.py` (after imports):

```python
from abc import ABC, abstractmethod

class FormatStrategy(ABC):
    source: str

    @abstractmethod
    def parse(self, data: str) -> list[dict[str, Any]]:
        ...
```

No tests change; no behavior changes.

---

### Step 3 — Extract `JsonStrategy`

Move the JSON branch body into a new class:

```python
class JsonStrategy(FormatStrategy):
    source = "json"

    def parse(self, data: str) -> list[dict[str, Any]]:
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            parsed = [parsed]
        result = []
        for item in parsed:
            result.append({
                "source": self.source,
                "fields": item,
                "field_count": len(item),
            })
        return result
```

Run `make test` — all tests must still pass (the if/elif chain is still in place at this point).

---

### Step 4 — Extract `CsvStrategy`

```python
class CsvStrategy(FormatStrategy):
    source = "csv"

    def parse(self, data: str) -> list[dict[str, Any]]:
        reader = csv.DictReader(io.StringIO(data))
        result = []
        for row in reader:
            cleaned = {k: v.strip() for k, v in row.items()}
            result.append({
                "source": self.source,
                "fields": cleaned,
                "field_count": len(cleaned),
            })
        return result
```

Run `make test`.

---

### Step 5 — Extract `KeyValueStrategy`

```python
class KeyValueStrategy(FormatStrategy):
    source = "key_value"

    def parse(self, data: str) -> list[dict[str, Any]]:
        result = []
        for line in data.strip().split("\n"):
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            result.append({
                "source": self.source,
                "fields": {key.strip(): value.strip()},
                "field_count": 1,
            })
        return result
```

Run `make test`.

---

### Step 6 — Extract `XmlSimpleStrategy`

```python
class XmlSimpleStrategy(FormatStrategy):
    source = "xml_simple"

    def parse(self, data: str) -> list[dict[str, Any]]:
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
                            "source": self.source,
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
                "source": self.source,
                "fields": dict(fields),
                "field_count": len(fields),
            })
        return result
```

Run `make test`.

---

### Step 7 — Extract `FixedWidthStrategy`

```python
class FixedWidthStrategy(FormatStrategy):
    source = "fixed_width"

    def parse(self, data: str) -> list[dict[str, Any]]:
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
                "source": self.source,
                "fields": fields,
                "field_count": len(fields),
            })
        return result
```

Run `make test`.

---

### Step 8 — Build the registry and replace the if/elif chain

After all five strategy classes are defined, replace the old `process` function and update `get_supported_formats`:

```python
_STRATEGIES: dict[str, FormatStrategy] = {
    s.source: s for s in [
        JsonStrategy(),
        CsvStrategy(),
        KeyValueStrategy(),
        XmlSimpleStrategy(),
        FixedWidthStrategy(),
    ]
}


def process(data: str, format_type: str) -> list[dict[str, Any]]:
    if format_type not in _STRATEGIES:
        raise ValueError(f"Unsupported format: {format_type}")
    return _STRATEGIES[format_type].parse(data)


def get_supported_formats() -> list[str]:
    return list(_STRATEGIES.keys())
```

Run `make test` — all 11 existing tests must still pass. No test file changes needed.

---

### Step 9 — Final cleanup

- Remove the `from abc import ABC, abstractmethod` import if you prefer a simpler duck-typed protocol over a formal ABC (optional; keep if you want enforcement).
- Verify no dead code remains.
- Run `make test` one final time.

---

## Final file structure

`data_processor.py` will contain, in order:

1. Imports (`json`, `csv`, `io`, `typing`, optionally `abc`)
2. `FormatStrategy` base class
3. `JsonStrategy`
4. `CsvStrategy`
5. `KeyValueStrategy`
6. `XmlSimpleStrategy`
7. `FixedWidthStrategy`
8. `_STRATEGIES` registry dict
9. `process()` public function
10. `get_supported_formats()` public function

`test_data_processor.py` — **no changes required**.

---

## Acceptance Criteria

- `make test` passes with all 11 tests green after each step.
- The `process` and `get_supported_formats` public API signatures are unchanged.
- The `if/elif` chain is fully removed from `process`.
- Adding a new format only requires: writing a new strategy class and adding it to the `_STRATEGIES` list — zero changes to `process` or `get_supported_formats`.
