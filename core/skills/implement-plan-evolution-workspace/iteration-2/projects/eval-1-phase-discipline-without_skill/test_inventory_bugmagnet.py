"""
BugMagnet edge-case tests for inventory.py
"""
import pytest
from inventory import Inventory


# ── add_item edge cases ───────────────────────────────────────────────────────

def test_add_item_zero_quantity():
    """Adding 0 units should be allowed (no stock change but item is created)."""
    inv = Inventory()
    inv.add_item("apple", 0, 1.50)
    assert inv.get_item("apple") == {"quantity": 0, "price": 1.50}


def test_add_item_zero_price():
    """Price of 0 should be valid (free items)."""
    inv = Inventory()
    inv.add_item("promo", 5, 0.0)
    assert inv.get_item("promo") == {"quantity": 5, "price": 0.0}


def test_add_item_price_ignored_on_second_add():
    """When adding more stock for an existing item, the price in the call is ignored;
    the original price is preserved."""
    inv = Inventory()
    inv.add_item("apple", 5, 1.00)
    inv.add_item("apple", 5, 9.99)   # different price — should be ignored
    assert inv.get_item("apple")["price"] == 1.00


def test_add_item_negative_price_raises():
    """Negative price must raise ValueError."""
    inv = Inventory()
    with pytest.raises(ValueError, match="Price cannot be negative"):
        inv.add_item("apple", 5, -0.01)


def test_add_item_float_quantity_raises_or_accepts():
    """Float quantities are ambiguous; document current behaviour."""
    inv = Inventory()
    # Current code accepts floats without validation — document it
    inv.add_item("apple", 2.5, 1.00)
    assert inv.get_item("apple")["quantity"] == 2.5


# ── remove_item edge cases ────────────────────────────────────────────────────

def test_remove_zero_quantity():
    """Removing 0 units from an item that exists should leave it unchanged."""
    inv = Inventory()
    inv.add_item("apple", 5, 1.50)
    inv.remove_item("apple", 0)
    assert inv.get_item("apple") == {"quantity": 5, "price": 1.50}


@pytest.mark.skip(reason="remove_item with negative quantity does not raise - BUG")
def test_remove_negative_quantity_raises_bug():
    """
    ROOT CAUSE: remove_item checks `quantity > self._items[name]["quantity"]`
                which is False for negative values, so the subtraction
                silently *increases* the stored quantity (double-negative).
    CODE LOCATION: inventory.py:23-27
    PROPOSED FIX: add `if quantity < 0: raise ValueError("Quantity cannot be negative")`
                  at the start of remove_item, mirroring the guard in add_item.
    EXPECTED: raises ValueError for a negative quantity argument
    ACTUAL: silently increases the stored quantity instead of raising
    """
    inv = Inventory()
    inv.add_item("apple", 5, 1.50)
    with pytest.raises(ValueError):
        inv.remove_item("apple", -1)


def test_remove_item_does_not_mutate_price():
    """Removing items must not change the stored price."""
    inv = Inventory()
    inv.add_item("apple", 10, 2.50)
    inv.remove_item("apple", 3)
    assert inv.get_item("apple")["price"] == 2.50


def test_remove_missing_item_key_error_contains_name():
    """KeyError should identify the missing item name for clarity."""
    inv = Inventory()
    with pytest.raises(KeyError) as exc_info:
        inv.remove_item("ghost", 1)
    assert "ghost" in str(exc_info.value)


# ── total_value edge cases ────────────────────────────────────────────────────

def test_total_value_after_item_fully_removed():
    """After an item is fully removed, it no longer contributes to total value."""
    inv = Inventory()
    inv.add_item("apple", 5, 2.00)
    inv.add_item("banana", 3, 1.00)
    inv.remove_item("apple", 5)
    assert inv.total_value() == 3.00


def test_total_value_with_zero_price_items():
    """Items with price 0 contribute nothing to total value."""
    inv = Inventory()
    inv.add_item("freebie", 100, 0.0)
    inv.add_item("apple", 2, 1.50)
    assert inv.total_value() == 3.00


def test_total_value_floating_point_precision():
    """Floating-point arithmetic shouldn't produce wildly incorrect results."""
    inv = Inventory()
    inv.add_item("item", 3, 0.1)
    # 3 * 0.1 in floating point is 0.30000000000000004; use approx
    assert inv.total_value() == pytest.approx(0.30, rel=1e-9)


# ── apply_discount edge cases ─────────────────────────────────────────────────

def test_apply_zero_percent_discount():
    """0% discount should leave the price unchanged."""
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    inv.apply_discount("apple", 0)
    assert inv.get_item("apple")["price"] == pytest.approx(2.00)


def test_apply_100_percent_discount():
    """100% discount should set the price to 0."""
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    inv.apply_discount("apple", 100)
    assert inv.get_item("apple")["price"] == pytest.approx(0.0)


def test_apply_discount_negative_raises():
    """Negative discount percentages must raise ValueError."""
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        inv.apply_discount("apple", -10)


def test_apply_discount_exactly_100_boundary():
    """101% discount is invalid."""
    inv = Inventory()
    inv.add_item("apple", 10, 2.00)
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        inv.apply_discount("apple", 101)


def test_apply_discount_missing_item_key_error_contains_name():
    """KeyError should identify the missing item."""
    inv = Inventory()
    with pytest.raises(KeyError) as exc_info:
        inv.apply_discount("ghost", 10)
    assert "ghost" in str(exc_info.value)


def test_apply_discount_compounds_correctly():
    """Two successive discounts compound multiplicatively."""
    inv = Inventory()
    inv.add_item("apple", 1, 100.00)
    inv.apply_discount("apple", 50)   # → 50.00
    inv.apply_discount("apple", 50)   # → 25.00
    assert inv.get_item("apple")["price"] == pytest.approx(25.00)


def test_apply_discount_total_value_reflects_new_price():
    """total_value uses the discounted price, not the original."""
    inv = Inventory()
    inv.add_item("apple", 4, 10.00)
    inv.apply_discount("apple", 25)   # price → 7.50
    assert inv.total_value() == pytest.approx(30.00)


# ── interaction / integration edge cases ─────────────────────────────────────

def test_add_after_full_removal_creates_new_entry():
    """After an item is fully removed, adding it again treats it as a new item."""
    inv = Inventory()
    inv.add_item("apple", 5, 1.00)
    inv.remove_item("apple", 5)
    assert inv.get_item("apple") is None
    inv.add_item("apple", 3, 2.00)   # new entry — new price allowed
    assert inv.get_item("apple") == {"quantity": 3, "price": 2.00}


def test_get_item_returns_copy_not_reference():
    """get_item must return a copy so callers can't mutate internal state."""
    inv = Inventory()
    inv.add_item("apple", 10, 1.50)
    copy = inv.get_item("apple")
    copy["quantity"] = 999
    assert inv.get_item("apple")["quantity"] == 10


@pytest.mark.skip(reason="remove_item with negative quantity does not raise - BUG")
def test_remove_negative_quantity_is_rejected_bug():
    """
    ROOT CAUSE: remove_item performs `quantity > self._items[name]["quantity"]`
                which is False when quantity is negative, so the subtraction
                `self._items[name]["quantity"] -= quantity` silently *adds* stock.
    CODE LOCATION: inventory.py:23-27
    PROPOSED FIX: add `if quantity < 0: raise ValueError("Quantity cannot be negative")`
                  at the top of remove_item, mirroring the guard in add_item.
    EXPECTED: raises ValueError for negative quantity argument
    ACTUAL: silently increases the stored quantity
    """
    inv = Inventory()
    inv.add_item("apple", 5, 1.50)
    with pytest.raises(ValueError):
        inv.remove_item("apple", -3)   # should reject; currently adds 3 instead
