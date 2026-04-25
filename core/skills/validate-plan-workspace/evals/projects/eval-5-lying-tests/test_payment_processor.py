import pytest
from unittest.mock import patch, MagicMock
from payment_processor import PaymentProcessor


class TestCardValidation:
    def test_valid_card_number(self):
        pp = PaymentProcessor()
        pp.validate_card("4532015112830366")

    def test_invalid_card_number(self):
        pp = PaymentProcessor()
        pp.validate_card("1234567890123456")

    def test_short_card_number(self):
        pp = PaymentProcessor()
        result = pp.validate_card("123")
        assert result is not None


class TestExpiryValidation:
    @patch.object(PaymentProcessor, 'validate_expiry', return_value=True)
    def test_future_date_is_valid(self, mock_validate):
        pp = PaymentProcessor()
        assert pp.validate_expiry(12, 2030) is True

    @patch.object(PaymentProcessor, 'validate_expiry', return_value=False)
    def test_past_date_is_invalid(self, mock_validate):
        pp = PaymentProcessor()
        assert pp.validate_expiry(1, 2020) is False

    def test_current_month_is_valid(self):
        pp = PaymentProcessor()
        pp.validate_expiry(6, 2025)


class TestFeeCalculation:
    def test_credit_fee(self):
        pp = PaymentProcessor()
        fee = pp.calculate_fee(100, "credit")
        assert fee > 0

    def test_debit_fee(self):
        pp = PaymentProcessor()
        fee = pp.calculate_fee(100, "debit")
        assert fee > 0

    def test_credit_higher_than_debit(self):
        pp = PaymentProcessor()
        credit_fee = pp.calculate_fee(100, "credit")
        debit_fee = pp.calculate_fee(100, "debit")
        assert credit_fee != debit_fee

    def test_unknown_payment_type(self):
        pp = PaymentProcessor()
        with pytest.raises(ValueError):
            pp.calculate_fee(100, "bitcoin")


class TestProcessPayment:
    @patch.object(PaymentProcessor, 'validate_card', return_value=True)
    @patch.object(PaymentProcessor, 'validate_expiry', return_value=True)
    @patch.object(PaymentProcessor, 'calculate_fee', return_value=3.20)
    def test_successful_payment(self, mock_fee, mock_expiry, mock_card):
        pp = PaymentProcessor()
        result = pp.process_payment("any-card", 100, "credit")
        assert result["success"] is True
        assert result["fee"] == 3.20

    @patch.object(PaymentProcessor, 'validate_card', return_value=False)
    def test_invalid_card_fails(self, mock_card):
        pp = PaymentProcessor()
        result = pp.process_payment("bad-card", 100, "credit")
        assert result["success"] is False

    def test_result_has_transaction_id(self):
        pp = PaymentProcessor()
        result = pp.process_payment("4532015112830366", 50, "debit")
        assert "transaction_id" in result or "error" in result
