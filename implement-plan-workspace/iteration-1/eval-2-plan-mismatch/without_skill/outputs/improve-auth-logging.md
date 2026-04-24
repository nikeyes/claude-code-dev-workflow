# Improve Authentication Logging

## Overview
Add structured logging to the authentication flow so we can track login attempts for security auditing.

## Phase 1: Add logging to authenticate method

### Changes Required:

#### 1. auth.py
**File**: `auth.py`
**Changes**: Modify the `UserService.authenticate()` method to add logging:
- Log `INFO` with message `"Login successful for user: {username}"` when credentials are valid
- Log `WARNING` with message `"Failed login attempt for user: {username}"` when password is wrong
- Log `WARNING` with message `"Login attempt for unknown user: {username}"` when username doesn't exist

The method currently has no logging. Add `logger.info()` and `logger.warning()` calls at the appropriate points in the `authenticate()` method logic.

### Success Criteria:
- [ ] `UserService.authenticate()` logs INFO on successful login
- [ ] `UserService.authenticate()` logs WARNING on failed login
- [ ] `UserService.authenticate()` logs WARNING for unknown user
- [ ] All tests pass with `make test`
