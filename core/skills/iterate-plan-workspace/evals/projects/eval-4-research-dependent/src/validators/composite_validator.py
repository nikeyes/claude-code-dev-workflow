from .base import BaseValidator, ValidationResult


class CompositeValidator(BaseValidator):
    def __init__(self, field_name: str = "", validators: list[BaseValidator] | None = None):
        super().__init__(field_name, required=False)
        self.validators = validators or []

    def add(self, validator: BaseValidator) -> "CompositeValidator":
        self.validators.append(validator)
        return self

    def validate(self, value) -> ValidationResult:
        result = ValidationResult(is_valid=True, field_name=self.field_name)
        for validator in self.validators:
            result = result.merge(validator.validate(value))
        return result

    @staticmethod
    def for_entity(field_validators: dict[str, BaseValidator]) -> "CompositeValidator":
        composite = CompositeValidator(field_name="entity")
        for field_name, validator in field_validators.items():
            validator.field_name = field_name
            composite.add(validator)
        return composite
