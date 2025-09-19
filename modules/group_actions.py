Create modules/group_actions.py — uses only html.parser. It expects an FBClient instance with .get/.post and .is_logged_in_response.

# modules/group_actions.py
import os, time, random, re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

BASE = "https://mbasic.facebook.com"

def _save_debug(html, name="debug_page"):
    d = os.path.join(os.path.dirname(__file__), "..", "debug")
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, f"{name}.html")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    return fn

def extract_post_id_from_href(href):
    if not href:
        return None
    if "story.php" in href and "story_fbid" in href:
        try:
            q = parse_qs(urlparse(href).query)
            return q.get("story_fbid", [None])[0]
        except:
            return None
    m = re.search(r"/(?:permalink|posts)/(\d+)", href)
    if m:
        return m.group(1)
    parts = href.rstrip("/").split("/")
    for p in reversed(parts):
        if p.isdigit():
            return p
    return None

def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    for a in soup.find_all("a", href=True):
        pid = extract_post_id_from_href(a["href"])
        if pid:
            full = a["href"] if a["href"].startswith("http") else urljoin(BASE, a["href"])
            posts.append({"post_id": pid, "post_url": full})
    return posts

def find_next_page_link(html):
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        if any(k in txt for k in ("see more posts", "more posts", "older posts", "view more", "see more")):
            href = a["href"]
            return href if href.startswith("http") else urljoin(BASE, href)
    # fallback
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(x in href for x in ("after=", "m_s", "page=")):
            return href if href.startswith("http") else urljoin(BASE, href)
    return None

def fetch_all_posts(client, group_id, max_pages=20, logger=print, debug=False):
    seen = set(); posts = []
    page_url = f"/groups/{group_id}"
    pages = 0

    while page_url and pages < max_pages:
        pages += 1
        logger(f"[Pagination] Fetching page {pages}: {page_url}")
        try:
            r = client.get(page_url)
        except Exception as e:
            logger(f"[Pagination] Request failed: {e}")
            break

        if debug:
            _save_debug(r.text, f"page_{pages}")

        if not client.is_logged_in_response(r):
            logger(f"[Pagination] Not logged in or bad status: {getattr(r,'status_code',None)}")
            break

        new_posts = parse_posts_from_html(r.text)
        added = 0
        for p in new_posts:
            pid = p["post_id"]
            if pid not in seen:
                seen.add(pid)
                posts.append(p)
                added += 1
        logger(f"[Pagination] Page {pages} -> found {len(new_posts)} posts, added {added}")

        next_link = find_next_page_link(r.text)
        if not next_link:
            logger("[Pagination] No next link; stopping.")
            break
        page_url = next_link.replace(BASE, "") if next_link.startswith(BASE) else next_link
        time.sleep(random.uniform(1.0, 2.0))

    logger(f"[Pagination] Completed. Total unique posts: {len(posts)} (pages fetched: {pages})")
    return posts

def react_post_simple(client, post_id, reaction="like", logger=print, dry_run=False):
    """
    Attempts to react on a post. dry_run True => only log.
    reaction: like, love, care, haha, wow, sad, angry (mbasic link heuristics)
    """
    if dry_run:
        logger(f"[DRY RUN] Would react '{reaction}' on {post_id}")
        return True, "dry_run"

    post_url = f"/story.php?story_fbid={post_id}"
    r = client.get(post_url)
    if r.status_code != 200:
        return False, f"status_{r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    react_href = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        txt = (a.get_text() or "").strip().lower()
        if reaction == "like" and (txt == "like" or "like this" in txt):
            react_href = href; break
        if "reaction_type=" in href and reaction in href:
            react_href = href; break
    if not react_href:
        # try open reaction menu and pick first matching link
        for a in soup.find_all("a", href=True):
            if "reactions" in (a.get_text() or "").lower() or "react" in (a.get_text() or "").lower():
                react_href = a["href"]; break
    if not react_href:
        return False, "no_reaction_link"
    target = react_href if react_href.startswith("http") else urljoin(BASE, react_href)
    r2 = client.get(target)
    success = (r2.status_code == 200)
    return success, f"status_{getattr(r2, 'status_code', None)}"

def comment_on_post(client, post_id, text, logger=print, dry_run=False):
    if dry_run:
        logger(f"[DRY RUN] Would comment on {post_id}: {text}")
        return True, "dry_run"
    post_url = f"/story.php?story_fbid={post_id}"
    r = client.get(post_url)
    if r.status_code != 200:
        return False, f"status_{r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    form = None
    for f in soup.find_all("form", action=True):
        if f.find("input", {"name": "comment_text"}) or "comment" in (f.get("action") or ""):
            form = f; break
    if not form:
        form = soup.find("form", action=True)
    if not form:
        return False, "no_comment_form"
    action = form.get("action")
    action = action if action.startswith("http") else urljoin(BASE, action)
    data = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if name:
            data[name] = inp.get("value", "")
    data["comment_text"] = text
    r2 = client.post(action, data=data)
    if r2.status_code == 200:
        # some pages reflect comment immediately
        if text in (r2.text or ""):
            return True, "posted"
        return True, "posted_but_not_verified"
    return False, f"status_{getattr(r2,'status_code',None)}"
