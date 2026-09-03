"""
Binary Search Tree (BST) Implementation with Recursive Operations.
Demonstrates tree invariants, recursive node search, and in-order traversal.
"""

from typing import Optional, List


class TreeNode:
    def __init__(self, key: int, value: str):
        self.key: int = key
        self.value: str = value
        self.left: Optional[TreeNode] = None
        self.right: Optional[TreeNode] = None

    def __repr__(self) -> str:
        return f"TreeNode({self.key}: '{self.value}')"


class BinarySearchTree:
    def __init__(self):
        self.root: Optional[TreeNode] = None
        self._size: int = 0

    def insert(self, key: int, value: str) -> None:
        """Insert a key-value pair preserving the BST property."""
        if self.root is None:
            self.root = TreeNode(key, value)
            self._size += 1
        else:
            self._insert_recursive(self.root, key, value)

    def _insert_recursive(self, node: TreeNode, key: int, value: str) -> None:
        if key < node.key:
            if node.left is None:
                node.left = TreeNode(key, value)
                self._size += 1
            else:
                self._insert_recursive(node.left, key, value)
        elif key > node.key:
            if node.right is None:
                node.right = TreeNode(key, value)
                self._size += 1
            else:
                self._insert_recursive(node.right, key, value)
        else:
            # Update value for existing key
            node.value = value

    def search(self, key: int) -> Optional[str]:
        """Recursively search for a key in O(log n) expected time."""
        return self._search_recursive(self.root, key)

    def _search_recursive(self, node: Optional[TreeNode], key: int) -> Optional[str]:
        if node is None:
            return None
        if key == node.key:
            return node.value
        elif key < node.key:
            return self._search_recursive(node.left, key)
        else:
            return self._search_recursive(node.right, key)

    def inorder_keys(self) -> List[int]:
        """In-order traversal yields keys in strictly ascending order."""
        result: List[int] = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node: Optional[TreeNode], result: List[int]) -> None:
        if node is not None:
            self._inorder_recursive(node.left, result)
            result.append(node.key)
            self._inorder_recursive(node.right, result)

    def height(self) -> int:
        """Calculate maximum tree depth."""
        return self._height_recursive(self.root)

    def _height_recursive(self, node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        left_h = self._height_recursive(node.left)
        right_h = self._height_recursive(node.right)
        return 1 + max(left_h, right_h)

    def __len__(self) -> int:
        return self._size


if __name__ == "__main__":
    bst = BinarySearchTree()
    records = [(50, "Root"), (30, "Left Subtree"), (70, "Right Subtree"),
               (20, "Leaf 20"), (40, "Leaf 40"), (60, "Leaf 60"), (80, "Leaf 80")]
    
    print("[BST Demo] Inserting records into Binary Search Tree...")
    for k, v in records:
        bst.insert(k, v)

    keys = bst.inorder_keys()
    print(f"Total Nodes: {len(bst)} | Tree Height: {bst.height()}")
    print(f"Sorted In-Order Traversal: {keys}")
    
    query = 40
    print(f"Query key {query}: '{bst.search(query)}'")
    assert keys == sorted(keys), "BST invariant violation: keys are not sorted!"
    print("[BST Demo] Status: SUCCESS - All tree invariants verified.")
