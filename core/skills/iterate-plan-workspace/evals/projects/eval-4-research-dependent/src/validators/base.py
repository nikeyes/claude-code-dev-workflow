from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    field_name: str = ""

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            field_name=self.field_name or other.field_name,
        )


class BaseValidator(ABC):
    def __init__(self, field_name: str = "", required: bool = True):
        self.field_name = field_name
        self.required = required

    @abstractmethod
    def validate(self, value) -> ValidationResult:
        pass

    def _check_required(self, value) -> ValidationResult | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            if self.required:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"{self.field_name} is required"],
                    field_name=self.field_name,
                )
            return ValidationResult(is_valid=True, field_name=self.field_name)
        return None
