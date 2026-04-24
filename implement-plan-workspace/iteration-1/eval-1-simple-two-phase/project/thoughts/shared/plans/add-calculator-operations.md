# Add Calculator Operations

## Overview
Extend the calculator module with `multiply` and `divide` functions. Tests already exist and are currently failing.

## Phase 1: Add multiply function

### Changes Required:

#### 1. calculator.py
**File**: `calculator.py`
**Changes**: Add a `multiply` function that takes two arguments and returns their product.

### Success Criteria:
- [x] `multiply` function exists in `calculator.py`
- [x] `test_multiply` passes when running `make test`

## Phase 2: Add divide function with error handling

### Changes Required:

#### 1. calculator.py
**File**: `calculator.py`
**Changes**: Add a `divide` function that takes two arguments and returns the division result as a float. Raise `ValueError("Cannot divide by zero")` when the divisor is zero.

### Success Criteria:
- [x] `divide` function exists in `calculator.py`
- [x] `test_divide` passes when running `make test`
- [x] `test_divide_by_zero` passes when running `make test`
