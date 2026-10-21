"""Optional: sign in yourself, locally, and hand the browser state to the agent.

This is the "human does the login, agent does the rest" test. It opens a visible
Chromium window at the app's console URL. You sign in by hand (use a throwaway or
test account), then press Enter here. The signed-in state is saved to
secrets/<slug>_state.json, which run.py can upload with --storage-state.

The saved file holds live session cookies: treat it like a password, never commit it,
and delete it after the run. Requires: .venv/bin/pip install playwright && .venv/bin/playwright install chromium
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: login_capture.py <slug>")
    slug = sys.argv[1]
    app = next((a for a in json.loads((HERE / "apps.json").read_text()) if a["slug"] == slug), None)
    if app is None:
        raise SystemExit(f"unknown slug {slug!r}")

    out = HERE / "secrets" / f"{slug}_state.json"
    out.parent.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.new_page().goto(app["console_url"])
        input(f"Sign in to {app['name']} in the browser window, then press Enter here... ")
        context.storage_state(path=str(out))
        browser.close()
    print(f"Saved {out}. Run: .venv/bin/python run.py --apps {slug} --storage-state {slug}={out}")


if __name__ == "__main__":
    main()
