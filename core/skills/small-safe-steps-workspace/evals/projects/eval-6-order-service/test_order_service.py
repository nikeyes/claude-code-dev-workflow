import pytest
from order_service import OrderService


ITEMS = [
    {"product_id": "SKU-001", "quantity": 2, "unit_price": 10.0},
    {"product_id": "SKU-002", "quantity": 1, "unit_price": 25.0},
]


@pytest.fixture
def svc():
    return OrderService()


def test_create_order(svc):
    order = svc.create_order("cust-1", ITEMS)
    assert order.customer_id == "cust-1"
    assert len(order.items) == 2
    assert order.total == 45.0
    assert order.status == "pending"


def test_get_order(svc):
    order = svc.create_order("cust-1", ITEMS)
    fetched = svc.get_order(order.id)
    assert fetched is not None
    assert fetched.id == order.id


def test_get_nonexistent_order(svc):
    assert svc.get_order("does-not-exist") is None


def test_list_orders_for_customer(svc):
    svc.create_order("cust-1", ITEMS)
    svc.create_order("cust-1", ITEMS)
    svc.create_order("cust-2", ITEMS)
    orders = svc.list_orders_for_customer("cust-1")
    assert len(orders) == 2


def test_charge_order_success(svc):
    order = svc.create_order("cust-1", ITEMS)
    result = svc.charge_order(order.id, "tok_valid")
    assert result is True
    charged = svc.get_order(order.id)
    assert charged.status == "paid"
    assert charged.payment_id is not None


def test_charge_order_invalid_token(svc):
    order = svc.create_order("cust-1", ITEMS)
    result = svc.charge_order(order.id, "")
    assert result is False
    assert svc.get_order(order.id).status == "pending"


def test_charge_already_paid_order(svc):
    order = svc.create_order("cust-1", ITEMS)
    svc.charge_order(order.id, "tok_valid")
    result = svc.charge_order(order.id, "tok_valid")
    assert result is False


def test_refund_order(svc):
    order = svc.create_order("cust-1", ITEMS)
    svc.charge_order(order.id, "tok_valid")
    result = svc.refund_order(order.id)
    assert result is True
    assert svc.get_order(order.id).status == "refunded"


def test_ship_order(svc):
    order = svc.create_order("cust-1", ITEMS)
    svc.charge_order(order.id, "tok_valid")
    tracking = svc.ship_order(order.id, "123 Main St")
    assert tracking is not None
    assert svc.get_order(order.id).status == "shipped"


def test_ship_unpaid_order(svc):
    order = svc.create_order("cust-1", ITEMS)
    tracking = svc.ship_order(order.id, "123 Main St")
    assert tracking is None


def test_process_order_full_lifecycle(svc):
    tracking = svc.process_order("cust-1", ITEMS, "tok_valid", "123 Main St")
    assert tracking is not None
    assert tracking.startswith("TRACK-")
