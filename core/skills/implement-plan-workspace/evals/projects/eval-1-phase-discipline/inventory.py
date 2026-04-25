class Inventory:
    def __init__(self):
        self._items = {}

    def add_item(self, name, quantity, price):
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if price < 0:
            raise ValueError("Price cannot be negative")
        if name in self._items:
            self._items[name]["quantity"] += quantity
        else:
            self._items[name] = {"quantity": quantity, "price": price}

    def get_item(self, name):
        if name not in self._items:
            return None
        return dict(self._items[name])
