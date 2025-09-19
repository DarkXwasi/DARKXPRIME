# main.py
import os
import subprocess

def auto_update():
    if os.path.exists(".git"):
        print("[UPDATER] Checking for updates...")
        try:
            subprocess.run(["git", "fetch", "--all"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            local = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()
            remote = subprocess.check_output(["git", "rev-parse", "@{u}"]).strip()
            if local != remote:
                print("[UPDATER] Remote changed — pulling latest...")
                subprocess.run(["git", "pull"], check=True)
                print("[UPDATER] Updated.")
            else:
                print("[UPDATER] Already up-to-date.")
        except Exception as e:
            print(f"[UPDATER] Update check failed: {e}")
    else:
        print("[UPDATER] Not a git repo — skip auto-update.")

# run updater then menu
if __name__ == "__main__":
    auto_update()
    try:
        from menu import main_menu
    except Exception as e:
        print("Error importing menu.py:", e)
        raise
    main_menu()