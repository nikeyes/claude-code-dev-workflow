# Iterate Plan Response

## Task

Update `thoughts/shared/plans/2026-04-20-order-validation.md`: Replace the custom validation functions in Phase 1 with the existing validator framework from `src/validators/` — use `BaseValidator`, `StringValidator`, `NumericValidator`, and `CompositeValidator` instead of writing custom functions.

---

## Step 1: Current Plan

Read the plan at `thoughts/shared/plans/2026-04-20-order-validation.md`. The plan had two phases:
- **Phase 1**: Extract validation into custom functions in a new `src/services/order_validator.py`
- **Phase 2**: Add tests for those custom functions

The change request replaces the custom-function approach in Phase 1 with the existing `src/validators/` framework.

---

## Step 2: Research Findings

Investigated the full validator framework and the order service.

### Validator Framework (`src/validators/`)

**`BaseValidator`** (`src/validators/base.py:19-37`):
- Abstract base with `field_name: str`, `required: bool`
- Abstract method: `validate(value) -> ValidationResult`
- Helper: `_check_required(value) -> ValidationResult | None`
- `ValidationResult` dataclass: `is_valid: bool`, `errors: list[str]`, `field_name: str`, `merge(other)` method

**`StringValidator`** (`src/validators/string_validator.py:6-48`):
- Params: `min_length`, `max_length`, `pattern` (compiled from string), `pattern_description`
- Generates errors like: `"<field_name> must be at least N characters"`, `"<field_name> must <pattern_description>"`

**`NumericValidator`** (`src/validators/numeric_validator.py:4-51`):
- Params: `min_value`, `max_value`, `integer_only`
- Generates errors like: `"<field_name> must be at least N"`, `"<field_name> must be an integer"`

**`CompositeValidator`** (`src/validators/composite_validator.py:4-25`):
- `add(validator)` — fluent builder
- `validate(value)` — merges results from all child validators
- `for_entity(dict[str, BaseValidator])` — static factory that builds a composite from a field-name-to-validator mapping, sets `field_name` on each validator

**`__init__.py`** exports: `BaseValidator`, `ValidationResult`, `StringValidator`, `NumericValidator`, `CompositeValidator`

### Current Order Service (`src/services/order_service.py:24-52`)

Inline validation rules:
| Field | Rule |
|---|---|
| `customer_name` | required, min 2 chars, max 100 chars |
| `email` | required, must contain `@`, max 254 chars |
| `quantity` | required, must be positive integer, max 10000 |
| `unit_price` | required, must be positive (>0), max 999999.99 |
| `notes` | optional, max 500 chars |

### Existing Tests (`tests/test_order_service.py:32-47`)

Tests use `pytest.raises(ValueError, match="Customer name")`, `match="email"`, `match="Quantity"`, `match="Unit price"`. The framework generates lowercase field-name-prefixed messages (e.g., `"customer_name must be at least 2 characters"`), so the `match=` patterns that use capitalized words like `"Customer name"` and `"Unit price"` would break. The plan update addresses this.

### Framework Mapping for Order Fields

| Field | Validator | Key Parameters |
|---|---|---|
| `customer_name` | `StringValidator` | `min_length=2, max_length=100` |
| `email` | `StringValidator` | `max_length=254, pattern=r".+@.+", pattern_description="be a valid email"` |
| `quantity` | `NumericValidator` | `min_value=1, max_value=10000, integer_only=True` |
| `unit_price` | `NumericValidator` | `min_value=0.01, max_value=999999.99` |
| `notes` | `StringValidator` | `required=False, max_length=500` |

---

## Step 3: Understanding and Approach

**Changes requested**: Replace the "create custom validation functions" approach in Phase 1 with instantiating `StringValidator`, `NumericValidator`, and `CompositeValidator` from the existing `src/validators/` framework.

**Key finding that affects the plan**: The framework produces error messages prefixed by the `field_name` argument passed to the validator constructor (e.g., `"customer_name must be at least 2 characters"`). The existing tests match on capitalized English phrases like `"Customer name"` and `"Unit price"`. These tests will need their `match=` patterns updated alongside the implementation change — the plan must call this out explicitly rather than silently breaking tests.

**Plan modifications**:
1. Rewrite Phase 1 "Changes" to use framework classes instead of custom functions, with explicit field-to-validator mapping and the exact constructor arguments needed
2. Add a note about error message alignment and test `match=` pattern updates
3. Update the "What We're NOT Doing" section to state we are not writing custom functions
4. Update success criteria to verify `order_service.py` has no inline if/elif blocks
5. Keep Phase 2 largely intact, but update it to test validator instances rather than custom functions

---

## Step 4: Changes Made

The plan at `thoughts/shared/plans/2026-04-20-order-validation.md` was updated with the following changes:

1. **Overview line** — updated to reference `src/validators/` framework explicitly
2. **Key Discoveries** — added item 4 documenting all four framework classes with file:line references and the key APIs of each
3. **Desired End State** — rewritten to name `StringValidator`, `NumericValidator`, `CompositeValidator` specifically
4. **What We're NOT Doing** — added bullet: "Not writing custom validation functions — the framework already covers all needed cases"
5. **Phase 1 Changes** — replaced "create custom functions" with:
   - Create `src/services/order_validator.py` using `CompositeValidator.for_entity()` with specific validator constructors per field (with exact parameters)
   - Update `create_order` to use the composite validator result
   - Added explicit note about error message format change and required test `match=` pattern updates
   - Added the import statement needed
6. **Phase 1 Success Criteria** — added criteria: no inline if/elif blocks in order_service.py; order_validator.py imports only from src/validators/
7. **Phase 2** — updated to test validator instances from `src/services/order_validator.py` and to test composite error collection
8. **Overall Success Criteria** — added: order_service.py uses CompositeValidator, not custom if/elif blocks; validator classes are reusable

---

## Result

Updated plan saved to:
- `thoughts/shared/plans/2026-04-20-order-validation.md` (in project)
- `outputs/updated-plan.md` (copy for eval output)

Next steps:
- Review the updated plan
- Use `/stepwise-core:implement-plan thoughts/shared/plans/2026-04-20-order-validation.md` to execute it
- Or use `/stepwise-core:iterate-plan thoughts/shared/plans/2026-04-20-order-validation.md [more changes]` for further refinement

Tip: Use `/clear` to free up context before starting implementation.
