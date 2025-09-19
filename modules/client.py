# modules/client.py
import requests

class FBClient:
    def __init__(self, uid=None, password=None, cookie_str=None, user_agent=None):
        self.session = requests.Session()
        self.uid = uid
        self.password = password
        self.cookie_str = cookie_str
        self.user_agent = user_agent or "Mozilla/5.0 (Linux; Android 9; Mobile)"
        self.logged_in = False

        if self.cookie_str:
            self._load_cookie()

    def _load_cookie(self):
        cookies = {}
        for c in self.cookie_str.split(";"):
            if "=" in c:
                k, v = c.strip().split("=", 1)
                cookies[k.strip()] = v.strip()
        self.session.cookies.update(cookies)
        self.session.headers.update({"User-Agent": self.user_agent})

    def login(self):
        if self.cookie_str:
            self.logged_in = True
            return True, "cookie_login"
        if self.uid and self.password:
            # dummy login placeholder (real login bypass not implemented)
            self.logged_in = True
            return True, "uid_pass_login"
        return False, "no_credentials"

    def is_logged_in_response(self, resp):
        return resp is not None and resp.status_code == 200

    def get(self, url, **kwargs):
        if not url.startswith("http"):
            url = "https://mbasic.facebook.com" + url
        return self.session.get(url, **kwargs)

    def post(self, url, data=None, **kwargs):
        if not url.startswith("http"):
            url = "https://mbasic.facebook.com" + url
        return self.session.post(url, data=data, **kwargs)