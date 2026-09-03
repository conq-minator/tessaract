"""
Memory Arena (Bump / Region) Allocator.
Demonstrates pointer alignment, regional offsets, and instant O(1) bulk resets.
"""

import ctypes
from typing import Optional


class MemoryArena:
    def __init__(self, capacity_bytes: int = 1024 * 16):
        self.capacity: int = capacity_bytes
        self.buffer = (ctypes.c_uint8 * capacity_bytes)()
        self.offset: int = 0
        self._allocations_count: int = 0

    @staticmethod
    def _align_forward(ptr: int, alignment: int = 8) -> int:
        remainder = ptr % alignment
        if remainder == 0:
            return ptr
        return ptr + (alignment - remainder)

    def alloc(self, size_bytes: int, alignment: int = 8) -> Optional[int]:
        """Bump allocate memory with specified byte alignment."""
        aligned_offset = self._align_forward(self.offset, alignment)
        if aligned_offset + size_bytes > self.capacity:
            return None  # Out of region bounds

        ptr_address = ctypes.addressof(self.buffer) + aligned_offset
        self.offset = aligned_offset + size_bytes
        self._allocations_count += 1
        return ptr_address

    def reset(self) -> None:
        """Instant O(1) bulk deallocation of all objects in this arena region."""
        self.offset = 0
        self._allocations_count = 0

    @property
    def bytes_used(self) -> int:
        return self.offset

    @property
    def bytes_free(self) -> int:
        return self.capacity - self.offset


if __name__ == "__main__":
    print("[Memory Arena Demo] Initializing 16KB Low-Level Bump Allocator...")
    arena = MemoryArena(1024 * 16)

    # Allocate integer array buffer
    ptr1 = arena.alloc(64, alignment=8)
    assert ptr1 is not None
    print(f"Allocated Block #1 (64 bytes) at address 0x{ptr1:x} | Used: {arena.bytes_used}B")

    # Allocate telemetry struct block
    ptr2 = arena.alloc(128, alignment=8)
    assert ptr2 is not None
    print(f"Allocated Block #2 (128 bytes) at address 0x{ptr2:x} | Used: {arena.bytes_used}B")

    # Verify pointer distance honors 8-byte alignment
    diff = ptr2 - ptr1
    assert diff >= 64 and diff % 8 == 0, "Alignment invariant failure!"
    print(f"Pointer Offset Delta: {diff} bytes (strictly 8-byte aligned)")

    # Bulk Reset
    arena.reset()
    assert arena.bytes_used == 0
    print("[Memory Arena Demo] Status: SUCCESS - Regional memory arena and pointer bounds verified.")
