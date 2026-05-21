import pytest
from inventory import Inventory


def test_add_and_get_item():
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    assert inv.get_item("apple") == {"quantity": 10, "price": 1.50}


def test_add_existing_item_increases_quantity():
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    inv.add_item("apple", 5, 1.50)
    assert inv.get_item("apple")["quantity"] == 15


def test_get_missing_item():
    inv = Inventory()
    assert inv.get_item("banana") is None


def test_negative_quantity_raises():
    inv = Inventory()
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        inv.add_item("apple", -1, 1.50)


# --- Phase 2: remove_item ---

def test_remove_item():
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    inv.remove_item("apple", 3)
    assert inv.get_item("apple")["quantity"] == 7


def test_remove_item_completely():
    inv = Inventory()
    inv.add_item("apple", 5, 1.50)
    inv.remove_item("apple", 5)
    assert inv.get_item("apple") is None


def test_remove_more_than_available_raises():
    inv = Inventory()
    inv.add_item("apple", 3, 1.50)
    with pytest.raises(ValueError, match="Not enough stock"):
        inv.remove_item("apple", 5)


def test_remove_missing_item_raises():
    inv = Inventory()
    with pytest.raises(KeyError):
        inv.remove_item("banana", 1)


# --- Phase 3: total_value (depends on correct remove_item) ---

def test_total_value_single_item():
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    assert inv.total_value() == 15.00


def test_total_value_multiple_items():
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    inv.add_item("banana", 5, 2.00)
    assert inv.total_value() == 25.00


def test_total_value_after_removal():
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    inv.remove_item("apple", 4)
    assert inv.total_value() == 9.00


def test_total_value_empty():
    inv = Inventory()
    assert inv.total_value() == 0.00


# --- Phase 4: apply_discount ---

def test_apply_discount():
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    inv.apply_discount("apple", 25)
    assert inv.get_item("apple")["price"] == 1.50


def test_apply_discount_invalid_percentage():
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        inv.apply_discount("apple", 150)


def test_apply_discount_missing_item():
    inv = Inventory()
    with pytest.raises(KeyError):
        inv.apply_discount("banana", 10)


def test_total_value_after_discount():
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    inv.apply_discount("apple", 50)
    assert inv.total_value() == 10.00
