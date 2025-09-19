Create empty file modules/__init__.py:

# modules package


---

4) modules/client.py (REAL login + cookie save/restore)

Create modules/client.py — this performs a mbasic login form submit and saves cookies to sessions/{uid}.json. It will detect if login failed or a checkpoint appeared.

# modules/client.py
import os
import json
import requests
from bs4 import BeautifulSoup
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

BASE = "https://mbasic.facebook.com"
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "sessions")

if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR, exist_ok=True)

class FBClient:
    def __init__(self, uid=None, password=None, cookie_str=None, user_agent=None):
        self.uid = uid
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or "Mozilla/5.0 (Linux; Android 10; Mobile)",
            "Accept-Language": "en-US,en;q=0.9"
        })
        # if cookie string provided, set header
        if cookie_str:
            self.session.headers.update({"Cookie": cookie_str})

    def session_file(self):
        if not self.uid:
            return None
        fn = os.path.join(SESSIONS_DIR, f"{self.uid}.json")
        return fn

    def save_cookies(self):
        fn = self.session_file()
        if not fn:
            return
        d = dict_from_cookiejar(self.session.cookies)
        with open(fn, "w") as f:
            json.dump(d, f)

    def load_cookies(self):
        fn = self.session_file()
        if not fn or not os.path.exists(fn):
            return False
        with open(fn, "r") as f:
            d = json.load(f)
        self.session.cookies = cookiejar_from_dict(d)
        return True

    def get(self, url, **kwargs):
        if not url.startswith("http"):
            url = BASE + url
        return self.session.get(url, **kwargs)

    def post(self, url, data=None, **kwargs):
        if not url.startswith("http"):
            url = BASE + url
        return self.session.post(url, data=data, **kwargs)

    def is_logged_in_response(self, response):
        """Heuristic: logged in if logout button or home link present, or URL shows /home.php"""
        if response is None:
            return False
        txt = (response.text or "").lower()
        if "mbasic_logout_button" in txt:
            return True
        if "/home.php" in getattr(response, "url", ""):
            return True
        # login form content indicates not logged in
        if "login" in txt and "password" in txt:
            return False
        return response.status_code == 200

    def login(self, use_saved_cookies=True):
        """
        Attempt login:
         1) Try load cookies saved for uid (if configured)
         2) If cookies exist and valid -> done
         3) Else perform mbasic form login using uid/password
        Returns: (True, msg) or (False, reason)
        """
        # 1) try saved cookies
        if use_saved_cookies and self.uid:
            loaded = self.load_cookies()
            if loaded:
                try:
                    r = self.get("/")
                    if self.is_logged_in_response(r):
                        return True, "loaded_cookies"
                except Exception:
                    pass
        # 2) try cookie header if provided in session headers
        try:
            r = self.get("/")
            if self.is_logged_in_response(r):
                # save cookies
                if self.uid:
                    self.save_cookies()
                return True, "already_logged"
        except Exception:
            pass

        # 3) perform form login if uid/password provided
        if not (self.uid and self.password):
            return False, "no_credentials"

        try:
            r = self.get("/login")
            soup = BeautifulSoup(r.text, "html.parser")
            form = soup.find("form")
            if not form:
                return False, "no_login_form"

            action = form.get("action") or "/login"
            action = action if action.startswith("http") else BASE + action

            data = {}
            # collect form inputs
            for inp in form.find_all("input", {"name": True}):
                name = inp["name"]
                value = inp.get("value", "")
                data[name] = value

            # fill in common names
            # prefer 'email'/'pass' fields, fallback set
            if "email" in data:
                data["email"] = self.uid
            else:
                data["email"] = self.uid
            if "pass" in data:
                data["pass"] = self.password
            else:
                data["pass"] = self.password

            # submit login
            r2 = self.session.post(action, data=data)
            # If Facebook prompts checkpoint/2fa, page will contain words like 'security' or 'we detected'
            txt = (r2.text or "").lower()
            if "checkpoint" in txt or "security" in txt or "two-factor" in txt or "suspended" in txt:
                return False, "checkpoint_or_2fa"
            if not self.is_logged_in_response(r2):
                # maybe redirected to login page again
                return False, "login_failed"
            # success
            if self.uid:
                self.save_cookies()
            return True, "login_ok"
        except Exception as e:
            return False, f"exception:{e}"

Notes about client.py

login() returns (True, msg) or (False, reason). Check the reason in your code and stop if checkpoint.

Cookies saved at sessions/{uid}.json for reuse.


