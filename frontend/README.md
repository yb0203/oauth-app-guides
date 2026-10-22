# Frontend

Next.js (App Router) app for OAuth App Guides. It uses AI SDK UI and AI Elements to render the live generation stream, citations and the "Ask this guide" chat. It talks to the FastAPI backend in `../backend`, following the protocol in [`../docs/CONTRACT.md`](../docs/CONTRACT.md).

## Pages

| Route | What it does |
|---|---|
| `/` | Short pitch, an "Enter an app name or website" box, and the filterable catalog of 100 apps (verified tier when a guide exists, otherwise a marked guess) |
| `/guides/[slug]` | Guide page: "Your situation" toggles (kept in the URL) → verdict, difficulty ladder, work vs. wait; steps with actor chips, copy buttons and citation hover cards; review, limits, gates, gotchas, "if blocked", "prepared for you", console probe, sources; Markdown export and print layout; the "Ask this guide" panel with Apply actions |
| `/generate?app=…` | Live run view: stage stepper, narration, sources, console probe card, quote-verification meter, then a hand-off to the finished guide with a permanent link. Clear error and partial states, plus a "Demo replay" banner when the backend is in fake mode |

## Run

```bash
npm install
npm run dev            # http://localhost:3000
npm run build          # type-check and production build
```

| Env var | Default | Meaning |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |
| `NEXT_PUBLIC_USE_MOCK` | unset | `1` streams generation from the built-in dev mock instead of the backend |

Deploy with `../scripts/deploy_frontend.sh` (Vercel; deploys from git HEAD).
