"""Comprehensive edge-case and bug-detection tests for order_processor.

Each test class covers a distinct concern. Tests are named to describe the
behaviour they assert, and comments call out the bug each test exposes.
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
    TAX_RATES,
    SHIPPING_RATES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _us_ca_address():
    return Address(country="US", region="CA", postal_code="90210")


def _eu_de_address():
    return Address(country="EU", region="DE", postal_code="10115")


def _unknown_address():
    return Address(country="XX", region="ZZ", postal_code="00000")


def _make_item(product_id="P1", name="Widget", unit_price=10.0, quantity=1,
               discount_type=None, discount_value=0.0):
    return OrderItem(
        product_id=product_id,
        name=name,
        unit_price=unit_price,
        quantity=quantity,
        discount_type=discount_type,
        discount_value=discount_value,
    )


def _make_order(items=None, discounts=None, customer_id="C001", address=None):
    return Order(
        items=items or [_make_item(unit_price=25.0, quantity=2)],
        customer_id=customer_id,
        shipping_address=address or _us_ca_address(),
        discounts=discounts or [],
    )


def _processor(stock=None):
    return OrderProcessor(Inventory(stock or {"P1": 100}))


# ===========================================================================
# Inventory
# ===========================================================================

class TestInventory:

    def test_check_availability_sufficient_stock(self):
        inv = Inventory({"P1": 5})
        errors = inv.check_availability([_make_item(quantity=5)])
        assert errors == []

    def test_check_availability_insufficient_stock(self):
        inv = Inventory({"P1": 2})
        errors = inv.check_availability([_make_item(quantity=3)])
        assert len(errors) == 1
        assert "Widget" in errors[0]

    def test_check_availability_zero_stock(self):
        inv = Inventory({})
        errors = inv.check_availability([_make_item(quantity=1)])
        assert len(errors) == 1

    def test_reserve_reduces_stock(self):
        inv = Inventory({"P1": 10})
        inv.reserve([_make_item(quantity=4)])
        assert inv.get_stock("P1") == 6

    def test_reserve_raises_when_insufficient(self):
        inv = Inventory({"P1": 2})
        with pytest.raises(ValueError, match="Insufficient stock"):
            inv.reserve([_make_item(quantity=5)])

    def test_reserve_exact_stock_succeeds(self):
        inv = Inventory({"P1": 3})
        inv.reserve([_make_item(quantity=3)])
        assert inv.get_stock("P1") == 0

    def test_release_restores_stock(self):
        inv = Inventory({"P1": 5})
        inv.reserve([_make_item(quantity=3)])
        inv.release([_make_item(quantity=3)])
        assert inv.get_stock("P1") == 5

    def test_release_for_unknown_product_starts_from_zero(self):
        """release() should handle products not initially in stock dict."""
        inv = Inventory({})
        inv.release([_make_item(product_id="NEW", quantity=2)])
        assert inv.get_stock("NEW") == 2

    def test_get_stock_unknown_product_returns_zero(self):
        inv = Inventory({})
        assert inv.get_stock("GHOST") == 0

    def test_check_availability_multiple_items_some_unavailable(self):
        inv = Inventory({"P1": 10, "P2": 1})
        items = [
            _make_item(product_id="P1", quantity=5),
            _make_item(product_id="P2", name="Gadget", quantity=3),
        ]
        errors = inv.check_availability(items)
        assert len(errors) == 1
        assert "Gadget" in errors[0]


# ===========================================================================
# PricingEngine — line totals
# ===========================================================================

class TestPricingEngineLineTotals:

    def test_simple_line_total(self):
        engine = PricingEngine()
        item = _make_item(unit_price=10.0, quantity=3)
        assert engine.calculate_line_total(item) == 30.0

    def test_percentage_discount_on_line(self):
        engine = PricingEngine()
        item = _make_item(unit_price=100.0, quantity=1,
                          discount_type=DiscountType.PERCENTAGE,
                          discount_value=20)
        assert engine.calculate_line_total(item) == 80.0

    def test_fixed_discount_on_line(self):
        engine = PricingEngine()
        item = _make_item(unit_price=50.0, quantity=2,
                          discount_type=DiscountType.FIXED,
                          discount_value=10.0)
        assert engine.calculate_line_total(item) == 90.0

    # BUG #1: quantity break uses '>' so exactly QUANTITY_BREAK_THRESHOLD
    # units does NOT receive the bulk discount.
    def test_quantity_break_exactly_at_threshold_does_not_discount(self):
        """
        BUG: QUANTITY_BREAK_THRESHOLD=10 but condition is quantity > 10,
        so ordering exactly 10 units yields no bulk discount.
        Expected (if fixed): 10 * 10 * 0.95 = 95.0
        Actual: 10 * 10 = 100.0
        """
        engine = PricingEngine()
        item = _make_item(unit_price=10.0, quantity=QUANTITY_BREAK_THRESHOLD)
        total = engine.calculate_line_total(item)
        # Current (buggy) behaviour — no discount at exactly the threshold
        assert total == 100.0  # documents the bug

    def test_quantity_break_above_threshold_applies_discount(self):
        engine = PricingEngine()
        item = _make_item(unit_price=10.0, quantity=QUANTITY_BREAK_THRESHOLD + 1)
        expected = round(10.0 * (QUANTITY_BREAK_THRESHOLD + 1) * (1 - QUANTITY_BREAK_DISCOUNT), 2)
        assert engine.calculate_line_total(item) == expected

    def test_quantity_break_one_below_threshold_no_discount(self):
        engine = PricingEngine()
        item = _make_item(unit_price=10.0, quantity=QUANTITY_BREAK_THRESHOLD - 1)
        assert engine.calculate_line_total(item) == 10.0 * (QUANTITY_BREAK_THRESHOLD - 1)

    def test_quantity_break_applies_before_percentage_discount(self):
        """Bulk discount should be applied first, then item-level percentage."""
        engine = PricingEngine()
        item = _make_item(unit_price=10.0, quantity=11,
                          discount_type=DiscountType.PERCENTAGE,
                          discount_value=10)
        # base = 110, after quantity break = 110 * 0.95 = 104.5
        # after 10% percentage = 104.5 * 0.90 = 94.05
        assert engine.calculate_line_total(item) == 94.05

    def test_fixed_discount_larger_than_base_gives_negative_line_total(self):
        """
        No guard prevents a fixed line discount exceeding the base price.
        Documents current behaviour (negative total allowed).
        """
        engine = PricingEngine()
        item = _make_item(unit_price=5.0, quantity=1,
                          discount_type=DiscountType.FIXED,
                          discount_value=100.0)
        total = engine.calculate_line_total(item)
        assert total < 0  # documents that no floor is applied

    def test_zero_unit_price_item(self):
        engine = PricingEngine()
        item = _make_item(unit_price=0.0, quantity=5)
        assert engine.calculate_line_total(item) == 0.0

    def test_fractional_unit_price_rounds_to_two_decimals(self):
        engine = PricingEngine()
        item = _make_item(unit_price=0.1, quantity=3)
        assert engine.calculate_line_total(item) == round(0.3, 2)


# ===========================================================================
# PricingEngine — subtotal
# ===========================================================================

class TestPricingEngineSubtotal:

    def test_single_item_subtotal(self):
        engine = PricingEngine()
        subtotal, line_items = engine.calculate_subtotal([
            _make_item(unit_price=10.0, quantity=2),
        ])
        assert subtotal == 20.0
        assert len(line_items) == 1

    def test_multiple_items_subtotal(self):
        engine = PricingEngine()
        subtotal, line_items = engine.calculate_subtotal([
            _make_item(product_id="P1", unit_price=10.0, quantity=2),
            _make_item(product_id="P2", name="Gadget", unit_price=5.0, quantity=4),
        ])
        assert subtotal == 40.0
        assert len(line_items) == 2

    def test_line_items_contain_expected_keys(self):
        engine = PricingEngine()
        _, line_items = engine.calculate_subtotal([_make_item()])
        assert set(line_items[0].keys()) == {
            "product_id", "name", "quantity", "unit_price", "line_total"
        }

    def test_empty_items_list_gives_zero_subtotal(self):
        engine = PricingEngine()
        subtotal, line_items = engine.calculate_subtotal([])
        assert subtotal == 0.0
        assert line_items == []


# ===========================================================================
# PricingEngine — discounts
# ===========================================================================

class TestPricingEngineDiscounts:

    def test_no_discounts_returns_original_subtotal(self):
        engine = PricingEngine()
        result, applied = engine.apply_discounts(100.0, [])
        assert result == 100.0
        assert applied == []

    def test_percentage_discount(self):
        engine = PricingEngine()
        d = Discount(code="D10", discount_type=DiscountType.PERCENTAGE, value=10)
        result, applied = engine.apply_discounts(100.0, [d])
        assert result == 90.0
        assert len(applied) == 1

    def test_fixed_discount(self):
        engine = PricingEngine()
        d = Discount(code="FLAT5", discount_type=DiscountType.FIXED, value=5.0)
        result, applied = engine.apply_discounts(100.0, [d])
        assert result == 95.0

    def test_minimum_order_not_met_skips_discount(self):
        engine = PricingEngine()
        d = Discount(code="VIP", discount_type=DiscountType.PERCENTAGE,
                     value=20, minimum_order=200.0)
        result, applied = engine.apply_discounts(100.0, [d])
        assert result == 100.0
        assert applied == []

    def test_minimum_order_exactly_met_applies_discount(self):
        engine = PricingEngine()
        d = Discount(code="VIP", discount_type=DiscountType.PERCENTAGE,
                     value=20, minimum_order=100.0)
        result, applied = engine.apply_discounts(100.0, [d])
        assert result == 80.0

    def test_stacked_discounts_apply_sequentially_on_running_total(self):
        """Second percentage discount is applied on already-reduced amount."""
        engine = PricingEngine()
        d1 = Discount(code="D10", discount_type=DiscountType.PERCENTAGE, value=10)
        d2 = Discount(code="D10B", discount_type=DiscountType.PERCENTAGE, value=10)
        result, applied = engine.apply_discounts(100.0, [d1, d2])
        # After d1: 90.0; after d2: 90 - 9 = 81.0
        assert result == 81.0
        assert len(applied) == 2

    # BUG #2: minimum_order guard uses original subtotal while discounts
    # stack on the running total. A second discount may qualify based on the
    # original subtotal even though the running total is already below minimum.
    def test_minimum_order_check_uses_original_subtotal_not_running_total(self):
        """
        BUG: The minimum_order eligibility check always compares against the
        original subtotal passed into apply_discounts, not the running
        'discounted' value. This means a second discount can still trigger
        when the current price has already dropped below its minimum_order.
        """
        engine = PricingEngine()
        d1 = Discount(code="FIRST", discount_type=DiscountType.FIXED, value=50.0)
        d2 = Discount(code="SECOND", discount_type=DiscountType.PERCENTAGE,
                      value=10, minimum_order=60.0)
        # subtotal=100: d1 brings running total to 50.0, but check is against 100 >= 60 → applies
        result, applied = engine.apply_discounts(100.0, [d1, d2])
        # Expected if check used running total (50 < 60): 50.0, 1 applied
        # Actual (current bug): 50 - 5 = 45.0, 2 applied
        assert len(applied) == 2  # documents the bug

    # BUG #3: fixed discount can produce a negative total — no floor enforced
    def test_fixed_discount_exceeding_subtotal_produces_negative_total(self):
        """
        BUG: No floor at 0 for fixed discounts. A large fixed discount code
        makes the post-discount amount negative, which then propagates to the
        final total.
        """
        engine = PricingEngine()
        d = Discount(code="BIGDEAL", discount_type=DiscountType.FIXED, value=200.0)
        result, applied = engine.apply_discounts(50.0, [d])
        assert result == -150.0  # documents the bug — should be 0.0

    def test_zero_value_percentage_discount(self):
        engine = PricingEngine()
        d = Discount(code="ZERO", discount_type=DiscountType.PERCENTAGE, value=0)
        result, _ = engine.apply_discounts(100.0, [d])
        assert result == 100.0

    def test_100_percent_discount_gives_zero(self):
        engine = PricingEngine()
        d = Discount(code="FREE", discount_type=DiscountType.PERCENTAGE, value=100)
        result, _ = engine.apply_discounts(100.0, [d])
        assert result == 0.0


# ===========================================================================
# PricingEngine — tax
# ===========================================================================

class TestPricingEngineTax:

    def test_known_region_tax_rate(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, Address("US", "CA", "90210"))
        assert tax == round(100.0 * TAX_RATES["US-CA"], 2)

    def test_zero_tax_region(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, Address("US", "OR", "97201"))
        assert tax == 0.0

    def test_unknown_region_defaults_to_zero_tax(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, _unknown_address())
        assert tax == 0.0

    def test_eu_tax_rates(self):
        engine = PricingEngine()
        for country_region, rate in TAX_RATES.items():
            country, region = country_region.split("-")
            tax = engine.calculate_tax(100.0, Address(country, region, "00000"))
            assert tax == round(100.0 * rate, 2)

    def test_tax_rounds_to_two_decimals(self):
        engine = PricingEngine()
        # 100.01 * 0.0725 = 7.250725 → rounds to 7.25
        tax = engine.calculate_tax(100.01, Address("US", "CA", "90210"))
        assert tax == round(100.01 * 0.0725, 2)


# ===========================================================================
# PricingEngine — shipping
# ===========================================================================

class TestPricingEngineShipping:

    def test_shipping_below_threshold(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(99.99, Address("US", "CA", "90210"))
        assert shipping == SHIPPING_RATES["US"]

    def test_free_shipping_at_threshold(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(FREE_SHIPPING_THRESHOLD, _us_ca_address())
        assert shipping == 0.0

    def test_free_shipping_above_threshold(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(FREE_SHIPPING_THRESHOLD + 0.01, _us_ca_address())
        assert shipping == 0.0

    def test_eu_shipping_rate(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(50.0, _eu_de_address())
        assert shipping == SHIPPING_RATES["EU"]

    def test_unknown_country_uses_default_rate(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(50.0, _unknown_address())
        assert shipping == 19.99

    def test_zero_subtotal_charges_shipping(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(0.0, _us_ca_address())
        assert shipping == SHIPPING_RATES["US"]


# ===========================================================================
# OrderProcessor — validate
# ===========================================================================

class TestOrderProcessorValidate:

    def test_valid_order_has_no_errors(self):
        processor = _processor({"P1": 10})
        errors = processor.validate(_make_order())
        assert errors == []

    def test_empty_items_is_invalid(self):
        processor = _processor()
        order = Order(items=[], customer_id="C001",
                      shipping_address=_us_ca_address())
        errors = processor.validate(order)
        assert any("at least one item" in e for e in errors)

    def test_zero_quantity_is_invalid(self):
        processor = _processor()
        order = _make_order(items=[_make_item(quantity=0)])
        errors = processor.validate(order)
        assert any("Invalid quantity" in e for e in errors)

    def test_negative_quantity_is_invalid(self):
        processor = _processor()
        order = _make_order(items=[_make_item(quantity=-1)])
        errors = processor.validate(order)
        assert any("Invalid quantity" in e for e in errors)

    def test_negative_unit_price_is_invalid(self):
        processor = _processor()
        order = _make_order(items=[_make_item(unit_price=-5.0)])
        errors = processor.validate(order)
        assert any("Invalid price" in e for e in errors)

    # Note: zero unit_price is intentionally accepted (free items)
    def test_zero_unit_price_is_valid(self):
        processor = _processor({"P1": 10})
        order = _make_order(items=[_make_item(unit_price=0.0)])
        errors = processor.validate(order)
        assert not any("Invalid price" in e for e in errors)

    def test_missing_customer_id_is_invalid(self):
        processor = _processor()
        order = _make_order(customer_id="")
        errors = processor.validate(order)
        assert any("Customer ID" in e for e in errors)

    def test_insufficient_stock_reported_in_errors(self):
        processor = _processor({"P1": 0})
        errors = processor.validate(_make_order())
        assert len(errors) > 0

    def test_multiple_validation_errors_collected(self):
        processor = _processor({"P1": 0})
        order = Order(
            items=[_make_item(quantity=0)],
            customer_id="",
            shipping_address=_us_ca_address(),
        )
        errors = processor.validate(order)
        # Should contain at least: invalid quantity, missing customer ID, no stock
        assert len(errors) >= 2


# ===========================================================================
# OrderProcessor — process
# ===========================================================================

class TestOrderProcessorProcess:

    def test_process_returns_processed_order(self):
        processor = _processor({"P1": 10})
        result = processor.process(_make_order())
        assert isinstance(result, ProcessedOrder)

    def test_process_increments_order_id(self):
        processor = _processor({"P1": 20})
        r1 = processor.process(_make_order(items=[_make_item(quantity=1)]))
        r2 = processor.process(_make_order(items=[_make_item(quantity=1)]))
        assert r1.order_id == "ORD-000001"
        assert r2.order_id == "ORD-000002"

    def test_process_reserves_inventory(self):
        inv = Inventory({"P1": 5})
        processor = OrderProcessor(inv)
        processor.process(_make_order(items=[_make_item(quantity=3)]))
        assert inv.get_stock("P1") == 2

    def test_process_invalid_order_raises_value_error(self):
        processor = _processor({"P1": 0})
        with pytest.raises(ValueError, match="Invalid order"):
            processor.process(_make_order())

    def test_process_invalid_order_does_not_reserve_inventory(self):
        inv = Inventory({"P1": 0})
        processor = OrderProcessor(inv)
        with pytest.raises(ValueError):
            processor.process(_make_order())
        assert inv.get_stock("P1") == 0  # unchanged

    # BUG #4: tax is calculated on pre-discount subtotal instead of the
    # discounted amount. Customers pay more tax than they should.
    def test_tax_calculated_on_pre_discount_subtotal(self):
        """
        BUG: In process(), calculate_tax is called with `subtotal` (before
        discounts), not `discounted`. This inflates tax when discounts apply.

        Example:
          subtotal = 100.0, discount = 10%  → discounted = 90.0
          Correct tax (US-CA, 7.25%):  90.0 * 0.0725 = 6.53
          Actual (buggy) tax:          100.0 * 0.0725 = 7.25
        """
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        discount = Discount(code="D10", discount_type=DiscountType.PERCENTAGE,
                            value=10, minimum_order=0)
        # 4 x $25 = $100 subtotal, 10% discount → should be taxed on $90
        order = _make_order(
            items=[_make_item(unit_price=25.0, quantity=4)],
            discounts=[discount],
            address=Address("US", "CA", "90210"),
        )
        result = processor.process(order)
        tax_on_discounted = round(90.0 * TAX_RATES["US-CA"], 2)
        tax_on_original = round(100.0 * TAX_RATES["US-CA"], 2)
        # Current (buggy) behaviour: tax uses original subtotal
        assert result.tax == tax_on_original  # documents the bug
        # Proposed fix: assert result.tax == tax_on_discounted

    def test_process_free_shipping_when_subtotal_at_threshold(self):
        processor = _processor({"P1": 100})
        # unit_price=50, quantity=2 → subtotal=100 == FREE_SHIPPING_THRESHOLD
        order = _make_order(items=[_make_item(unit_price=50.0, quantity=2)])
        result = processor.process(order)
        assert result.shipping == 0.0

    def test_process_charging_shipping_below_threshold(self):
        processor = _processor({"P1": 10})
        order = _make_order(items=[_make_item(unit_price=10.0, quantity=1)])
        result = processor.process(order)
        assert result.shipping == SHIPPING_RATES["US"]

    def test_process_no_tax_for_zero_rate_region(self):
        processor = _processor({"P1": 10})
        order = _make_order(
            items=[_make_item(unit_price=50.0, quantity=2)],
            address=Address("US", "OR", "97201"),
        )
        result = processor.process(order)
        assert result.tax == 0.0

    def test_process_discount_total_equals_subtotal_minus_discounted(self):
        processor = _processor({"P1": 10})
        discount = Discount(code="D20", discount_type=DiscountType.PERCENTAGE, value=20)
        order = _make_order(
            items=[_make_item(unit_price=50.0, quantity=2)],
            discounts=[discount],
        )
        result = processor.process(order)
        assert result.discount_total == round(result.subtotal - (result.subtotal * 0.80), 2)

    def test_process_total_components_are_consistent(self):
        """total should equal discounted subtotal + tax + shipping."""
        processor = _processor({"P1": 10})
        result = processor.process(_make_order(items=[_make_item(unit_price=30.0, quantity=2)]))
        expected_total = round(
            (result.subtotal - result.discount_total) + result.tax + result.shipping,
            2
        )
        assert result.total == expected_total

    def test_process_with_eu_address_uses_eu_tax_and_shipping(self):
        processor = _processor({"P1": 10})
        order = _make_order(
            items=[_make_item(unit_price=10.0, quantity=2)],
            address=_eu_de_address(),
        )
        result = processor.process(order)
        assert result.shipping == SHIPPING_RATES["EU"]
        assert result.tax == round(20.0 * TAX_RATES["EU-DE"], 2)


# ===========================================================================
# OrderProcessor — process_batch
# ===========================================================================

class TestOrderProcessorProcessBatch:

    def test_all_valid_orders_processed(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        orders = [_make_order(items=[_make_item(quantity=1)]) for _ in range(3)]
        results = processor.process_batch(orders)
        assert len(results) == 3
        assert all(isinstance(r, ProcessedOrder) for r in results)

    def test_invalid_order_in_batch_returns_error_dict(self):
        inv = Inventory({"P1": 0})
        processor = OrderProcessor(inv)
        results = processor.process_batch([_make_order()])
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert "error" in results[0]
        assert results[0]["customer_id"] == "C001"

    def test_batch_partial_failure_continues_processing(self):
        inv = Inventory({"P1": 1, "P2": 10})
        processor = OrderProcessor(inv)
        order_ok = _make_order(items=[_make_item(product_id="P2", quantity=1)])
        order_bad = _make_order(
            customer_id="C002",
            items=[_make_item(product_id="P1", quantity=5)]
        )
        results = processor.process_batch([order_bad, order_ok])
        assert isinstance(results[0], dict)
        assert isinstance(results[1], ProcessedOrder)

    def test_batch_reserves_inventory_for_successful_orders(self):
        inv = Inventory({"P1": 5})
        processor = OrderProcessor(inv)
        order = _make_order(items=[_make_item(quantity=2)])
        processor.process_batch([order])
        assert inv.get_stock("P1") == 3

    def test_batch_does_not_reserve_inventory_for_failed_orders(self):
        inv = Inventory({"P1": 1})
        processor = OrderProcessor(inv)
        order_fail = _make_order(items=[_make_item(quantity=5)])
        processor.process_batch([order_fail])
        assert inv.get_stock("P1") == 1  # unchanged

    def test_empty_batch_returns_empty_list(self):
        processor = _processor()
        results = processor.process_batch([])
        assert results == []


# ===========================================================================
# OrderProcessor — loyalty points
# ===========================================================================

class TestLoyaltyPoints:

    def test_non_member_base_points(self):
        processor = _processor()
        assert processor.calculate_loyalty_points(150.0) == 150

    def test_member_doubles_points(self):
        processor = _processor()
        assert processor.calculate_loyalty_points(150.0, is_member=True) == 300

    def test_truncates_fractional_total(self):
        processor = _processor()
        assert processor.calculate_loyalty_points(99.9) == 99

    # BUG #5: for members, int() truncates BEFORE doubling, not after.
    # int(99.9) * 2 = 198, but int(99.9 * 2) = int(199.8) = 199.
    def test_member_truncation_order_discards_value(self):
        """
        BUG: calculate_loyalty_points truncates with int() before the member
        doubling multiplication. For a total of 99.9:
          Current:  int(99.9) * 2 = 198
          Expected: int(99.9 * 2) = 199  (if doubling should happen first)
        This means members silently lose up to 1 point per transaction.
        """
        processor = _processor()
        points = processor.calculate_loyalty_points(99.9, is_member=True)
        assert points == 198  # documents the bug (int(99.9) * 2 = 99 * 2)

    def test_zero_total_gives_zero_points(self):
        processor = _processor()
        assert processor.calculate_loyalty_points(0.0) == 0

    def test_negative_total_gives_negative_points(self):
        """Documents that no guard prevents negative points."""
        processor = _processor()
        points = processor.calculate_loyalty_points(-10.0)
        assert points == -10  # documents: no floor at 0


# ===========================================================================
# OrderProcessor — generate_invoice
# ===========================================================================

class TestGenerateInvoice:

    def _processed_order(self):
        processor = _processor({"P1": 10})
        return processor.process(_make_order(
            items=[_make_item(unit_price=25.0, quantity=2)],
        ))

    def test_invoice_contains_order_id(self):
        processed = self._processed_order()
        processor = _processor()
        invoice = processor.generate_invoice(processed)
        assert processed.order_id in invoice

    def test_invoice_contains_item_name(self):
        processed = self._processed_order()
        processor = _processor()
        invoice = processor.generate_invoice(processed)
        assert "Widget" in invoice

    def test_invoice_contains_subtotal(self):
        processed = self._processed_order()
        processor = _processor()
        invoice = processor.generate_invoice(processed)
        assert f"{processed.subtotal:.2f}" in invoice

    def test_invoice_contains_total(self):
        processed = self._processed_order()
        processor = _processor()
        invoice = processor.generate_invoice(processed)
        assert f"{processed.total:.2f}" in invoice

    def test_invoice_omits_discount_section_when_no_discount(self):
        processed = self._processed_order()
        processor = _processor()
        invoice = processor.generate_invoice(processed)
        assert "Discount" not in invoice

    def test_invoice_shows_discount_section_when_discount_applied(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        discount = Discount(code="D10", discount_type=DiscountType.PERCENTAGE, value=10)
        processed = processor.process(_make_order(
            items=[_make_item(unit_price=25.0, quantity=2)],
            discounts=[discount],
        ))
        invoice = processor.generate_invoice(processed)
        assert "Discount" in invoice
        assert "D10" in invoice

    def test_invoice_omits_shipping_line_when_free_shipping(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        # subtotal=100 triggers free shipping
        processed = processor.process(_make_order(
            items=[_make_item(unit_price=50.0, quantity=2)],
        ))
        invoice = processor.generate_invoice(processed)
        assert "Shipping" not in invoice

    def test_invoice_shows_shipping_line_when_charged(self):
        processor = _processor({"P1": 10})
        processed = processor.process(_make_order(
            items=[_make_item(unit_price=10.0, quantity=1)],
        ))
        invoice = processor.generate_invoice(processed)
        assert "Shipping" in invoice


# ===========================================================================
# OrderProcessor — apply_refund
# ===========================================================================

class TestApplyRefund:

    def _make_processed_two_items(self):
        inv = Inventory({"P1": 10, "P2": 10})
        processor = OrderProcessor(inv)
        order = Order(
            items=[
                _make_item(product_id="P1", name="Widget", unit_price=40.0, quantity=1),
                _make_item(product_id="P2", name="Gadget", unit_price=20.0, quantity=1),
            ],
            customer_id="C001",
            shipping_address=_us_ca_address(),
            discounts=[],
        )
        return processor, processor.process(order)

    def test_refund_reduces_subtotal(self):
        processor, processed = self._make_processed_two_items()
        refunded = processor.apply_refund(processed, ["P1"], _us_ca_address())
        assert refunded.subtotal < processed.subtotal

    def test_refund_removes_line_item(self):
        processor, processed = self._make_processed_two_items()
        refunded = processor.apply_refund(processed, ["P1"], _us_ca_address())
        ids = [i["product_id"] for i in refunded.line_items]
        assert "P1" not in ids
        assert "P2" in ids

    def test_refund_invalid_product_id_raises(self):
        processor, processed = self._make_processed_two_items()
        with pytest.raises(ValueError, match="No matching items found for refund"):
            processor.apply_refund(processed, ["NONEXISTENT"], _us_ca_address())

    def test_refund_order_id_has_suffix(self):
        processor, processed = self._make_processed_two_items()
        refunded = processor.apply_refund(processed, ["P1"], _us_ca_address())
        assert refunded.order_id == f"{processed.order_id}-R"

    def test_full_refund_all_items(self):
        processor, processed = self._make_processed_two_items()
        refunded = processor.apply_refund(processed, ["P1", "P2"], _us_ca_address())
        assert refunded.subtotal == 0.0
        assert refunded.line_items == []

    # BUG #6: apply_refund never calls inventory.release(), so stock is
    # permanently consumed even when items are refunded.
    def test_refund_does_not_restore_inventory(self):
        """
        BUG: apply_refund() does not call inventory.release() after processing
        a refund. The stock for refunded items is permanently consumed.
        After a full refund, P1 stock should be restored to 10 but remains 9.
        """
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        order = _make_order(items=[_make_item(product_id="P1", quantity=1)])
        processed = processor.process(order)
        assert inv.get_stock("P1") == 9  # reserved during process
        processor.apply_refund(processed, ["P1"], _us_ca_address())
        # BUG: stock is still 9 instead of being restored to 10
        assert inv.get_stock("P1") == 9  # documents the bug

    def test_refund_with_discount_proportionally_adjusts_discount(self):
        inv = Inventory({"P1": 10, "P2": 10})
        processor = OrderProcessor(inv)
        discount = Discount(code="D10", discount_type=DiscountType.PERCENTAGE, value=10)
        order = Order(
            items=[
                _make_item(product_id="P1", name="Widget", unit_price=60.0, quantity=1),
                _make_item(product_id="P2", name="Gadget", unit_price=40.0, quantity=1),
            ],
            customer_id="C001",
            shipping_address=_us_ca_address(),
            discounts=[discount],
        )
        processed = processor.process(order)
        # Refund P1 (60% of subtotal), so 60% of discount_total should be removed
        refunded = processor.apply_refund(processed, ["P1"], _us_ca_address())
        expected_new_discount = round(processed.discount_total * 0.40, 2)
        assert refunded.discount_total == expected_new_discount

    def test_refund_preserves_shipping(self):
        processor, processed = self._make_processed_two_items()
        refunded = processor.apply_refund(processed, ["P1"], _us_ca_address())
        assert refunded.shipping == processed.shipping


# ===========================================================================
# Boundary / integration scenarios
# ===========================================================================

class TestBoundaryAndIntegration:

    def test_order_with_single_item_at_quantity_break_boundary(self):
        """Order with exactly QUANTITY_BREAK_THRESHOLD units gets no bulk discount (off-by-one bug)."""
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        order = _make_order(items=[_make_item(unit_price=10.0, quantity=QUANTITY_BREAK_THRESHOLD)])
        result = processor.process(order)
        # No bulk discount applied at exactly the threshold (bug: should have been)
        assert result.subtotal == 10.0 * QUANTITY_BREAK_THRESHOLD

    def test_order_subtotal_exactly_at_free_shipping_threshold(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        order = _make_order(items=[_make_item(unit_price=FREE_SHIPPING_THRESHOLD, quantity=1)])
        result = processor.process(order)
        assert result.shipping == 0.0

    def test_order_subtotal_just_below_free_shipping_threshold(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        # unit_price=99.99 → subtotal=99.99 < 100.0
        order = _make_order(items=[_make_item(unit_price=99.99, quantity=1)])
        result = processor.process(order)
        assert result.shipping > 0.0

    def test_process_batch_order_counter_increments_across_batch(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        orders = [_make_order(items=[_make_item(quantity=1)]) for _ in range(5)]
        results = processor.process_batch(orders)
        order_ids = [r.order_id for r in results]
        assert order_ids == [
            "ORD-000001", "ORD-000002", "ORD-000003", "ORD-000004", "ORD-000005"
        ]

    def test_multiple_discount_codes_all_appear_in_applied_discounts(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        discounts = [
            Discount(code="CODE1", discount_type=DiscountType.PERCENTAGE, value=5),
            Discount(code="CODE2", discount_type=DiscountType.FIXED, value=2.0),
        ]
        order = _make_order(
            items=[_make_item(unit_price=50.0, quantity=2)],
            discounts=discounts,
        )
        result = processor.process(order)
        assert len(result.applied_discounts) == 2
        codes_in_output = " ".join(result.applied_discounts)
        assert "CODE1" in codes_in_output
        assert "CODE2" in codes_in_output

    def test_order_with_uk_address_uses_uk_shipping(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        order = _make_order(
            items=[_make_item(unit_price=10.0, quantity=1)],
            address=Address(country="UK", region="ENG", postal_code="SW1A1AA"),
        )
        result = processor.process(order)
        assert result.shipping == SHIPPING_RATES["UK"]

    def test_process_two_items_subtotal_is_sum_of_line_totals(self):
        inv = Inventory({"P1": 10, "P2": 10})
        processor = OrderProcessor(inv)
        order = Order(
            items=[
                _make_item(product_id="P1", unit_price=15.0, quantity=2),
                _make_item(product_id="P2", name="Gadget", unit_price=7.0, quantity=3),
            ],
            customer_id="C001",
            shipping_address=_us_ca_address(),
        )
        result = processor.process(order)
        assert result.subtotal == 30.0 + 21.0
