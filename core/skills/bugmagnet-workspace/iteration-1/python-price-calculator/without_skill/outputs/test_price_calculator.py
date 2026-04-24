"""Comprehensive tests for price_calculator.py."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../../../skills/bugmagnet/evals/files"))

from price_calculator import (
    apply_coupon,
    calculate_discount,
    calculate_total,
    format_price,
    split_payment,
)


# ---------------------------------------------------------------------------
# calculate_discount
# ---------------------------------------------------------------------------

class TestCalculateDiscount:
    def test_ten_percent_off_round_number(self):
        assert calculate_discount(100, 10) == 90.0

    def test_zero_discount_returns_original_price(self):
        assert calculate_discount(50.0, 0) == 50.0

    def test_hundred_percent_discount_returns_zero(self):
        assert calculate_discount(100.0, 100) == 0.0

    def test_fractional_discount_rounds_to_two_decimals(self):
        # 99 * 33% = 32.67  → 99 - 32.67 = 66.33
        assert calculate_discount(99.0, 33) == 66.33

    def test_small_price_with_discount(self):
        assert calculate_discount(1.0, 50) == 0.5

    def test_discount_on_decimal_price(self):
        # 19.99 * 10% = 1.999 → 19.99 - 2.00 = 17.99
        assert calculate_discount(19.99, 10) == 17.99

    def test_result_is_float(self):
        result = calculate_discount(100, 10)
        assert isinstance(result, float)

    # --- edge / boundary cases that may reveal bugs ---

    def test_negative_discount_increases_price(self):
        """A negative discount percentage should increase the price."""
        result = calculate_discount(100.0, -10)
        assert result == 110.0

    def test_discount_greater_than_100_returns_negative_price(self):
        """There is no guard against discounts > 100; result will be negative."""
        result = calculate_discount(100.0, 110)
        assert result == -10.0

    def test_zero_price_any_discount_returns_zero(self):
        assert calculate_discount(0.0, 50) == 0.0


# ---------------------------------------------------------------------------
# calculate_total
# ---------------------------------------------------------------------------

class TestCalculateTotal:
    def test_single_item_no_discount_default_tax(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items)
        assert result["subtotal"] == 10.0
        assert result["tax"] == 2.1
        assert result["total"] == 12.1
        assert result["item_count"] == 1

    def test_result_contains_required_keys(self):
        items = [{"name": "Item", "price": 5.0, "quantity": 1}]
        result = calculate_total(items)
        assert set(result.keys()) == {"subtotal", "tax", "total", "item_count"}

    def test_multiple_items(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 3},
        ]
        result = calculate_total(items)
        # subtotal = 20 + 15 = 35
        assert result["subtotal"] == 35.0
        assert result["item_count"] == 5

    def test_item_with_discount(self):
        items = [{"name": "X", "price": 100.0, "quantity": 1, "discount": 10}]
        result = calculate_total(items)
        # price after discount = 90; tax = 90 * 0.21 = 18.9; total = 108.9
        assert result["subtotal"] == 90.0
        assert result["tax"] == 18.9
        assert result["total"] == 108.9

    def test_custom_tax_rate(self):
        items = [{"name": "Item", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.10)
        assert result["subtotal"] == 100.0
        assert result["tax"] == 10.0
        assert result["total"] == 110.0

    def test_zero_tax_rate(self):
        items = [{"name": "Item", "price": 50.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.0)
        assert result["subtotal"] == 50.0
        assert result["tax"] == 0.0
        assert result["total"] == 50.0

    def test_item_count_reflects_quantities(self):
        items = [
            {"name": "A", "price": 1.0, "quantity": 10},
            {"name": "B", "price": 1.0, "quantity": 5},
        ]
        result = calculate_total(items)
        assert result["item_count"] == 15

    def test_missing_discount_key_defaults_to_zero(self):
        """Items without a 'discount' key should be treated as 0% discount."""
        items = [{"name": "Item", "price": 20.0, "quantity": 1}]
        result = calculate_total(items)
        assert result["subtotal"] == 20.0

    def test_subtotal_plus_tax_equals_total(self):
        items = [{"name": "Item", "price": 37.50, "quantity": 3}]
        result = calculate_total(items)
        assert round(result["subtotal"] + result["tax"], 2) == result["total"]

    # --- edge / boundary cases that may reveal bugs ---

    def test_empty_items_list(self):
        """An empty list should produce zeros."""
        result = calculate_total([])
        assert result["subtotal"] == 0.0
        assert result["tax"] == 0.0
        assert result["total"] == 0.0
        assert result["item_count"] == 0

    def test_quantity_zero_item(self):
        """An item with quantity 0 should not contribute to the total."""
        items = [{"name": "Ghost", "price": 99.99, "quantity": 0}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["item_count"] == 0

    def test_floating_point_precision_rounding(self):
        """Subtotal rounding should prevent floating-point accumulation."""
        items = [{"name": "Cent", "price": 0.1, "quantity": 3}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.3


# ---------------------------------------------------------------------------
# format_price
# ---------------------------------------------------------------------------

class TestFormatPrice:
    def test_eur_default_currency(self):
        assert format_price(10.5) == "€10.50"

    def test_usd_symbol(self):
        assert format_price(9.99, "USD") == "$9.99"

    def test_gbp_symbol(self):
        assert format_price(5.0, "GBP") == "£5.00"

    def test_unknown_currency_uses_code_as_symbol(self):
        """Currencies not in the symbol map should use the code itself."""
        assert format_price(100.0, "JPY") == "JPY100.00"

    def test_zero_amount(self):
        assert format_price(0.0) == "€0.00"

    def test_large_amount_formatted_correctly(self):
        assert format_price(1234567.89, "USD") == "$1234567.89"

    def test_two_decimal_places_always(self):
        result = format_price(5.0, "USD")
        assert result.endswith("5.00")

    def test_result_is_string(self):
        assert isinstance(format_price(1.0), str)


# ---------------------------------------------------------------------------
# apply_coupon
# ---------------------------------------------------------------------------

class TestApplyCoupon:
    def test_percent_coupon_reduces_total(self):
        coupon = {"type": "percent", "value": 10}
        assert apply_coupon(100.0, coupon) == 90.0

    def test_fixed_coupon_reduces_total(self):
        coupon = {"type": "fixed", "value": 15.0}
        assert apply_coupon(100.0, coupon) == 85.0

    def test_unknown_coupon_type_returns_total_unchanged(self):
        coupon = {"type": "bogo", "value": 50}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_percent_coupon_result_rounded_to_two_decimals(self):
        # 99.99 * 33% = 32.9967 → 99.99 - 32.9967 ≈ 66.99
        coupon = {"type": "percent", "value": 33}
        result = apply_coupon(99.99, coupon)
        assert result == round(99.99 - (99.99 * 33 / 100), 2)

    def test_fixed_coupon_result_rounded_to_two_decimals(self):
        coupon = {"type": "fixed", "value": 0.015}
        result = apply_coupon(10.0, coupon)
        assert result == round(10.0 - 0.015, 2)

    def test_zero_percent_coupon_returns_total_unchanged(self):
        coupon = {"type": "percent", "value": 0}
        assert apply_coupon(50.0, coupon) == 50.0

    def test_zero_fixed_coupon_returns_total_unchanged(self):
        coupon = {"type": "fixed", "value": 0}
        assert apply_coupon(50.0, coupon) == 50.0

    def test_hundred_percent_coupon_returns_zero(self):
        coupon = {"type": "percent", "value": 100}
        assert apply_coupon(200.0, coupon) == 0.0

    # --- edge / boundary cases that may reveal bugs ---

    def test_fixed_coupon_exceeding_total_returns_negative(self):
        """No guard against coupon > total; result will be negative."""
        coupon = {"type": "fixed", "value": 150.0}
        result = apply_coupon(100.0, coupon)
        assert result == -50.0

    def test_percent_coupon_over_100_returns_negative(self):
        """No guard against percent > 100; result will be negative."""
        coupon = {"type": "percent", "value": 110}
        result = apply_coupon(100.0, coupon)
        assert result == -10.0


# ---------------------------------------------------------------------------
# split_payment
# ---------------------------------------------------------------------------

class TestSplitPayment:
    def test_evenly_divisible_total(self):
        result = split_payment(90.0, 3)
        assert result == [30.0, 30.0, 30.0]

    def test_returns_correct_number_of_parts(self):
        result = split_payment(100.0, 4)
        assert len(result) == 4

    def test_parts_sum_to_total(self):
        result = split_payment(100.0, 3)
        assert round(sum(result), 2) == 100.0

    def test_rounding_remainder_added_to_last_part(self):
        """When total doesn't divide evenly, the remainder goes to the last part."""
        result = split_payment(10.0, 3)
        # per_part = 3.33; 3.33 * 3 = 9.99; diff = 0.01 → last part = 3.34
        assert result[0] == 3.33
        assert result[1] == 3.33
        assert result[-1] == 3.34

    def test_single_part_equals_total(self):
        result = split_payment(99.99, 1)
        assert result == [99.99]

    def test_two_parts_sum_to_total(self):
        result = split_payment(1.0, 2)
        assert round(sum(result), 2) == 1.0

    def test_large_total_split_correctly(self):
        result = split_payment(1000.0, 4)
        assert result == [250.0, 250.0, 250.0, 250.0]

    def test_all_parts_except_last_are_equal(self):
        result = split_payment(100.0, 3)
        assert result[0] == result[1]

    # --- edge / boundary cases that may reveal bugs ---

    def test_split_into_one_part_returns_list_with_original_total(self):
        result = split_payment(75.5, 1)
        assert result == [75.5]

    def test_zero_total_split_into_parts_returns_zeros(self):
        result = split_payment(0.0, 3)
        assert result == [0.0, 0.0, 0.0]
