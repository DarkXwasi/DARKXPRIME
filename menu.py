def main_menu():
    print("🔥 DARKXPRIME 🔥")
    print("1. Facebook Group Automation")
    print("2. Reacts on Post")
    print("3. Poll Voting")
    print("4. Exit")

    choice = input("Select option: ")
    if choice == "1":
        print("👉 Group Automation running...")
    elif choice == "2":
        print("👉 Reacting on post...")
    elif choice == "3":
        print("👉 Poll voting started...")
    else:
        print("Exiting...")