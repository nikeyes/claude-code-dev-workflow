"""Tests for price_calculator — generated following bugmagnet skill workflow."""
import pytest
from price_calculator import (
    calculate_discount,
    calculate_total,
    format_price,
    apply_coupon,
    split_payment,
)


# =============================================================================
# Phase 3: Core functionality gaps (High Priority)
# =============================================================================

class TestCalculateDiscount:
    def test_returns_discounted_price_for_10_percent(self):
        assert calculate_discount(100, 10) == 90.0

    def test_returns_original_price_when_discount_is_zero(self):
        assert calculate_discount(50.0, 0) == 50.0

    def test_returns_zero_when_discount_is_100_percent(self):
        assert calculate_discount(100, 100) == 0.0

    def test_returns_negative_price_when_discount_exceeds_100(self):
        result = calculate_discount(100, 150)
        assert result == -50.0

    def test_returns_increased_price_when_discount_is_negative(self):
        result = calculate_discount(100, -10)
        assert result == 110.0

    def test_returns_zero_when_price_is_zero(self):
        assert calculate_discount(0, 50) == 0.0

    def test_returns_negative_result_for_negative_price(self):
        result = calculate_discount(-100, 10)
        assert result == -90.0

    def test_rounds_to_two_decimal_places(self):
        result = calculate_discount(10.0, 33.33)
        assert result == 6.67


class TestCalculateTotal:
    def test_returns_correct_total_for_single_item(self):
        items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
        result = calculate_total(items)
        assert result["subtotal"] == 10.0
        assert result["tax"] == 2.1
        assert result["total"] == 12.1
        assert result["item_count"] == 1

    def test_returns_zeros_for_empty_items_list(self):
        result = calculate_total([])
        assert result["subtotal"] == 0
        assert result["tax"] == 0
        assert result["total"] == 0
        assert result["item_count"] == 0

    def test_returns_correct_total_for_multiple_items(self):
        items = [
            {"name": "A", "price": 10.0, "quantity": 2},
            {"name": "B", "price": 5.0, "quantity": 3},
        ]
        result = calculate_total(items)
        assert result["subtotal"] == 35.0
        assert result["item_count"] == 5

    def test_applies_item_discount_before_summing(self):
        items = [{"name": "A", "price": 100.0, "quantity": 1, "discount": 10}]
        result = calculate_total(items)
        assert result["subtotal"] == 90.0

    def test_uses_custom_tax_rate(self):
        items = [{"name": "A", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=0.0)
        assert result["tax"] == 0.0
        assert result["total"] == 100.0

    def test_handles_negative_tax_rate(self):
        items = [{"name": "A", "price": 100.0, "quantity": 1}]
        result = calculate_total(items, tax_rate=-0.1)
        assert result["tax"] == -10.0
        assert result["total"] == 90.0

    def test_handles_large_quantity(self):
        items = [{"name": "A", "price": 0.01, "quantity": 10000}]
        result = calculate_total(items)
        assert result["subtotal"] == 100.0

    def test_handles_item_with_zero_price(self):
        items = [{"name": "Free", "price": 0.0, "quantity": 5}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["item_count"] == 5

    def test_handles_item_with_zero_quantity(self):
        items = [{"name": "A", "price": 10.0, "quantity": 0}]
        result = calculate_total(items)
        assert result["subtotal"] == 0.0
        assert result["item_count"] == 0


class TestFormatPrice:
    def test_formats_eur_with_symbol(self):
        assert format_price(10.5) == "€10.50"

    def test_formats_usd_with_symbol(self):
        assert format_price(10.5, "USD") == "$10.50"

    def test_formats_gbp_with_symbol(self):
        assert format_price(10.5, "GBP") == "£10.50"

    def test_uses_currency_code_for_unknown_currency(self):
        assert format_price(10.5, "JPY") == "JPY10.50"

    def test_formats_zero_amount(self):
        assert format_price(0) == "€0.00"

    def test_formats_negative_amount(self):
        assert format_price(-5.5) == "€-5.50"

    def test_formats_very_large_amount(self):
        assert format_price(1000000.99) == "€1000000.99"

    def test_rounds_to_two_decimal_places(self):
        assert format_price(10.999) == "€11.00"


class TestApplyCoupon:
    def test_applies_percent_coupon(self):
        assert apply_coupon(100.0, {"type": "percent", "value": 10}) == 90.0

    def test_applies_fixed_coupon(self):
        assert apply_coupon(100.0, {"type": "fixed", "value": 15}) == 85.0

    def test_returns_original_total_for_unknown_coupon_type(self):
        assert apply_coupon(100.0, {"type": "bogo", "value": 10}) == 100.0

    def test_returns_zero_for_100_percent_coupon(self):
        assert apply_coupon(100.0, {"type": "percent", "value": 100}) == 0.0

    @pytest.mark.skip(reason="BUG: apply_coupon produces negative total when fixed coupon exceeds total")
    def test_returns_negative_total_when_fixed_coupon_exceeds_total_BUG(self):
        """
        BUG: Fixed coupon larger than total produces negative result.

        ROOT CAUSE: No minimum-zero clamp in the fixed coupon branch.

        CODE LOCATION: price_calculator.py:45
        CURRENT CODE:
            return round(total - coupon["value"], 2)
        PROPOSED FIX:
            return max(round(total - coupon["value"], 2), 0)

        EXPECTED: 0.0
        ACTUAL: -50.0
        """
        result = apply_coupon(50.0, {"type": "fixed", "value": 100})
        assert result >= 0

    @pytest.mark.skip(reason="BUG: apply_coupon produces negative total when percent coupon exceeds 100")
    def test_returns_negative_total_when_percent_coupon_exceeds_100_BUG(self):
        """
        BUG: Percent coupon > 100% produces negative result.

        ROOT CAUSE: No upper bound validation on coupon percent value.

        CODE LOCATION: price_calculator.py:43
        CURRENT CODE:
            return round(total - (total * coupon["value"] / 100), 2)
        PROPOSED FIX:
            capped = min(coupon["value"], 100)
            return round(total - (total * capped / 100), 2)

        EXPECTED: 0.0
        ACTUAL: -50.0
        """
        result = apply_coupon(100.0, {"type": "percent", "value": 150})
        assert result >= 0

    def test_applies_coupon_to_zero_total(self):
        assert apply_coupon(0.0, {"type": "percent", "value": 50}) == 0.0
        assert apply_coupon(0.0, {"type": "fixed", "value": 10}) == -10.0

    def test_applies_zero_value_coupon(self):
        assert apply_coupon(100.0, {"type": "percent", "value": 0}) == 100.0
        assert apply_coupon(100.0, {"type": "fixed", "value": 0}) == 100.0


class TestSplitPayment:
    def test_splits_evenly_into_two_parts(self):
        result = split_payment(100.0, 2)
        assert result == [50.0, 50.0]

    def test_splits_into_three_parts_with_remainder(self):
        result = split_payment(100.0, 3)
        assert len(result) == 3
        assert sum(result) == pytest.approx(100.0)

    def test_splits_into_single_part(self):
        result = split_payment(100.0, 1)
        assert result == [100.0]

    @pytest.mark.skip(reason="BUG: split_payment(total, 0) raises ZeroDivisionError")
    def test_raises_error_for_zero_parts_BUG(self):
        """
        BUG: Dividing by zero parts raises unhandled ZeroDivisionError.

        ROOT CAUSE: No guard clause for parts <= 0.

        CODE LOCATION: price_calculator.py:51
        CURRENT CODE:
            per_part = round(total / parts, 2)
        PROPOSED FIX:
            if parts <= 0:
                raise ValueError("parts must be positive")
            per_part = round(total / parts, 2)

        EXPECTED: ValueError with descriptive message
        ACTUAL: ZeroDivisionError
        """
        with pytest.raises(ValueError):
            split_payment(100.0, 0)

    def test_handles_negative_total(self):
        result = split_payment(-100.0, 2)
        assert result == [-50.0, -50.0]

    def test_splits_very_small_total(self):
        result = split_payment(0.01, 3)
        assert len(result) == 3
        assert sum(result) == pytest.approx(0.01)

    def test_splits_zero_total(self):
        result = split_payment(0.0, 5)
        assert result == [0.0, 0.0, 0.0, 0.0, 0.0]

    def test_splits_into_many_parts(self):
        result = split_payment(1.00, 7)
        assert len(result) == 7
        assert sum(result) == pytest.approx(1.00)


# =============================================================================
# Phase 4: Advanced Coverage — Floating point and rounding
# =============================================================================

class TestFloatingPointEdgeCases:
    def test_discount_with_recurring_decimal(self):
        result = calculate_discount(10.0, 33.33)
        assert result == 6.67

    def test_total_accumulation_precision(self):
        items = [{"name": f"item{i}", "price": 0.1, "quantity": 1} for i in range(10)]
        result = calculate_total(items)
        assert result["subtotal"] == 1.0

    def test_split_payment_sums_to_exact_total(self):
        result = split_payment(99.99, 7)
        assert sum(result) == pytest.approx(99.99, abs=0.01)

    def test_format_price_with_many_decimals(self):
        assert format_price(1.005) == "€1.00" or format_price(1.005) == "€1.01"
