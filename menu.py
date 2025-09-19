# menu.py
import os
import json
import time
import random
from modules.client import FBClient
from modules.group_actions import fetch_all_posts, react_post_simple, comment_on_post
from modules.poll_vote import vote_poll

CONFIG = "config.json"

def load_config():
    if not os.path.exists(CONFIG):
        print("Error: config.json not found in repo root.")
        return None
    with open(CONFIG, "r") as f:
        return json.load(f)

def banner(text="DARKXPRIME"):
    os.system("clear")
    try:
        from pyfiglet import Figlet
        f = Figlet(font="doom")
        print("\033[1;36m" + f.renderText(text) + "\033[0m")
    except Exception:
        print("==== " + text + " ====")

def get_client(acc, settings):
    uid = acc.get("uid")
    pwd = acc.get("password")
    cookie = acc.get("cookie")
    print(f"\n[Login] Starting for account: {uid}")
    client = FBClient(uid=uid, password=pwd, cookie_str=cookie, user_agent=settings.get("user_agent"))
    ok, msg = client.login()
    if ok:
        print(f"[Login] {uid} -> SUCCESS ({msg})")
        return client
    else:
        print(f"[Login] {uid} -> FAILED ({msg})")
        return None

def ask_post_id_or_url(prompt="Enter post id or full mbasic/story URL: "):
    v = input(prompt).strip()
    # accept full urls like https://mbasic.facebook.com/story.php?story_fbid=123...
    # or numeric id; return post id if possible
    if v.startswith("http"):
        # try extract story_fbid param
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(v).query)
        if "story_fbid" in q:
            return q["story_fbid"][0]
        # fallback: try digits at end
        parts = v.rstrip("/").split("/")
        for p in reversed(parts):
            if p.isdigit():
                return p
        return v
    return v

def main_menu():
    cfg = load_config()
    if not cfg:
        return
    settings = cfg.get("settings", {})
    group = cfg.get("group", {})

    while True:
        banner("DARKXPRIME")
        print("[1] Group Automation (fetch -> react + comment on each post)")
        print("[2] React on Target Post (asks for post id/url)")
        print("[3] Comment on Target Post (asks for post id/url)")
        print("[4] Vote on Poll (asks for post id and option index)")
        print("[5] Add Account (save in config.json)")
        print("[0] Exit")
        ch = input("\nChoose option: ").strip()

        if ch == "1":
            # group automation
            for acc in cfg.get("accounts", []):
                if not acc.get("active", True):
                    print(f"[SKIP] account {acc.get('uid')} inactive")
                    continue
                client = get_client(acc, settings)
                if not client:
                    continue
                print(f"[Fetch] Fetching posts for group {group.get('id')}")
                posts = fetch_all_posts(client, group.get("id"), max_pages=group.get("max_pages", 5),
                                        logger=print, debug=cfg.get("debug", False))
                print(f"[Fetch] Total posts fetched: {len(posts)}")
                for idx, p in enumerate(posts, start=1):
                    pid = p.get("post_id")
                    print(f"\n[Post {idx}/{len(posts)}] post_id={pid} url={p.get('post_url')}")
                    # react
                    reaction = random.choice(group.get("reactions", ["like"]))
                    ok, msg = react_post_simple(client, pid, reaction=reaction, logger=print, dry_run=cfg.get("dry_run", True))
                    print(f"[React] Account={acc.get('uid')} Reaction={reaction} -> {ok} ({msg})")
                    time.sleep(random.uniform(settings.get("reaction_delay_min",5), settings.get("reaction_delay_max",10)))
                    # comment
                    comment_text = random.choice(group.get("comment_texts", ["🔥"]))
                    ok2, msg2 = comment_on_post(client, pid, comment_text, logger=print, dry_run=cfg.get("dry_run", True))
                    print(f"[Comment] Account={acc.get('uid')} Text='{comment_text}' -> {ok2} ({msg2})")
                    time.sleep(random.uniform(settings.get("comment_delay_min",6), settings.get("comment_delay_max",12)))
                print(f"[DONE] Account {acc.get('uid')} finished.\n")
            input("Press Enter to return to menu...")

        elif ch == "2":
            post = ask_post_id_or_url("Enter target post id or URL: ")
            reaction = input("Enter reaction (like/love/care/haha/wow/sad/angry) [like]: ").strip().lower() or "like"
            for acc in cfg.get("accounts", []):
                if not acc.get("active", True): continue
                client = get_client(acc, settings)
                if not client: continue
                ok, msg = react_post_simple(client, post, reaction=reaction, logger=print, dry_run=cfg.get("dry_run", True))
                print(f"[{acc.get('uid')}] React -> {ok}, {msg}")
                time.sleep(random.uniform(1,3))
            input("Press Enter to return to menu...")

        elif ch == "3":
            post = ask_post_id_or_url("Enter target post id or URL: ")
            text = input("Enter comment text (or leave blank to use random): ").strip()
            for acc in cfg.get("accounts", []):
                if not acc.get("active", True): continue
                client = get_client(acc, settings)
                if not client: continue
                comment_text = text or random.choice(group.get("comment_texts", ["🔥"]))
                ok, msg = comment_on_post(client, post, comment_text, logger=print, dry_run=cfg.get("dry_run", True))
                print(f"[{acc.get('uid')}] Comment -> {ok}, {msg}")
                time.sleep(random.uniform(1,3))
            input("Press Enter to return to menu...")

        elif ch == "4":
            post = ask_post_id_or_url("Enter poll post id or URL (story_fbid): ")
            try:
                opt = int(input("Enter option index (0-based): ").strip())
            except:
                opt = 0
            for acc in cfg.get("accounts", []):
                if not acc.get("active", True): continue
                client = get_client(acc, settings)
                if not client: continue
                ok, msg = vote_poll(client, post, option_index=opt, logger=print, dry_run=cfg.get("dry_run", True))
                print(f"[{acc.get('uid')}] Vote -> {ok}, {msg}")
                time.sleep(1)
            input("Press Enter to return to menu...")

        elif ch == "5":
            # add account
            uid = input("UID (email/phone): ").strip()
            pwd = input("Password: ").strip()
            cfg["accounts"].append({"uid": uid, "password": pwd, "active": True})
            with open(CONFIG, "w") as f:
                json.dump(cfg, f, indent=2)
            print("Account added to config.json")
            input("Press Enter to return to menu...")

        elif ch == "0":
            print("Exiting DARKXPRIME. Bye.")
            break
        else:
            print("Invalid choice.")
            time.sleep(1)