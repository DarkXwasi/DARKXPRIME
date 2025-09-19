def fetch_all_posts(client, group_id, max_pages=5, logger=None, debug=False):
    seen = set()
    posts = []
    page_url = f"/groups/{group_id}"
    pages = 0

    while page_url and pages < max_pages:
        pages += 1
        if debug:
            print(f"[DEBUG] Fetching page {pages}: {page_url}")
        if logger: logger(f"[Pagination] Fetching page {pages}: {page_url}")
        try:
            r = client.get(page_url)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Request failed: {e}")
            if logger: logger(f"[Pagination] Request failed: {e}")
            break
        if not getattr(client, "is_logged_in_response", lambda x: True)(r):
            if debug:
                print(f"[DEBUG] Not logged in or bad status: {getattr(r,'status_code',None)}")
            if logger: logger(f"[Pagination] Not logged in or bad status: {getattr(r,'status_code',None)}")
            break

        new_posts = parse_posts_from_html(r.text)
        for p in new_posts:
            pid = p.get("post_id")
            if pid and pid not in seen:
                seen.add(pid)
                posts.append(p)
        if debug:
            print(f"[DEBUG] Page {pages} -> total posts {len(posts)}")
        if logger: logger(f"[Pagination] Page {pages} -> total posts {len(posts)}")

        next_link = find_next_page_link(r.text)
        if not next_link:
            break
        if next_link.startswith("https://mbasic.facebook.com"):
            page_url = next_link.replace("https://mbasic.facebook.com", "")
        else:
            page_url = next_link
        time.sleep(random.uniform(1.0, 2.0))

    if debug:
        print(f"[DEBUG] Completed. Total posts: {len(posts)}")
    if logger: logger(f"[Pagination] Completed. Total posts: {len(posts)}")
    return posts