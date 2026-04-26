# Implementation Plan: Improve Order Validation

## Overview

Replace the inline validation in `OrderService.create_order()` with a structured validation approach that is reusable and testable, using the existing validator framework in `src/validators/`.

## Current State Analysis

The `OrderService.create_order()` method (`src/services/order_service.py:23-60`) contains ~40 lines of inline validation with hardcoded rules. Each new field requires adding more if/elif blocks.

### Key Discoveries

1. **Inline validation** (`src/services/order_service.py:25-52`): All validation is embedded in create_order
2. **No validation reuse**: Same email validation would need to be duplicated in a future `CustomerService`
3. **Error collection pattern**: Errors are collected in a list and joined — this is good but not formalized
4. **Existing validator framework** (`src/validators/`): `BaseValidator`, `StringValidator`, `NumericValidator`, and `CompositeValidator` already exist and are ready to use

## Desired End State

Order validation uses the existing validator framework declaratively. Each field has a named validator configured with the appropriate rules, making it easy to add new fields or reuse validators across services.

## What We're NOT Doing

- Not changing the Order dataclass or its fields
- Not modifying the list_orders method
- Not adding new validation rules beyond what exists today
- Not changing the public API of create_order (still takes a dict, still raises ValueError)
- Not writing custom validator classes — only configuring the existing ones

## Implementation Phases

### Phase 1: Use Validator Framework in order_validator.py

**Scope**: Move inline validation from create_order into a separate module that uses `StringValidator`, `NumericValidator`, and `CompositeValidator` from `src/validators/`

**Changes**:
- Create `src/services/order_validator.py` that imports from `src.validators`
- Define a `build_order_validator()` function that returns a configured `CompositeValidator` using `CompositeValidator.for_entity()`:
  - `customer_name`: `StringValidator(min_length=2, max_length=100)`
  - `email`: `StringValidator(max_length=254, pattern=r'.+@.+', pattern_description='be a valid email')`
  - `quantity`: `NumericValidator(min_value=1, max_value=10000, integer_only=True)`
  - `unit_price`: `NumericValidator(min_value=0.01, max_value=999999.99)`
  - `notes`: `StringValidator(required=False, max_length=500)`
- Update `create_order` to call `build_order_validator().validate(data)` and raise `ValueError` if `not result.is_valid`

**Note on error messages**: The validator framework produces slightly different messages than the current inline code (e.g., "Quantity must be at least 1.0" vs. "Quantity must be a positive integer"). The existing tests use loose substring matching ("Quantity", "email", "Customer name", "Unit price") so they will continue to pass. Document any message changes in a comment in `order_validator.py`.

**Success Criteria**:
- Automated:
  - `python -m pytest tests/` passes — all existing tests still work
  - `order_validator.py` imports only from `src.validators` — no custom validation logic
- Manual:
  - All validation rules from the original inline code are represented as validator configurations
  - Error messages contain the field name (tests rely on substring match)

### Phase 2: Add Validation Tests

**Scope**: Add comprehensive tests for the configured validators

**Changes**:
- Create `tests/test_order_validator.py` with per-field validation tests using the `build_order_validator()` function directly
- Test boundary conditions (min/max values, empty strings, None) against `ValidationResult.is_valid` and `ValidationResult.errors`
- Test error message content

**Success Criteria**:
- Automated:
  - `python -m pytest tests/` passes — all tests including new ones
  - Each field validator configuration has at least 3 test cases
- Manual:
  - Test names clearly describe what they verify
  - Tests call `build_order_validator()` directly, not through `create_order`

## Success Criteria (Overall)

### Automated Verification
- `python -m pytest tests/` — all tests pass
- No changes to Order dataclass
- create_order public API unchanged
- `order_validator.py` contains zero hand-written validation logic — only framework configuration

### Manual Verification
- Validation rules match original behavior (same field names, same boundary values)
- Validators are individually importable and testable
