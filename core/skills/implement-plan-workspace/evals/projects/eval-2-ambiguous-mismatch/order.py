class PurchaseOrder:
    def __init__(self, order_id):
        self.order_id = order_id
        self.lines = []
        self.status = "draft"

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
        return self.status
