# Migration Plan: event_log.metadata from Plain String to Structured JSON

## Context

The `EventLog` class stores events in SQLite. The `metadata` column is declared as `TEXT` and currently
accepts plain strings. In practice, callers already serialize dictionaries into it with `json.dumps`,
but this is unenforced. The goal is to make the column contract explicit: `metadata` must always be a
JSON object (`dict`), serialized automatically by `EventLog` and deserialized on read.

Existing tests pass plain strings (e.g., `"session started"`) and raw JSON strings as metadata, so
those tests will need to be updated in a later step.

---

## Step 1 — Add internal JSON serialization in `log()` (backward-compatible write path)

**What:** Change `log()` to accept `metadata` as a `dict` (defaulting to `{}`). Serialize it to a
JSON string before inserting into the database. The database column type stays `TEXT`.

**Why this is safe:** No schema change. Existing rows are unaffected. Only new writes change behavior.

**Changes to `event_log.py`:**
- Change the `metadata` parameter type from `str = ""` to `dict = None` (use `{}` when `None`).
- Before the `INSERT`, call `json.dumps(metadata or {})` to produce the stored string.

**Test to write first (Red):**
```python
def test_log_with_dict_metadata(log):
    event = log.log("user.login", user_id=1, metadata={"ip": "1.2.3.4", "browser": "Firefox"})
    assert event["metadata"] == {"ip": "1.2.3.4", "browser": "Firefox"}
```
This test fails because `log()` does not yet accept dicts and `get_event()` does not deserialize.

---

## Step 2 — Add JSON deserialization in read methods (complete the round-trip)

**What:** In `get_event()`, deserialize the `metadata` field from its stored JSON string back to a
`dict` before returning. Apply the same deserialization in `get_events_by_type()` and
`get_events_by_user()`.

**Why this is safe:** All callers go through these three read methods. Centralizing deserialization
here means no caller needs to change.

**Changes to `event_log.py`:**
- Extract a helper `_deserialize_row(row: dict) -> dict` that calls `json.loads(row["metadata"])` and
  handles any value that is already a dict (defensive) or is `None` (returns `{}`).
- Use `_deserialize_row` in `get_event()`, `get_events_by_type()`, and `get_events_by_user()`.

**Test passes after this step:**
```python
def test_log_with_dict_metadata(log):  # now Green
    event = log.log("user.login", user_id=1, metadata={"ip": "1.2.3.4", "browser": "Firefox"})
    assert event["metadata"] == {"ip": "1.2.3.4", "browser": "Firefox"}
```

---

## Step 3 — Update existing tests to use the new dict-based contract

**What:** Replace the two tests that pass plain strings or raw JSON strings:

| Old test | New behavior |
|---|---|
| `test_log_and_get_event` — passes `metadata="session started"` | Change to `metadata={"note": "session started"}`, assert the dict is returned |
| `test_log_with_json_string_metadata` — passes `json.dumps(...)` as a string | Change to pass the dict directly; assert the dict is returned |

**Why now:** The production code is already correct. Updating these tests removes the last use of the
old string contract and documents the intended API.

---

## Step 4 — Add a default `metadata` value for calls that omit it

**What:** Verify that `log()` calls without a `metadata` argument still work and return `{}`.

**Test to write first (Red):**
```python
def test_log_without_metadata_defaults_to_empty_dict(log):
    event = log.log("system.startup")
    assert event["metadata"] == {}
```

**Changes to `event_log.py`:**
- Ensure `metadata=None` default in `log()` is treated as `{}` before serialization (already handled
  in Step 1, but this test makes it explicit).

---

## Step 5 — (Optional, low risk) Rename the column in a new migration for future clarity

**What:** This step is purely cosmetic and only needed if the project ever wants the SQLite schema to
communicate intent to readers of the DB directly (e.g., tooling, BI). It is **not required** for
correct behavior after Step 4.

If pursued:
- Add a schema migration that `ALTER TABLE events RENAME COLUMN metadata TO metadata_json` (SQLite 3.25+).
- Update all SQL statements in `event_log.py` to reference `metadata_json`.
- Update tests accordingly.

**Risk:** Column rename touches every SQL string. Only do this if the team values schema legibility
enough to justify the diff.

---

## Execution Order Summary

| Step | Risk | Duration | Tests change |
|---|---|---|---|
| 1 — Serialize dict on write | Low | ~15 min | Add 1 failing test |
| 2 — Deserialize on read | Low | ~15 min | Step 1 test turns green |
| 3 — Update existing string tests | Low | ~10 min | 2 tests updated |
| 4 — Default metadata = {} | Low | ~10 min | Add 1 failing test, then make green |
| 5 — Schema rename (optional) | Medium | ~20 min | Multiple tests updated |

Steps 1–4 can be done in a single session with no downtime risk because the database column type
(`TEXT`) does not change; only the application-layer contract changes.
