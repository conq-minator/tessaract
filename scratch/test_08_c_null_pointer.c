/**
 * Test Case 08: C NULL Pointer Dereference
 * Expected Error: Segmentation fault (exit code != 0)
 * Testing: Can Tesseract accurately classify this as a C pointer dereference problem?
 */

#include <stdio.h>
#include <stdlib.h>

void update_score(int *score_ptr, int delta) {
    // Bug: score_ptr is NULL, dereferencing crashes immediately
    *score_ptr += delta;
}

int main(void) {
    int *player_score = NULL;
    printf("Updating player score...\n");
    update_score(player_score, 50);
    printf("Updated score: %d\n", *player_score);
    return 0;
}
