import pytest
from order import PurchaseOrder


def test_add_line():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 2, 10.00)
    assert len(order.lines) == 1


def test_calculate_total_no_tax():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 2, 10.00)
    assert order.calculate_total() == 20.00


def test_calculate_total_with_tax():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 2, 10.00)
    assert order.calculate_total(tax_rate=0.1) == 22.00


def test_calculate_total_with_discount():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 2, 10.00)
    assert order.calculate_total(discount_code="HALF") == 10.00


def test_submit_order():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 1, 5.00)
    assert order.submit() == "submitted"


def test_submit_empty_raises():
    order = PurchaseOrder("ORD-1")
    with pytest.raises(ValueError, match="Cannot submit empty order"):
        order.submit()


# --- Phase 2 tests: cancellation ---

def test_cancel_submitted_order():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 1, 5.00)
    order.submit()
    order.cancel(reason="Customer request")
    assert order.status == "cancelled"
    assert order.cancellation_reason == "Customer request"


def test_cancel_draft_raises():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 1, 5.00)
    with pytest.raises(ValueError, match="Can only cancel submitted orders"):
        order.cancel(reason="Changed mind")


# --- Phase 3 tests: history ---

def test_status_history_tracks_changes():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 1, 5.00)
    order.submit()
    order.cancel(reason="Test")
    history = order.get_status_history()
    assert [h["status"] for h in history] == ["draft", "submitted", "cancelled"]


def test_status_history_has_timestamps():
    order = PurchaseOrder("ORD-1")
    order.add_line("Widget", 1, 5.00)
    order.submit()
    history = order.get_status_history()
    assert all("timestamp" in h for h in history)
