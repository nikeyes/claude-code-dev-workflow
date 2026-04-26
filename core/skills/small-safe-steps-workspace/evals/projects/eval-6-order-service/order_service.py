from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float


@dataclass
class Order:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    items: list = field(default_factory=list)
    status: str = "pending"
    total: float = 0.0
    payment_id: Optional[str] = None
    shipping_address: Optional[str] = None


class OrderService:
    """Monolith that handles orders, payments, and shipping in one place.
    Payment and shipping logic have grown organically and are now tightly
    coupled to the order lifecycle.
    """

    def __init__(self):
        self._orders: dict[str, Order] = {}
        self._payment_gateway_url = "https://payments.internal/v1"
        self._shipping_provider_url = "https://shipping.internal/v1"

    # ── Order management ──────────────────────────────────────────────────

    def create_order(self, customer_id: str, items: list[dict]) -> Order:
        order = Order(customer_id=customer_id)
        for item in items:
            order.items.append(OrderItem(**item))
        order.total = sum(i.quantity * i.unit_price for i in order.items)
        self._orders[order.id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def list_orders_for_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    # ── Payment processing (candidate for extraction) ────────────────────

    def charge_order(self, order_id: str, card_token: str) -> bool:
        order = self._orders.get(order_id)
        if order is None or order.status != "pending":
            return False

        # Simulate payment gateway call
        payment_id = f"pay_{order_id[:8]}"
        success = self._call_payment_gateway(card_token, order.total)

        if success:
            order.payment_id = payment_id
            order.status = "paid"
            self._orders[order_id] = order
        return success

    def refund_order(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if order is None or order.payment_id is None:
            return False

        success = self._call_payment_refund(order.payment_id, order.total)
        if success:
            order.status = "refunded"
            self._orders[order_id] = order
        return success

    def _call_payment_gateway(self, card_token: str, amount: float) -> bool:
        # In production this would POST to self._payment_gateway_url
        # Simplified: always succeeds for non-empty tokens
        return bool(card_token) and amount > 0

    def _call_payment_refund(self, payment_id: str, amount: float) -> bool:
        # In production this would POST to self._payment_gateway_url + '/refund'
        return bool(payment_id) and amount > 0

    # ── Shipping (also candidate for extraction) ──────────────────────────

    def ship_order(self, order_id: str, address: str) -> Optional[str]:
        order = self._orders.get(order_id)
        if order is None or order.status != "paid":
            return None

        tracking_number = self._call_shipping_provider(order_id, address)
        if tracking_number:
            order.shipping_address = address
            order.status = "shipped"
            self._orders[order_id] = order
        return tracking_number

    def _call_shipping_provider(self, order_id: str, address: str) -> Optional[str]:
        # In production this would POST to self._shipping_provider_url
        if not address:
            return None
        return f"TRACK-{order_id[:8].upper()}"

    # ── Full lifecycle ────────────────────────────────────────────────────

    def process_order(self, customer_id: str, items: list[dict], card_token: str, address: str) -> Optional[str]:
        """Creates order, charges card, and arranges shipping in one call."""
        order = self.create_order(customer_id, items)
        if not self.charge_order(order.id, card_token):
            return None
        tracking = self.ship_order(order.id, address)
        return tracking
