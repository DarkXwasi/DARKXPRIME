Create main.py at repo root:

# main.py
from menu import main_menu

if __name__ == "__main__":
    main_menu()
import os
import subprocess

def auto_update():
    if os.path.exists(".git"):
        print("[UPDATER] Checking for updates...")
        try:
            subprocess.run(["git", "pull"], check=True)
            print("[UPDATER] Repo updated successfully.\n")
        except Exception as e:
            print(f"[UPDATER] Failed to update: {e}\n")
    else:
        print("[UPDATER] Not a git repo! Please clone with git.\n")

# Run auto-update at start
auto_update()

# Import your menu system
try:
    from menu import main_menu
except ImportError:
    print("Error: Could not import menu. Make sure menu.py exists.")
    exit(1)

if __name__ == "__main__":
    main_menu()

