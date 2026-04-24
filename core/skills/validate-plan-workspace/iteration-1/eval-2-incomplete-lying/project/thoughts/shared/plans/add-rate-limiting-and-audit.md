# Plan: Add Rate Limiting and Audit Logging

## Overview
Protect the authentication system with rate limiting and add audit logging for security compliance.

## Phase 1: Rate Limiting
- [x] Add `rate_limiter.py` with `RateLimiter` class
- [x] `RateLimiter` tracks login attempts per username
- [x] Block login after 5 failed attempts within 60 seconds
- [x] Add `is_blocked(username)` method
- [x] Add `record_attempt(username, success)` method that resets counter on success
- [x] Add tests for rate limiting in `test_rate_limiter.py`

## Phase 2: Audit Logging
- [x] Add `audit_logger.py` with `AuditLogger` class
- [x] `AuditLogger` writes structured JSON logs to a file
- [x] Log all login attempts (success and failure) with timestamp, username, IP, and result
- [x] Add `log_event(event_type, username, ip, details)` method
- [x] Add `get_events(username=None, event_type=None)` query method
- [x] Add tests for audit logging in `test_audit_logger.py`

## Success Criteria

### Automated Verification
```bash
make test
```
- All tests pass for both rate limiting and audit logging
- `RateLimiter` blocks after 5 failures
- `AuditLogger` produces valid JSON entries
- Events can be filtered by username and event_type

### Manual Verification
- [ ] Rate limiter integrates cleanly with auth module
- [ ] Audit logs are human-readable
- [ ] No performance impact on login flow
