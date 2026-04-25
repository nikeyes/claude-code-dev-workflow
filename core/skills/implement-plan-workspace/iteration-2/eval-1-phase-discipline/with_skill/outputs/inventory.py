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

    def remove_item(self, name, quantity):
        if name not in self._items:
            raise KeyError(name)
        if quantity > self._items[name]["quantity"]:
            raise ValueError("Not enough stock")
        self._items[name]["quantity"] -= quantity
        if self._items[name]["quantity"] == 0:
            del self._items[name]

    def total_value(self):
        return sum(item["quantity"] * item["price"] for item in self._items.values())

    def apply_discount(self, name, percentage):
        if name not in self._items:
            raise KeyError(name)
        if not (0 <= percentage <= 100):
            raise ValueError("Discount must be between 0 and 100")
        self._items[name]["price"] *= (1 - percentage / 100)
