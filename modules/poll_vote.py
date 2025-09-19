# modules/poll_vote.py
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://mbasic.facebook.com"

def vote_poll(client, post_id, option_index=0, logger=print, dry_run=False):
    """
    Try to find poll form on a post and submit a vote.
    option_index is 0-based.
    """
    if dry_run:
        logger(f"[DRY RUN] Would vote on {post_id} option {option_index}")
        return True, "dry_run"

    post_url = f"/story.php?story_fbid={post_id}"
    r = client.get(post_url)
    if r.status_code != 200:
        return False, f"status_{r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    for form in soup.find_all("form", action=True):
        radios = form.find_all("input", {"type": "radio"})
        selects = form.find_all("select")
        if radios:
            if option_index < 0 or option_index >= len(radios):
                return False, "option_index_out_of_range"
            data = {}
            for inp in form.find_all("input"):
                if inp.get("name"):
                    data[inp["name"]] = inp.get("value","")
            chosen = radios[option_index]
            if chosen.get("name"):
                data[chosen["name"]] = chosen.get("value","")
            action = form.get("action")
            action = action if action.startswith("http") else urljoin(BASE, action)
            r2 = client.post(action, data=data)
            return (r2.status_code == 200), f"status_{getattr(r2,'status_code',None)}"
        elif selects:
            sel = selects[0]
            options = sel.find_all("option")
            if option_index < 0 or option_index >= len(options):
                return False, "option_index_out_of_range"
            data = {}
            for inp in form.find_all("input"):
                if inp.get("name"):
                    data[inp["name"]] = inp.get("value","")
            sel_name = sel.get("name")
            data[sel_name] = options[option_index].get("value","")
            action = form.get("action")
            action = action if action.startswith("http") else urljoin(BASE, action)
            r2 = client.post(action, data=data)
            return (r2.status_code == 200), f"status_{getattr(r2,'status_code',None)}"
    return False, "no_poll_form_found"