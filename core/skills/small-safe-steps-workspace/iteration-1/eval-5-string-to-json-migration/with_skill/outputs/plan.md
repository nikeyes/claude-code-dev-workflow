# Small Safe Steps Plan: Migrate event_log.metadata from String to JSON Object

## Goal

Migrate the `metadata` column in the `events` table from storing plain strings to storing structured JSON objects. Callers already stuff JSON-encoded dictionaries into the field informally; the goal is to enforce this as the canonical format, parse metadata automatically on read, and preserve backward compatibility for callers that still pass plain strings.

## Why This Is a Risky Change

This is a **data type / format change (String → JSON Object)** — a classic risky change:
- Existing rows have mixed data: some plain strings (`"session started"`), some JSON-encoded strings (`'{"ip":"1.2.3.4"}'`)
- Changing the `log()` signature or return shape breaks existing callers without warning
- The `metadata` column is TEXT in SQLite — the DB type stays the same, but the application contract changes
- Tests currently assert `event["metadata"] == "session started"` (a plain string), so the deserialized form will break existing tests unless handled carefully

**Pattern to apply: Expand-Contract** (data format change variant)

---

## Phase 1: EXPAND — Support Both Formats Simultaneously

Goal: System reads and writes correctly whether metadata is a plain string or a JSON object. No caller is broken yet.

### Step 1.1 — Learning: Audit all callers of `log()` and usages of `event["metadata"]` (max 1h)

**Type:** Learning step (time-boxed investigation)

- Search the codebase for all calls to `.log(` with a `metadata=` argument
- Search for all reads of `event["metadata"]` or `row["metadata"]`
- Categorize each call site:
  - Passes a plain string (e.g. `"session started"`)
  - Passes a JSON-encoded string (e.g. `json.dumps({...})`)
  - Reads metadata and treats it as a string
  - Reads metadata and does `json.loads()` on it
- Document findings (a short list is enough)
- Output: Decision on whether `metadata` parameter should accept `str | dict` or `dict` only

**Verification:** List of all callers + readers is complete. No surprises in how metadata is used.

**Reversibility:** This is read-only research — trivially reversible.

---

### Step 1.2 — Add internal `_serialize_metadata` and `_deserialize_metadata` helpers (1h)

**Type:** Earning step

In `event_log.py`, add two private helpers that encode/decode metadata:

```python
def _serialize_metadata(self, metadata) -> str:
    """Accept str or dict; always store as JSON string."""
    if isinstance(metadata, dict):
        return json.dumps(metadata)
    if metadata is None:
        return json.dumps({})
    # Legacy plain string: wrap in a dict to keep the column consistent
    # during the transition period
    return metadata  # kept as-is during EXPAND phase (dual format)

def _deserialize_metadata(self, raw: str):
    """Return parsed dict if valid JSON, else return raw string (legacy)."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw  # legacy plain string — returned unchanged for now
```

- Deploy / commit
- All existing tests still pass (no behavior change yet — callers still pass strings, helpers are not yet wired in)

**Verification:** `pytest` passes with no changes to test assertions.

**Reversibility:** Delete the two functions — no other code calls them yet.

---

### Step 1.3 — Wire `_serialize_metadata` into `log()` (1h)

**Type:** Earning step

Update `log()` to call `_serialize_metadata` before inserting:

```python
def log(self, event_type: str, user_id: Optional[int] = None, metadata=None) -> dict:
    serialized = self._serialize_metadata(metadata if metadata is not None else "")
    cursor = self._conn.execute(
        "INSERT INTO events (event_type, user_id, metadata) VALUES (?, ?, ?)",
        (event_type, user_id, serialized),
    )
    self._conn.commit()
    return self.get_event(cursor.lastrowid)
```

- The `metadata` parameter type is widened from `str` to `str | dict | None`
- During EXPAND, `_serialize_metadata` still stores plain strings unchanged (legacy path)
- `json.dumps({...})` strings passed by callers are stored as-is (they are valid JSON and will round-trip through `_deserialize_metadata` correctly)

**Verification:** All existing tests pass. Manually verify a dict can be passed: `log.log("test", metadata={"key": "val"})` stores `'{"key": "val"}'`.

**Reversibility:** Revert the change to `log()`. Only new events are affected; existing rows are unchanged.

---

### Step 1.4 — Wire `_deserialize_metadata` into all read methods (1h)

**Type:** Earning step

Add a private helper `_row_to_dict` that applies deserialization to `metadata` when converting a row:

```python
def _row_to_dict(self, row) -> dict:
    d = dict(row)
    d["metadata"] = self._deserialize_metadata(d.get("metadata", ""))
    return d
```

Update `get_event`, `get_events_by_type`, `get_events_by_user` to call `_row_to_dict` instead of `dict(row)`.

- Rows with plain-string metadata now return the plain string (legacy, unchanged)
- Rows with JSON-encoded metadata now return a parsed dict

**Verification:** Write a new test (do not change existing tests):

```python
def test_log_with_dict_metadata_is_deserialized(log):
    event = log.log("user.login", user_id=1, metadata={"ip": "1.2.3.4", "browser": "Firefox"})
    assert event["metadata"] == {"ip": "1.2.3.4", "browser": "Firefox"}
```

Existing tests still pass (they pass plain strings — `_deserialize_metadata` returns them unchanged). New test passes.

**Reversibility:** Revert `_row_to_dict` usage in the three read methods. No data loss.

---

### Step 1.5 — Backfill: migrate existing plain-string rows to JSON objects (1h)

**Type:** Earning step

Add a migration method `migrate_legacy_metadata()`:

```python
def migrate_legacy_metadata(self):
    """One-time migration: wrap any non-JSON metadata values in {\"message\": ...}."""
    rows = self._conn.execute("SELECT id, metadata FROM events").fetchall()
    updated = 0
    for row in rows:
        raw = row["metadata"] or ""
        try:
            json.loads(raw)  # already valid JSON — skip
        except (json.JSONDecodeError, TypeError):
            structured = json.dumps({"message": raw})
            self._conn.execute(
                "UPDATE events SET metadata = ? WHERE id = ?",
                (structured, row["id"]),
            )
            updated += 1
    self._conn.commit()
    return updated
```

Run this migration once against the production database (or as part of app startup, guarded by a flag).

**Verification:** After running the migration, `SELECT metadata FROM events WHERE json_valid(metadata) = 0` returns 0 rows (SQLite 3.38+). All rows now hold valid JSON.

**Reversibility:** Restore from backup or re-run inverse migration (`json_extract(metadata, '$.message')` to recover plain strings). Because the migration wraps values predictably, it is recoverable.

---

## Phase 2: MIGRATE — Switch All Callers to Pass Dicts, Update Existing Tests

Goal: All callers pass `dict` metadata; all readers expect `dict` metadata. Dual-format support remains active as a safety net.

### Step 2.1 — Update existing tests to pass dicts and assert dict responses (1h)

**Type:** Earning step

Update `test_event_log.py`:

- `test_log_and_get_event`: change `metadata="session started"` to `metadata={"message": "session started"}` and assert `event["metadata"] == {"message": "session started"}`
- `test_log_with_json_string_metadata`: replace the `json.dumps` call with a plain dict: `metadata={"ip": "1.2.3.4", "browser": "Firefox"}` and assert `event["metadata"] == {"ip": "1.2.3.4", "browser": "Firefox"}`

All other tests remain unchanged (they don't pass metadata).

**Verification:** `pytest` passes with 0 failures.

**Reversibility:** Revert test file changes.

---

### Step 2.2 — Update all production callers to pass dicts instead of strings (1h per call-site cluster)

**Type:** Earning step (one step per cluster of call sites found in Step 1.1)

For each caller that passes a plain string:
- Replace `metadata="some string"` with `metadata={"message": "some string"}`
- For callers already doing `json.dumps({...})`, replace with the raw dict

Deploy and monitor. Dual-format support in `_deserialize_metadata` is still active — no caller is at risk even if one is missed.

**Verification:** Search codebase — zero remaining calls pass a plain string to `metadata=`. Logs confirm dict metadata in all new event rows.

**Reversibility:** Revert individual caller changes. Safety net still in place.

---

### Step 2.3 — Monitor production for 1-2 weeks: confirm zero plain-string metadata rows (passive)

**Type:** Learning step (monitoring)

- Run a query: `SELECT COUNT(*) FROM events WHERE json_valid(metadata) = 0`
- Should remain 0 after the backfill and caller updates
- Review application logs for any `json.JSONDecodeError` in `_deserialize_metadata`

**Verification:** Zero non-JSON rows for at least 5-7 days. No deserialization errors in logs.

---

## Phase 3: CONTRACT — Remove Legacy Support, Enforce Dict-Only

Goal: Remove the backward-compatibility code paths. `metadata` is now exclusively a JSON object.

### Step 3.1 — Tighten `_serialize_metadata` to reject plain strings (1h)

**Type:** Earning step

Update `_serialize_metadata` to enforce dict-only input:

```python
def _serialize_metadata(self, metadata) -> str:
    if metadata is None:
        return json.dumps({})
    if isinstance(metadata, str):
        raise TypeError(
            "metadata must be a dict, not a string. "
            "Pass a dict, e.g. metadata={'message': 'your text'}."
        )
    return json.dumps(metadata)
```

Update `log()` default: `metadata: Optional[dict] = None`.

**Verification:** `pytest` passes. Any caller still passing a string will raise `TypeError` immediately — easily discoverable.

**Reversibility:** Revert `_serialize_metadata`. No data change.

---

### Step 3.2 — Tighten `_deserialize_metadata` to remove legacy plain-string fallback (30min)

**Type:** Earning step

```python
def _deserialize_metadata(self, raw: str) -> dict:
    if not raw:
        return {}
    return json.loads(raw)  # Will raise if data is somehow not JSON
```

Remove the `except (json.JSONDecodeError, TypeError): return raw` branch.

**Verification:** `pytest` passes. If there were any missed plain-string rows, this would raise in tests — good signal.

**Reversibility:** Revert the method.

---

### Step 3.3 — Clean up: remove `migrate_legacy_metadata` method and related comments (30min)

**Type:** Earning step

- Remove `migrate_legacy_metadata()` from `EventLog`
- Remove any inline comments referencing "legacy" or "transition"
- Remove any compatibility notes in docstrings

**Verification:** `pytest` passes. Code is clean — no mention of legacy string format.

**Reversibility:** Trivial revert.

---

## Summary

| Phase | Steps | Duration | Outcome |
|-------|-------|----------|---------|
| Expand | 1.1 – 1.5 | 4-5h over 1 week | Both string and dict metadata work; new rows store JSON |
| Migrate | 2.1 – 2.3 | 2-3h + 1-2 weeks monitoring | All callers pass dicts; tests updated; production clean |
| Contract | 3.1 – 3.3 | ~2h | Legacy code removed; dict-only enforced |

**Total active work:** ~9-10 hours  
**Total calendar time:** 2-4 weeks (dominated by the monitoring window in Phase 2)

---

## Self-Check

- [x] Every step takes 1-3 hours
- [x] Every step is deployable / commits a verifiable artifact
- [x] Every step is reversible
- [x] Risky change uses expand-contract (3 phases: Expand -> Migrate -> Contract)
- [x] Learning step (1.1 audit, 2.3 monitoring) separated from earning steps
- [x] Dual-format support active during entire Migrate phase
- [x] Contract phase starts only after zero plain-string rows confirmed for 1-2 weeks
- [x] Each phase is independently valuable
