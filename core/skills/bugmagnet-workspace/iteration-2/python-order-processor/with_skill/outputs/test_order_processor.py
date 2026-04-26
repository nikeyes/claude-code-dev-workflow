"""Tests for order processor — baseline + comprehensive gap coverage + bugmagnet session."""

import pytest

from order_processor import (
    OrderItem,
    Discount,
    DiscountType,
    Address,
    Order,
    Inventory,
    OrderProcessor,
    PricingEngine,
    ProcessedOrder,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_address(country="US", region="CA", postal_code="90210"):
    return Address(country=country, region=region, postal_code=postal_code)


def _make_order(items=None, discounts=None, customer_id="C001", address=None):
    return Order(
        items=items or [
            OrderItem(product_id="P1", name="Widget", unit_price=25.0, quantity=2),
        ],
        customer_id=customer_id,
        shipping_address=address or _make_address(),
        discounts=discounts or [],
    )


def _make_processor(stock=None):
    if stock is None:
        stock = {"P1": 10}
    return OrderProcessor(Inventory(stock))


# ---------------------------------------------------------------------------
# Original baseline tests (kept intact)
# ---------------------------------------------------------------------------

def test_process_basic_order():
    inv = Inventory({"P1": 10})
    processor = OrderProcessor(inv)
    result = processor.process(_make_order())
    assert result.subtotal == 50.0
    assert result.total > 0


def test_validate_empty_order():
    inv = Inventory({})
    processor = OrderProcessor(inv)
    errors = processor.validate(
        Order(items=[], customer_id="C001",
              shipping_address=Address("US", "CA", "90210"))
    )
    assert "Order must contain at least one item" in errors


def test_percentage_discount_applied():
    inv = Inventory({"P1": 10})
    processor = OrderProcessor(inv)
    discount = Discount(
        code="SAVE10", discount_type=DiscountType.PERCENTAGE,
        value=10, minimum_order=0,
    )
    result = processor.process(_make_order(discounts=[discount]))
    assert result.discount_total > 0


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Validation
# ---------------------------------------------------------------------------

class TestValidation:

    def test_returns_error_when_quantity_is_zero(self):
        processor = _make_processor({"P1": 10})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=0),
        ])
        errors = processor.validate(order)
        assert any("Invalid quantity" in e for e in errors)

    def test_returns_error_when_quantity_is_negative(self):
        processor = _make_processor({"P1": 10})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=-3),
        ])
        errors = processor.validate(order)
        assert any("Invalid quantity" in e for e in errors)

    def test_returns_error_when_unit_price_is_negative(self):
        processor = _make_processor({"P1": 10})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=-5.0, quantity=1),
        ])
        errors = processor.validate(order)
        assert any("Invalid price" in e for e in errors)

    def test_returns_no_error_when_unit_price_is_zero(self):
        """Zero price is a valid free item — no error expected."""
        processor = _make_processor({"P1": 10})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Freebie", unit_price=0.0, quantity=1),
        ])
        errors = processor.validate(order)
        assert not any("Invalid price" in e for e in errors)

    def test_returns_error_when_customer_id_is_empty_string(self):
        processor = _make_processor()
        order = _make_order(customer_id="")
        errors = processor.validate(order)
        assert "Customer ID is required" in errors

    def test_returns_error_when_item_is_out_of_stock(self):
        processor = _make_processor({"P1": 1})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=5),
        ])
        errors = processor.validate(order)
        assert any("Widget" in e for e in errors)

    def test_returns_error_when_product_not_in_inventory(self):
        processor = _make_processor({})
        order = _make_order(items=[
            OrderItem(product_id="UNKNOWN", name="Ghost", unit_price=10.0, quantity=1),
        ])
        errors = processor.validate(order)
        assert any("Ghost" in e for e in errors)

    def test_returns_multiple_errors_for_multiple_invalid_items(self):
        processor = _make_processor({"P1": 10, "P2": 10})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=-1.0, quantity=0),
            OrderItem(product_id="P2", name="Gadget", unit_price=-5.0, quantity=-2),
        ])
        errors = processor.validate(order)
        assert len(errors) >= 2

    def test_raises_value_error_when_processing_invalid_order(self):
        processor = _make_processor({})
        order = _make_order(customer_id="")
        with pytest.raises(ValueError, match="Invalid order"):
            processor.process(order)


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — PricingEngine line totals
# ---------------------------------------------------------------------------

class TestPricingEngineLineTotals:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_returns_correct_line_total_without_discount(self):
        item = OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=3)
        assert self.engine.calculate_line_total(item) == 30.0

    def test_applies_percentage_discount_to_line_total(self):
        item = OrderItem(
            product_id="P1", name="Widget", unit_price=100.0, quantity=1,
            discount_type=DiscountType.PERCENTAGE, discount_value=20.0,
        )
        assert self.engine.calculate_line_total(item) == 80.0

    def test_applies_fixed_discount_to_line_total(self):
        item = OrderItem(
            product_id="P1", name="Widget", unit_price=100.0, quantity=1,
            discount_type=DiscountType.FIXED, discount_value=15.0,
        )
        assert self.engine.calculate_line_total(item) == 85.0

    def test_applies_quantity_break_discount_when_quantity_exceeds_threshold(self):
        """Quantity > 10 triggers 5% quantity break discount before item discounts."""
        item = OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=11)
        # base = 110.0 * (1 - 0.05) = 104.50
        assert self.engine.calculate_line_total(item) == 104.50

    def test_does_not_apply_quantity_break_discount_at_exact_threshold(self):
        """Quantity == 10 does NOT trigger the break (strictly > 10)."""
        item = OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=10)
        assert self.engine.calculate_line_total(item) == 100.0

    def test_applies_quantity_break_before_percentage_item_discount(self):
        """Quantity break and item percentage discount both apply."""
        item = OrderItem(
            product_id="P1", name="Widget", unit_price=10.0, quantity=11,
            discount_type=DiscountType.PERCENTAGE, discount_value=10.0,
        )
        # base = 110 * 0.95 = 104.50 * 0.90 = 94.05
        assert self.engine.calculate_line_total(item) == 94.05


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — PricingEngine apply_discounts
# ---------------------------------------------------------------------------

class TestApplyDiscounts:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_returns_original_subtotal_when_no_discounts(self):
        discounted, applied = self.engine.apply_discounts(100.0, [])
        assert discounted == 100.0
        assert applied == []

    def test_skips_discount_when_minimum_order_not_met(self):
        discount = Discount(
            code="BIG10", discount_type=DiscountType.PERCENTAGE,
            value=10.0, minimum_order=200.0,
        )
        discounted, applied = self.engine.apply_discounts(100.0, [discount])
        assert discounted == 100.0
        assert applied == []

    def test_applies_discount_when_subtotal_equals_minimum_order(self):
        """Boundary: subtotal exactly equal to minimum_order should apply discount."""
        discount = Discount(
            code="EXACT50", discount_type=DiscountType.PERCENTAGE,
            value=10.0, minimum_order=100.0,
        )
        discounted, applied = self.engine.apply_discounts(100.0, [discount])
        assert discounted == 90.0
        assert applied == ["EXACT50: -10.00"]

    def test_applies_fixed_discount_and_returns_applied_codes(self):
        discount = Discount(
            code="FLAT5", discount_type=DiscountType.FIXED,
            value=5.0, minimum_order=0.0,
        )
        discounted, applied = self.engine.apply_discounts(50.0, [discount])
        assert discounted == 45.0
        assert applied == ["FLAT5: -5.00"]

    def test_applies_multiple_discounts_in_sequence(self):
        """Second percentage discount is calculated on already-discounted amount."""
        d1 = Discount(code="D1", discount_type=DiscountType.PERCENTAGE, value=10.0)
        d2 = Discount(code="D2", discount_type=DiscountType.PERCENTAGE, value=10.0)
        discounted, applied = self.engine.apply_discounts(100.0, [d1, d2])
        # d1: 100 - 10 = 90; d2: 90 - 9 = 81
        assert discounted == 81.0
        assert len(applied) == 2

    def test_returns_negative_total_when_fixed_discount_exceeds_subtotal(self):
        """
        Fixed discount larger than subtotal produces a negative discounted value.
        This may be a domain bug — there is no guard against negative totals.
        """
        discount = Discount(
            code="HUGE", discount_type=DiscountType.FIXED,
            value=200.0, minimum_order=0.0,
        )
        discounted, applied = self.engine.apply_discounts(50.0, [discount])
        assert discounted == -150.0


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Tax calculation
# ---------------------------------------------------------------------------

class TestTaxCalculation:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_returns_correct_tax_for_us_california(self):
        address = _make_address(country="US", region="CA")
        assert self.engine.calculate_tax(100.0, address) == 7.25

    def test_returns_zero_tax_for_us_oregon(self):
        address = _make_address(country="US", region="OR")
        assert self.engine.calculate_tax(100.0, address) == 0.0

    def test_returns_correct_tax_for_eu_spain(self):
        address = _make_address(country="EU", region="ES")
        assert self.engine.calculate_tax(100.0, address) == 21.0

    def test_returns_zero_tax_for_unknown_region(self):
        """Regions not in TAX_RATES default to 0% tax."""
        address = _make_address(country="AU", region="NSW")
        assert self.engine.calculate_tax(100.0, address) == 0.0


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Shipping calculation
# ---------------------------------------------------------------------------

class TestShippingCalculation:

    def setup_method(self):
        self.engine = PricingEngine()

    def test_returns_free_shipping_when_subtotal_meets_threshold(self):
        address = _make_address(country="US")
        assert self.engine.calculate_shipping(100.0, address) == 0.0

    def test_returns_free_shipping_when_subtotal_exceeds_threshold(self):
        address = _make_address(country="US")
        assert self.engine.calculate_shipping(150.0, address) == 0.0

    def test_returns_us_rate_when_subtotal_below_threshold(self):
        address = _make_address(country="US")
        assert self.engine.calculate_shipping(50.0, address) == 9.99

    def test_returns_eu_rate_when_subtotal_below_threshold(self):
        address = _make_address(country="EU")
        assert self.engine.calculate_shipping(50.0, address) == 14.99

    def test_returns_uk_rate_when_subtotal_below_threshold(self):
        address = _make_address(country="UK")
        assert self.engine.calculate_shipping(50.0, address) == 12.99

    def test_returns_default_rate_for_unknown_country(self):
        """Countries not in SHIPPING_RATES fall back to 19.99."""
        address = _make_address(country="AU")
        assert self.engine.calculate_shipping(50.0, address) == 19.99

    def test_returns_shipping_cost_just_below_free_threshold(self):
        """Boundary: subtotal of 99.99 still charges shipping."""
        address = _make_address(country="US")
        assert self.engine.calculate_shipping(99.99, address) == 9.99


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — OrderProcessor.process full pipeline
# ---------------------------------------------------------------------------

class TestOrderProcessorPipeline:

    def test_returns_correct_order_id_format(self):
        processor = _make_processor()
        result = processor.process(_make_order())
        assert result.order_id == "ORD-000001"

    def test_increments_order_id_on_each_process_call(self):
        processor = _make_processor({"P1": 20})
        r1 = processor.process(_make_order())
        r2 = processor.process(_make_order())
        assert r1.order_id == "ORD-000001"
        assert r2.order_id == "ORD-000002"

    def test_reserves_inventory_after_successful_process(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        processor.process(_make_order())
        assert inv.get_stock("P1") == 8

    def test_does_not_reserve_inventory_when_order_is_invalid(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        invalid_order = _make_order(customer_id="")
        with pytest.raises(ValueError):
            processor.process(invalid_order)
        assert inv.get_stock("P1") == 10

    def test_calculates_tax_on_subtotal_not_discounted_amount(self):
        """
        Tax is applied to `subtotal` (pre-discount) in the current implementation.
        This documents the actual behaviour so changes are visible.
        """
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        # subtotal = 50.0; discount = 10% => discounted = 45.0
        # tax on subtotal (50.0) at 7.25% = 3.62
        discount = Discount(code="D10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        result = processor.process(_make_order(discounts=[discount]))
        assert result.tax == round(50.0 * 0.0725, 2)  # 3.62

    def test_returns_correct_full_total_with_tax_and_shipping(self):
        """subtotal=50, no discount, tax=3.62 (US-CA 7.25%), shipping=9.99 (US, <100)."""
        processor = _make_processor()
        result = processor.process(_make_order())
        assert result.subtotal == 50.0
        assert result.tax == 3.62
        assert result.shipping == 9.99
        assert result.total == round(50.0 + 3.62 + 9.99, 2)

    def test_returns_zero_shipping_when_subtotal_at_free_threshold(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=50.0, quantity=2),
        ])
        result = processor.process(order)
        assert result.shipping == 0.0

    def test_returns_correct_line_items_in_processed_order(self):
        processor = _make_processor()
        result = processor.process(_make_order())
        assert len(result.line_items) == 1
        assert result.line_items[0]["product_id"] == "P1"
        assert result.line_items[0]["name"] == "Widget"
        assert result.line_items[0]["quantity"] == 2
        assert result.line_items[0]["unit_price"] == 25.0
        assert result.line_items[0]["line_total"] == 50.0

    def test_returns_correct_discount_total_for_percentage_discount(self):
        processor = _make_processor()
        discount = Discount(code="SAVE10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        result = processor.process(_make_order(discounts=[discount]))
        assert result.discount_total == 5.0
        assert result.applied_discounts == ["SAVE10: -5.00"]


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Inventory
# ---------------------------------------------------------------------------

class TestInventory:

    def test_check_availability_returns_empty_when_all_in_stock(self):
        inv = Inventory({"P1": 5})
        items = [OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=3)]
        assert inv.check_availability(items) == []

    def test_check_availability_returns_message_when_insufficient_stock(self):
        inv = Inventory({"P1": 2})
        items = [OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=5)]
        result = inv.check_availability(items)
        assert len(result) == 1
        assert "Widget" in result[0]
        assert "requested 5" in result[0]
        assert "available 2" in result[0]

    def test_reserve_decrements_stock_correctly(self):
        inv = Inventory({"P1": 10})
        items = [OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=4)]
        inv.reserve(items)
        assert inv.get_stock("P1") == 6

    def test_reserve_raises_when_insufficient_stock(self):
        inv = Inventory({"P1": 2})
        items = [OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=5)]
        with pytest.raises(ValueError, match="Insufficient stock"):
            inv.reserve(items)

    def test_release_restores_stock(self):
        inv = Inventory({"P1": 10})
        items = [OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=4)]
        inv.reserve(items)
        inv.release(items)
        assert inv.get_stock("P1") == 10

    def test_release_adds_stock_even_for_unknown_product(self):
        """Release on unknown product creates an entry at the released quantity."""
        inv = Inventory({})
        items = [OrderItem(product_id="NEW", name="New", unit_price=10.0, quantity=3)]
        inv.release(items)
        assert inv.get_stock("NEW") == 3

    def test_get_stock_returns_zero_for_unknown_product(self):
        inv = Inventory({})
        assert inv.get_stock("NONEXISTENT") == 0


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Batch processing
# ---------------------------------------------------------------------------

class TestBatchProcessing:

    def test_returns_processed_order_for_valid_order(self):
        processor = _make_processor({"P1": 10})
        results = processor.process_batch([_make_order()])
        assert len(results) == 1
        assert isinstance(results[0], ProcessedOrder)

    def test_returns_error_dict_for_invalid_order(self):
        processor = _make_processor({"P1": 10})
        invalid = _make_order(customer_id="")
        results = processor.process_batch([invalid])
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert "error" in results[0]
        assert results[0]["customer_id"] == ""

    def test_processes_mix_of_valid_and_invalid_orders(self):
        processor = _make_processor({"P1": 10})
        valid = _make_order()
        invalid = _make_order(customer_id="")
        results = processor.process_batch([valid, invalid])
        assert len(results) == 2
        assert isinstance(results[0], ProcessedOrder)
        assert isinstance(results[1], dict)

    def test_returns_empty_list_for_empty_batch(self):
        processor = _make_processor()
        results = processor.process_batch([])
        assert results == []


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Loyalty points
# ---------------------------------------------------------------------------

class TestLoyaltyPoints:

    def test_returns_integer_floor_of_total_for_non_member(self):
        processor = _make_processor()
        assert processor.calculate_loyalty_points(49.99) == 49

    def test_returns_doubled_points_for_member(self):
        processor = _make_processor()
        assert processor.calculate_loyalty_points(50.0, is_member=True) == 100

    def test_returns_zero_points_for_zero_total(self):
        processor = _make_processor()
        assert processor.calculate_loyalty_points(0.0) == 0

    def test_returns_zero_points_for_zero_total_member(self):
        processor = _make_processor()
        assert processor.calculate_loyalty_points(0.0, is_member=True) == 0


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Invoice generation
# ---------------------------------------------------------------------------

class TestInvoiceGeneration:

    def test_invoice_contains_order_id(self):
        processor = _make_processor()
        result = processor.process(_make_order())
        invoice = processor.generate_invoice(result)
        assert "ORD-000001" in invoice

    def test_invoice_contains_item_name_and_line_total(self):
        processor = _make_processor()
        result = processor.process(_make_order())
        invoice = processor.generate_invoice(result)
        assert "Widget" in invoice
        assert "50.00" in invoice

    def test_invoice_omits_discount_section_when_no_discounts(self):
        processor = _make_processor()
        result = processor.process(_make_order())
        invoice = processor.generate_invoice(result)
        assert "Discount" not in invoice

    def test_invoice_includes_discount_section_when_discount_applied(self):
        processor = _make_processor()
        discount = Discount(code="SAVE10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        result = processor.process(_make_order(discounts=[discount]))
        invoice = processor.generate_invoice(result)
        assert "Discount" in invoice
        assert "SAVE10" in invoice

    def test_invoice_omits_shipping_line_when_shipping_is_free(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=50.0, quantity=2),
        ])
        result = processor.process(order)
        invoice = processor.generate_invoice(result)
        assert "Shipping" not in invoice


# ---------------------------------------------------------------------------
# Phase 3: Gap Tests — Refund
# ---------------------------------------------------------------------------

class TestApplyRefund:

    def _process_two_item_order(self):
        inv = Inventory({"P1": 10, "P2": 10})
        processor = OrderProcessor(inv)
        order = Order(
            items=[
                OrderItem(product_id="P1", name="Widget", unit_price=30.0, quantity=2),
                OrderItem(product_id="P2", name="Gadget", unit_price=20.0, quantity=1),
            ],
            customer_id="C001",
            shipping_address=_make_address(),
            discounts=[],
        )
        return processor, processor.process(order)

    def test_raises_when_product_id_not_in_order(self):
        processor, result = self._process_two_item_order()
        with pytest.raises(ValueError, match="No matching items found for refund"):
            processor.apply_refund(result, ["NONEXISTENT"], _make_address())

    def test_returns_order_with_refund_suffix_in_id(self):
        processor, result = self._process_two_item_order()
        refunded = processor.apply_refund(result, ["P2"], _make_address())
        assert refunded.order_id == f"{result.order_id}-R"

    def test_removes_refunded_item_from_line_items(self):
        processor, result = self._process_two_item_order()
        refunded = processor.apply_refund(result, ["P2"], _make_address())
        product_ids = [item["product_id"] for item in refunded.line_items]
        assert "P2" not in product_ids
        assert "P1" in product_ids

    def test_reduces_subtotal_by_refunded_item_line_total(self):
        processor, result = self._process_two_item_order()
        # P1 line total = 60, P2 line total = 20; subtotal = 80
        refunded = processor.apply_refund(result, ["P2"], _make_address())
        assert refunded.subtotal == 60.0

    def test_full_refund_of_all_items_produces_zero_subtotal(self):
        processor, result = self._process_two_item_order()
        refunded = processor.apply_refund(result, ["P1", "P2"], _make_address())
        assert refunded.subtotal == 0.0


# ===========================================================================
# Phase 4: Bugmagnet Session 2026-04-26
# ===========================================================================


class TestBugmagnetSession20260426:
    """Advanced edge cases discovered during exploratory bugmagnet session."""

    # --- Numeric edge cases ---

    def test_returns_correct_subtotal_for_single_item_with_quantity_one(self):
        processor = _make_processor({"P1": 10})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget", unit_price=9.99, quantity=1),
        ])
        result = processor.process(order)
        assert result.subtotal == 9.99

    def test_calculates_line_total_with_zero_unit_price(self):
        """Free items (unit_price=0) should produce line_total=0."""
        engine = PricingEngine()
        item = OrderItem(product_id="P1", name="Freebie", unit_price=0.0, quantity=5)
        assert engine.calculate_line_total(item) == 0.0

    def test_handles_very_large_order_total(self):
        """Stress test: 1000 items at high price."""
        inv = Inventory({"P1": 2000})
        processor = OrderProcessor(inv)
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Expensive", unit_price=9999.99, quantity=1000),
        ])
        result = processor.process(order)
        # quantity > 10 => 5% break: 9999999.0 * 0.95 = 9499999.05
        assert result.subtotal == 9499999.05

    def test_loyalty_points_truncates_fractional_total(self):
        """int() truncates toward zero — verify 99.99 becomes 99 not 100."""
        processor = _make_processor()
        assert processor.calculate_loyalty_points(99.99) == 99

    # --- Boundary: quantity break threshold ---

    def test_quantity_break_not_applied_at_threshold_minus_one(self):
        engine = PricingEngine()
        item = OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=9)
        assert engine.calculate_line_total(item) == 90.0

    def test_quantity_break_applied_at_threshold_plus_one(self):
        engine = PricingEngine()
        item = OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=11)
        assert engine.calculate_line_total(item) == 104.50

    # --- Boundary: free shipping threshold ---

    def test_shipping_not_free_at_threshold_minus_one_cent(self):
        engine = PricingEngine()
        address = _make_address(country="US")
        assert engine.calculate_shipping(99.99, address) == 9.99

    def test_shipping_is_free_at_exact_threshold(self):
        engine = PricingEngine()
        address = _make_address(country="US")
        assert engine.calculate_shipping(100.0, address) == 0.0

    # --- Tax calculation: EU regions ---

    def test_correct_tax_for_eu_germany(self):
        engine = PricingEngine()
        address = _make_address(country="EU", region="DE")
        assert engine.calculate_tax(100.0, address) == 19.0

    def test_correct_tax_for_eu_france(self):
        engine = PricingEngine()
        address = _make_address(country="EU", region="FR")
        assert engine.calculate_tax(100.0, address) == 20.0

    def test_correct_tax_for_eu_ireland(self):
        engine = PricingEngine()
        address = _make_address(country="EU", region="IE")
        assert engine.calculate_tax(100.0, address) == 23.0

    def test_correct_tax_for_us_new_york(self):
        engine = PricingEngine()
        address = _make_address(country="US", region="NY")
        assert engine.calculate_tax(100.0, address) == 8.0

    def test_correct_tax_for_us_texas(self):
        engine = PricingEngine()
        address = _make_address(country="US", region="TX")
        assert engine.calculate_tax(100.0, address) == 6.25

    # --- Violated domain constraints ---

    @pytest.mark.skip(reason="BUG: fixed discount can make total negative — no guard")
    def test_total_is_not_negative_when_fixed_discount_exceeds_subtotal_BUG(self):
        """
        BUG: No minimum-total guard in apply_discounts for FIXED type.

        ROOT CAUSE: apply_discounts subtracts fixed discount value without
        checking that the result stays >= 0.
        CODE LOCATION: order_processor.py:171
        CURRENT CODE:
            discounted -= discount.value
        PROPOSED FIX:
            discounted = max(0.0, discounted - discount.value)
        EXPECTED: total >= 0
        ACTUAL: total can be negative (e.g. -150.0 when discount=200 and subtotal=50)
        """
        engine = PricingEngine()
        discount = Discount(
            code="HUGE", discount_type=DiscountType.FIXED,
            value=200.0, minimum_order=0.0,
        )
        discounted, _ = engine.apply_discounts(50.0, [discount])
        assert discounted >= 0.0

    @pytest.mark.skip(reason="BUG: tax is calculated on pre-discount subtotal, not post-discount amount")
    def test_tax_is_calculated_on_post_discount_amount_BUG(self):
        """
        BUG: In OrderProcessor.process(), tax is calculated on subtotal
        (pre-discount) rather than on the discounted amount.

        ROOT CAUSE: calculate_tax is called with `subtotal` not `discounted`.
        CODE LOCATION: order_processor.py:237
        CURRENT CODE:
            tax = self.pricing.calculate_tax(subtotal, order.shipping_address)
        PROPOSED FIX:
            tax = self.pricing.calculate_tax(discounted, order.shipping_address)
        EXPECTED: tax = round(discounted_amount * tax_rate, 2)
        ACTUAL:   tax = round(subtotal * tax_rate, 2)  (over-charges tax after discounts)
        """
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        # subtotal=50, 10% off => discounted=45; tax should be on 45 not 50
        discount = Discount(code="D10", discount_type=DiscountType.PERCENTAGE, value=10.0)
        result = processor.process(_make_order(discounts=[discount]))
        # expected tax on discounted amount 45.0 at 7.25% = 3.26
        assert result.tax == round(45.0 * 0.0725, 2)

    def test_minimum_order_check_uses_original_subtotal_not_discounted(self):
        """
        Documents that minimum_order check compares against original `subtotal`,
        not the running `discounted` amount. Second discount's minimum check
        still sees the original subtotal.
        """
        engine = PricingEngine()
        d1 = Discount(code="D1", discount_type=DiscountType.FIXED, value=30.0, minimum_order=0.0)
        # After d1: discounted = 70. d2 requires minimum_order=80.
        # Since subtotal=100 >= 80, d2 IS applied even though discounted=70 < 80.
        d2 = Discount(code="D2", discount_type=DiscountType.PERCENTAGE, value=10.0, minimum_order=80.0)
        discounted, applied = engine.apply_discounts(100.0, [d1, d2])
        assert "D2" in " ".join(applied)

    # --- Stateful: order counter across multiple processors ---

    def test_each_processor_instance_has_independent_order_counter(self):
        inv = Inventory({"P1": 20})
        p1 = OrderProcessor(inv)
        p2 = OrderProcessor(inv)
        r1 = p1.process(_make_order())
        r2 = p2.process(_make_order())
        assert r1.order_id == "ORD-000001"
        assert r2.order_id == "ORD-000001"

    # --- Collection edge cases ---

    def test_process_order_with_single_item_of_quantity_one(self):
        processor = _make_processor({"P1": 5})
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Solo", unit_price=42.0, quantity=1),
        ])
        result = processor.process(order)
        assert result.line_items[0]["line_total"] == 42.0

    def test_process_order_with_many_items(self):
        stock = {f"P{i}": 100 for i in range(50)}
        inv = Inventory(stock)
        processor = OrderProcessor(inv)
        items = [
            OrderItem(product_id=f"P{i}", name=f"Item{i}", unit_price=1.0, quantity=1)
            for i in range(50)
        ]
        order = _make_order(items=items)
        result = processor.process(order)
        assert len(result.line_items) == 50
        assert result.subtotal == 50.0

    def test_check_availability_with_empty_items_list(self):
        inv = Inventory({"P1": 10})
        assert inv.check_availability([]) == []

    # --- Error conditions ---

    def test_validate_returns_error_for_each_out_of_stock_item(self):
        """Multiple out-of-stock items each produce their own error message."""
        inv = Inventory({"P1": 0, "P2": 0})
        processor = OrderProcessor(inv)
        order = Order(
            items=[
                OrderItem(product_id="P1", name="Widget", unit_price=10.0, quantity=1),
                OrderItem(product_id="P2", name="Gadget", unit_price=10.0, quantity=1),
            ],
            customer_id="C001",
            shipping_address=_make_address(),
            discounts=[],
        )
        errors = processor.validate(order)
        assert any("Widget" in e for e in errors)
        assert any("Gadget" in e for e in errors)

    def test_process_batch_does_not_stop_on_first_error(self):
        """A failing order in the middle of a batch does not halt processing."""
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        orders = [
            _make_order(),
            _make_order(customer_id=""),  # invalid
            _make_order(),
        ]
        results = processor.process_batch(orders)
        assert len(results) == 3
        assert isinstance(results[0], ProcessedOrder)
        assert isinstance(results[1], dict)
        assert isinstance(results[2], ProcessedOrder)

    # --- Refund edge cases ---

    @pytest.mark.skip(reason="BUG: refund proportion calculation breaks when subtotal is zero")
    def test_apply_refund_handles_zero_subtotal_without_division_by_zero_BUG(self):
        """
        BUG: apply_refund computes proportion = refund_subtotal / processed.subtotal.
        If subtotal is 0 the guard `if processed.subtotal` prevents ZeroDivisionError,
        but the proportion becomes 0, so no discount is refunded even if discount_total > 0.
        This is an unusual scenario but the guard produces silently wrong output.

        ROOT CAUSE: order_processor.py:330
        CURRENT CODE:
            proportion = refund_subtotal / processed.subtotal if processed.subtotal else 0
        PROPOSED FIX: Either raise a meaningful error, or handle via explicit test expectation.
        EXPECTED: proportion is meaningful or an error is raised
        ACTUAL: proportion silently becomes 0
        """
        # Construct a synthetic ProcessedOrder with subtotal=0 to trigger the guard
        processed = ProcessedOrder(
            order_id="ORD-000001",
            subtotal=0.0,
            discount_total=10.0,
            tax=0.0,
            shipping=0.0,
            total=0.0,
            applied_discounts=["D: -10.00"],
            line_items=[{"product_id": "P1", "name": "Widget",
                         "quantity": 1, "unit_price": 0.0, "line_total": 0.0}],
        )
        processor = _make_processor()
        refunded = processor.apply_refund(processed, ["P1"], _make_address())
        # With proportion=0, refund_discount=0, but full discount_total was on this item
        assert refunded.discount_total == 0.0

    def test_apply_refund_preserves_shipping_on_remaining_items(self):
        """Shipping cost from original order is preserved in the refunded order."""
        inv = Inventory({"P1": 10, "P2": 10})
        processor = OrderProcessor(inv)
        order = Order(
            items=[
                OrderItem(product_id="P1", name="Widget", unit_price=20.0, quantity=1),
                OrderItem(product_id="P2", name="Gadget", unit_price=20.0, quantity=1),
            ],
            customer_id="C001",
            shipping_address=_make_address(),
            discounts=[],
        )
        result = processor.process(order)
        refunded = processor.apply_refund(result, ["P2"], _make_address())
        assert refunded.shipping == result.shipping

    # --- Domain constraint: duplicate product IDs ---

    def test_processes_order_with_duplicate_product_ids(self):
        """
        Two line items with the same product_id. The second reserve call will
        see already-decremented stock. Documents actual behavior.
        """
        inv = Inventory({"P1": 20})
        processor = OrderProcessor(inv)
        order = _make_order(items=[
            OrderItem(product_id="P1", name="Widget A", unit_price=10.0, quantity=3),
            OrderItem(product_id="P1", name="Widget B", unit_price=10.0, quantity=3),
        ])
        result = processor.process(order)
        # Both line items should be in the result
        assert len(result.line_items) == 2
        assert inv.get_stock("P1") == 14  # 20 - 3 - 3
