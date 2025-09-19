Create menu.py at repo root:

# menu.py
import os, json, time, random
from pyfiglet import Figlet
from modules.client import FBClient
from modules.group_actions import (fetch_all_posts, react_post_simple, comment_on_post)
from modules.poll_vote import vote_poll

CONFIG = "config.json"

def load_config():
    if not os.path.exists(CONFIG):
        print("config.json not found")
        return None
    with open(CONFIG) as f:
        return json.load(f)

def banner(text="DARKXPRIME"):
    os.system("clear")
    f = Figlet(font="doom")
    print("\033[1;36m" + f.renderText(text) + "\033[0m")

def get_client(acc, settings):
    # server: try saved cookies first; else use uid/password to login
    uid = acc.get("uid")
    pwd = acc.get("password")
    cookie = acc.get("cookie")
    client = FBClient(uid=uid, password=pwd, cookie_str=cookie, user_agent=settings.get("user_agent"))
    ok, msg = client.login()
    if not ok:
        print(f"[Login] {uid} -> failed: {msg}")
        return None
    print(f"[Login] {uid} -> ok ({msg})")
    return client

def main_menu():
    cfg = load_config()
    if not cfg:
        return
    settings = cfg.get("settings", {})
    accounts = cfg.get("accounts", [])
    group = cfg.get("group", {})

    banner("DARKXPRIME")
    print("[1] Group Automation (fetch -> react+comment)")
    print("[2] Vote on Poll (single post)")
    print("[3] React on Target Post")
    print("[4] Comment on Target Post")
    print("[5] Add Account (and save to config)")
    print("[0] Exit")
    ch = input("Choose: ").strip()

    if ch == "1":
        for acc in accounts:
            if not acc.get("active", True): continue
            client = get_client(acc, settings)
            if not client: continue
            posts = fetch_all_posts(client, group["id"], max_pages=group.get("max_pages", 5),
                                    logger=print, debug=cfg.get("debug", False))
            print(f"[Posts] Found {len(posts)} posts")
            for p in posts:
                pid = p["post_id"]
                reaction = random.choice(group.get("reactions", ["like"]))
                ok,msg = react_post_simple(client, pid, reaction=reaction, logger=print, dry_run=cfg.get("dry_run", True))
                print(f"[React] {pid} -> {ok}, {msg}")
                time.sleep(random.uniform(settings.get("reaction_delay_min",5), settings.get("reaction_delay_max",10)))
                ctext = random.choice(group.get("comment_texts", ["🔥"]))
                ok2,msg2 = comment_on_post(client, pid, ctext, logger=print, dry_run=cfg.get("dry_run", True))
                print(f"[Comment] {pid} -> {ok2}, {msg2}")
                time.sleep(random.uniform(settings.get("comment_delay_min",6), settings.get("comment_delay_max",12)))
    elif ch == "2":
        post = input("Enter post id (story_fbid): ").strip()
        opt = int(input("Option index (0-based): ").strip())
        for acc in accounts:
            if not acc.get("active", True): continue
            client = get_client(acc, settings)
            if not client: continue
            ok,msg = vote_poll(client, post, option_index=opt, logger=print, dry_run=cfg.get("dry_run", True))
            print(f"[{acc.get('uid')}] vote -> {ok}, {msg}")
            time.sleep(1)
    elif ch == "3":
        post = input("Enter post id: ").strip()
        reaction = input("Reaction (like/love/care/haha/wow/sad/angry): ").strip().lower() or "like"
        for acc in accounts:
            if not acc.get("active", True): continue
            client = get_client(acc, settings)
            if not client: continue
            ok,msg = react_post_simple(client, post, reaction=reaction, logger=print, dry_run=cfg.get("dry_run", True))
            print(f"[{acc.get('uid')}] react -> {ok}, {msg}")
            time.sleep(1)
    elif ch == "4":
        post = input("Enter post id: ").strip()
        text = input("Enter comment text (or leave empty to pick random): ").strip()
        for acc in accounts:
            if not acc.get("active", True): continue
            client = get_client(acc, settings)
            if not client: continue
            comment_text = text or random.choice(group.get("comment_texts", ["🔥"]))
            ok,msg = comment_on_post(client, post, comment_text, logger=print, dry_run=cfg.get("dry_run", True))
            print(f"[{acc.get('uid')}] comment -> {ok}, {msg}")
            time.sleep(1)
    elif ch == "5":
        # add account to config
        uid = input("UID (email/phone): ").strip()
        pwd = input("Password: ").strip()
        cfg["accounts"].append({"uid": uid, "password": pwd, "active": True})
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        print("Saved to config.json")
    else:
        print("Exiting.")