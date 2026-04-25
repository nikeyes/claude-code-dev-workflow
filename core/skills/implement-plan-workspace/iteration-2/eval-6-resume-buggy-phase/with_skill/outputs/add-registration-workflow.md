# Add Registration Workflow

Build a registration system with validation, single registration, and batch processing.

## Phase 1: Input validators

- [x] `validate_email(email)` validates email format with regex
- [x] `validate_age(age)` ensures age is between 18 and 120 inclusive
- [x] `validate_username(username)` ensures min 3 chars, alphanumeric + underscore only
- [x] All validator tests pass

## Phase 2: Register function

- [x] `register(username, email, age)` validates all inputs then returns registration dict
- [x] Return dict includes: username, email, age, registered_at (ISO timestamp)
- [x] Raises validation errors from the individual validators
- [x] Tests pass for register scenarios

## Phase 3: Batch register function

- [x] `batch_register(users)` processes a list of user dicts
- [x] Returns `{"succeeded": [...], "failed": [...]}`
- [x] Failed entries include the original data plus an "error" key with the message
- [x] Does not stop on first failure — processes all entries
- [x] All tests pass with `make test`
