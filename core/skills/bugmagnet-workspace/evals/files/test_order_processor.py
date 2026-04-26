"""Baseline tests for order processor — happy path only."""

from order_processor import (
    OrderItem,
    Discount,
    DiscountType,
    Address,
    Order,
    Inventory,
    OrderProcessor,
)


def _make_order(items=None, discounts=None):
    return Order(
        items=items or [
            OrderItem(product_id="P1", name="Widget", unit_price=25.0, quantity=2),
        ],
        customer_id="C001",
        shipping_address=Address(country="US", region="CA", postal_code="90210"),
        discounts=discounts or [],
    )


def test_process_basic_order():
    inv = Inventory({"P1": 10})
    processor = OrderProcessor(inv)
    result = processor.process(_make_order())
    assert result.subtotal == 50.0
    assert result.total > 0


def test_validate_empty_order():
    inv = Inventory({})
    processor = OrderProcessor(inv)
    errors = processor.validate(
        Order(items=[], customer_id="C001",
              shipping_address=Address("US", "CA", "90210"))
    )
    assert "Order must contain at least one item" in errors


def test_percentage_discount_applied():
    inv = Inventory({"P1": 10})
    processor = OrderProcessor(inv)
    discount = Discount(
        code="SAVE10", discount_type=DiscountType.PERCENTAGE,
        value=10, minimum_order=0,
    )
    result = processor.process(_make_order(discounts=[discount]))
    assert result.discount_total > 0
