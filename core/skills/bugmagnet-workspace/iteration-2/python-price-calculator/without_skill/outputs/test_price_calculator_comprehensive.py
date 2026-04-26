"""Comprehensive tests for price_calculator — edge cases, boundary conditions, and bug discovery."""
import pytest
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
    def test_basic_ten_percent(self):
        assert calculate_discount(100, 10) == 90.0

    def test_zero_discount_returns_original_price(self):
        assert calculate_discount(50.0, 0) == 50.0

    def test_hundred_percent_discount_returns_zero(self):
        assert calculate_discount(100, 100) == 0.0

    def test_fractional_price_rounds_to_two_decimals(self):
        result = calculate_discount(9.99, 10)
        assert result == 8.99

    def test_small_price_with_discount(self):
        result = calculate_discount(1.00, 33)
        assert result == 0.67

    def test_negative_discount_increases_price(self):
        # No guard: a negative discount acts as a price increase.
        # Document the current (buggy?) behavior.
        result = calculate_discount(100, -10)
        assert result == 110.0  # BUG: no validation — negative discount silently accepted

    def test_discount_above_100_gives_negative_price(self):
        # No guard: discount > 100 produces a negative price.
        result = calculate_discount(100, 150)
        assert result == -50.0  # BUG: no validation — result is negative

    def test_zero_price_with_discount(self):
        assert calculate_discount(0, 50) == 0.0

    def test_negative_price(self):
        # No guard on negative price.
        result = calculate_discount(-100, 10)
        assert result == -90.0  # BUG: no validation — negative price silently accepted

    def test_large_price_precision(self):
        result = calculate_discount(999.99, 15)
        assert result == 849.99


# ---------------------------------------------------------------------------
# calculate_total
# ---------------------------------------------------------------------------

class TestCalculateTotal:
    def test_single_item_no_discount(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items)
        assert result["subtotal"] == 10.0
        assert result["tax"] == 2.10
        assert result["total"] == 12.10
        assert result["item_count"] == 1

    def test_multiple_items_sum(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 3},
        ]
        result = calculate_total(items)
        assert result["subtotal"] == 35.0
        assert result["item_count"] == 5

    def test_item_with_discount(self):
        items = [{"name": "A", "price": 100.0, "quantity": 1, "discount": 20}]
        result = calculate_total(items)
        assert result["subtotal"] == 80.0

    def test_custom_tax_rate(self):
        items = [{"name": "A", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.10)
        assert result["tax"] == 10.0
        assert result["total"] == 110.0

    def test_zero_tax_rate(self):
        items = [{"name": "A", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.0)
        assert result["tax"] == 0.0
        assert result["total"] == 100.0

    def test_empty_items_list(self):
        # Empty list: subtotal=0, tax=0, total=0, item_count=0
        result = calculate_total([])
        assert result["subtotal"] == 0.0
        assert result["tax"] == 0.0
        assert result["total"] == 0.0
        assert result["item_count"] == 0

    def test_zero_quantity_item(self):
        items = [{"name": "A", "price": 50.0, "quantity": 0}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["item_count"] == 0

    def test_large_quantity(self):
        items = [{"name": "A", "price": 1.0, "quantity": 1000}]
        result = calculate_total(items)
        assert result["subtotal"] == 1000.0

    def test_item_count_sums_all_quantities(self):
        items = [
            {"name": "A", "price": 1.0, "quantity": 3},
            {"name": "B", "price": 2.0, "quantity": 7},
        ]
        result = calculate_total(items)
        assert result["item_count"] == 10

    def test_high_precision_subtotal_rounds_correctly(self):
        # 3 x 3.33 = 9.99 — check rounding
        items = [{"name": "A", "price": 3.33, "quantity": 3}]
        result = calculate_total(items)
        assert result["subtotal"] == 9.99

    def test_negative_quantity_reduces_subtotal(self):
        # No guard: negative quantities are silently accepted.
        items = [{"name": "A", "price": 10.0, "quantity": -1}]
        result = calculate_total(items)
        assert result["subtotal"] == -10.0  # BUG: no validation — negative quantity accepted

    def test_missing_price_key_raises(self):
        items = [{"name": "A", "quantity": 1}]
        with pytest.raises(KeyError):
            calculate_total(items)

    def test_missing_quantity_key_raises(self):
        items = [{"name": "A", "price": 10.0}]
        with pytest.raises(KeyError):
            calculate_total(items)

    def test_floating_point_tax_accumulation(self):
        # Repeated small values: 3 items at $1.10 each, 21% tax
        items = [{"name": "A", "price": 1.10, "quantity": 3}]
        result = calculate_total(items)
        assert result["subtotal"] == 3.30
        assert result["total"] == round(3.30 * 1.21, 2)


# ---------------------------------------------------------------------------
# format_price
# ---------------------------------------------------------------------------

class TestFormatPrice:
    def test_eur_default_currency(self):
        assert format_price(10.5) == "€10.50"

    def test_usd_currency(self):
        assert format_price(9.99, "USD") == "$9.99"

    def test_gbp_currency(self):
        assert format_price(5.0, "GBP") == "£5.00"

    def test_unknown_currency_uses_code_as_symbol(self):
        # Falls back to raw currency code when symbol not found.
        assert format_price(10.0, "JPY") == "JPY10.00"

    def test_zero_amount(self):
        assert format_price(0) == "€0.00"

    def test_negative_amount(self):
        # No guard: negative amounts are formatted without error.
        result = format_price(-5.0)
        assert result == "€-5.00"  # BUG: no validation — negative amount silently formatted

    def test_large_amount(self):
        assert format_price(1000000.00) == "€1000000.00"

    def test_amount_with_many_decimal_places_truncated(self):
        # Only 2 decimal places displayed; no rounding guard in format_price itself.
        result = format_price(1.005)
        # Python f-string rounds at display level: 1.005 -> "€1.00" or "€1.01" depending on float repr
        assert result in ("€1.00", "€1.01")  # document behavior

    def test_empty_string_currency_uses_empty_symbol(self):
        result = format_price(10.0, "")
        assert result == "10.00"  # BUG: empty currency string produces no symbol


# ---------------------------------------------------------------------------
# apply_coupon
# ---------------------------------------------------------------------------

class TestApplyCoupon:
    def test_percent_coupon_basic(self):
        coupon = {"type": "percent", "value": 10}
        assert apply_coupon(100.0, coupon) == 90.0

    def test_fixed_coupon_basic(self):
        coupon = {"type": "fixed", "value": 5.0}
        assert apply_coupon(100.0, coupon) == 95.0

    def test_unknown_coupon_type_returns_total_unchanged(self):
        # Unknown type silently returns original total — no error raised.
        coupon = {"type": "gift_card", "value": 20}
        assert apply_coupon(100.0, coupon) == 100.0  # BUG: silent no-op for unknown type

    def test_percent_coupon_100_percent_gives_zero(self):
        coupon = {"type": "percent", "value": 100}
        assert apply_coupon(100.0, coupon) == 0.0

    def test_percent_coupon_above_100_gives_negative_total(self):
        coupon = {"type": "percent", "value": 150}
        result = apply_coupon(100.0, coupon)
        assert result == -50.0  # BUG: no validation — result is negative

    def test_fixed_coupon_exceeds_total_gives_negative_total(self):
        coupon = {"type": "fixed", "value": 150.0}
        result = apply_coupon(50.0, coupon)
        assert result == -100.0  # BUG: no validation — fixed coupon can exceed total

    def test_zero_percent_coupon(self):
        coupon = {"type": "percent", "value": 0}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_zero_fixed_coupon(self):
        coupon = {"type": "fixed", "value": 0}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_negative_percent_coupon_increases_total(self):
        coupon = {"type": "percent", "value": -10}
        result = apply_coupon(100.0, coupon)
        assert result == 110.0  # BUG: no validation — negative coupon adds to total

    def test_negative_fixed_coupon_increases_total(self):
        coupon = {"type": "fixed", "value": -10}
        result = apply_coupon(100.0, coupon)
        assert result == 110.0  # BUG: no validation — negative fixed coupon adds to total

    def test_percent_coupon_rounds_to_two_decimals(self):
        coupon = {"type": "percent", "value": 33}
        result = apply_coupon(10.0, coupon)
        assert result == 6.70

    def test_fixed_coupon_rounds_to_two_decimals(self):
        coupon = {"type": "fixed", "value": 0.005}
        result = apply_coupon(10.0, coupon)
        # 10.0 - 0.005 = 9.995, rounds to 10.0 or 9.99 depending on float repr
        assert result in (9.99, 10.0)

    def test_missing_type_key_raises(self):
        coupon = {"value": 10}
        with pytest.raises(KeyError):
            apply_coupon(100.0, coupon)

    def test_missing_value_key_raises_for_percent(self):
        coupon = {"type": "percent"}
        with pytest.raises(KeyError):
            apply_coupon(100.0, coupon)


# ---------------------------------------------------------------------------
# split_payment
# ---------------------------------------------------------------------------

class TestSplitPayment:
    def test_even_split(self):
        result = split_payment(100.0, 4)
        assert result == [25.0, 25.0, 25.0, 25.0]

    def test_split_two_parts(self):
        result = split_payment(10.0, 2)
        assert result == [5.0, 5.0]

    def test_uneven_split_remainder_in_last_part(self):
        # 10 / 3 = 3.33 each; remainder goes to last part
        result = split_payment(10.0, 3)
        assert len(result) == 3
        assert sum(result) == pytest.approx(10.0, abs=0.01)
        assert result[0] == result[1]  # first parts are equal
        # Last part absorbs rounding diff
        assert result[-1] == pytest.approx(result[0], abs=0.01)

    def test_split_one_part_returns_full_total(self):
        result = split_payment(100.0, 1)
        assert result == [100.0]

    def test_split_sum_equals_original_total(self):
        for parts in [2, 3, 5, 7]:
            result = split_payment(99.99, parts)
            assert sum(result) == pytest.approx(99.99, abs=0.01)

    def test_zero_total_split(self):
        result = split_payment(0.0, 3)
        assert result == [0.0, 0.0, 0.0]

    def test_split_by_zero_raises(self):
        # Division by zero should raise ZeroDivisionError — no guard exists.
        with pytest.raises(ZeroDivisionError):
            split_payment(100.0, 0)  # BUG: no validation — zero parts causes ZeroDivisionError

    def test_negative_parts_raises_index_error(self):
        # Negative parts: round(100/-1, 2) = -100.0; result = [-100.0] * -1 = []
        # Then result[-1] raises IndexError on an empty list.
        with pytest.raises(IndexError):
            split_payment(100.0, -1)  # BUG: no validation — negative parts causes IndexError

    def test_large_number_of_parts(self):
        result = split_payment(100.0, 100)
        assert len(result) == 100
        assert all(p == pytest.approx(1.0) for p in result)

    def test_fractional_total_split_two(self):
        result = split_payment(0.01, 2)
        assert len(result) == 2
        assert sum(result) == pytest.approx(0.01, abs=0.01)

    def test_result_length_equals_parts(self):
        result = split_payment(50.0, 5)
        assert len(result) == 5
