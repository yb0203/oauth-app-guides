"""Read-only browser capture for the OAuth setup POC.

It only navigates, scrolls and takes screenshots. It never types, clicks or submits.

  capture.py shot  URL OUT.png [--find TEXT] [--full]   screenshot (optionally scrolled to TEXT)
  capture.py text  URL OUT.txt                          save the page's visible text
  capture.py quote URL "exact quote"                    check a quote appears on the live page

Each command prints one JSON line: requested and final URL, redirect chain, HTTP status,
title, and (for shot) whether --find matched.
"""

import argparse
import json
import re
import sys

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def normalize(text):
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def open_page(p, url):
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(viewport={"width": 1280, "height": 800}, user_agent=UA).new_page()
    chain = []
    page.on("framenavigated", lambda f: f == page.main_frame and chain.append(f.url))
    resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PWTimeout:
        pass  # busy pages (analytics, long polling) never go idle; the DOM is loaded anyway
    page.wait_for_timeout(1500)
    info = {
        "requested_url": url,
        "final_url": page.url,
        "redirect_chain": list(dict.fromkeys(chain)),
        "status": resp.status if resp else None,
        "title": page.title(),
    }
    return browser, page, info


def cmd_shot(args):
    with sync_playwright() as p:
        browser, page, info = open_page(p, args.url)
        clip = None
        if args.find:
            loc = page.get_by_text(args.find, exact=False).first
            try:
                loc.scroll_into_view_if_needed(timeout=5000)
                # Crop the full page around the match, starting a little above it for context.
                # Works whatever element scrolls and avoids sticky headers covering the match.
                top = loc.evaluate("e => e.getBoundingClientRect().top + window.scrollY")
                height = page.evaluate("document.documentElement.scrollHeight")
                y = max(0, min(top - 160, height - 800))
                clip = {"x": 0, "y": y, "width": 1280, "height": min(800, height)}
                info["find_matched"] = True
            except PWTimeout:
                info["find_matched"] = False
        if clip:
            page.screenshot(path=args.out, full_page=True, clip=clip)
        else:
            page.screenshot(path=args.out, full_page=args.full)
        info["screenshot"] = args.out
        info["visible_text_excerpt"] = " ".join(page.inner_text("body").split())[:600]
        browser.close()
    print(json.dumps(info))


def cmd_text(args):
    with sync_playwright() as p:
        browser, page, info = open_page(p, args.url)
        text = page.inner_text("body")
        browser.close()
    with open(args.out, "w") as fh:
        fh.write(text)
    info["text_file"] = args.out
    info["chars"] = len(text)
    print(json.dumps(info))


def cmd_quote(args):
    with sync_playwright() as p:
        browser, page, info = open_page(p, args.url)
        visible = normalize(page.inner_text("body"))
        # textContent includes collapsed accordions and tabs that innerText skips
        # (Google's help pages hide their limits this way).
        everything = normalize(page.evaluate("document.body.textContent"))
        browser.close()
    needle = normalize(args.quote)
    info["quote"] = args.quote
    info["found_in"] = None
    for where, body in (("visible", visible), ("hidden_section", everything)):
        idx = body.find(needle)
        if idx >= 0:
            info["found_in"] = where
            info["context"] = body[max(0, idx - 80): idx + len(needle) + 80]
            break
    info["found"] = info["found_in"] is not None
    print(json.dumps(info))
    sys.exit(0 if info["found"] else 1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shot")
    s.add_argument("url"); s.add_argument("out")
    s.add_argument("--find"); s.add_argument("--full", action="store_true")
    t = sub.add_parser("text")
    t.add_argument("url"); t.add_argument("out")
    q = sub.add_parser("quote")
    q.add_argument("url"); q.add_argument("quote")
    args = ap.parse_args()
    {"shot": cmd_shot, "text": cmd_text, "quote": cmd_quote}[args.cmd](args)


if __name__ == "__main__":
    main()
