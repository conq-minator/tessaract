#include <stdio.h>
#include <stdlib.h>

int main() {
    // Intentional Mistake 1: Dereferencing unallocated / NULL pointer
    int *ptr = NULL;
    *ptr = 42; 

    // Intentional Mistake 2: Missing semicolon / type mismatch
    printf("Value: %d\n", *ptr)
    return 0;
}
