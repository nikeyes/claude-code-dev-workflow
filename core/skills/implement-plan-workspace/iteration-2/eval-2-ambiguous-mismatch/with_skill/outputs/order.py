class PurchaseOrder:
    def __init__(self, order_id):
        from datetime import datetime, timezone
        self.order_id = order_id
        self.lines = []
        self.status = "draft"
        self.cancellation_reason = None
        self._status_history = [
            {"status": "draft", "timestamp": datetime.now(timezone.utc).isoformat()}
        ]

    def add_line(self, product, quantity, unit_price):
        self.lines.append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
        })

    def calculate_total(self, tax_rate=0.0, discount_code=None):
        subtotal = sum(l["quantity"] * l["unit_price"] for l in self.lines)
        if discount_code == "HALF":
            subtotal *= 0.5
        tax = subtotal * tax_rate
        return round(subtotal + tax, 2)

    def submit(self):
        if not self.lines:
            raise ValueError("Cannot submit empty order")
        self.status = "submitted"
        self._add_history("submitted")
        return self.status

    def cancel(self, reason):
        if self.status != "submitted":
            raise ValueError("Can only cancel submitted orders")
        self.status = "cancelled"
        self.cancellation_reason = reason
        self._add_history("cancelled")

    def get_status_history(self):
        return list(self._status_history)

    def _add_history(self, status):
        from datetime import datetime, timezone
        self._status_history.append({
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
