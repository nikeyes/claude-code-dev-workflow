# Add Inventory Features

Extend the Inventory class with removal, valuation, and discount capabilities.

## Phase 1: Add remove_item method

Add a method to remove items from inventory.

- [ ] `remove_item(name, quantity)` removes the specified quantity
- [ ] When quantity reaches 0, the item is deleted from inventory
- [ ] Raises `ValueError("Not enough stock")` if removing more than available
- [ ] Raises `KeyError` if item doesn't exist

## Phase 2: Add total_value method

Add a method to calculate the total value of all inventory.

- [ ] `total_value()` returns sum of (quantity * price) for all items
- [ ] Returns 0.0 for empty inventory
- [ ] Correctly reflects value after removals

## Phase 3: Add apply_discount method

Add a method to apply percentage discounts to item prices.

- [ ] `apply_discount(name, percentage)` reduces the item's price by the given percentage
- [ ] Raises `ValueError("Discount must be between 0 and 100")` for invalid percentages
- [ ] Raises `KeyError` if item doesn't exist
- [ ] total_value reflects discounted prices

## Phase 4: Final verification

- [ ] All tests pass with `make test`
- [ ] All phases integrated correctly
