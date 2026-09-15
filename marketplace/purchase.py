from main import phone_numbers

def purchase_number(user, selected_number, balance):
 for number in phone_numbers:
    if number["number"] == selected_number:
        if number["available"] == False:
            print("already sold")
    
        elif number["available"] == True:
            if balance >= number["price"]:
                number["available"] = False
                debit = balance - number["price"]
                print(f"purchase successful, change: ₦{debit}")
            else:
                print("insufficient balance")
        break
 
purchase_number("angel", "+1 (415) 555-0145", 10000)