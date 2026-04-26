# Transcript: Test Desiderata Analysis — test_notification_service.py

**Date:** 2026-04-26
**Skill:** stepwise-core:test-desiderata
**File analyzed:** `core/skills/test-desiderata-workspace/evals/files/test_notification_service.py`

---

## Step 1: Read the Skill File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata/SKILL.md`.

Confirmed the analysis workflow:
1. Read the test code
2. Evaluate against the 12 Test Desiderata properties
3. Identify tradeoffs
4. Prioritize improvements
5. Suggest specific changes

Also confirmed the output format:
```
Issue: <test name> violates <property> property
Location: Line <n> - <description>
Impact: <why it matters>
Fix: <concrete fix>
Tradeoff: <acknowledged conflicts>
```

---

## Step 2: Read the Test File

Read `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/test-desiderata-workspace/evals/files/test_notification_service.py`.

**Structure observed:**
- 83 lines total
- One production class: `NotificationService` (lines 14–47)
  - `__init__(self, smtp_client)`: stores smtp client, initializes `_sent_count = 0` and `_last_sent_at = None`
  - `send_welcome_email(to, name) -> bool`: calls smtp.send, increments counter, sets timestamp, returns True or False on exception
  - `send_password_reset(to, token) -> bool`: same pattern
  - `get_stats() -> dict`: returns `{"sent": _sent_count, "last_sent_at": _last_sent_at}`
- One test class: `TestNotificationService` (lines 50–83)
  - `test_send_welcome_email` (lines 51–61)
  - `test_send_password_reset` (lines 63–71)
  - `test_get_stats_after_two_sends` (lines 73–82)

**Embedded hints in file docstring (lines 1–8):**
The file docstring explicitly calls out four planted violations:
- Deterministic: `datetime.now()` used directly in assertion
- Predictive: no tests for SMTP failure path
- Inspiring: `test_send_welcome_email` never verifies recipient is correct
- Structure-insensitive: assertion on `_sent_count` (private attribute)

---

## Step 3: Evaluate Against Each Property

### 3.1 Isolated

Each test method creates a new `MagicMock()` and a fresh `NotificationService(smtp)`. No shared class-level state. No database, file system, or network. Tests are fully independent.

**Verdict: PASS**

### 3.2 Composable

Three tests, three distinct concerns. Stats test reuses operations from the other two tests intentionally to verify accumulation. No monolithic test mixing unrelated concerns.

**Verdict: PASS**

### 3.3 Deterministic

Line 60: `assert service._last_sent_at <= datetime.now()`

This calls `datetime.now()` at assertion evaluation time. Issues:
1. This is always `True` for any past timestamp — it is a vacuous assertion that can never fail regardless of what `_last_sent_at` was set to.
2. If the system clock has low resolution, a race between `_last_sent_at` assignment and the assertion-time `now()` could theoretically make them equal or diverge in edge cases.
3. The assertion provides no confidence that the timestamp is accurate — it would pass even if `_last_sent_at` were set to `datetime(1970, 1, 1)`.

**Verdict: VIOLATION (Medium severity)**

Root cause: No time injection or clock freezing. Fix: use `freezegun` or inject a clock.

### 3.4 Fast

All SMTP calls are mocked via `MagicMock()`. No I/O, no network, no sleeps. Expected runtime: milliseconds.

**Verdict: PASS**

### 3.5 Writable

Setup is minimal (3 lines: mock, service, call). No complex fixtures, no conftest, no test framework configuration beyond imports.

**Verdict: PASS**

### 3.6 Readable

- Test names clearly describe the scenario being tested.
- Arrange-Act-Assert structure is present and clear.
- `test_get_stats_after_two_sends` is particularly well-named.
- The inline violation comments are evaluation artifacts, not real test comments.

**Verdict: PASS**

### 3.7 Behavioral

- `test_send_password_reset`: checks return value AND verifies smtp.send was called AND checks token in body. Good behavioral coverage.
- `test_get_stats_after_two_sends`: checks stats through public API. Behavioral.
- `test_send_welcome_email`: checks return value only. Does not verify smtp.send was called with correct arguments. Partial behavioral coverage.

**Verdict: PARTIAL PASS** — overlaps with Inspiring violation.

### 3.8 Structure-insensitive

Line 58: `assert service._sent_count == 1`

`_sent_count` is a private attribute (Python underscore convention). This assertion couples the test to the internal implementation detail of how the count is stored. If a developer renames `_sent_count` to `_emails_sent`, extracts it to a separate `EmailCounter` object, or changes the storage mechanism, this test breaks — even though `get_stats()["sent"]` would still return `1`.

The public `get_stats()` method already exposes this information. There is no reason to reach into private state.

**Verdict: VIOLATION (High severity)**

Fix: `assert service.get_stats()["sent"] == 1`

### 3.9 Automated

No `print()` statements requiring human inspection. No interactive prompts. No manual setup steps. Tests use standard pytest patterns.

**Verdict: PASS**

### 3.10 Specific

Each test covers one primary scenario. Assertion failures in `test_send_welcome_email` would point to that one method. Minor concern: three assertions in one test mean the exact failure requires reading the stack trace line, but this is minor.

**Verdict: PASS**

### 3.11 Predictive

`send_welcome_email` contains:
```python
try:
    self._smtp.send(...)
    self._sent_count += 1
    self._last_sent_at = datetime.now()
    return True
except Exception:
    return False
```

There is no test that:
- Calls `smtp.send.side_effect = Exception(...)` and verifies `send_welcome_email` returns `False`
- Verifies `_sent_count` is not incremented on failure
- Tests the same failure path for `send_password_reset`

This exception-handling code is production logic. Without tests, any refactoring that accidentally removes it, inverts the boolean, or introduces a new exception type would go undetected.

**Verdict: VIOLATION (High severity)**

Fix: Add `smtp.send.side_effect = Exception(...)` tests for both methods.

### 3.12 Inspiring

`test_send_welcome_email` assertions:
1. `assert result is True` — verifies the return value
2. `assert service._sent_count == 1` — verifies internal counter (private)
3. `assert service._last_sent_at <= datetime.now()` — vacuous timestamp check

Missing:
- `smtp.send.assert_called_once()` — was smtp even called?
- Verification that `to="user@example.com"` was passed
- Verification that `subject="Welcome!"` was passed
- Verification that `name="Alice"` appears in the body

A developer could introduce a bug that sends the email to `admin@company.com` instead of the provided address, and this test would still pass. A developer could remove the smtp.send call entirely and return True unconditionally, and this test would still pass (except the test doesn't check smtp was called at all).

Compare with `test_send_password_reset` which properly checks `smtp.send.assert_called_once()` and verifies the token in the body.

**Verdict: VIOLATION (Medium severity)**

---

## Step 4: Identify Tradeoffs

| Tradeoff | Analysis |
|----------|----------|
| Predictive vs. Fast | Adding error-path tests adds test count but not execution time — all mocked. No real conflict. |
| Inspiring vs. Structure-insensitive | Asserting on SMTP call arguments couples to the message format (external interface), not internal state. This is acceptable — external interface is the right level of coupling. |
| Deterministic vs. Writable | `freezegun` adds a dependency and one decorator. Minor friction, but worth it for meaningful assertions. |

---

## Step 5: Prioritize Improvements

1. **Structure-insensitive (High):** Replace `service._sent_count` with `service.get_stats()["sent"]`. Zero-effort, zero-risk, zero tradeoffs.

2. **Predictive (High):** Add 3 tests for SMTP failure paths. Easy to write, fast to run, high value.

3. **Inspiring (Medium):** Add `smtp.send.assert_called_once_with(...)` to `test_send_welcome_email`. Straightforward, closes the behavioral gap.

4. **Deterministic (Medium):** Use `freezegun` to freeze time and assert exact timestamp value. Requires adding a dependency but makes the assertion meaningful.

---

## Output

Analysis saved to:
`core/skills/test-desiderata-workspace/iteration-1/eval-4/with_skill/outputs/analysis.md`

Transcript saved to:
`core/skills/test-desiderata-workspace/iteration-1/eval-4/with_skill/outputs/transcript.md`
