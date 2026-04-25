import uuid
from datetime import datetime


class PaymentProcessor:
    CREDIT_FEE_PERCENT = 2.9
    DEBIT_FEE_PERCENT = 0.5
    FLAT_FEE = 0.30

    def validate_card(self, card_number):
        digits = [int(d) for d in str(card_number) if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        checksum = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    def validate_expiry(self, month, year):
        if not (1 <= month <= 12):
            return False
        now = datetime.now()
        if year < now.year:
            return False
        if year == now.year and month < now.month:
            return False
        return True

    def calculate_fee(self, amount, payment_type):
        if payment_type == "credit":
            percent_fee = amount * self.CREDIT_FEE_PERCENT / 100
        elif payment_type == "debit":
            percent_fee = amount * self.DEBIT_FEE_PERCENT / 100
        else:
            raise ValueError(f"Unknown payment type: {payment_type}")
        return round(percent_fee + self.FLAT_FEE, 2)

    def process_payment(self, card_number, amount, payment_type, expiry_month=12, expiry_year=2030):
        if not self.validate_card(card_number):
            return {"success": False, "error": "Invalid card number"}
        if not self.validate_expiry(expiry_month, expiry_year):
            return {"success": False, "error": "Card expired"}
        fee = self.calculate_fee(amount, payment_type)
        return {
            "success": True,
            "amount": amount,
            "fee": fee,
            "net_amount": round(amount - fee, 2),
            "transaction_id": str(uuid.uuid4()),
        }
