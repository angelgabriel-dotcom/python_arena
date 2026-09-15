phone_numbers = [
        {"number": "+1 (212) 555-0164", "price": 5000, "available": True},
        {"number": "+1 (310) 555-0170", "price": 5000, "available": True},
        {"number": "+1 (312) 555-0139", "price": 5000, "available": True},
        {"number": "+1 (415) 555-0145", "price": 5000, "available": False},
        {"number": "+1 (305) 555-0152", "price": 5000, "available": False},
    ]

def list_numbers():
    for numbers in phone_numbers:
        if numbers["available"] == True:
            print_format = f"available:  {numbers['number']} | ₦{numbers['price']}"
            print(print_format)
        else:
            print("not available")
list_numbers()


