from .base import BaseValidator, ValidationResult


class NumericValidator(BaseValidator):
    def __init__(
        self,
        field_name: str = "",
        required: bool = True,
        min_value: float | None = None,
        max_value: float | None = None,
        integer_only: bool = False,
    ):
        super().__init__(field_name, required)
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only

    def validate(self, value) -> ValidationResult:
        required_check = self._check_required(value)
        if required_check is not None:
            return required_check

        errors = []

        try:
            num_value = float(value)
        except (TypeError, ValueError):
            return ValidationResult(
                is_valid=False,
                errors=[f"{self.field_name} must be a number"],
                field_name=self.field_name,
            )

        if self.integer_only and num_value != int(num_value):
            errors.append(f"{self.field_name} must be an integer")

        if self.min_value is not None and num_value < self.min_value:
            errors.append(
                f"{self.field_name} must be at least {self.min_value}"
            )

        if self.max_value is not None and num_value > self.max_value:
            errors.append(
                f"{self.field_name} must be at most {self.max_value}"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            field_name=self.field_name,
        )
