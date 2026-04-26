# Implementation Plan: Improve Order Validation

## Overview

Replace the inline validation in `OrderService.create_order()` with a structured validation approach using the existing validator framework in `src/validators/`.

## Current State Analysis

The `OrderService.create_order()` method (`src/services/order_service.py:23-60`) contains ~40 lines of inline validation with hardcoded rules. Each new field requires adding more if/elif blocks.

### Key Discoveries

1. **Inline validation** (`src/services/order_service.py:25-52`): All validation is embedded in create_order
2. **No validation reuse**: Same email validation would need to be duplicated in a future `CustomerService`
3. **Error collection pattern**: Errors are collected in a list and joined — this is good but not formalized
4. **Existing validator framework** (`src/validators/`): A full validator hierarchy already exists and is unused by order validation:
   - `BaseValidator` (`src/validators/base.py:19-37`): Abstract base with `field_name`, `required`, and `_check_required()` helper. Returns `ValidationResult` (has `is_valid`, `errors`, `field_name`, and `merge()` method)
   - `StringValidator` (`src/validators/string_validator.py:6-48`): Supports `min_length`, `max_length`, `pattern` (compiled regex), `pattern_description`
   - `NumericValidator` (`src/validators/numeric_validator.py:4-51`): Supports `min_value`, `max_value`, `integer_only`
   - `CompositeValidator` (`src/validators/composite_validator.py:4-25`): Merges multiple validators; `for_entity(dict[str, BaseValidator])` static method builds an entity-level composite from a mapping of field names to validators

## Desired End State

Order validation uses the existing `src/validators/` framework — `StringValidator`, `NumericValidator`, and `CompositeValidator` — so adding new fields or reusing validators in other services requires no custom code.

## What We're NOT Doing

- Not changing the Order dataclass or its fields
- Not modifying the list_orders method
- Not adding new validation rules beyond what exists today
- Not changing the public API of create_order (still takes a dict, still raises ValueError)
- Not writing custom validation functions — the framework already covers all needed cases

## Implementation Phases

### Phase 1: Replace Inline Validation with Framework Validators

**Scope**: Remove the custom inline validation in `create_order` and replace it with validator instances from `src/validators/`

**Changes**:
- Create `src/services/order_validator.py` that builds a `CompositeValidator` using `CompositeValidator.for_entity()` with these field validators:
  - `customer_name`: `StringValidator(field_name="customer_name", min_length=2, max_length=100)`
  - `email`: `StringValidator(field_name="email", max_length=254, pattern=r".+@.+", pattern_description="be a valid email")`
  - `quantity`: `NumericValidator(field_name="quantity", min_value=1, max_value=10000, integer_only=True)`
  - `unit_price`: `NumericValidator(field_name="unit_price", min_value=0.01, max_value=999999.99)`
  - `notes`: `StringValidator(field_name="notes", required=False, max_length=500)`
- Update `create_order` (`src/services/order_service.py:21`) to call the composite validator and raise `ValueError` from `result.errors` if `result.is_valid` is False
- **Error message alignment**: The framework generates messages like `"customer_name must be at least 2 characters"` and `"email must be a valid email"`. Update the existing tests in `tests/test_order_service.py` so the `match=` patterns align with the new framework error messages (e.g., `match="customer_name"` instead of `match="Customer name"`)

**Imports to add** in `src/services/order_validator.py`:
```python
from src.validators import StringValidator, NumericValidator, CompositeValidator
```

**Success Criteria**:
- Automated:
  - `python -m pytest tests/` passes — all existing tests still work (with updated match patterns)
  - `src/services/order_service.py` contains no inline if/elif validation blocks
  - `src/services/order_validator.py` exists and imports only from `src/validators/`
- Manual:
  - Error messages clearly identify the field and the constraint that was violated

### Phase 2: Add Validation Tests

**Scope**: Add comprehensive tests for the validator configuration used for orders

**Changes**:
- Create `tests/test_order_validator.py` with per-field validation tests
- Test boundary conditions (min/max values, empty strings, None)
- Test each validator instance directly (import from `src/services/order_validator.py`)
- Test `CompositeValidator.for_entity` collects errors from all failing fields in a single pass

**Success Criteria**:
- Automated:
  - `python -m pytest tests/` passes — all tests including new ones
  - Each field validator has at least 3 test cases (valid, below-min, above-max or invalid format)
- Manual:
  - Test names clearly describe what they verify

## Success Criteria (Overall)

### Automated Verification
- `python -m pytest tests/` — all tests pass
- No changes to Order dataclass
- create_order public API unchanged
- `src/services/order_service.py` uses `CompositeValidator` from `src/validators/`, not custom if/elif blocks

### Manual Verification
- Validation errors clearly identify the failing field
- Validator classes are reusable — e.g., `StringValidator` for email could be imported by a future `CustomerService`
