"""
Test Case 03: Python Dictionary Missing Key
Expected Error: KeyError: 'zipcode'
Testing: Can Tesseract detect missing key access and suggest dict.get() or 'in' check?
"""

def get_shipping_label(user_profile):
    address = user_profile["address"]
    # Bug: user profile does not contain 'zipcode'
    zip_code = address["zipcode"]
    return f"{address['city']}, {zip_code}"

if __name__ == "__main__":
    user = {
        "name": "Alice",
        "address": {
            "city": "Bengaluru",
            "country": "India"
        }
    }
    print(get_shipping_label(user))
