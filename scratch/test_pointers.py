# Intentional Python Mistakes for Tesseract Friction Test

def process_data(items):
    # Mistake 1: Unhandled type error in loop
    total = ""
    for num in items:
        total += num  # Crashes on integer
    return total

if __name__ == "__main__":
    data = [1, 2, 3, 4]
    print(process_data(data))
