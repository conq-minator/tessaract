"""
Test Case 02: Python Off-By-One List Indexing
Expected Error: IndexError: list index out of range
Testing: Can Tesseract detect 0-indexing boundaries and off-by-one loops?
"""

def print_leaderboard(scores):
    # Bug: range(1, len(scores) + 1) exceeds valid 0-based indices
    for i in range(1, len(scores) + 1):
        print(f"Rank {i}: {scores[i]}")

if __name__ == "__main__":
    top_scores = [98, 85, 72, 60]
    print_leaderboard(top_scores)
