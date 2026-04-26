import pytest

from src.services.order_service import OrderService


@pytest.fixture
def service():
    return OrderService()


def valid_order_data(**overrides):
    data = {
        "customer_name": "Alice Smith",
        "email": "alice@example.com",
        "quantity": 5,
        "unit_price": 19.99,
        "notes": "Rush delivery",
    }
    data.update(overrides)
    return data


class TestCreateOrder:
    def test_valid_order(self, service):
        order = service.create_order(valid_order_data())
        assert order.customer_name == "Alice Smith"
        assert order.email == "alice@example.com"
        assert order.quantity == 5
        assert order.unit_price == 19.99
        assert order.total == 99.95

    def test_missing_customer_name(self, service):
        with pytest.raises(ValueError, match="Customer name"):
            service.create_order(valid_order_data(customer_name=""))

    def test_invalid_email(self, service):
        with pytest.raises(ValueError, match="email"):
            service.create_order(valid_order_data(email="not-an-email"))

    def test_negative_quantity(self, service):
        with pytest.raises(ValueError, match="Quantity"):
            service.create_order(valid_order_data(quantity=-1))

    def test_zero_price(self, service):
        with pytest.raises(ValueError, match="Unit price"):
            service.create_order(valid_order_data(unit_price=0))

    def test_notes_optional(self, service):
        order = service.create_order(valid_order_data(notes=""))
        assert order.notes == ""


class TestListOrders:
    def test_empty(self, service):
        assert service.list_orders() == []

    def test_after_create(self, service):
        service.create_order(valid_order_data())
        assert len(service.list_orders()) == 1
