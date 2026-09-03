"""
Dynamic Programming (DP) on 2D Matrix Grids.
Solves the Minimum Cost Path problem using bottom-up 2D tabulation memoization.
"""

from typing import List, Tuple


def min_cost_path(grid: List[List[int]]) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Computes minimum path cost from top-left (0,0) to bottom-right (m-1, n-1).
    Movement is restricted to Right and Down only.
    Uses O(m * n) Dynamic Programming table memoization.
    """
    if not grid or not grid[0]:
        return 0, []

    rows, cols = len(grid), len(grid[0])
    # 2D DP Table to store minimum cost to reach (r, c)
    dp = [[0] * cols for _ in range(rows)]
    dp[0][0] = grid[0][0]

    # Initialize first row (can only arrive from left)
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + grid[0][c]

    # Initialize first column (can only arrive from top)
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + grid[r][0]

    # Fill DP Table
    for r in range(1, rows):
        for c in range(1, cols):
            dp[r][c] = grid[r][c] + min(dp[r - 1][c], dp[r][c - 1])

    # Backtrack to reconstruct optimal path
    path = []
    curr_r, curr_c = rows - 1, cols - 1
    while curr_r > 0 or curr_c > 0:
        path.append((curr_r, curr_c))
        if curr_r == 0:
            curr_c -= 1
        elif curr_c == 0:
            curr_r -= 1
        else:
            if dp[curr_r - 1][curr_c] < dp[curr_r][curr_c - 1]:
                curr_r -= 1
            else:
                curr_c -= 1
    path.append((0, 0))
    path.reverse()

    return dp[rows - 1][cols - 1], path


if __name__ == "__main__":
    matrix = [
        [1, 3, 1, 5],
        [2, 1, 4, 2],
        [5, 2, 1, 1],
        [4, 3, 2, 1]
    ]

    print("[Dynamic Programming Demo] Calculating Minimum Cost Grid Path...")
    min_cost, optimal_path = min_cost_path(matrix)
    print(f"Grid Dimensions: {len(matrix)}x{len(matrix[0])}")
    print(f"Minimum Accumulated Path Cost: {min_cost}")
    print(f"Optimal Traversal Route: {optimal_path}")
    assert min_cost == 9, f"Expected 9, got {min_cost}"
    print("[Dynamic Programming Demo] Status: SUCCESS - 2D DP state transition verified.")
