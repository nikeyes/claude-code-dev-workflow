"""Price calculator for an e-commerce platform."""


def calculate_discount(price: float, discount_percent: float) -> float:
    """Apply a percentage discount to a price."""
    return round(price - (price * discount_percent / 100), 2)


def calculate_total(items: list[dict], tax_rate: float = 0.21) -> dict:
    """Calculate total for a list of items with tax.

    Each item: {"name": str, "price": float, "quantity": int, "discount": float}
    """
    subtotal = 0
    for item in items:
        item_price = calculate_discount(item["price"], item.get("discount", 0))
        subtotal += item_price * item["quantity"]

    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    return {
        "subtotal": round(subtotal, 2),
        "tax": tax,
        "total": total,
        "item_count": sum(i["quantity"] for i in items),
    }


def format_price(amount: float, currency: str = "EUR") -> str:
    """Format a price for display."""
    symbols = {"EUR": "€", "USD": "$", "GBP": "£"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"


def apply_coupon(total: float, coupon: dict) -> float:
    """Apply a coupon to a total.

    coupon: {"type": "percent" | "fixed", "value": float}
    """
    if coupon["type"] == "percent":
        return round(total - (total * coupon["value"] / 100), 2)
    elif coupon["type"] == "fixed":
        return round(total - coupon["value"], 2)
    return total


def split_payment(total: float, parts: int) -> list[float]:
    """Split a total into equal payment parts."""
    per_part = round(total / parts, 2)
    result = [per_part] * parts
    diff = round(total - sum(result), 2)
    result[-1] = round(result[-1] + diff, 2)
    return result
