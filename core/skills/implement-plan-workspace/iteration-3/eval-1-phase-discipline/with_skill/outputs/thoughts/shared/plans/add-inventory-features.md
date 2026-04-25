# Add Inventory Features

Extend the Inventory class with removal, valuation, and discount capabilities.

## Phase 1: Add remove_item method

Add a method to remove items from inventory.

- [x] `remove_item(name, quantity)` removes the specified quantity
- [x] When quantity reaches 0, the item is deleted from inventory
- [x] Raises `ValueError("Not enough stock")` if removing more than available
- [x] Raises `KeyError` if item doesn't exist

## Phase 2: Add total_value method

Add a method to calculate the total value of all inventory.

- [x] `total_value()` returns sum of (quantity * price) for all items
- [x] Returns 0.0 for empty inventory
- [x] Correctly reflects value after removals

## Phase 3: Add apply_discount method

Add a method to apply percentage discounts to item prices.

- [x] `apply_discount(name, percentage)` reduces the item's price by the given percentage
- [x] Raises `ValueError("Discount must be between 0 and 100")` for invalid percentages
- [x] Raises `KeyError` if item doesn't exist
- [x] total_value reflects discounted prices

## Phase 4: Final verification

- [x] All tests pass with `make test`
- [x] All phases integrated correctly
