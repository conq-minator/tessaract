"""
Test Case 04: Python Missing Base Case in Recursion
Expected Error: RecursionError: maximum recursion depth exceeded
Testing: Can Tesseract detect missing or unreachable base cases in recursion?
"""

def countdown_sum(n):
    # Bug: Forgot base case (if n <= 0: return 0), n continues negative forever
    return n + countdown_sum(n - 1)

if __name__ == "__main__":
    print(countdown_sum(5))
