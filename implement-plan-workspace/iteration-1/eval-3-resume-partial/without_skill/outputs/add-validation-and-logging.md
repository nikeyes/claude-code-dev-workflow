# Add Validation and Logging

## Overview
Improve the registration flow with proper input validation (Phase 1, already done) and structured error logging (Phase 2, pending).

## Phase 1: Add input validation

### Changes Required:

#### 1. validator.js
**File**: `validator.js`
**Changes**: Create validation functions for email and age with proper error messages.

#### 2. app.js
**File**: `app.js`
**Changes**: Use validator functions in processRegistration.

### Success Criteria:
- [x] `validateEmail` function exists and validates email format
- [x] `validateAge` function exists and validates age range
- [x] `processRegistration` calls both validators
- [x] First 3 tests pass with `make test`

## Phase 2: Add error logging

### Changes Required:

#### 1. app.js
**File**: `app.js`
**Changes**: Add structured logging to `processRegistration`:
- On validation failure: `console.error('Validation failed', { field: '<fieldname>', error: '<message>' })` before re-throwing
- On success: `console.info('Registration successful', { email: data.email })` before returning

Wrap each validation call in a try/catch to log before re-throwing. The logging should identify which field failed.

### Success Criteria:
- [x] Validation errors are logged with `console.error` including field name
- [x] Successful registrations are logged with `console.info`
- [x] All 5 tests pass with `make test`
