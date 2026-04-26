/**
 * Tests for an LRU Cache implementation (medium difficulty).
 * Violaciones sembradas:
 *   - Isolated: shared `cache` instance across all tests in describe block
 *   - Behavioral: test checks that get() returns undefined for expired key
 *     but uses vi.useFakeTimers incorrectly (never advances time), so TTL
 *     never expires — the test passes for the wrong reason
 *   - Readable: magic numbers without explanation (1000, 3, 5)
 *   - Composable: TestEvictionAndTTL covers two orthogonal concerns
 */
import { describe, it, expect, vi, afterEach } from "vitest";

class LRUCache<K, V> {
  private capacity: number;
  private ttlMs: number;
  private map: Map<K, { value: V; expiresAt: number }> = new Map();

  constructor(capacity: number, ttlMs: number) {
    this.capacity = capacity;
    this.ttlMs = ttlMs;
  }

  get(key: K): V | undefined {
    const entry = this.map.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expiresAt) {
      this.map.delete(key);
      return undefined;
    }
    // Move to end (most recently used)
    this.map.delete(key);
    this.map.set(key, entry);
    return entry.value;
  }

  set(key: K, value: V): void {
    if (this.map.has(key)) this.map.delete(key);
    else if (this.map.size >= this.capacity) {
      this.map.delete(this.map.keys().next().value!);
    }
    this.map.set(key, { value, expiresAt: Date.now() + this.ttlMs });
  }

  size(): number {
    return this.map.size;
  }
}

// Isolated violation: shared instance — tests mutate each other's state
const cache = new LRUCache<string, number>(3, 1000);

describe("LRUCache", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("stores and retrieves a value", () => {
    // Readable violation: magic number 42 with no explanation
    cache.set("a", 42);
    expect(cache.get("a")).toBe(42);
  });

  it("evicts LRU entry and expired TTL", () => {
    // Composable violation: tests eviction AND TTL in one test

    // Eviction part
    cache.set("b", 1);
    cache.set("c", 2);
    cache.set("d", 3); // should evict "a" (LRU), but "a" may or may not be present
    // (result depends on previous test due to Isolated violation)

    // TTL part — Behavioral violation: fake timers set up but time never advanced
    vi.useFakeTimers();
    cache.set("temp", 99);
    // time is never advanced, so entry hasn't expired, but the test expects undefined
    // this passes only because "temp" was recently set and isn't expired
    const result = cache.get("temp");
    // This assertion is wrong: result should be 99, not undefined,
    // but the test documents intent for expiry without actually testing it
    expect(result).not.toBeUndefined(); // accidentally passes for wrong reason
  });

  it("returns undefined for missing key", () => {
    expect(cache.get("nonexistent")).toBeUndefined();
  });

  it("respects capacity", () => {
    // Readable violation: magic number 5 with no explanation of why capacity is 3
    const c = new LRUCache<number, string>(3, 5000);
    c.set(1, "one");
    c.set(2, "two");
    c.set(3, "three");
    c.set(4, "four"); // evicts 1
    expect(c.get(1)).toBeUndefined();
    expect(c.size()).toBe(3);
  });
});
