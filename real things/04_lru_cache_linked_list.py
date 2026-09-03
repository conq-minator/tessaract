"""
Least Recently Used (LRU) Cache Implementation.
Uses a Doubly Linked List and Hash Map to achieve strictly O(1) get and put time complexity.
"""

from typing import Optional, Dict


class DNode:
    def __init__(self, key: int = 0, val: int = 0):
        self.key: int = key
        self.val: int = val
        self.prev: Optional['DNode'] = None
        self.next: Optional['DNode'] = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity: int = capacity
        self.cache: Dict[int, DNode] = {}
        # Dummy head and tail to eliminate null boundary checks
        self.head: DNode = DNode()
        self.tail: DNode = DNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _add_node_to_front(self, node: DNode) -> None:
        """Inserts node right after head."""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: DNode) -> None:
        """Unlinks a node from the doubly linked list."""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _move_to_front(self, node: DNode) -> None:
        """Mark node as most recently used."""
        self._remove_node(node)
        self._add_node_to_front(node)

    def _pop_tail(self) -> DNode:
        """Evicts the least recently used item."""
        lru = self.tail.prev
        self._remove_node(lru)
        return lru

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._move_to_front(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.val = value
            self._move_to_front(node)
        else:
            new_node = DNode(key, value)
            self.cache[key] = new_node
            self._add_node_to_front(new_node)
            if len(self.cache) > self.capacity:
                tail = self._pop_tail()
                del self.cache[tail.key]

    def state(self) -> list:
        """Return list of keys from MRU to LRU."""
        items = []
        curr = self.head.next
        while curr != self.tail:
            items.append((curr.key, curr.val))
            curr = curr.next
        return items


if __name__ == "__main__":
    print("[LRU Cache Demo] Initializing O(1) Cache with Capacity = 3...")
    lru = LRUCache(3)
    lru.put(1, 100)
    lru.put(2, 200)
    lru.put(3, 300)
    print(f"Initial Cache State (MRU -> LRU): {lru.state()}")

    print("Accessing key 1 (bringing to MRU)...")
    val = lru.get(1)
    assert val == 100
    print(f"State after get(1): {lru.state()}")

    print("Inserting key 4 (causes eviction of LRU key 2)...")
    lru.put(4, 400)
    print(f"State after put(4): {lru.state()}")
    assert lru.get(2) == -1, "Key 2 should have been evicted!"
    assert lru.get(4) == 400
    print("[LRU Cache Demo] Status: SUCCESS - O(1) Doubly Linked List Cache invariants verified.")
