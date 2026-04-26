import re

from .base import BaseValidator, ValidationResult


class StringValidator(BaseValidator):
    def __init__(
        self,
        field_name: str = "",
        required: bool = True,
        min_length: int = 0,
        max_length: int | None = None,
        pattern: str | None = None,
        pattern_description: str = "",
    ):
        super().__init__(field_name, required)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.pattern_description = pattern_description

    def validate(self, value) -> ValidationResult:
        required_check = self._check_required(value)
        if required_check is not None:
            return required_check

        errors = []
        str_value = str(value)

        if len(str_value) < self.min_length:
            errors.append(
                f"{self.field_name} must be at least {self.min_length} characters"
            )

        if self.max_length and len(str_value) > self.max_length:
            errors.append(
                f"{self.field_name} must be at most {self.max_length} characters"
            )

        if self.pattern and not self.pattern.match(str_value):
            desc = self.pattern_description or f"match pattern {self.pattern.pattern}"
            errors.append(f"{self.field_name} must {desc}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            field_name=self.field_name,
        )
