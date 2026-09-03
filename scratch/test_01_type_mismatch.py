"""
Test Case 01: Python Type Mismatch
Expected Error: TypeError: can only concatenate str (not "int") to str
Testing: Can Tesseract detect type incompatibility and hint about str/int conversion?
"""

def calculate_invoice_total(base_fee, items):
    # Bug: base_fee is string, but prices are integers
    total = base_fee
    for price in items:
        total += price  # Crashes: cannot add int to str
    return total

if __name__ == "__main__":
    prices = [25, 40, 15]
    print("Total:", calculate_invoice_total("$10", prices))
