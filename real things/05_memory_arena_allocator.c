/**
 * Memory Arena (Region / Bump) Allocator Implementation in C.
 * Demonstrates pointer offsets, 8-byte memory alignment, and O(1) bulk deallocation.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define ARENA_DEFAULT_CAPACITY (1024 * 16) // 16 KB region

typedef struct {
    uint8_t *buffer;
    size_t capacity;
    size_t offset;
} MemoryArena;

// Align offset to multiple of alignment (default 8 bytes)
static inline size_t align_forward(size_t ptr, size_t alignment) {
    size_t remainder = ptr % alignment;
    if (remainder == 0) return ptr;
    return ptr + (alignment - remainder);
}

// Initialize Arena buffer on heap
MemoryArena arena_create(size_t capacity) {
    MemoryArena arena;
    arena.buffer = (uint8_t *)malloc(capacity);
    assert(arena.buffer != NULL && "Fatal: Failed to allocate arena buffer");
    arena.capacity = capacity;
    arena.offset = 0;
    return arena;
}

// Bump allocate memory with 8-byte alignment
void *arena_alloc(MemoryArena *arena, size_t size) {
    if (arena == NULL || arena->buffer == NULL) return NULL;

    size_t aligned_offset = align_forward(arena->offset, 8);
    if (aligned_offset + size > arena->capacity) {
        // Out of memory in this arena region
        return NULL;
    }

    void *ptr = &arena->buffer[aligned_offset];
    arena->offset = aligned_offset + size;
    return ptr;
}

// O(1) Instant Bulk Reset
void arena_reset(MemoryArena *arena) {
    if (arena != NULL) {
        arena->offset = 0;
    }
}

// Free underlying region
void arena_destroy(MemoryArena *arena) {
    if (arena != NULL && arena->buffer != NULL) {
        free(arena->buffer);
        arena->buffer = NULL;
        arena->capacity = 0;
        arena->offset = 0;
    }
}

int main(void) {
    printf("[Arena Allocator Demo] Initializing 16KB Bump Arena...\n");
    MemoryArena arena = arena_create(ARENA_DEFAULT_CAPACITY);

    // Allocate an array of 5 integers
    int *numbers = (int *)arena_alloc(&arena, sizeof(int) * 5);
    assert(numbers != NULL);
    for (int i = 0; i < 5; i++) {
        numbers[i] = (i + 1) * 10;
    }

    // Allocate string buffer
    char *message = (char *)arena_alloc(&arena, 32);
    assert(message != NULL);
    strncpy(message, "Tesseract Memory Region", 31);

    printf("Allocated integers: [%d, %d, %d, %d, %d]\n", numbers[0], numbers[1], numbers[2], numbers[3], numbers[4]);
    printf("Allocated message: '%s'\n", message);
    printf("Arena current offset: %zu bytes / %zu capacity\n", arena.offset, arena.capacity);

    // Bulk reset demo
    arena_reset(&arena);
    printf("Arena reset complete. New offset: %zu bytes.\n", arena.offset);

    arena_destroy(&arena);
    printf("[Arena Allocator Demo] Status: SUCCESS - Regional bump allocator verified.\n");
    return 0;
}
