/**
 * Tests for an OrderService.
 * Violaciones sembradas:
 *   - Readable: test names don't describe behavior (test1, test2)
 *   - Fast: real setTimeout of 500ms in a test
 *   - Behavioral: mock overrides the function under test, making the test vacuous
 *   - Writable: 40+ lines of boilerplate setup duplicated across tests
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

interface Order {
  id: string;
  items: { sku: string; qty: number; price: number }[];
  customerId: string;
}

class OrderService {
  private db: Map<string, Order> = new Map();

  async createOrder(order: Order): Promise<string> {
    if (!order.items.length) throw new Error("Order must have items");
    this.db.set(order.id, order);
    return order.id;
  }

  async getTotal(orderId: string): Promise<number> {
    const order = this.db.get(orderId);
    if (!order) throw new Error("Order not found");
    return order.items.reduce((sum, i) => sum + i.qty * i.price, 0);
  }

  async cancelOrder(orderId: string): Promise<void> {
    if (!this.db.has(orderId)) throw new Error("Order not found");
    this.db.delete(orderId);
  }
}

describe("OrderService", () => {
  let service: OrderService;

  beforeEach(() => {
    service = new OrderService();
  });

  // Readable violation: test name says nothing about the behavior
  it("test1", async () => {
    // Writable violation: 15 lines of boilerplate repeated in every test
    const order: Order = {
      id: "ord-001",
      customerId: "cust-123",
      items: [
        { sku: "SKU-A", qty: 2, price: 10.0 },
        { sku: "SKU-B", qty: 1, price: 5.0 },
      ],
    };
    const id = await service.createOrder(order);
    expect(id).toBe("ord-001");
  });

  it("test2", async () => {
    // Writable violation: same boilerplate duplicated
    const order: Order = {
      id: "ord-002",
      customerId: "cust-123",
      items: [
        { sku: "SKU-A", qty: 2, price: 10.0 },
        { sku: "SKU-B", qty: 1, price: 5.0 },
      ],
    };
    await service.createOrder(order);
    const total = await service.getTotal("ord-002");
    expect(total).toBe(25);
  });

  it("test3", async () => {
    // Fast violation: real async delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    const order: Order = {
      id: "ord-003",
      customerId: "cust-999",
      items: [{ sku: "SKU-C", qty: 3, price: 8.0 }],
    };
    await service.createOrder(order);
    await service.cancelOrder("ord-003");
    expect(true).toBe(true); // vacuous assertion
  });

  it("test4 behavioral violation", async () => {
    // Behavioral violation: mocks the method under test, making assertion meaningless
    const spy = vi.spyOn(service, "getTotal").mockResolvedValue(999);
    const order: Order = {
      id: "ord-004",
      customerId: "cust-001",
      items: [{ sku: "SKU-D", qty: 1, price: 50.0 }],
    };
    await service.createOrder(order);
    const total = await service.getTotal("ord-004");
    expect(total).toBe(999); // tests the mock, not the implementation
    spy.mockRestore();
  });
});
