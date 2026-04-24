# Plan: Add Power and Modulo Operations

## Overview
Add `power` and `modulo` mathematical operations to the calculator module, with full test coverage and error handling.

## Phase 1: Power Operation
- [x] Add `power(base, exponent)` function to `calculator.py`
- [x] Handle negative exponents (return float)
- [x] Add tests for power in `test_calculator.py`

## Phase 2: Modulo Operation
- [x] Add `modulo(a, b)` function to `calculator.py`
- [x] Raise `ValueError` when divisor is zero
- [x] Add tests for modulo in `test_calculator.py`

## Success Criteria

### Automated Verification
```bash
make test
```
- All tests pass including new power and modulo tests
- `power(2, 3)` returns `8`
- `power(2, -1)` returns `0.5`
- `modulo(10, 3)` returns `1`
- `modulo(10, 0)` raises `ValueError`

### Manual Verification
- [ ] Code follows existing patterns (similar to add/subtract)
- [ ] No regressions in existing operations
