#include <stdio.h>

int main() {
    int *ptr = NULL;
    *ptr = 42;
    printf("%d\n", *ptr);
    return 0;
}
