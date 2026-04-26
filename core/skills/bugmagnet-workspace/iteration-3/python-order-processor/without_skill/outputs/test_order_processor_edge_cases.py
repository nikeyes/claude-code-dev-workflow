"""Comprehensive edge-case and bug-hunting tests for order_processor.py.

Covers boundary conditions, error paths, and untested behaviors not present
in the baseline happy-path test suite.
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
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def us_ca_address():
    return Address(country="US", region="CA", postal_code="90210")


def us_or_address():
    return Address(country="US", region="OR", postal_code="97201")


def eu_es_address():
    return Address(country="EU", region="ES", postal_code="28001")


def unknown_address():
    return Address(country="AU", region="NSW", postal_code="2000")


def make_item(product_id="P1", name="Widget", unit_price=25.0, quantity=2,
              discount_type=None, discount_value=0.0):
    return OrderItem(
        product_id=product_id,
        name=name,
        unit_price=unit_price,
        quantity=quantity,
        discount_type=discount_type,
        discount_value=discount_value,
    )


def make_order(items=None, customer_id="C001", address=None, discounts=None):
    return Order(
        items=items or [make_item()],
        customer_id=customer_id,
        shipping_address=address or us_ca_address(),
        discounts=discounts or [],
    )


def make_processor(stock=None):
    return OrderProcessor(Inventory(stock or {"P1": 100}))


# ===========================================================================
# PricingEngine.calculate_line_total — boundary and negative-value conditions
# ===========================================================================

class TestCalculateLineTotal:

    def test_quantity_exactly_at_break_threshold_does_not_get_discount(self):
        """BUG CANDIDATE: quantity == 10 uses '> 10', so 10 items get no discount."""
        engine = PricingEngine()
        item_at_threshold = make_item(unit_price=10.0, quantity=10)
        item_just_over = make_item(unit_price=10.0, quantity=11)

        total_at = engine.calculate_line_total(item_at_threshold)
        total_over = engine.calculate_line_total(item_just_over)

        # At exactly 10 items: 10 * 10 = 100.0 (no discount applied)
        assert total_at == 100.0

        # At 11 items: 11 * 10 * 0.95 = 104.50 (discount applied)
        assert total_over == pytest.approx(104.50, rel=1e-4)

        # A business expectation might be that >= 10 gets the discount,
        # in which case the following assertion will fail, revealing the bug:
        # assert total_at < 100.0  # uncomment to confirm the boundary bug

    def test_fixed_item_discount_larger_than_line_total_produces_negative(self):
        """BUG: fixed discount larger than base price yields a negative line total."""
        engine = PricingEngine()
        item = make_item(
            unit_price=5.0,
            quantity=1,
            discount_type=DiscountType.FIXED,
            discount_value=50.0,  # discount > price
        )
        total = engine.calculate_line_total(item)
        # Currently returns -45.0 — a negative line total
        assert total == pytest.approx(-45.0, rel=1e-4)  # documents current (buggy) behavior
        # A correct implementation would floor at 0:
        # assert total >= 0.0

    def test_percentage_discount_of_100_percent_gives_zero(self):
        engine = PricingEngine()
        item = make_item(
            unit_price=20.0,
            quantity=1,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=100.0,
        )
        assert engine.calculate_line_total(item) == 0.0

    def test_percentage_discount_over_100_percent_gives_negative(self):
        """BUG: percentage > 100 produces a negative line total with no guard."""
        engine = PricingEngine()
        item = make_item(
            unit_price=20.0,
            quantity=1,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=150.0,
        )
        total = engine.calculate_line_total(item)
        assert total < 0.0  # documents current (buggy) behavior

    def test_zero_unit_price_item(self):
        """Free items (price=0) should produce a zero line total."""
        engine = PricingEngine()
        item = make_item(unit_price=0.0, quantity=3)
        assert engine.calculate_line_total(item) == 0.0

    def test_zero_percent_discount_is_noop(self):
        engine = PricingEngine()
        item = make_item(unit_price=10.0, quantity=2,
                         discount_type=DiscountType.PERCENTAGE, discount_value=0.0)
        assert engine.calculate_line_total(item) == 20.0

    def test_zero_fixed_discount_is_noop(self):
        engine = PricingEngine()
        item = make_item(unit_price=10.0, quantity=2,
                         discount_type=DiscountType.FIXED, discount_value=0.0)
        assert engine.calculate_line_total(item) == 20.0

    def test_quantity_break_and_item_discount_compound(self):
        """Both the quantity break and item discount should apply sequentially."""
        engine = PricingEngine()
        # 11 * $10 = $110; after 5% quantity break = $104.50;
        # after 10% item discount = $94.05
        item = make_item(unit_price=10.0, quantity=11,
                         discount_type=DiscountType.PERCENTAGE, discount_value=10.0)
        assert engine.calculate_line_total(item) == pytest.approx(94.05, rel=1e-4)


# ===========================================================================
# PricingEngine.apply_discounts — order-level discount edge cases
# ===========================================================================

class TestApplyDiscounts:

    def test_fixed_discount_larger_than_subtotal_produces_negative_total(self):
        """BUG: no floor at zero; fixed discount can drive total negative."""
        engine = PricingEngine()
        discount = Discount(
            code="BIGDEAL",
            discount_type=DiscountType.FIXED,
            value=200.0,
            minimum_order=0.0,
        )
        discounted, applied = engine.apply_discounts(50.0, [discount])
        assert discounted == pytest.approx(-150.0, rel=1e-4)  # current buggy behavior
        # A correct implementation should floor at 0.0

    def test_minimum_order_check_uses_original_subtotal_not_running_total(self):
        """BUG: minimum_order is checked against original subtotal, not the
        running discounted total. A second discount can apply even after the
        first has already dropped the amount below its minimum."""
        engine = PricingEngine()
        first = Discount(
            code="FIRST50",
            discount_type=DiscountType.FIXED,
            value=40.0,
            minimum_order=0.0,
        )
        # minimum_order=60 means it should only apply when total >= 60.
        # After the first discount: 80 - 40 = 40 (below 60), but the check
        # still compares against the original subtotal (80 >= 60), so it applies.
        second = Discount(
            code="SECOND20",
            discount_type=DiscountType.FIXED,
            value=20.0,
            minimum_order=60.0,
        )
        discounted, applied = engine.apply_discounts(80.0, [first, second])
        # Under current (buggy) behavior: both discounts apply → 80 - 40 - 20 = 20
        assert "SECOND20" in " ".join(applied)
        assert discounted == pytest.approx(20.0, rel=1e-4)

    def test_discount_skipped_when_below_minimum_order(self):
        engine = PricingEngine()
        discount = Discount(
            code="HIGHVALUE",
            discount_type=DiscountType.PERCENTAGE,
            value=10.0,
            minimum_order=200.0,
        )
        discounted, applied = engine.apply_discounts(50.0, [discount])
        assert discounted == 50.0
        assert applied == []

    def test_discount_applied_at_exact_minimum_order(self):
        """Boundary: discount should apply when subtotal == minimum_order."""
        engine = PricingEngine()
        discount = Discount(
            code="EXACT",
            discount_type=DiscountType.PERCENTAGE,
            value=10.0,
            minimum_order=50.0,
        )
        discounted, applied = engine.apply_discounts(50.0, [discount])
        assert discounted == pytest.approx(45.0, rel=1e-4)

    def test_no_discounts_returns_original_subtotal(self):
        engine = PricingEngine()
        discounted, applied = engine.apply_discounts(99.99, [])
        assert discounted == 99.99
        assert applied == []

    def test_multiple_percentage_discounts_apply_sequentially(self):
        """Each percentage discount should apply to the running total, not the original."""
        engine = PricingEngine()
        d1 = Discount(code="A", discount_type=DiscountType.PERCENTAGE, value=10.0)
        d2 = Discount(code="B", discount_type=DiscountType.PERCENTAGE, value=10.0)
        # 100 → -10% → 90 → -10% of 90 → 81
        discounted, applied = engine.apply_discounts(100.0, [d1, d2])
        assert discounted == pytest.approx(81.0, rel=1e-4)
        assert len(applied) == 2


# ===========================================================================
# PricingEngine.calculate_tax — region key formation and unknown regions
# ===========================================================================

class TestCalculateTax:

    def test_known_us_ca_tax_rate(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, us_ca_address())
        assert tax == pytest.approx(7.25, rel=1e-4)

    def test_zero_tax_region_us_or(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, us_or_address())
        assert tax == 0.0

    def test_unknown_country_region_defaults_to_zero_tax(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, unknown_address())
        assert tax == 0.0

    def test_tax_applied_to_zero_amount(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(0.0, us_ca_address())
        assert tax == 0.0

    def test_eu_es_tax_rate(self):
        engine = PricingEngine()
        tax = engine.calculate_tax(100.0, eu_es_address())
        assert tax == pytest.approx(21.0, rel=1e-4)


# ===========================================================================
# PricingEngine.calculate_shipping — free shipping boundary and unknown country
# ===========================================================================

class TestCalculateShipping:

    def test_free_shipping_when_subtotal_meets_threshold(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(100.0, us_ca_address())
        assert shipping == 0.0

    def test_free_shipping_boundary_just_below_threshold(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(99.99, us_ca_address())
        assert shipping == 9.99

    def test_free_shipping_boundary_exactly_at_threshold(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(100.0, us_ca_address())
        assert shipping == 0.0

    def test_shipping_for_unknown_country_uses_default_rate(self):
        """Unknown countries should fall back to the default 19.99 rate."""
        engine = PricingEngine()
        shipping = engine.calculate_shipping(50.0, unknown_address())
        assert shipping == 19.99

    def test_shipping_for_eu(self):
        engine = PricingEngine()
        shipping = engine.calculate_shipping(50.0, eu_es_address())
        assert shipping == 14.99


# ===========================================================================
# OrderProcessor.validate — all validation branches
# ===========================================================================

class TestValidate:

    def test_empty_items_list(self):
        processor = make_processor()
        errors = processor.validate(
            Order(items=[], customer_id="C001", shipping_address=us_ca_address())
        )
        assert "Order must contain at least one item" in errors

    def test_zero_quantity_item_is_invalid(self):
        processor = make_processor({"P1": 10})
        errors = processor.validate(make_order(items=[make_item(quantity=0)]))
        assert any("Invalid quantity" in e for e in errors)

    def test_negative_quantity_item_is_invalid(self):
        processor = make_processor({"P1": 10})
        errors = processor.validate(make_order(items=[make_item(quantity=-5)]))
        assert any("Invalid quantity" in e for e in errors)

    def test_negative_unit_price_is_invalid(self):
        processor = make_processor({"P1": 10})
        errors = processor.validate(make_order(items=[make_item(unit_price=-1.0)]))
        assert any("Invalid price" in e for e in errors)

    def test_zero_unit_price_is_valid(self):
        """Zero-price items (free goods) are explicitly allowed by the validator."""
        processor = make_processor({"P1": 10})
        errors = processor.validate(make_order(items=[make_item(unit_price=0.0)]))
        assert not any("Invalid price" in e for e in errors)

    def test_missing_customer_id_empty_string(self):
        processor = make_processor()
        errors = processor.validate(
            Order(items=[make_item()], customer_id="",
                  shipping_address=us_ca_address())
        )
        assert "Customer ID is required" in errors

    def test_whitespace_only_customer_id_passes_validation(self):
        """BUG CANDIDATE: a whitespace-only customer ID passes the empty-string check."""
        processor = make_processor({"P1": 10})
        errors = processor.validate(
            Order(items=[make_item()], customer_id="   ",
                  shipping_address=us_ca_address())
        )
        # Current behavior: no error — whitespace is treated as valid
        assert "Customer ID is required" not in errors

    def test_insufficient_stock_reported_in_errors(self):
        processor = make_processor({"P1": 1})
        errors = processor.validate(make_order(items=[make_item(quantity=5)]))
        assert any("Widget" in e for e in errors)

    def test_multiple_validation_errors_all_reported(self):
        processor = make_processor({})
        errors = processor.validate(
            Order(items=[make_item(quantity=-1, unit_price=-5.0)],
                  customer_id="",
                  shipping_address=us_ca_address())
        )
        assert len(errors) >= 3  # quantity, price, and customer_id

    def test_item_not_in_inventory_treated_as_zero_stock(self):
        processor = make_processor({})  # empty inventory
        errors = processor.validate(make_order(items=[make_item(quantity=1)]))
        assert any("Widget" in e for e in errors)


# ===========================================================================
# OrderProcessor.process — tax applied to subtotal, not discounted amount
# ===========================================================================

class TestProcessTaxBug:

    def test_tax_is_calculated_on_subtotal_not_discounted_amount(self):
        """BUG: tax is calculated on `subtotal` instead of the post-discount amount.
        Customers are taxed on the original price, not the discounted price."""
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)

        discount = Discount(
            code="HALF",
            discount_type=DiscountType.PERCENTAGE,
            value=50.0,
            minimum_order=0.0,
        )
        # subtotal = $100, discounted = $50, CA tax rate = 7.25%
        # Expected (correct): tax on $50 → $3.63
        # Actual (buggy): tax on $100 → $7.25
        order = make_order(
            items=[make_item(unit_price=50.0, quantity=2)],
            address=us_ca_address(),
            discounts=[discount],
        )
        result = processor.process(order)

        # This assertion documents the current buggy behavior:
        assert result.tax == pytest.approx(7.25, rel=1e-4)  # taxed on $100 subtotal

        # The following would assert the correct behavior:
        # assert result.tax == pytest.approx(3.63, rel=1e-4)  # taxed on $50 discounted


# ===========================================================================
# OrderProcessor.process — order ID counter and general flow
# ===========================================================================

class TestProcessOrderId:

    def test_order_ids_increment_sequentially(self):
        processor = make_processor({"P1": 100})
        r1 = processor.process(make_order())
        r2 = processor.process(make_order())
        assert r1.order_id == "ORD-000001"
        assert r2.order_id == "ORD-000002"

    def test_process_raises_on_invalid_order(self):
        processor = make_processor({})
        with pytest.raises(ValueError, match="Invalid order"):
            processor.process(make_order())

    def test_inventory_reserved_after_process(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        processor.process(make_order(items=[make_item(quantity=3)]))
        assert inv.get_stock("P1") == 7

    def test_process_free_shipping_when_subtotal_at_threshold(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        # $50 * 2 = $100.00 exactly — should get free shipping
        result = processor.process(make_order(items=[make_item(unit_price=50.0, quantity=2)]))
        assert result.shipping == 0.0

    def test_process_paid_shipping_when_subtotal_below_threshold(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        result = processor.process(make_order(items=[make_item(unit_price=10.0, quantity=2)]))
        assert result.shipping == 9.99


# ===========================================================================
# Inventory — reserve, release, and edge cases
# ===========================================================================

class TestInventory:

    def test_reserve_reduces_stock(self):
        inv = Inventory({"P1": 10})
        inv.reserve([make_item(quantity=3)])
        assert inv.get_stock("P1") == 7

    def test_reserve_raises_when_insufficient_stock(self):
        inv = Inventory({"P1": 2})
        with pytest.raises(ValueError, match="Insufficient stock"):
            inv.reserve([make_item(quantity=5)])

    def test_reserve_raises_when_product_not_in_inventory(self):
        inv = Inventory({})
        with pytest.raises(ValueError, match="Insufficient stock"):
            inv.reserve([make_item(quantity=1)])

    def test_reserve_to_exactly_zero_stock(self):
        inv = Inventory({"P1": 3})
        inv.reserve([make_item(quantity=3)])
        assert inv.get_stock("P1") == 0

    def test_check_availability_passes_when_stock_equals_quantity(self):
        inv = Inventory({"P1": 3})
        unavailable = inv.check_availability([make_item(quantity=3)])
        assert unavailable == []

    def test_check_availability_fails_when_stock_just_below_quantity(self):
        inv = Inventory({"P1": 2})
        unavailable = inv.check_availability([make_item(quantity=3)])
        assert len(unavailable) == 1

    def test_release_restores_stock(self):
        inv = Inventory({"P1": 5})
        inv.reserve([make_item(quantity=5)])
        inv.release([make_item(quantity=5)])
        assert inv.get_stock("P1") == 5

    def test_release_creates_stock_for_unknown_product(self):
        """release() silently creates stock for products not in original inventory."""
        inv = Inventory({})
        inv.release([make_item(product_id="GHOST", quantity=3)])
        assert inv.get_stock("GHOST") == 3

    def test_check_availability_product_not_in_inventory_treated_as_zero(self):
        inv = Inventory({})
        unavailable = inv.check_availability([make_item(quantity=1)])
        assert len(unavailable) == 1


# ===========================================================================
# OrderProcessor.process_batch
# ===========================================================================

class TestProcessBatch:

    def test_empty_batch_returns_empty_list(self):
        processor = make_processor()
        results = processor.process_batch([])
        assert results == []

    def test_batch_returns_error_dict_for_invalid_orders(self):
        processor = make_processor({})
        results = processor.process_batch([make_order()])
        assert len(results) == 1
        assert "error" in results[0]
        assert results[0]["customer_id"] == "C001"

    def test_batch_mixes_success_and_failure(self):
        inv = Inventory({"P1": 10})
        processor = OrderProcessor(inv)
        valid = make_order(items=[make_item(quantity=2)])
        invalid = make_order(items=[make_item(product_id="NONE", quantity=99)], customer_id="C002")
        results = processor.process_batch([valid, invalid])
        assert hasattr(results[0], "order_id")  # ProcessedOrder
        assert "error" in results[1]

    def test_batch_order_counter_increments_across_batch(self):
        inv = Inventory({"P1": 100})
        processor = OrderProcessor(inv)
        results = processor.process_batch([make_order(), make_order()])
        assert results[0].order_id == "ORD-000001"
        assert results[1].order_id == "ORD-000002"


# ===========================================================================
# OrderProcessor.calculate_loyalty_points
# ===========================================================================

class TestCalculateLoyaltyPoints:

    def test_non_member_gets_integer_points_equal_to_floor_of_total(self):
        processor = make_processor()
        assert processor.calculate_loyalty_points(49.99) == 49

    def test_member_gets_double_points(self):
        processor = make_processor()
        assert processor.calculate_loyalty_points(50.0, is_member=True) == 100

    def test_zero_total_gives_zero_points(self):
        processor = make_processor()
        assert processor.calculate_loyalty_points(0.0) == 0

    def test_negative_total_gives_negative_points(self):
        """BUG CANDIDATE: negative total produces negative loyalty points."""
        processor = make_processor()
        points = processor.calculate_loyalty_points(-10.0)
        assert points == -10  # documents current (likely buggy) behavior

    def test_fractional_total_truncates_to_int(self):
        processor = make_processor()
        assert processor.calculate_loyalty_points(9.99) == 9


# ===========================================================================
# OrderProcessor.generate_invoice
# ===========================================================================

class TestGenerateInvoice:

    def _make_processed_order(self, discount_total=0.0, shipping=9.99):
        from order_processor import ProcessedOrder
        return ProcessedOrder(
            order_id="ORD-000001",
            subtotal=50.0,
            discount_total=discount_total,
            tax=3.63,
            shipping=shipping,
            total=round(50.0 - discount_total + 3.63 + shipping, 2),
            applied_discounts=["SAVE10: -5.00"] if discount_total > 0 else [],
            line_items=[{
                "product_id": "P1",
                "name": "Widget",
                "quantity": 2,
                "unit_price": 25.0,
                "line_total": 50.0,
            }],
        )

    def test_invoice_contains_order_id(self):
        processor = make_processor()
        invoice = processor.generate_invoice(self._make_processed_order())
        assert "ORD-000001" in invoice

    def test_invoice_discount_section_absent_when_no_discount(self):
        processor = make_processor()
        invoice = processor.generate_invoice(self._make_processed_order(discount_total=0.0))
        assert "Discount" not in invoice

    def test_invoice_discount_section_present_when_discounted(self):
        processor = make_processor()
        invoice = processor.generate_invoice(self._make_processed_order(discount_total=5.0))
        assert "Discount" in invoice
        assert "Applied discounts" in invoice

    def test_invoice_shipping_absent_when_free(self):
        processor = make_processor()
        invoice = processor.generate_invoice(
            self._make_processed_order(shipping=0.0)
        )
        assert "Shipping" not in invoice

    def test_invoice_shipping_present_when_charged(self):
        processor = make_processor()
        invoice = processor.generate_invoice(
            self._make_processed_order(shipping=9.99)
        )
        assert "Shipping" in invoice

    def test_invoice_empty_line_items(self):
        """Invoice generation with no line items should not crash."""
        from order_processor import ProcessedOrder
        processed = ProcessedOrder(
            order_id="ORD-000002",
            subtotal=0.0,
            discount_total=0.0,
            tax=0.0,
            shipping=0.0,
            total=0.0,
            applied_discounts=[],
            line_items=[],
        )
        processor = make_processor()
        invoice = processor.generate_invoice(processed)
        assert "ORD-000002" in invoice


# ===========================================================================
# OrderProcessor.apply_refund — edge cases
# ===========================================================================

class TestApplyRefund:

    def _make_processed_for_refund(self):
        from order_processor import ProcessedOrder
        return ProcessedOrder(
            order_id="ORD-000001",
            subtotal=100.0,
            discount_total=10.0,
            tax=7.25,
            shipping=0.0,
            total=97.25,
            applied_discounts=["SAVE10: -10.00"],
            line_items=[
                {"product_id": "P1", "name": "Widget", "quantity": 2,
                 "unit_price": 25.0, "line_total": 50.0},
                {"product_id": "P2", "name": "Gadget", "quantity": 2,
                 "unit_price": 25.0, "line_total": 50.0},
            ],
        )

    def test_refund_raises_when_no_matching_product(self):
        processor = make_processor()
        processed = self._make_processed_for_refund()
        with pytest.raises(ValueError, match="No matching items found"):
            processor.apply_refund(processed, ["NONEXISTENT"], us_ca_address())

    def test_partial_refund_removes_correct_item(self):
        processor = make_processor()
        processed = self._make_processed_for_refund()
        result = processor.apply_refund(processed, ["P1"], us_ca_address())
        assert len(result.line_items) == 1
        assert result.line_items[0]["product_id"] == "P2"

    def test_partial_refund_reduces_subtotal(self):
        processor = make_processor()
        processed = self._make_processed_for_refund()
        result = processor.apply_refund(processed, ["P1"], us_ca_address())
        assert result.subtotal == pytest.approx(50.0, rel=1e-4)

    def test_full_refund_of_all_items_leaves_empty_line_items(self):
        """Refunding all items produces an order with empty line_items but
        the original shipping still included in total."""
        processor = make_processor()
        processed = self._make_processed_for_refund()
        result = processor.apply_refund(processed, ["P1", "P2"], us_ca_address())
        assert result.line_items == []
        # Shipping is preserved; this may be a bug when all items are refunded
        assert result.shipping == processed.shipping

    def test_refund_order_id_has_suffix(self):
        processor = make_processor()
        processed = self._make_processed_for_refund()
        result = processor.apply_refund(processed, ["P1"], us_ca_address())
        assert result.order_id == "ORD-000001-R"

    def test_refund_with_zero_subtotal_does_not_raise(self):
        """Division by zero is guarded; confirm it does not raise."""
        from order_processor import ProcessedOrder
        processor = make_processor()
        processed = ProcessedOrder(
            order_id="ORD-000001",
            subtotal=0.0,
            discount_total=0.0,
            tax=0.0,
            shipping=0.0,
            total=0.0,
            applied_discounts=[],
            line_items=[
                {"product_id": "P1", "name": "Widget", "quantity": 1,
                 "unit_price": 0.0, "line_total": 0.0},
            ],
        )
        result = processor.apply_refund(processed, ["P1"], us_ca_address())
        assert result.subtotal == 0.0

    def test_refund_preserves_applied_discounts(self):
        processor = make_processor()
        processed = self._make_processed_for_refund()
        result = processor.apply_refund(processed, ["P1"], us_ca_address())
        assert result.applied_discounts == processed.applied_discounts
