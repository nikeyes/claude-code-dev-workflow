"""BugMagnet session — order_processor.py (iteration-3).

Focuses on boundary values, compound interactions, and error paths
that were not covered in the baseline or prior sessions.
"""

import pytest

from order_processor import (
    Address,
    Discount,
    DiscountType,
    Inventory,
    Order,
    OrderItem,
    OrderProcessor,
    PricingEngine,
    ProcessedOrder,
    FREE_SHIPPING_THRESHOLD,
    QUANTITY_BREAK_THRESHOLD,
    QUANTITY_BREAK_DISCOUNT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _addr(country="US", region="CA", postal_code="90210"):
    return Address(country=country, region=region, postal_code=postal_code)


def _item(product_id="P1", name="Widget", unit_price=25.0, quantity=2,
          discount_type=None, discount_value=0.0):
    return OrderItem(
        product_id=product_id,
        name=name,
        unit_price=unit_price,
        quantity=quantity,
        discount_type=discount_type,
        discount_value=discount_value,
    )


def _order(items=None, customer_id="C001", address=None, discounts=None):
    return Order(
        items=items or [_item()],
        customer_id=customer_id,
        shipping_address=address or _addr(),
        discounts=discounts or [],
    )


def _processor(stock=None):
    return OrderProcessor(Inventory(stock if stock is not None else {"P1": 100}))


# ===========================================================================
# Inventory — edge cases
# ===========================================================================

class TestInventoryEdgeCases:

    def test_check_availability_returns_empty_list_for_empty_items(self):
        inv = Inventory({"P1": 5})
        assert inv.check_availability([]) == []

    def test_check_availability_returns_empty_when_stock_exactly_equals_request(self):
        inv = Inventory({"P1": 3})
        items = [_item(quantity=3)]
        assert inv.check_availability(items) == []

    def test_check_availability_reports_unavailable_when_stock_is_one_short(self):
        inv = Inventory({"P1": 2})
        items = [_item(quantity=3)]
        result = inv.check_availability(items)
        assert len(result) == 1
        assert "Widget" in result[0]

    def test_check_availability_reports_all_unavailable_items(self):
        inv = Inventory({"P1": 0, "P2": 0})
        items = [_item("P1", "Alpha", quantity=1), _item("P2", "Beta", quantity=1)]
        result = inv.check_availability(items)
        assert len(result) == 2

    def test_reserve_succeeds_when_stock_exactly_meets_request(self):
        inv = Inventory({"P1": 5})
        inv.reserve([_item(quantity=5)])
        assert inv.get_stock("P1") == 0

    def test_reserve_raises_when_stock_is_zero(self):
        inv = Inventory({"P1": 0})
        with pytest.raises(ValueError, match="Insufficient stock"):
            inv.reserve([_item(quantity=1)])

    def test_reserve_raises_for_unknown_product(self):
        """Product not in inventory has effective stock of 0."""
        inv = Inventory({})
        with pytest.raises(ValueError, match="Insufficient stock"):
            inv.reserve([_item("UNKNOWN", quantity=1)])

    def test_release_on_unknown_product_creates_positive_stock_entry(self):
        """Releasing stock for an unknown product silently creates it."""
        inv = Inventory({})
        inv.release([_item("NEW", quantity=7)])
        assert inv.get_stock("NEW") == 7

    def test_reserve_then_release_returns_to_original_stock(self):
        inv = Inventory({"P1": 10})
        items = [_item(quantity=4)]
        inv.reserve(items)
        inv.release(items)
        assert inv.get_stock("P1") == 10

    def test_multiple_reserves_deplete_stock_sequentially(self):
        inv = Inventory({"P1": 10})
        inv.reserve([_item(quantity=3)])
        inv.reserve([_item(quantity=3)])
        assert inv.get_stock("P1") == 4


# ===========================================================================
# PricingEngine — calculate_line_total
# ===========================================================================

class TestLineTotalEdgeCases:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_line_total_is_zero_for_zero_unit_price(self):
        assert self.engine.calculate_line_total(_item(unit_price=0.0, quantity=5)) == 0.0

    def test_line_total_is_zero_for_zero_quantity_and_nonzero_price(self):
        """quantity=0 is technically invalid but the engine still computes 0."""
        assert self.engine.calculate_line_total(_item(unit_price=10.0, quantity=0)) == 0.0

    def test_quantity_break_threshold_is_exclusive_at_ten(self):
        """quantity == 10 must NOT trigger the 5% break."""
        item = _item(unit_price=10.0, quantity=QUANTITY_BREAK_THRESHOLD)
        assert self.engine.calculate_line_total(item) == 100.0

    def test_quantity_break_triggers_at_eleven(self):
        """quantity == 11 IS strictly greater than 10."""
        item = _item(unit_price=10.0, quantity=QUANTITY_BREAK_THRESHOLD + 1)
        expected = round(10.0 * 11 * (1 - QUANTITY_BREAK_DISCOUNT), 2)
        assert self.engine.calculate_line_total(item) == expected

    def test_percentage_discount_of_zero_leaves_total_unchanged(self):
        item = _item(unit_price=50.0, quantity=2,
                     discount_type=DiscountType.PERCENTAGE, discount_value=0.0)
        assert self.engine.calculate_line_total(item) == 100.0

    def test_percentage_discount_of_100_produces_zero_line_total(self):
        """100% off should yield 0."""
        item = _item(unit_price=50.0, quantity=1,
                     discount_type=DiscountType.PERCENTAGE, discount_value=100.0)
        assert self.engine.calculate_line_total(item) == 0.0

    @pytest.mark.skip(reason="BUG: percentage discount > 100 makes line total negative - BUG")
    def test_percentage_discount_over_100_does_not_produce_negative_line_total_BUG(self):
        """
        ROOT CAUSE: calculate_line_total does not guard against
        discount_value > 100 for DiscountType.PERCENTAGE. The formula
        base *= 1 - discount_value / 100 becomes negative when discount_value > 100.
        CODE LOCATION: order_processor.py:129
        PROPOSED FIX: Clamp discount_value to [0, 100] before applying, or validate
        at the OrderItem construction / validation stage.
        EXPECTED: line_total >= 0 for any discount_value
        ACTUAL: line_total = -50.0 when unit_price=50, quantity=1, discount_value=200
        """
        item = _item(unit_price=50.0, quantity=1,
                     discount_type=DiscountType.PERCENTAGE, discount_value=200.0)
        assert self.engine.calculate_line_total(item) >= 0.0

    def test_fixed_discount_of_zero_leaves_total_unchanged(self):
        item = _item(unit_price=30.0, quantity=2,
                     discount_type=DiscountType.FIXED, discount_value=0.0)
        assert self.engine.calculate_line_total(item) == 60.0

    @pytest.mark.skip(reason="BUG: fixed item discount larger than line total makes line total negative - BUG")
    def test_fixed_item_discount_larger_than_line_total_does_not_go_negative_BUG(self):
        """
        ROOT CAUSE: calculate_line_total subtracts the FIXED discount_value
        unconditionally. When discount_value > base there is no floor guard.
        CODE LOCATION: order_processor.py:131
        PROPOSED FIX: base = max(0.0, base - item.discount_value)
        EXPECTED: line_total >= 0 always
        ACTUAL: line_total = -40.0 when line base = 10.0 and discount_value = 50.0
        """
        item = _item(unit_price=10.0, quantity=1,
                     discount_type=DiscountType.FIXED, discount_value=50.0)
        assert self.engine.calculate_line_total(item) >= 0.0

    def test_quantity_break_applied_before_percentage_item_discount(self):
        """5% quantity break is applied first, then item-level percentage discount."""
        item = _item(unit_price=10.0, quantity=11,
                     discount_type=DiscountType.PERCENTAGE, discount_value=10.0)
        # base = 110 * 0.95 = 104.5 * 0.9 = 94.05
        assert self.engine.calculate_line_total(item) == 94.05

    def test_quantity_break_applied_before_fixed_item_discount(self):
        """5% quantity break reduces base before fixed discount is subtracted."""
        item = _item(unit_price=10.0, quantity=11,
                     discount_type=DiscountType.FIXED, discount_value=4.50)
        # base = 110 * 0.95 = 104.50 - 4.50 = 100.0
        assert self.engine.calculate_line_total(item) == 100.0

    def test_floating_point_rounding_to_two_decimal_places(self):
        """Result is rounded to 2 decimal places."""
        item = _item(unit_price=0.1, quantity=3)
        result = self.engine.calculate_line_total(item)
        assert result == round(result, 2)


# ===========================================================================
# PricingEngine — apply_discounts
# ===========================================================================

class TestApplyDiscountsEdgeCases:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_no_discounts_returns_original_subtotal_unchanged(self):
        discounted, applied = self.engine.apply_discounts(75.0, [])
        assert discounted == 75.0
        assert applied == []

    def test_percentage_discount_applied_to_100_gives_correct_reduction(self):
        d = Discount(code="PCT20", discount_type=DiscountType.PERCENTAGE, value=20.0)
        discounted, applied = self.engine.apply_discounts(100.0, [d])
        assert discounted == 80.0
        assert applied == ["PCT20: -20.00"]

    def test_discount_skipped_when_subtotal_strictly_below_minimum_order(self):
        d = Discount(code="BIG", discount_type=DiscountType.PERCENTAGE,
                     value=10.0, minimum_order=100.01)
        discounted, applied = self.engine.apply_discounts(100.0, [d])
        assert discounted == 100.0
        assert applied == []

    def test_discount_applied_when_subtotal_equals_minimum_order(self):
        """Boundary: subtotal == minimum_order should apply the discount."""
        d = Discount(code="EXACT", discount_type=DiscountType.PERCENTAGE,
                     value=10.0, minimum_order=100.0)
        discounted, _ = self.engine.apply_discounts(100.0, [d])
        assert discounted == 90.0

    def test_minimum_order_check_uses_original_subtotal_not_running_discounted(self):
        """
        The minimum_order guard always compares against the original subtotal,
        not the running `discounted` value. A second discount whose minimum_order
        is met by the original subtotal but NOT the post-first-discount amount
        is still applied.
        """
        # After D1 (fixed 40): discounted drops from 100 to 60.
        # D2 minimum_order=80 — the running total (60) does NOT meet it,
        # but the original subtotal (100) DOES, so D2 is applied.
        d1 = Discount(code="D1", discount_type=DiscountType.FIXED,
                      value=40.0, minimum_order=0.0)
        d2 = Discount(code="D2", discount_type=DiscountType.PERCENTAGE,
                      value=10.0, minimum_order=80.0)
        discounted, applied = self.engine.apply_discounts(100.0, [d1, d2])
        # D2 should be applied: 10% of 60 = 6 → discounted = 54
        assert "D2" in " ".join(applied)
        assert discounted == 54.0

    @pytest.mark.skip(reason="BUG: fixed order-level discount can push discounted amount negative - BUG")
    def test_fixed_discount_does_not_make_total_negative_BUG(self):
        """
        ROOT CAUSE: apply_discounts has no floor guard for DiscountType.FIXED.
        The line `discounted -= discount.value` can produce a negative result.
        CODE LOCATION: order_processor.py:171
        PROPOSED FIX: discounted = max(0.0, discounted - discount.value)
        EXPECTED: discounted >= 0 always
        ACTUAL: discounted = -100.0 when subtotal=50 and discount.value=150
        """
        d = Discount(code="HUGE", discount_type=DiscountType.FIXED,
                     value=150.0, minimum_order=0.0)
        discounted, _ = self.engine.apply_discounts(50.0, [d])
        assert discounted >= 0.0

    def test_percentage_discount_second_applied_to_already_reduced_amount(self):
        """Stacked percentage discounts compound on the running total."""
        d1 = Discount(code="D1", discount_type=DiscountType.PERCENTAGE, value=10.0)
        d2 = Discount(code="D2", discount_type=DiscountType.PERCENTAGE, value=10.0)
        discounted, applied = self.engine.apply_discounts(100.0, [d1, d2])
        # d1: reduction = 10.00 off 100 → 90; d2: reduction = 9.00 off 90 → 81
        assert discounted == 81.0
        assert len(applied) == 2

    def test_fixed_discount_on_exact_subtotal_results_in_zero(self):
        d = Discount(code="EXACT", discount_type=DiscountType.FIXED,
                     value=50.0, minimum_order=0.0)
        discounted, applied = self.engine.apply_discounts(50.0, [d])
        assert discounted == 0.0
        assert applied == ["EXACT: -50.00"]

    def test_applied_list_contains_formatted_code_and_amount(self):
        d = Discount(code="FLAT5", discount_type=DiscountType.FIXED, value=5.0)
        _, applied = self.engine.apply_discounts(50.0, [d])
        assert applied[0] == "FLAT5: -5.00"

    def test_zero_value_percentage_discount_has_no_effect(self):
        d = Discount(code="ZERO", discount_type=DiscountType.PERCENTAGE, value=0.0)
        discounted, applied = self.engine.apply_discounts(100.0, [d])
        assert discounted == 100.0
        # Applied list still records the coupon even if reduction is 0
        assert len(applied) == 1

    def test_zero_value_fixed_discount_has_no_monetary_effect(self):
        d = Discount(code="ZERO", discount_type=DiscountType.FIXED, value=0.0)
        discounted, applied = self.engine.apply_discounts(100.0, [d])
        assert discounted == 100.0


# ===========================================================================
# PricingEngine — tax calculation
# ===========================================================================

class TestTaxCalculation:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_us_california_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("US", "CA")) == 7.25

    def test_us_new_york_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("US", "NY")) == 8.0

    def test_us_texas_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("US", "TX")) == 6.25

    def test_us_oregon_zero_tax(self):
        assert self.engine.calculate_tax(100.0, _addr("US", "OR")) == 0.0

    def test_eu_spain_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("EU", "ES")) == 21.0

    def test_eu_germany_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("EU", "DE")) == 19.0

    def test_eu_france_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("EU", "FR")) == 20.0

    def test_eu_ireland_tax_rate(self):
        assert self.engine.calculate_tax(100.0, _addr("EU", "IE")) == 23.0

    def test_unknown_country_region_defaults_to_zero_tax(self):
        assert self.engine.calculate_tax(100.0, _addr("AU", "NSW")) == 0.0

    def test_tax_on_zero_amount_is_zero(self):
        assert self.engine.calculate_tax(0.0, _addr("US", "CA")) == 0.0

    def test_tax_result_rounded_to_two_decimal_places(self):
        """7.25% of 99.99 = 7.249275 → rounds to 7.25."""
        result = self.engine.calculate_tax(99.99, _addr("US", "CA"))
        assert result == round(result, 2)

    def test_tax_key_is_case_sensitive(self):
        """Country and region strings are used verbatim; lowercase won't match."""
        assert self.engine.calculate_tax(100.0, _addr("us", "ca")) == 0.0


# ===========================================================================
# PricingEngine — shipping calculation
# ===========================================================================

class TestShippingCalculation:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_shipping_free_at_exact_threshold(self):
        assert self.engine.calculate_shipping(FREE_SHIPPING_THRESHOLD, _addr("US")) == 0.0

    def test_shipping_free_above_threshold(self):
        assert self.engine.calculate_shipping(FREE_SHIPPING_THRESHOLD + 0.01, _addr("US")) == 0.0

    def test_shipping_charged_one_cent_below_threshold(self):
        subtotal = FREE_SHIPPING_THRESHOLD - 0.01
        assert self.engine.calculate_shipping(subtotal, _addr("US")) == 9.99

    def test_us_shipping_rate(self):
        assert self.engine.calculate_shipping(50.0, _addr("US")) == 9.99

    def test_eu_shipping_rate(self):
        assert self.engine.calculate_shipping(50.0, _addr("EU")) == 14.99

    def test_uk_shipping_rate(self):
        assert self.engine.calculate_shipping(50.0, _addr("UK")) == 12.99

    def test_unknown_country_uses_default_rate(self):
        """Default rate for unknown countries is 19.99."""
        assert self.engine.calculate_shipping(50.0, _addr("AU")) == 19.99

    def test_shipping_based_on_subtotal_not_discounted_amount(self):
        """
        calculate_shipping receives the raw subtotal (before order-level discounts).
        Document this: even if a coupon brings the effective total below the free
        threshold, the original subtotal determines whether shipping is free.
        This is the current behavior — not necessarily correct business logic.
        """
        # subtotal=110 → free shipping threshold met (no shipping charge)
        # If an order-level 20% discount were applied the effective total would
        # be 88, which is below 100, but shipping was already determined from subtotal.
        engine = PricingEngine()
        # Direct call: shipping is evaluated on the raw subtotal passed in
        assert engine.calculate_shipping(110.0, _addr("US")) == 0.0


# ===========================================================================
# OrderProcessor — validation
# ===========================================================================

class TestValidation:

    def test_empty_items_list_produces_error(self):
        p = _processor()
        errors = p.validate(_order(items=[]))
        assert "Order must contain at least one item" in errors

    def test_zero_quantity_item_produces_error(self):
        p = _processor({"P1": 10})
        errors = p.validate(_order(items=[_item(quantity=0)]))
        assert any("Invalid quantity" in e for e in errors)

    def test_negative_quantity_item_produces_error(self):
        p = _processor({"P1": 10})
        errors = p.validate(_order(items=[_item(quantity=-1)]))
        assert any("Invalid quantity" in e for e in errors)

    def test_negative_price_produces_error(self):
        p = _processor({"P1": 10})
        errors = p.validate(_order(items=[_item(unit_price=-0.01)]))
        assert any("Invalid price" in e for e in errors)

    def test_zero_price_is_valid(self):
        """Zero-price (free) items are allowed."""
        p = _processor({"P1": 10})
        errors = p.validate(_order(items=[_item(unit_price=0.0)]))
        assert not any("Invalid price" in e for e in errors)

    def test_empty_customer_id_produces_error(self):
        p = _processor()
        errors = p.validate(_order(customer_id=""))
        assert "Customer ID is required" in errors

    def test_out_of_stock_item_produces_error(self):
        p = _processor({"P1": 0})
        errors = p.validate(_order(items=[_item(quantity=1)]))
        assert len(errors) > 0
        assert any("Widget" in e for e in errors)

    def test_multiple_validation_errors_accumulate(self):
        p = _processor({"P1": 0})
        errors = p.validate(_order(
            items=[_item(unit_price=-1.0, quantity=-1)],
            customer_id="",
        ))
        # Expect at least: invalid price, invalid quantity, customer ID, out-of-stock
        assert len(errors) >= 3

    def test_validate_returns_empty_list_for_valid_order(self):
        p = _processor({"P1": 10})
        errors = p.validate(_order())
        assert errors == []

    def test_process_raises_value_error_when_validation_fails(self):
        p = _processor({"P1": 10})
        with pytest.raises(ValueError, match="Invalid order"):
            p.process(_order(customer_id=""))

    def test_inventory_not_reserved_when_validation_fails(self):
        inv = Inventory({"P1": 5})
        p = OrderProcessor(inv)
        with pytest.raises(ValueError):
            p.process(_order(customer_id=""))
        assert inv.get_stock("P1") == 5


# ===========================================================================
# OrderProcessor — process pipeline
# ===========================================================================

class TestProcessPipeline:

    def test_order_id_starts_at_ORD_000001(self):
        p = _processor()
        result = p.process(_order())
        assert result.order_id == "ORD-000001"

    def test_order_id_increments_per_instance(self):
        p = _processor({"P1": 100})
        r1 = p.process(_order())
        r2 = p.process(_order())
        assert r1.order_id == "ORD-000001"
        assert r2.order_id == "ORD-000002"

    def test_each_processor_instance_has_independent_counter(self):
        inv = Inventory({"P1": 100})
        p1 = OrderProcessor(inv)
        p2 = OrderProcessor(inv)
        assert p1.process(_order()).order_id == "ORD-000001"
        assert p2.process(_order()).order_id == "ORD-000001"

    def test_subtotal_matches_sum_of_line_totals(self):
        p = _processor({"P1": 5, "P2": 5})
        order = _order(items=[
            _item("P1", unit_price=10.0, quantity=2),
            _item("P2", "Gadget", unit_price=15.0, quantity=1),
        ])
        result = p.process(order)
        expected_subtotal = sum(li["line_total"] for li in result.line_items)
        assert result.subtotal == round(expected_subtotal, 2)

    def test_discount_total_equals_subtotal_minus_discounted_amount(self):
        p = _processor()
        d = Discount(code="SAVE10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        order = _order(discounts=[d])
        result = p.process(order)
        # subtotal=50, 10% off → discounted=45 → discount_total=5
        assert result.discount_total == 5.0

    def test_tax_is_calculated_on_pre_discount_subtotal(self):
        """
        Documents current behavior: tax is based on the original subtotal,
        not the post-discount amount. This is the actual (potentially incorrect)
        behavior.
        """
        p = _processor()
        d = Discount(code="SAVE10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        result = p.process(_order(discounts=[d]))
        # subtotal=50, CA rate 7.25% → 3.625 → 3.62 (not on discounted 45)
        assert result.tax == round(50.0 * 0.0725, 2)

    @pytest.mark.skip(reason="BUG: tax computed on pre-discount subtotal, not post-discount amount - BUG")
    def test_tax_should_be_calculated_on_post_discount_amount_BUG(self):
        """
        ROOT CAUSE: In OrderProcessor.process(), calculate_tax is called with
        `subtotal` (line 237) rather than `discounted`. Customers with coupons
        are over-charged on tax.
        CODE LOCATION: order_processor.py:237
        CURRENT CODE:
            tax = self.pricing.calculate_tax(subtotal, order.shipping_address)
        PROPOSED FIX:
            tax = self.pricing.calculate_tax(discounted, order.shipping_address)
        EXPECTED: tax = round(45.0 * 0.0725, 2) = 3.26  (post-discount subtotal)
        ACTUAL:   tax = round(50.0 * 0.0725, 2) = 3.62  (pre-discount subtotal)
        """
        p = _processor()
        d = Discount(code="SAVE10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        result = p.process(_order(discounts=[d]))
        assert result.tax == round(45.0 * 0.0725, 2)

    def test_shipping_determined_by_pre_discount_subtotal(self):
        """
        Shipping threshold is evaluated against raw subtotal, not the discounted
        amount. An order whose subtotal is 110 gets free shipping even if a coupon
        brings the payable amount below 100.
        """
        inv = Inventory({"P1": 10})
        p = OrderProcessor(inv)
        # subtotal = 110 → free shipping
        order = _order(
            items=[_item(unit_price=55.0, quantity=2)],
            discounts=[Discount(code="BIG", discount_type=DiscountType.FIXED, value=30.0)],
        )
        result = p.process(order)
        assert result.subtotal == 110.0
        assert result.shipping == 0.0

    def test_total_equals_discounted_plus_tax_plus_shipping(self):
        p = _processor()
        result = p.process(_order())
        expected = round(
            (result.subtotal - result.discount_total) + result.tax + result.shipping, 2
        )
        assert result.total == expected

    def test_inventory_decremented_after_successful_process(self):
        inv = Inventory({"P1": 10})
        p = OrderProcessor(inv)
        p.process(_order(items=[_item(quantity=3)]))
        assert inv.get_stock("P1") == 7

    def test_line_items_contain_required_keys(self):
        p = _processor()
        result = p.process(_order())
        for li in result.line_items:
            for key in ("product_id", "name", "quantity", "unit_price", "line_total"):
                assert key in li

    def test_applied_discounts_list_is_empty_when_no_discount(self):
        p = _processor()
        result = p.process(_order())
        assert result.applied_discounts == []

    def test_applied_discounts_list_contains_description_for_each_applied_discount(self):
        p = _processor()
        d1 = Discount(code="D1", discount_type=DiscountType.PERCENTAGE, value=5.0)
        d2 = Discount(code="D2", discount_type=DiscountType.FIXED, value=2.0)
        result = p.process(_order(discounts=[d1, d2]))
        assert len(result.applied_discounts) == 2


# ===========================================================================
# OrderProcessor — shipping on the overall pipeline
# ===========================================================================

class TestShippingInPipeline:

    def test_us_order_below_threshold_incurs_shipping_charge(self):
        p = _processor()
        # subtotal = 50 < 100
        result = p.process(_order())
        assert result.shipping == 9.99

    def test_us_order_at_threshold_is_free_shipping(self):
        p = _processor()
        order = _order(items=[_item(unit_price=50.0, quantity=2)])
        result = p.process(order)
        assert result.shipping == 0.0

    def test_eu_order_below_threshold_incurs_eu_shipping_rate(self):
        p = _processor()
        order = _order(address=_addr("EU", "DE"))
        result = p.process(order)
        assert result.shipping == 14.99

    def test_unknown_country_order_incurs_default_shipping_rate(self):
        p = _processor()
        order = _order(address=_addr("AU", "NSW"))
        result = p.process(order)
        assert result.shipping == 19.99


# ===========================================================================
# OrderProcessor — batch processing
# ===========================================================================

class TestBatchProcessing:

    def test_empty_batch_returns_empty_list(self):
        p = _processor()
        assert p.process_batch([]) == []

    def test_single_valid_order_in_batch(self):
        p = _processor({"P1": 10})
        results = p.process_batch([_order()])
        assert len(results) == 1
        assert isinstance(results[0], ProcessedOrder)

    def test_single_invalid_order_returns_error_dict(self):
        p = _processor()
        results = p.process_batch([_order(customer_id="")])
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert "error" in results[0]

    def test_error_dict_contains_customer_id(self):
        p = _processor()
        results = p.process_batch([_order(customer_id="BAD-CID")])
        assert results[0]["customer_id"] == "BAD-CID"

    def test_failed_order_does_not_stop_subsequent_orders(self):
        p = _processor({"P1": 100})
        orders = [_order(), _order(customer_id=""), _order()]
        results = p.process_batch(orders)
        assert len(results) == 3
        assert isinstance(results[0], ProcessedOrder)
        assert isinstance(results[1], dict)
        assert isinstance(results[2], ProcessedOrder)

    def test_order_ids_increment_through_batch_skipping_invalid(self):
        """
        Only successfully processed orders increment the counter.
        The failed order does not consume an order ID.
        """
        p = _processor({"P1": 100})
        results = p.process_batch([_order(), _order(customer_id=""), _order()])
        valid_results = [r for r in results if isinstance(r, ProcessedOrder)]
        assert valid_results[0].order_id == "ORD-000001"
        assert valid_results[1].order_id == "ORD-000002"

    def test_inventory_not_consumed_by_invalid_batch_order(self):
        inv = Inventory({"P1": 5})
        p = OrderProcessor(inv)
        p.process_batch([_order(customer_id=""), _order()])
        # Invalid order consumed no stock; valid order used 2
        assert inv.get_stock("P1") == 3


# ===========================================================================
# OrderProcessor — loyalty points
# ===========================================================================

class TestLoyaltyPoints:

    def test_non_member_base_points_equals_int_of_total(self):
        p = _processor()
        assert p.calculate_loyalty_points(49.99) == 49

    def test_member_gets_double_points(self):
        p = _processor()
        assert p.calculate_loyalty_points(50.0, is_member=True) == 100

    def test_zero_total_gives_zero_points(self):
        p = _processor()
        assert p.calculate_loyalty_points(0.0) == 0

    def test_zero_total_member_gives_zero_points(self):
        p = _processor()
        assert p.calculate_loyalty_points(0.0, is_member=True) == 0

    def test_fractional_total_is_truncated_not_rounded(self):
        """int() truncates toward zero; 99.99 → 99, not 100."""
        p = _processor()
        assert p.calculate_loyalty_points(99.99) == 99
        assert p.calculate_loyalty_points(99.01) == 99

    @pytest.mark.skip(reason="BUG: loyalty points for negative total returns negative points - BUG")
    def test_loyalty_points_not_negative_for_negative_total_BUG(self):
        """
        ROOT CAUSE: calculate_loyalty_points uses int(total) with no lower bound.
        A negative total (possible due to the fixed-discount bug that makes totals
        negative) yields negative loyalty points.
        CODE LOCATION: order_processor.py:274
        CURRENT CODE:
            base_points = int(total)
        PROPOSED FIX:
            base_points = max(0, int(total))
        EXPECTED: points >= 0 always
        ACTUAL: calculate_loyalty_points(-10.0) returns -10
        """
        p = _processor()
        assert p.calculate_loyalty_points(-10.0) >= 0


# ===========================================================================
# OrderProcessor — invoice generation
# ===========================================================================

class TestInvoiceGeneration:

    def _make_processed(self, **kwargs):
        defaults = dict(
            order_id="ORD-000001",
            subtotal=50.0,
            discount_total=0.0,
            tax=3.62,
            shipping=9.99,
            total=63.61,
            applied_discounts=[],
            line_items=[{
                "product_id": "P1",
                "name": "Widget",
                "quantity": 2,
                "unit_price": 25.0,
                "line_total": 50.0,
            }],
        )
        defaults.update(kwargs)
        return ProcessedOrder(**defaults)

    def test_invoice_contains_order_id(self):
        p = _processor()
        processed = self._make_processed()
        invoice = p.generate_invoice(processed)
        assert "ORD-000001" in invoice

    def test_invoice_contains_item_name(self):
        p = _processor()
        processed = self._make_processed()
        invoice = p.generate_invoice(processed)
        assert "Widget" in invoice

    def test_invoice_contains_line_total(self):
        p = _processor()
        processed = self._make_processed()
        invoice = p.generate_invoice(processed)
        assert "50.00" in invoice

    def test_invoice_omits_discount_line_when_no_discount(self):
        p = _processor()
        processed = self._make_processed(discount_total=0.0)
        invoice = p.generate_invoice(processed)
        assert "Discount" not in invoice

    def test_invoice_includes_discount_line_when_discount_positive(self):
        p = _processor()
        processed = self._make_processed(
            discount_total=5.0,
            applied_discounts=["SAVE10: -5.00"],
        )
        invoice = p.generate_invoice(processed)
        assert "Discount" in invoice
        assert "SAVE10" in invoice

    def test_invoice_omits_shipping_line_when_shipping_is_zero(self):
        p = _processor()
        processed = self._make_processed(shipping=0.0)
        invoice = p.generate_invoice(processed)
        assert "Shipping" not in invoice

    def test_invoice_includes_shipping_line_when_shipping_charged(self):
        p = _processor()
        processed = self._make_processed(shipping=9.99)
        invoice = p.generate_invoice(processed)
        assert "Shipping" in invoice

    def test_invoice_contains_total(self):
        p = _processor()
        processed = self._make_processed()
        invoice = p.generate_invoice(processed)
        assert "TOTAL" in invoice

    def test_invoice_contains_separator_lines(self):
        p = _processor()
        processed = self._make_processed()
        invoice = p.generate_invoice(processed)
        assert "-" * 50 in invoice

    def test_invoice_for_order_with_no_items_does_not_crash(self):
        """An empty line_items list should still produce a valid invoice string."""
        p = _processor()
        processed = self._make_processed(line_items=[])
        invoice = p.generate_invoice(processed)
        assert "ORD-000001" in invoice

    @pytest.mark.skip(reason="BUG: item name longer than 30 chars overflows format string layout - BUG")
    def test_invoice_does_not_misalign_for_long_product_name_BUG(self):
        """
        ROOT CAUSE: generate_invoice uses a fixed-width format specifier of 30
        characters for the product name (`{item['name']:30s}`). When a product
        name exceeds 30 characters Python does NOT truncate — it expands the
        field and breaks the column alignment for all subsequent fields.
        CODE LOCATION: order_processor.py:285-288
        CURRENT CODE:
            f"  {item['name']:30s} x{item['quantity']:3d}  ..."
        PROPOSED FIX: Truncate or wrap names longer than 30 chars:
            name_col = item['name'][:30]
            f"  {name_col:30s} x{item['quantity']:3d}  ..."
        EXPECTED: Each line is exactly 50 characters (or a fixed width)
        ACTUAL: Lines with long names exceed 50 characters and misalign columns
        """
        p = _processor()
        processed = self._make_processed(line_items=[{
            "product_id": "P1",
            "name": "A" * 40,  # 40-char name exceeds 30-char column
            "quantity": 1,
            "unit_price": 50.0,
            "line_total": 50.0,
        }])
        invoice = p.generate_invoice(processed)
        # Each item line should be <= 50 chars (the header separator width)
        for line in invoice.splitlines():
            if "A" * 10 in line:  # find the item line
                assert len(line) <= 52  # generous bound, still catches overflow


# ===========================================================================
# OrderProcessor — apply_refund
# ===========================================================================

class TestApplyRefund:

    def _setup_two_item_order(self, p1_price=30.0, p2_price=20.0, discount=None):
        inv = Inventory({"P1": 10, "P2": 10})
        p = OrderProcessor(inv)
        discounts = [discount] if discount else []
        order = Order(
            items=[
                _item("P1", "Widget", unit_price=p1_price, quantity=2),
                _item("P2", "Gadget", unit_price=p2_price, quantity=1),
            ],
            customer_id="C001",
            shipping_address=_addr(),
            discounts=discounts,
        )
        return p, p.process(order)

    def test_raises_when_no_product_matches_refund_ids(self):
        p, processed = self._setup_two_item_order()
        with pytest.raises(ValueError, match="No matching items found for refund"):
            p.apply_refund(processed, ["NONEXISTENT"], _addr())

    def test_refund_order_id_has_dash_r_suffix(self):
        p, processed = self._setup_two_item_order()
        refunded = p.apply_refund(processed, ["P2"], _addr())
        assert refunded.order_id == f"{processed.order_id}-R"

    def test_refunded_item_removed_from_line_items(self):
        p, processed = self._setup_two_item_order()
        refunded = p.apply_refund(processed, ["P2"], _addr())
        ids = [li["product_id"] for li in refunded.line_items]
        assert "P2" not in ids
        assert "P1" in ids

    def test_subtotal_reduced_by_refunded_item_line_total(self):
        # P1 line total = 30*2 = 60; P2 line total = 20*1 = 20; subtotal = 80
        p, processed = self._setup_two_item_order()
        refunded = p.apply_refund(processed, ["P2"], _addr())
        assert refunded.subtotal == 60.0

    def test_full_refund_of_all_items_gives_zero_subtotal(self):
        p, processed = self._setup_two_item_order()
        refunded = p.apply_refund(processed, ["P1", "P2"], _addr())
        assert refunded.subtotal == 0.0

    def test_shipping_carried_over_to_refund_order(self):
        p, processed = self._setup_two_item_order()
        refunded = p.apply_refund(processed, ["P2"], _addr())
        assert refunded.shipping == processed.shipping

    def test_applied_discounts_carried_over_to_refund_order(self):
        d = Discount(code="SAVE5", discount_type=DiscountType.PERCENTAGE, value=5.0)
        p, processed = self._setup_two_item_order(discount=d)
        refunded = p.apply_refund(processed, ["P2"], _addr())
        assert refunded.applied_discounts == processed.applied_discounts

    def test_discount_proportionally_reduced_on_partial_refund(self):
        """
        A 10% order-level discount on subtotal=80 gives discount_total=8.
        Refunding P2 (line_total=20, proportion=0.25) should reduce
        discount_total by 0.25 * 8 = 2 → new discount_total = 6.
        """
        d = Discount(code="FLAT10PCT", discount_type=DiscountType.PERCENTAGE, value=10.0)
        p, processed = self._setup_two_item_order(discount=d)
        refunded = p.apply_refund(processed, ["P2"], _addr())
        # proportion = 20 / 80 = 0.25; refund_discount = 0.25 * 8 = 2.0
        assert refunded.discount_total == round(processed.discount_total * (1 - 0.25), 2)

    def test_refund_id_can_chain_with_another_r_suffix(self):
        """Applying refund twice appends -R to an already-R-suffixed order ID."""
        p, processed = self._setup_two_item_order()
        refund1 = p.apply_refund(processed, ["P2"], _addr())
        refund2 = p.apply_refund(refund1, ["P1"], _addr())
        assert refund2.order_id == f"{processed.order_id}-R-R"

    @pytest.mark.skip(reason="BUG: full refund of all items leaves total as shipping-only (negative edge case with discounts) - BUG")
    def test_full_refund_with_order_discount_total_is_zero_BUG(self):
        """
        ROOT CAUSE: When all items are refunded (subtotal → 0), the
        new_total computation is:
            new_total = new_subtotal - new_discount + new_tax + shipping
                      = 0 - 0 + 0 + shipping
        So the 'remaining' order total equals the original shipping cost.
        This means a full refund still charges the customer for shipping —
        the shipping is never refunded. There is no special handling for
        the case where all items are removed.
        CODE LOCATION: order_processor.py:344-346
        PROPOSED FIX: If remaining_items is empty (full refund), set shipping=0
        or raise an error indicating full refunds should be handled differently.
        EXPECTED: total == 0 when all items are refunded
        ACTUAL: total == original_shipping_cost when all items are refunded (and shipping < 100 threshold)
        """
        p, processed = self._setup_two_item_order(p1_price=20.0, p2_price=20.0)
        # subtotal=80 < 100, so shipping was charged (9.99)
        refunded = p.apply_refund(processed, ["P1", "P2"], _addr())
        assert refunded.total == 0.0

    def test_refund_raises_for_empty_product_ids_list(self):
        """Passing an empty list to apply_refund should raise ValueError."""
        p, processed = self._setup_two_item_order()
        with pytest.raises(ValueError, match="No matching items found for refund"):
            p.apply_refund(processed, [], _addr())


# ===========================================================================
# Cross-cutting: discount + shipping interaction
# ===========================================================================

class TestDiscountShippingInteraction:

    def test_free_shipping_determined_before_discount_coupon_applied(self):
        """
        The pipeline computes subtotal first, uses it for shipping threshold,
        then applies order-level discounts. A subtotal just above 100 qualifies
        for free shipping even if a coupon would reduce the payable amount.
        """
        inv = Inventory({"P1": 10})
        p = OrderProcessor(inv)
        # subtotal = 2 * 55 = 110 → free shipping
        d = Discount(code="CUT50", discount_type=DiscountType.FIXED, value=50.0)
        order = _order(items=[_item(unit_price=55.0, quantity=2)], discounts=[d])
        result = p.process(order)
        assert result.shipping == 0.0
        # effective payable before tax = 110 - 50 = 60, but shipping is still 0

    def test_no_free_shipping_when_subtotal_is_just_below_threshold(self):
        inv = Inventory({"P1": 10})
        p = OrderProcessor(inv)
        # subtotal = 2 * 49.99 = 99.98 < 100 → shipping charged
        order = _order(items=[_item(unit_price=49.99, quantity=2)])
        result = p.process(order)
        assert result.shipping == 9.99
