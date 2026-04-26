"""Tests for price_calculator."""
import pytest
from price_calculator import calculate_discount, calculate_total, format_price, apply_coupon, split_payment


# ── Existing Tests ──────────────────────────────────────────────────────────────

def test_calculate_discount_basic():
    assert calculate_discount(100, 10) == 90.0


def test_calculate_total_single_item():
    items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
    result = calculate_total(items)
    assert result["subtotal"] == 10.0
    assert result["total"] == 12.1


def test_format_price_eur():
    assert format_price(10.5) == "€10.50"


# ── Phase 3: Gap Tests – calculate_discount ─────────────────────────────────────

class TestCalculateDiscount:
    def test_returns_original_price_when_discount_is_zero(self):
        assert calculate_discount(100.0, 0) == 100.0

    def test_returns_zero_when_discount_is_100_percent(self):
        assert calculate_discount(100.0, 100) == 0.0

    def test_returns_rounded_result_when_price_produces_fractional_cents(self):
        # 10.00 with 33% discount -> 10 - 3.3 = 6.70
        assert calculate_discount(10.0, 33) == 6.70

    def test_returns_zero_when_price_is_zero(self):
        assert calculate_discount(0.0, 10) == 0.0

    def test_returns_correct_discount_for_float_price(self):
        # 19.99 * 10% discount -> 19.99 - 1.999 = 17.991 -> 17.99
        assert calculate_discount(19.99, 10) == 17.99

    def test_returns_negative_result_when_price_is_negative(self):
        # -100 with 10% discount: -100 - (-10) = -90.0
        assert calculate_discount(-100.0, 10) == -90.0

    def test_returns_increased_price_when_discount_percent_is_negative(self):
        # negative discount acts as a surcharge: 100 - (100 * -10 / 100) = 110
        assert calculate_discount(100.0, -10) == 110.0

    def test_returns_negative_result_when_discount_exceeds_100_percent(self):
        # 100 with 150% discount: 100 - 150 = -50
        assert calculate_discount(100.0, 150) == -50.0

    def test_returns_correct_result_for_very_small_price(self):
        # 0.01 * 50% = 0.005 -> rounds to 0.01 (banker's rounding) or 0.0
        result = calculate_discount(0.01, 50)
        assert result == round(0.01 - (0.01 * 50 / 100), 2)

    def test_returns_correct_result_for_very_large_price(self):
        assert calculate_discount(1_000_000.00, 25) == 750_000.00


# ── Phase 3: Gap Tests – calculate_total ─────────────────────────────────────────

class TestCalculateTotal:
    def test_returns_correct_item_count_for_single_item_with_quantity_three(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 3}]
        result = calculate_total(items)
        assert result["item_count"] == 3

    def test_returns_correct_tax_for_single_item(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items)
        assert result["tax"] == 2.1

    def test_returns_correct_subtotal_for_multiple_items(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 4},
        ]
        result = calculate_total(items)
        assert result["subtotal"] == 40.0

    def test_returns_correct_total_for_multiple_items_with_default_tax(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 4},
        ]
        # subtotal=40, tax=40*0.21=8.40, total=48.40
        result = calculate_total(items)
        assert result["total"] == 48.40

    def test_returns_correct_item_count_for_multiple_items(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 4},
        ]
        result = calculate_total(items)
        assert result["item_count"] == 6

    def test_applies_discount_to_item_price_before_totalling(self):
        items = [{"name": "Widget", "price": 100.0, "quantity": 1, "discount": 10}]
        # discounted price = 90, tax = 90 * 0.21 = 18.9, total = 108.9
        result = calculate_total(items)
        assert result["subtotal"] == 90.0
        assert result["tax"] == 18.9
        assert result["total"] == 108.9

    def test_returns_zero_values_when_items_list_is_empty(self):
        result = calculate_total([])
        assert result["subtotal"] == 0.0
        assert result["tax"] == 0.0
        assert result["total"] == 0.0
        assert result["item_count"] == 0

    def test_returns_correct_totals_when_tax_rate_is_zero(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.0)
        assert result["subtotal"] == 10.0
        assert result["tax"] == 0.0
        assert result["total"] == 10.0

    def test_returns_correct_totals_for_custom_tax_rate(self):
        items = [{"name": "Widget", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.10)
        assert result["subtotal"] == 100.0
        assert result["tax"] == 10.0
        assert result["total"] == 110.0

    def test_returns_correct_subtotal_when_item_has_zero_discount_explicitly(self):
        items = [{"name": "Widget", "price": 50.0, "quantity": 2, "discount": 0}]
        result = calculate_total(items)
        assert result["subtotal"] == 100.0

    def test_returns_zero_subtotal_when_item_has_full_100_percent_discount(self):
        items = [{"name": "Widget", "price": 50.0, "quantity": 2, "discount": 100}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["tax"] == 0.0
        assert result["total"] == 0.0

    def test_uses_zero_discount_when_discount_key_is_absent(self):
        item_without_discount = {"name": "Widget", "price": 10.0, "quantity": 1}
        item_with_zero_discount = {"name": "Widget", "price": 10.0, "quantity": 1, "discount": 0}
        result_no_key = calculate_total([item_without_discount])
        result_zero = calculate_total([item_with_zero_discount])
        assert result_no_key["subtotal"] == result_zero["subtotal"]

    def test_returns_dict_with_exactly_four_expected_keys(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items)
        assert set(result.keys()) == {"subtotal", "tax", "total", "item_count"}


# ── Phase 3: Gap Tests – format_price ────────────────────────────────────────────

class TestFormatPrice:
    def test_formats_usd_with_dollar_symbol(self):
        assert format_price(10.5, "USD") == "$10.50"

    def test_formats_gbp_with_pound_symbol(self):
        assert format_price(10.5, "GBP") == "£10.50"

    def test_uses_currency_code_as_prefix_for_unknown_currency(self):
        assert format_price(10.5, "JPY") == "JPY10.50"

    def test_formats_zero_amount(self):
        assert format_price(0.0) == "€0.00"

    def test_formats_negative_amount_with_negative_sign(self):
        assert format_price(-5.0) == "€-5.00"

    def test_formats_large_amount_without_separators(self):
        assert format_price(1_000_000.0) == "€1000000.00"

    def test_rounds_display_to_two_decimal_places(self):
        assert format_price(10.999) == "€11.00"

    def test_formats_whole_number_amount_with_two_decimal_zeros(self):
        assert format_price(100.0) == "€100.00"


# ── Phase 3: Gap Tests – apply_coupon ────────────────────────────────────────────

class TestApplyCoupon:
    def test_applies_percent_coupon_correctly(self):
        coupon = {"type": "percent", "value": 10}
        assert apply_coupon(100.0, coupon) == 90.0

    def test_applies_fixed_coupon_correctly(self):
        coupon = {"type": "fixed", "value": 15.0}
        assert apply_coupon(100.0, coupon) == 85.0

    def test_returns_total_unchanged_when_coupon_type_is_unknown(self):
        coupon = {"type": "bogus", "value": 50}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_applies_percent_coupon_of_100_returns_zero(self):
        coupon = {"type": "percent", "value": 100}
        assert apply_coupon(100.0, coupon) == 0.0

    def test_applies_fixed_coupon_resulting_in_negative_total(self):
        # No guard against negative: 100 - 150 = -50
        coupon = {"type": "fixed", "value": 150.0}
        assert apply_coupon(100.0, coupon) == -50.0

    def test_applies_fixed_coupon_of_zero_leaves_total_unchanged(self):
        coupon = {"type": "fixed", "value": 0.0}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_applies_percent_coupon_of_zero_leaves_total_unchanged(self):
        coupon = {"type": "percent", "value": 0}
        assert apply_coupon(100.0, coupon) == 100.0

    def test_returns_rounded_result_for_percent_coupon_with_fractional_cents(self):
        # 99.99 with 33% off -> 99.99 - 32.9967 = 66.9933 -> 66.99
        coupon = {"type": "percent", "value": 33}
        assert apply_coupon(99.99, coupon) == 66.99

    def test_returns_rounded_result_for_fixed_coupon_with_fractional_value(self):
        coupon = {"type": "fixed", "value": 0.015}
        assert apply_coupon(10.0, coupon) == round(10.0 - 0.015, 2)


# ── Phase 3: Gap Tests – split_payment ───────────────────────────────────────────

class TestSplitPayment:
    def test_splits_total_evenly_into_three_equal_parts(self):
        result = split_payment(90.0, 3)
        assert result == [30.0, 30.0, 30.0]

    def test_returns_list_with_correct_number_of_parts(self):
        result = split_payment(100.0, 4)
        assert len(result) == 4

    def test_parts_sum_to_original_total_for_three_parts(self):
        result = split_payment(100.0, 3)
        assert round(sum(result), 2) == 100.0

    def test_last_part_absorbs_rounding_difference_when_not_evenly_divisible(self):
        # 10.00 / 3 = 3.333... -> per_part = 3.33, last = 3.34
        result = split_payment(10.0, 3)
        assert result[0] == 3.33
        assert result[1] == 3.33
        assert result[2] == 3.34

    def test_splits_into_one_part_returns_list_with_original_total(self):
        result = split_payment(99.99, 1)
        assert result == [99.99]

    def test_splits_into_two_equal_parts_for_even_amount(self):
        result = split_payment(100.0, 2)
        assert result == [50.0, 50.0]

    def test_parts_sum_to_total_for_large_number_of_splits(self):
        result = split_payment(100.0, 7)
        assert len(result) == 7
        assert round(sum(result), 2) == 100.0

    @pytest.mark.skip(reason="BUG")
    def test_raises_error_when_parts_is_zero_BUG(self):
        """
        BUG: split_payment raises ZeroDivisionError when parts=0 instead of a
        meaningful ValueError.

        ROOT CAUSE: No guard clause validates that `parts` is positive before the
        division `total / parts` on line 51 of price_calculator.py.

        CODE LOCATION: price_calculator.py:51
            per_part = round(total / parts, 2)

        MINIMAL REPRODUCTION:
            split_payment(100.0, 0)  # raises ZeroDivisionError

        PROPOSED FIX:
            if parts <= 0:
                raise ValueError(f"parts must be a positive integer, got {parts}")
            per_part = round(total / parts, 2)

        EXPECTED: raises ValueError("parts must be a positive integer, got 0")
        ACTUAL:   raises ZeroDivisionError: float division by zero
        """
        with pytest.raises(ValueError, match="parts must be a positive integer"):
            split_payment(100.0, 0)

    @pytest.mark.skip(reason="BUG")
    def test_raises_error_when_parts_is_negative_BUG(self):
        """
        BUG: split_payment raises IndexError when parts is negative because
        `[per_part] * negative_int` produces an empty list, and then `result[-1]`
        fails with IndexError. No meaningful error is reported.

        ROOT CAUSE: No validation of the `parts` parameter.

        CODE LOCATION: price_calculator.py:52-54
            result = [per_part] * parts   # empty list when parts < 0
            diff = round(total - sum(result), 2)
            result[-1] = round(result[-1] + diff, 2)  # IndexError: list index out of range

        MINIMAL REPRODUCTION:
            split_payment(100.0, -3)  # raises IndexError

        PROPOSED FIX:
            if parts <= 0:
                raise ValueError(f"parts must be a positive integer, got {parts}")

        EXPECTED: raises ValueError("parts must be a positive integer, got -3")
        ACTUAL:   raises IndexError: list assignment index out of range
        """
        with pytest.raises(ValueError, match="parts must be a positive integer"):
            split_payment(100.0, -3)


# ── Phase 4: Advanced Coverage – bugmagnet session 2026-04-26 ────────────────────

class TestBugmagnetSession20260426:

    # ── Numeric edge cases – calculate_discount ───────────────────────────────

    def test_calculate_discount_with_float_discount_percent(self):
        # 100 * 10.5% off -> 100 - 10.5 = 89.5
        assert calculate_discount(100.0, 10.5) == 89.5

    def test_calculate_discount_returns_zero_for_very_small_price_with_50_percent(self):
        # 0.001 * 50% = 0.0005 -> rounds to 0.0
        result = calculate_discount(0.001, 50)
        assert result == round(0.001 - (0.001 * 50 / 100), 2)

    def test_calculate_discount_handles_very_large_price(self):
        result = calculate_discount(999_999_999.99, 1)
        assert result == round(999_999_999.99 * 0.99, 2)

    def test_calculate_discount_with_scientific_notation_price(self):
        # 1e-2 = 0.01, 50% off -> 0.005 -> round to 0.01 (banker's) or 0.0
        result = calculate_discount(1e-2, 50)
        assert result == round(1e-2 - (1e-2 * 50 / 100), 2)

    # ── Currency / financial edge cases – format_price ────────────────────────

    def test_format_price_handles_very_large_amount(self):
        result = format_price(9_999_999_999.99)
        assert result == "€9999999999.99"

    def test_format_price_handles_very_small_nonzero_amount(self):
        assert format_price(0.01) == "€0.01"

    def test_format_price_unknown_currency_chf_uses_code_as_prefix(self):
        assert format_price(5.0, "CHF") == "CHF5.00"

    def test_format_price_with_empty_string_currency_shows_no_symbol(self):
        # symbols.get("", "") returns "" -> prefix is ""
        result = format_price(5.0, "")
        assert result == "5.00"

    # ── apply_coupon – extreme values and missing keys ────────────────────────

    def test_apply_coupon_percent_with_200_percent_results_in_negative_total(self):
        # 100 - (100 * 200/100) = 100 - 200 = -100
        coupon = {"type": "percent", "value": 200}
        assert apply_coupon(100.0, coupon) == -100.0

    def test_apply_coupon_fixed_on_zero_total_returns_negative(self):
        coupon = {"type": "fixed", "value": 10.0}
        assert apply_coupon(0.0, coupon) == -10.0

    def test_apply_coupon_percent_on_zero_total_returns_zero(self):
        coupon = {"type": "percent", "value": 50}
        assert apply_coupon(0.0, coupon) == 0.0

    @pytest.mark.skip(reason="BUG")
    def test_apply_coupon_raises_key_error_when_type_key_is_missing_BUG(self):
        """
        BUG: apply_coupon raises KeyError when coupon dict is missing the 'type' key
        instead of raising a meaningful ValueError or returning the total unchanged.

        ROOT CAUSE: Direct key access `coupon["type"]` on line 42 of price_calculator.py
        without any prior validation of the coupon structure.

        CODE LOCATION: price_calculator.py:42
            if coupon["type"] == "percent":

        MINIMAL REPRODUCTION:
            apply_coupon(100.0, {"value": 10})  # raises KeyError: 'type'

        PROPOSED FIX:
            coupon_type = coupon.get("type")
            if coupon_type is None:
                raise ValueError("coupon must have a 'type' key")
            if coupon_type == "percent":
                ...

        EXPECTED: raises ValueError with descriptive message, or returns total unchanged
        ACTUAL:   raises KeyError: 'type'
        """
        with pytest.raises(ValueError):
            apply_coupon(100.0, {"value": 10})

    @pytest.mark.skip(reason="BUG")
    def test_apply_coupon_raises_key_error_when_value_key_is_missing_BUG(self):
        """
        BUG: apply_coupon raises KeyError when coupon dict is missing the 'value' key
        instead of raising a meaningful ValueError.

        ROOT CAUSE: Direct key access `coupon["value"]` on lines 43/45 without validation.

        CODE LOCATION: price_calculator.py:43
            return round(total - (total * coupon["value"] / 100), 2)

        MINIMAL REPRODUCTION:
            apply_coupon(100.0, {"type": "percent"})  # raises KeyError: 'value'

        PROPOSED FIX:
            if "value" not in coupon:
                raise ValueError("coupon must have a 'value' key")

        EXPECTED: raises ValueError with descriptive message
        ACTUAL:   raises KeyError: 'value'
        """
        with pytest.raises(ValueError):
            apply_coupon(100.0, {"type": "percent"})

    # ── calculate_total – error paths and boundary cases ─────────────────────

    def test_calculate_total_raises_key_error_when_item_missing_price_key(self):
        items = [{"name": "Bad", "quantity": 1}]
        with pytest.raises(KeyError):
            calculate_total(items)

    def test_calculate_total_raises_key_error_when_item_missing_quantity_key(self):
        items = [{"name": "Bad", "price": 10.0}]
        with pytest.raises(KeyError):
            calculate_total(items)

    def test_calculate_total_documents_negative_subtotal_when_discount_exceeds_100_percent(self):
        """Documents actual behavior: >100% discount produces negative subtotal."""
        items = [{"name": "Widget", "price": 10.0, "quantity": 1, "discount": 200}]
        result = calculate_total(items)
        # price after 200% discount: 10 - 20 = -10; subtotal = -10
        assert result["subtotal"] == -10.0

    def test_calculate_total_with_100_items_returns_correct_item_count(self):
        items = [{"name": f"Item{i}", "price": 1.0, "quantity": 1} for i in range(100)]
        result = calculate_total(items)
        assert result["item_count"] == 100
        assert result["subtotal"] == 100.0

    # ── split_payment – additional edge cases ─────────────────────────────────

    def test_split_payment_all_parts_are_non_negative_for_positive_total(self):
        result = split_payment(100.0, 3)
        assert all(p >= 0 for p in result)

    def test_split_payment_sums_to_total_for_small_amount_and_three_parts(self):
        result = split_payment(0.10, 3)
        assert round(sum(result), 2) == 0.10

    def test_split_payment_returns_list_type(self):
        result = split_payment(100.0, 2)
        assert isinstance(result, list)

    def test_split_payment_parts_sum_to_total_for_six_parts(self):
        result = split_payment(10.0, 6)
        assert len(result) == 6
        assert round(sum(result), 2) == 10.0

    # ── Domain constraint violations ──────────────────────────────────────────

    @pytest.mark.skip(reason="BUG")
    def test_apply_coupon_does_not_produce_negative_total_for_oversized_fixed_coupon_BUG(self):
        """
        BUG: apply_coupon allows a fixed coupon to reduce the total below zero,
        which in an e-commerce context means the store owes the customer money.
        This violates the implicit domain constraint that a final price >= 0.

        ROOT CAUSE: No minimum-value guard (max(0, ...)) in the fixed coupon branch
        at line 45 of price_calculator.py.

        CODE LOCATION: price_calculator.py:45
            return round(total - coupon["value"], 2)

        MINIMAL REPRODUCTION:
            apply_coupon(10.0, {"type": "fixed", "value": 50.0})
            # Returns -40.0

        PROPOSED FIX:
            return max(0.0, round(total - coupon["value"], 2))

        EXPECTED: 0.0 (total clamped to zero)
        ACTUAL:   -40.0
        """
        result = apply_coupon(10.0, {"type": "fixed", "value": 50.0})
        assert result >= 0.0

    @pytest.mark.skip(reason="BUG")
    def test_calculate_total_total_is_non_negative_when_discount_exceeds_price_BUG(self):
        """
        BUG: calculate_total can return a negative total when item discounts exceed
        100%, violating the domain constraint that a cart total must be >= 0.

        ROOT CAUSE: No clamping of subtotal or total to zero after accumulation
        in price_calculator.py lines 14-20.

        CODE LOCATION: price_calculator.py:19-20
            total = round(subtotal + tax, 2)
            return {"subtotal": ..., "tax": ..., "total": total, ...}

        MINIMAL REPRODUCTION:
            calculate_total([{"name": "X", "price": 100.0, "quantity": 1, "discount": 150}])
            # total = round((-50) * 1.21, 2) = -60.5

        PROPOSED FIX:
            total = max(0.0, round(subtotal + tax, 2))

        EXPECTED: total >= 0.0
        ACTUAL:   total = -60.5
        """
        items = [{"name": "Widget", "price": 100.0, "quantity": 1, "discount": 150}]
        result = calculate_total(items)
        assert result["total"] >= 0.0

    # ── format_price – None currency documents behavior ───────────────────────

    def test_format_price_with_none_currency_uses_none_string_as_prefix(self):
        """Documents actual behavior: passing None as currency uses 'None' as symbol."""
        result = format_price(5.0, None)
        # symbols.get(None, None) returns None -> f"{None}5.00" = "None5.00"
        assert result == "None5.00"
