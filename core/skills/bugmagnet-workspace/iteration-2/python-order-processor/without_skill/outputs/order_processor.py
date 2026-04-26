"""Order processing pipeline for an e-commerce platform.

Handles validation, inventory management, pricing with discounts,
tax calculation, and shipping cost determination.
"""

from dataclasses import dataclass, field
from enum import Enum


class DiscountType(Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


@dataclass
class OrderItem:
    product_id: str
    name: str
    unit_price: float
    quantity: int
    discount_type: DiscountType | None = None
    discount_value: float = 0.0


@dataclass
class Discount:
    code: str
    discount_type: DiscountType
    value: float
    minimum_order: float = 0.0


@dataclass
class Address:
    country: str
    region: str
    postal_code: str


@dataclass
class Order:
    items: list[OrderItem]
    customer_id: str
    shipping_address: Address
    discounts: list[Discount] = field(default_factory=list)


@dataclass
class ProcessedOrder:
    order_id: str
    subtotal: float
    discount_total: float
    tax: float
    shipping: float
    total: float
    applied_discounts: list[str]
    line_items: list[dict]


TAX_RATES = {
    "US-CA": 0.0725,
    "US-NY": 0.08,
    "US-TX": 0.0625,
    "US-OR": 0.0,
    "EU-ES": 0.21,
    "EU-DE": 0.19,
    "EU-FR": 0.20,
    "EU-IE": 0.23,
}

SHIPPING_RATES = {
    "US": 9.99,
    "EU": 14.99,
    "UK": 12.99,
}

FREE_SHIPPING_THRESHOLD = 100.0
QUANTITY_BREAK_THRESHOLD = 10
QUANTITY_BREAK_DISCOUNT = 0.05


class Inventory:
    """Tracks product stock levels and handles reservations."""

    def __init__(self, stock: dict[str, int]):
        self._stock = dict(stock)

    def check_availability(self, items: list[OrderItem]) -> list[str]:
        unavailable = []
        for item in items:
            available = self._stock.get(item.product_id, 0)
            if available < item.quantity:
                unavailable.append(
                    f"{item.name}: requested {item.quantity}, available {available}"
                )
        return unavailable

    def reserve(self, items: list[OrderItem]) -> None:
        for item in items:
            current = self._stock.get(item.product_id, 0)
            if current < item.quantity:
                raise ValueError(
                    f"Insufficient stock for {item.name}: "
                    f"requested {item.quantity}, available {current}"
                )
            self._stock[item.product_id] = current - item.quantity

    def release(self, items: list[OrderItem]) -> None:
        for item in items:
            self._stock[item.product_id] = (
                self._stock.get(item.product_id, 0) + item.quantity
            )

    def get_stock(self, product_id: str) -> int:
        return self._stock.get(product_id, 0)


class PricingEngine:
    """Calculates prices, discounts, tax, and shipping."""

    def calculate_line_total(self, item: OrderItem) -> float:
        base = item.unit_price * item.quantity

        if item.quantity > QUANTITY_BREAK_THRESHOLD:
            base *= 1 - QUANTITY_BREAK_DISCOUNT

        if item.discount_type == DiscountType.PERCENTAGE:
            base *= 1 - item.discount_value / 100
        elif item.discount_type == DiscountType.FIXED:
            base -= item.discount_value

        return round(base, 2)

    def calculate_subtotal(
        self, items: list[OrderItem]
    ) -> tuple[float, list[dict]]:
        line_items = []
        subtotal = 0.0

        for item in items:
            line_total = self.calculate_line_total(item)
            line_items.append(
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "line_total": line_total,
                }
            )
            subtotal += line_total

        return round(subtotal, 2), line_items

    def apply_discounts(
        self, subtotal: float, discounts: list[Discount]
    ) -> tuple[float, list[str]]:
        discounted = subtotal
        applied = []

        for discount in discounts:
            if subtotal < discount.minimum_order:
                continue

            if discount.discount_type == DiscountType.PERCENTAGE:
                reduction = round(discounted * discount.value / 100, 2)
                discounted -= reduction
                applied.append(f"{discount.code}: -{reduction:.2f}")
            elif discount.discount_type == DiscountType.FIXED:
                discounted -= discount.value
                applied.append(f"{discount.code}: -{discount.value:.2f}")

        return round(discounted, 2), applied

    def calculate_tax(self, amount: float, address: Address) -> float:
        region_key = f"{address.country}-{address.region}"
        rate = TAX_RATES.get(region_key, 0.0)
        return round(amount * rate, 2)

    def calculate_shipping(
        self, subtotal: float, address: Address
    ) -> float:
        if subtotal >= FREE_SHIPPING_THRESHOLD:
            return 0.0
        base_rate = SHIPPING_RATES.get(address.country, 19.99)
        return base_rate


class OrderProcessor:
    """Orchestrates the full order processing pipeline."""

    def __init__(self, inventory: Inventory):
        self.inventory = inventory
        self.pricing = PricingEngine()
        self._order_counter = 0

    def validate(self, order: Order) -> list[str]:
        errors = []

        if not order.items:
            errors.append("Order must contain at least one item")

        for item in order.items:
            if item.quantity <= 0:
                errors.append(
                    f"Invalid quantity for {item.name}: {item.quantity}"
                )
            if item.unit_price < 0:
                errors.append(
                    f"Invalid price for {item.name}: {item.unit_price}"
                )

        if not order.customer_id:
            errors.append("Customer ID is required")

        unavailable = self.inventory.check_availability(order.items)
        if unavailable:
            errors.extend(unavailable)

        return errors

    def process(self, order: Order) -> ProcessedOrder:
        errors = self.validate(order)
        if errors:
            raise ValueError(f"Invalid order: {'; '.join(errors)}")

        self.inventory.reserve(order.items)

        subtotal, line_items = self.pricing.calculate_subtotal(order.items)

        discounted, applied_discounts = self.pricing.apply_discounts(
            subtotal, order.discounts
        )
        discount_total = round(subtotal - discounted, 2)

        tax = self.pricing.calculate_tax(subtotal, order.shipping_address)
        shipping = self.pricing.calculate_shipping(
            subtotal, order.shipping_address
        )

        total = round(discounted + tax + shipping, 2)

        self._order_counter += 1

        return ProcessedOrder(
            order_id=f"ORD-{self._order_counter:06d}",
            subtotal=subtotal,
            discount_total=discount_total,
            tax=tax,
            shipping=shipping,
            total=total,
            applied_discounts=applied_discounts,
            line_items=line_items,
        )

    def process_batch(
        self, orders: list[Order]
    ) -> list[ProcessedOrder | dict]:
        results = []
        for order in orders:
            try:
                result = self.process(order)
                results.append(result)
            except ValueError as e:
                results.append(
                    {"error": str(e), "customer_id": order.customer_id}
                )
        return results

    def calculate_loyalty_points(
        self, total: float, is_member: bool = False
    ) -> int:
        base_points = int(total)
        if is_member:
            base_points *= 2
        return base_points

    def generate_invoice(self, processed: ProcessedOrder) -> str:
        lines = [
            f"Invoice: {processed.order_id}",
            "-" * 50,
        ]
        for item in processed.line_items:
            lines.append(
                f"  {item['name']:30s} x{item['quantity']:3d}  "
                f"${item['line_total']:>8.2f}"
            )
        lines.append("-" * 50)
        lines.append(
            f"  {'Subtotal':34s}  ${processed.subtotal:>8.2f}"
        )
        if processed.discount_total > 0:
            lines.append(
                f"  {'Discount':34s}  -${processed.discount_total:>7.2f}"
            )
        lines.append(f"  {'Tax':34s}  ${processed.tax:>8.2f}")
        if processed.shipping > 0:
            lines.append(
                f"  {'Shipping':34s}  ${processed.shipping:>8.2f}"
            )
        lines.append("=" * 50)
        lines.append(f"  {'TOTAL':34s}  ${processed.total:>8.2f}")

        if processed.applied_discounts:
            lines.append("")
            lines.append("Applied discounts:")
            for desc in processed.applied_discounts:
                lines.append(f"  - {desc}")

        return "\n".join(lines)

    def apply_refund(
        self,
        processed: ProcessedOrder,
        product_ids: list[str],
        address: Address,
    ) -> ProcessedOrder:
        refund_items = [
            item
            for item in processed.line_items
            if item["product_id"] in product_ids
        ]

        if not refund_items:
            raise ValueError("No matching items found for refund")

        refund_subtotal = sum(item["line_total"] for item in refund_items)

        proportion = refund_subtotal / processed.subtotal if processed.subtotal else 0
        refund_discount = round(processed.discount_total * proportion, 2)
        refund_after_discount = round(refund_subtotal - refund_discount, 2)
        refund_tax = self.pricing.calculate_tax(refund_after_discount, address)

        remaining_items = [
            item
            for item in processed.line_items
            if item["product_id"] not in product_ids
        ]
        new_subtotal = round(processed.subtotal - refund_subtotal, 2)
        new_discount = round(processed.discount_total - refund_discount, 2)
        new_tax = round(processed.tax - refund_tax, 2)

        new_total = round(
            new_subtotal - new_discount + new_tax + processed.shipping, 2
        )

        return ProcessedOrder(
            order_id=f"{processed.order_id}-R",
            subtotal=new_subtotal,
            discount_total=new_discount,
            tax=new_tax,
            shipping=processed.shipping,
            total=new_total,
            applied_discounts=processed.applied_discounts,
            line_items=remaining_items,
        )
