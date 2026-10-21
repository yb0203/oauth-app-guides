# GitHub capture findings (pilot, run by the main session)

- **Captured:** the console wall (1 redirect to `github.com/login`, no bot check, no cookie banner), two cropped docs screenshots covering all 11 documented steps, and 3 of 3 quotes verified on the live page.
- **Stopped at:** sign-in. The real "Register a new OAuth app" form was never seen.
- **Human must:** sign in, type the values, click Register, generate the secret, paste it into Composio.
- **Flaky or fixed during the pilot:** the first screenshots used mouse-wheel scrolling, which doesn't move GitHub Docs' scroll container, so the target heading was hidden. I switched to cropping the full-page render around the matched text, which works.
- **Time:** about 2 minutes of tool time for 1 console shot, 2 docs shots and 3 quote checks.
- **Verdict:** useful but limited. The docs screenshots plus a verified login wall give most of a guide for an instant-tier app. The one thing a reader would really want, a picture of the actual form with the callback field filled in, needs a signed-in human, or the logged-in handoff mode.
