// Tests for an Inventory manager.
// Violaciones sembradas:
//   - Isolated: tests share package-level var `globalInventory`
//   - Composable: one giant test covers add, reserve, release and restock in sequence
//   - Automated: fmt.Println requiring human inspection to verify result
//   - Specific: error message is generic "operation failed"
package inventory

import (
	"fmt"
	"testing"
)

type Inventory struct {
	stock    map[string]int
	reserved map[string]int
}

func NewInventory() *Inventory {
	return &Inventory{
		stock:    make(map[string]int),
		reserved: make(map[string]int),
	}
}

func (inv *Inventory) AddStock(sku string, qty int) error {
	if qty <= 0 {
		return fmt.Errorf("operation failed") // Specific violation: generic error
	}
	inv.stock[sku] += qty
	return nil
}

func (inv *Inventory) Reserve(sku string, qty int) error {
	available := inv.stock[sku] - inv.reserved[sku]
	if qty > available {
		return fmt.Errorf("operation failed") // Specific violation: same generic error
	}
	inv.reserved[sku] += qty
	return nil
}

func (inv *Inventory) Release(sku string, qty int) {
	inv.reserved[sku] -= qty
	if inv.reserved[sku] < 0 {
		inv.reserved[sku] = 0
	}
}

func (inv *Inventory) Available(sku string) int {
	return inv.stock[sku] - inv.reserved[sku]
}

// Isolated violation: shared state across tests
var globalInventory = NewInventory()

func TestFullInventoryFlow(t *testing.T) {
	// Composable violation: covers multiple concerns in one test
	globalInventory.AddStock("SKU-1", 10)

	err := globalInventory.Reserve("SKU-1", 3)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	globalInventory.Release("SKU-1", 1)

	available := globalInventory.Available("SKU-1")
	// Automated violation: human has to read stdout to confirm value
	fmt.Printf("Available after release: %d\n", available)

	if available != 8 {
		t.Errorf("expected 8, got %d", available)
	}
}

func TestReserveExceedsStock(t *testing.T) {
	// Isolated violation: depends on globalInventory modified by previous test
	err := globalInventory.Reserve("SKU-1", 100)
	if err == nil {
		t.Fatal("expected error reserving more than available")
	}
}

func TestAddNegativeStock(t *testing.T) {
	inv := NewInventory()
	err := inv.AddStock("SKU-X", -5)
	if err == nil {
		t.Fatal("expected error for negative qty")
	}
}
