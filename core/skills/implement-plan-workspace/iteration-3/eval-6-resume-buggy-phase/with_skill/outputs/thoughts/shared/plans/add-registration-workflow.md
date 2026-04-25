# Add Registration Workflow

Build a registration system with validation, single registration, and batch processing.

## Phase 1: Input validators

- [x] `validate_email(email)` validates email format with regex
- [x] `validate_age(age)` ensures age is between 18 and 120 inclusive
- [x] `validate_username(username)` ensures min 3 chars, alphanumeric + underscore only
- [x] All validator tests pass

## Phase 2: Register function

- [ ] `register(username, email, age)` validates all inputs then returns registration dict
- [ ] Return dict includes: username, email, age, registered_at (ISO timestamp)
- [ ] Raises validation errors from the individual validators
- [ ] Tests pass for register scenarios

## Phase 3: Batch register function

- [ ] `batch_register(users)` processes a list of user dicts
- [ ] Returns `{"succeeded": [...], "failed": [...]}`
- [ ] Failed entries include the original data plus an "error" key with the message
- [ ] Does not stop on first failure — processes all entries
- [ ] All tests pass with `make test`
