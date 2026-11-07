# GrahakNyay Menu Program

while True:

    print("\n===== GRAHAKNYAY MENU =====")
    print("1. About GrahakNyay")
    print("2. Sample Questions")
    print("3. Check Consumer Commission")
    print("0. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        print("GrahakNyay helps consumers understand their rights.")

    elif choice == "2":
        print("Sample Questions:")
        print("1. My laptop stopped working.")
        print("2. Seller refused to replace my product.")
        print("3. How can I file a complaint?")

    elif choice == "3":
        try:
            amount = float(input("Enter product amount: "))

            if amount <= 0:
                print("Please enter a valid positive amount.")

            elif amount <= 5000000:
                print("District Consumer Commission")

            elif amount <= 20000000:
                print("State Consumer Commission")

            else:
                print("National Consumer Commission")

        except ValueError:
            print("Please enter a valid numeric amount.")

    elif choice == "0":
        print("Thank you for using GrahakNyay!")
        break

    else:
        print("Invalid choice. Please try again.")