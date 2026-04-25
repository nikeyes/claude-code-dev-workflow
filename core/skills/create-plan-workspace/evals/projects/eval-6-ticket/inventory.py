from typing import Optional


class InventoryService:
    def __init__(self):
        self._products: dict[str, dict] = {}

    def add_product(self, sku: str, name: str, quantity: int, price: float) -> dict:
        self._products[sku] = {
            "sku": sku,
            "name": name,
            "quantity": quantity,
            "price": price,
        }
        return self._products[sku]

    def get_product(self, sku: str) -> Optional[dict]:
        return self._products.get(sku)

    def update_quantity(self, sku: str, delta: int) -> Optional[dict]:
        product = self._products.get(sku)
        if product is None:
            return None
        product["quantity"] += delta
        return product

    def list_products(self, in_stock_only: bool = False) -> list[dict]:
        products = list(self._products.values())
        if in_stock_only:
            products = [p for p in products if p["quantity"] > 0]
        return products

    def get_total_value(self) -> float:
        return sum(p["quantity"] * p["price"] for p in self._products.values())
