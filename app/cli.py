# GrahakNyay Command Line Application

from app.records import count_by, get_by_id, load_records, search

while True:
    print("\n========== GRAHAKNYAY ==========")
    print("1. Display All Records")
    print("2. Search Records")
    print("3. Count Records by Category")
    print("4. Find Record by ID")
    print("0. Exit")

    choice = input("\nEnter your choice: ")

    # Display all records
    if choice == "1":
        records = load_records()

        for record in records:
            print("\nID:", record["id"])
            print("Title:", record["provision_title"])
            print("Section:", record["section_or_rule"])
            print("Summary:", record["plain_summary"])

    # Search records
    elif choice == "2":
        keyword = input("Enter keyword: ")

        results = search(keyword)

        if results:
            for record in results:
                print("\nID:", record["id"])
                print("Title:", record["provision_title"])
                print("Section:", record["section_or_rule"])
        else:
            print("No records found.")

    # Count records by category
    elif choice == "3":
        counts = count_by()

        for category in counts:
            print(category, ":", counts[category])

    # Find record by ID
    elif choice == "4":
        try:
            record_id = int(input("Enter record ID: "))

            record = get_by_id(record_id)

            if record:
                print("\nTitle:", record["provision_title"])
                print("Section:", record["section_or_rule"])
                print("Summary:", record["plain_summary"])
            else:
                print("Record not found.")

        except ValueError:
            print("Please enter a valid numeric ID.")

    # Exit
    elif choice == "0":
        print("Thank you for using GrahakNyay!")
        break

    else:
        print("Invalid choice. Please try again.")
