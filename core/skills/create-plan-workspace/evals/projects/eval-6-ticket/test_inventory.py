from inventory import InventoryService


class TestInventoryService:
    def setup_method(self):
        self.service = InventoryService()

    def test_add_product(self):
        product = self.service.add_product("SKU001", "Widget", 10, 9.99)
        assert product["sku"] == "SKU001"
        assert product["quantity"] == 10

    def test_get_product(self):
        self.service.add_product("SKU001", "Widget", 10, 9.99)
        product = self.service.get_product("SKU001")
        assert product["name"] == "Widget"

    def test_get_product_not_found(self):
        assert self.service.get_product("MISSING") is None

    def test_update_quantity(self):
        self.service.add_product("SKU001", "Widget", 10, 9.99)
        updated = self.service.update_quantity("SKU001", -3)
        assert updated["quantity"] == 7

    def test_list_products_in_stock(self):
        self.service.add_product("SKU001", "Widget", 10, 9.99)
        self.service.add_product("SKU002", "Gadget", 0, 19.99)
        in_stock = self.service.list_products(in_stock_only=True)
        assert len(in_stock) == 1

    def test_total_value(self):
        self.service.add_product("SKU001", "Widget", 10, 9.99)
        self.service.add_product("SKU002", "Gadget", 5, 19.99)
        assert self.service.get_total_value() == 10 * 9.99 + 5 * 19.99
