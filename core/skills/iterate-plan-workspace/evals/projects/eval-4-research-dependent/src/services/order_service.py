from dataclasses import dataclass


@dataclass
class Order:
    customer_name: str
    email: str
    quantity: int
    unit_price: float
    notes: str = ""

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


class OrderService:
    def __init__(self):
        self._orders: list[Order] = []

    def create_order(self, data: dict) -> Order:
        errors = []

        if not data.get("customer_name") or len(data["customer_name"].strip()) < 2:
            errors.append("Customer name must be at least 2 characters")
        if len(data.get("customer_name", "")) > 100:
            errors.append("Customer name must be at most 100 characters")

        email = data.get("email", "")
        if not email or "@" not in email:
            errors.append("Valid email is required")
        if len(email) > 254:
            errors.append("Email must be at most 254 characters")

        qty = data.get("quantity")
        if qty is None:
            errors.append("Quantity is required")
        elif not isinstance(qty, int) or qty < 1:
            errors.append("Quantity must be a positive integer")
        elif qty > 10000:
            errors.append("Quantity must be at most 10000")

        price = data.get("unit_price")
        if price is None:
            errors.append("Unit price is required")
        elif not isinstance(price, (int, float)) or price <= 0:
            errors.append("Unit price must be positive")
        elif price > 999999.99:
            errors.append("Unit price must be at most 999999.99")

        if data.get("notes") and len(data["notes"]) > 500:
            errors.append("Notes must be at most 500 characters")

        if errors:
            raise ValueError("; ".join(errors))

        order = Order(
            customer_name=data["customer_name"].strip(),
            email=email.strip().lower(),
            quantity=qty,
            unit_price=float(price),
            notes=data.get("notes", "").strip(),
        )
        self._orders.append(order)
        return order

    def list_orders(self) -> list[Order]:
        return list(self._orders)
