"""Edge case and bug-discovery tests for price_calculator.

These tests target untested functions (apply_coupon, split_payment),
boundary conditions, error paths, and numeric edge cases not covered
by the existing test suite.
"""
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


class TestCalculateDiscountEdgeCases:
    def test_zero_discount_returns_original_price(self):
        assert calculate_discount(100.0, 0) == 100.0

    def test_hundred_percent_discount_returns_zero(self):
        assert calculate_discount(100.0, 100) == 0.0

    def test_discount_greater_than_100_produces_negative_price(self):
        # BUG: no guard — returns a negative value
        result = calculate_discount(100.0, 150)
        assert result < 0, "Discount > 100% produces a negative price with no error"

    def test_negative_discount_increases_price(self):
        # BUG: no guard — a negative discount silently raises the price
        result = calculate_discount(100.0, -10)
        assert result > 100.0, "Negative discount silently increases price with no error"

    def test_negative_price_with_discount(self):
        # BUG: no guard — negative prices are accepted
        result = calculate_discount(-50.0, 10)
        assert result == -45.0

    def test_zero_price_returns_zero(self):
        assert calculate_discount(0.0, 20) == 0.0

    def test_result_is_rounded_to_two_decimals(self):
        # 33.33 * 1/3 = 11.11, remainder price = 22.22
        result = calculate_discount(33.33, 33.333333)
        assert result == round(result, 2)

    def test_small_fractional_price_and_discount(self):
        result = calculate_discount(0.01, 50)
        assert result == 0.01  # round(0.005, 2) == 0.0 or 0.01 — reveals rounding behaviour
        # The actual value depends on Python banker's rounding; this test documents it.
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# calculate_total
# ---------------------------------------------------------------------------


class TestCalculateTotalEdgeCases:
    def test_empty_items_list_returns_zero_totals(self):
        result = calculate_total([])
        assert result["subtotal"] == 0.0
        assert result["tax"] == 0.0
        assert result["total"] == 0.0
        assert result["item_count"] == 0

    def test_zero_quantity_item_contributes_nothing(self):
        items = [{"name": "Ghost", "price": 99.99, "quantity": 0}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["item_count"] == 0

    def test_multiple_items_subtotal_is_sum_of_all(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 3},
        ]
        result = calculate_total(items)
        assert result["subtotal"] == 35.0
        assert result["item_count"] == 5

    def test_item_with_explicit_zero_discount(self):
        items = [{"name": "X", "price": 20.0, "quantity": 1, "discount": 0}]
        result = calculate_total(items)
        assert result["subtotal"] == 20.0

    def test_item_with_100_percent_discount_is_free(self):
        items = [{"name": "Free", "price": 50.0, "quantity": 1, "discount": 100}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["tax"] == 0.0
        assert result["total"] == 0.0

    def test_zero_tax_rate_total_equals_subtotal(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0)
        assert result["subtotal"] == result["total"]
        assert result["tax"] == 0.0

    def test_custom_tax_rate_applied_correctly(self):
        items = [{"name": "Widget", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.10)
        assert result["tax"] == 10.0
        assert result["total"] == 110.0

    def test_negative_tax_rate_reduces_total(self):
        # BUG: no guard — a negative tax rate silently reduces the total
        items = [{"name": "Widget", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=-0.10)
        assert result["total"] < result["subtotal"], (
            "Negative tax rate accepted with no error"
        )

    def test_missing_price_key_raises_key_error(self):
        # BUG: no validation — KeyError propagates to the caller
        items = [{"name": "Broken", "quantity": 1}]
        with pytest.raises(KeyError):
            calculate_total(items)

    def test_missing_quantity_key_raises_key_error(self):
        # BUG: no validation — KeyError propagates to the caller
        items = [{"name": "Broken", "price": 10.0}]
        with pytest.raises(KeyError):
            calculate_total(items)

    def test_explicit_none_discount_raises_type_error(self):
        # BUG: item.get("discount", 0) returns None when explicitly set,
        # which then causes a TypeError inside calculate_discount
        items = [{"name": "X", "price": 10.0, "quantity": 1, "discount": None}]
        with pytest.raises(TypeError):
            calculate_total(items)

    def test_negative_quantity_produces_negative_subtotal(self):
        # BUG: no guard — negative quantities silently produce negative subtotals
        items = [{"name": "Return", "price": 10.0, "quantity": -1}]
        result = calculate_total(items)
        assert result["subtotal"] < 0, "Negative quantity accepted with no error"

    def test_item_count_reflects_total_quantity_across_items(self):
        items = [
            {"name": "A", "price": 1.0, "quantity": 5},
            {"name": "B", "price": 2.0, "quantity": 3},
        ]
        result = calculate_total(items)
        assert result["item_count"] == 8

    def test_large_quantities_do_not_overflow(self):
        items = [{"name": "Bulk", "price": 0.01, "quantity": 1_000_000}]
        result = calculate_total(items)
        assert result["subtotal"] == 10000.0

    def test_floating_point_accumulation_stays_within_one_cent(self):
        # Classic floating-point trap: 0.1 + 0.2 != 0.3
        items = [
            {"name": "A", "price": 0.1, "quantity": 3},
        ]
        result = calculate_total(items, tax_rate=0)
        assert abs(result["subtotal"] - 0.30) < 0.01


# ---------------------------------------------------------------------------
# format_price
# ---------------------------------------------------------------------------


class TestFormatPriceEdgeCases:
    def test_usd_currency_uses_dollar_symbol(self):
        assert format_price(9.99, "USD") == "$9.99"

    def test_gbp_currency_uses_pound_symbol(self):
        assert format_price(9.99, "GBP") == "£9.99"

    def test_unknown_currency_falls_back_to_currency_code(self):
        # Documented behaviour: unknown currency codes are used verbatim as prefix
        assert format_price(9.99, "JPY") == "JPY9.99"

    def test_zero_amount_displays_two_decimal_places(self):
        assert format_price(0.0) == "€0.00"

    def test_negative_amount_displays_with_sign(self):
        # BUG candidate: no guard against negative amounts; result is e.g. "€-10.00"
        result = format_price(-10.0)
        assert result == "€-10.00"

    def test_large_amount_has_no_thousands_separator(self):
        # format_price does NOT add thousands separators
        assert format_price(1000000.0) == "€1000000.00"

    def test_amount_with_many_decimals_is_truncated_to_two(self):
        # f"{amount:.2f}" rounds at display time
        assert format_price(1.005) == "€1.00" or format_price(1.005) == "€1.01"
        # Either is acceptable — this test documents which path Python takes
        assert format_price(1.005) in ("€1.00", "€1.01")

    def test_empty_string_currency_uses_empty_prefix(self):
        # Unusual input: empty string currency code
        result = format_price(10.0, "")
        assert result == "10.00"


# ---------------------------------------------------------------------------
# apply_coupon  (NOT tested at all in existing suite)
# ---------------------------------------------------------------------------


class TestApplyCouponBasic:
    def test_percent_coupon_reduces_total(self):
        coupon = {"type": "percent", "value": 10}
        assert apply_coupon(100.0, coupon) == 90.0

    def test_fixed_coupon_reduces_total(self):
        coupon = {"type": "fixed", "value": 15.0}
        assert apply_coupon(100.0, coupon) == 85.0

    def test_unknown_coupon_type_returns_original_total(self):
        coupon = {"type": "bogus", "value": 50}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_zero_percent_coupon_returns_original_total(self):
        coupon = {"type": "percent", "value": 0}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_zero_fixed_coupon_returns_original_total(self):
        coupon = {"type": "fixed", "value": 0}
        assert apply_coupon(100.0, coupon) == 100.0


class TestApplyCouponEdgeCases:
    def test_hundred_percent_coupon_makes_total_zero(self):
        coupon = {"type": "percent", "value": 100}
        assert apply_coupon(100.0, coupon) == 0.0

    def test_percent_coupon_over_100_produces_negative_total(self):
        # BUG: no guard — over-100% discount produces a negative total
        coupon = {"type": "percent", "value": 150}
        result = apply_coupon(100.0, coupon)
        assert result < 0, "Percent coupon > 100 produces negative total with no error"

    def test_fixed_coupon_exceeding_total_produces_negative_total(self):
        # BUG: no guard — fixed coupon larger than total makes total negative
        coupon = {"type": "fixed", "value": 200.0}
        result = apply_coupon(50.0, coupon)
        assert result < 0, "Fixed coupon > total produces negative total with no error"

    def test_negative_percent_coupon_increases_total(self):
        # BUG: no guard — negative percent value silently raises the total
        coupon = {"type": "percent", "value": -10}
        result = apply_coupon(100.0, coupon)
        assert result > 100.0, "Negative percent coupon silently increases total"

    def test_negative_fixed_coupon_increases_total(self):
        # BUG: no guard — negative fixed value silently raises the total
        coupon = {"type": "fixed", "value": -20.0}
        result = apply_coupon(100.0, coupon)
        assert result > 100.0, "Negative fixed coupon silently increases total"

    def test_missing_type_key_raises_key_error(self):
        # BUG: no validation — accessing coupon["type"] raises KeyError
        coupon = {"value": 10}
        with pytest.raises(KeyError):
            apply_coupon(100.0, coupon)

    def test_missing_value_key_raises_key_error(self):
        # BUG: no validation — accessing coupon["value"] raises KeyError
        coupon = {"type": "percent"}
        with pytest.raises(KeyError):
            apply_coupon(100.0, coupon)

    def test_result_is_rounded_to_two_decimals(self):
        coupon = {"type": "percent", "value": 33.333333}
        result = apply_coupon(100.0, coupon)
        assert result == round(result, 2)

    def test_apply_percent_coupon_to_zero_total_returns_zero(self):
        coupon = {"type": "percent", "value": 50}
        assert apply_coupon(0.0, coupon) == 0.0

    def test_apply_fixed_coupon_to_zero_total_produces_negative(self):
        # BUG: no guard
        coupon = {"type": "fixed", "value": 10.0}
        result = apply_coupon(0.0, coupon)
        assert result < 0, "Fixed coupon on zero total produces negative with no error"


# ---------------------------------------------------------------------------
# split_payment  (NOT tested at all in existing suite)
# ---------------------------------------------------------------------------


class TestSplitPaymentBasic:
    def test_split_into_two_equal_parts(self):
        result = split_payment(100.0, 2)
        assert result == [50.0, 50.0]

    def test_split_into_three_parts_sums_to_total(self):
        result = split_payment(100.0, 3)
        assert abs(sum(result) - 100.0) < 0.001

    def test_split_into_three_parts_has_correct_length(self):
        result = split_payment(100.0, 3)
        assert len(result) == 3

    def test_split_into_one_part_returns_total(self):
        result = split_payment(100.0, 1)
        assert result == [100.0]

    def test_rounding_remainder_assigned_to_last_part(self):
        # 10.0 / 3 = 3.33 each; last part absorbs remainder -> 3.34
        result = split_payment(10.0, 3)
        assert result[0] == result[1]         # first two parts equal
        assert result[-1] != result[0]        # last part differs due to remainder
        assert abs(sum(result) - 10.0) < 0.001


class TestSplitPaymentEdgeCases:
    def test_zero_parts_raises_zero_division_error(self):
        # BUG: no guard — division by zero
        with pytest.raises(ZeroDivisionError):
            split_payment(100.0, 0)

    def test_negative_parts_raises_error_or_returns_empty(self):
        # BUG: no guard — negative parts produce a list of negative length (empty)
        # or raises ValueError; document actual behaviour
        try:
            result = split_payment(100.0, -2)
            # If it doesn't raise, the list is likely empty and the last-element
            # assignment will fail with IndexError — either is a bug
            assert False, f"Expected an error but got {result}"
        except (ZeroDivisionError, ValueError, IndexError):
            pass  # Any of these is acceptable failure behaviour

    def test_split_zero_total_returns_all_zeros(self):
        result = split_payment(0.0, 3)
        assert all(p == 0.0 for p in result)
        assert len(result) == 3

    def test_all_parts_sum_exactly_to_total_for_even_split(self):
        result = split_payment(99.99, 3)
        assert abs(sum(result) - 99.99) < 0.001

    def test_result_values_are_floats_rounded_to_two_decimals(self):
        result = split_payment(100.0, 3)
        for part in result:
            assert part == round(part, 2)

    def test_large_number_of_parts(self):
        result = split_payment(1.00, 100)
        assert len(result) == 100
        assert abs(sum(result) - 1.00) < 0.001

    def test_total_with_many_decimal_places_still_sums_correctly(self):
        # total that cannot be represented exactly in IEEE 754
        result = split_payment(0.1, 3)
        assert abs(sum(result) - 0.1) < 0.001

    def test_single_cent_split_among_many_parts(self):
        # 0.01 split into 3: per_part = 0.0, last gets all the diff
        result = split_payment(0.01, 3)
        assert abs(sum(result) - 0.01) < 0.001
