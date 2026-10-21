"""Run the OAuth setup recorder on a handful of apps, one Managed Agents session each.

Usage:
  .venv/bin/python run.py                          # all apps in apps.json
  .venv/bin/python run.py --apps github,spotify    # a subset
  .venv/bin/python run.py --apps github --storage-state github=secrets/github_state.json

Outputs land in runs/<timestamp>/<slug>/ (screenshots, steps.json, guide.md, findings.md,
events.jsonl), plus runs/<timestamp>/index.md linking them all.
"""

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
STATE_FILE = HERE / ".state.json"
MAX_WALL_SECONDS = 20 * 60
PRINT_LOCK = threading.Lock()


def log(slug, msg):
    with PRINT_LOCK:
        print(f"[{slug:8}] {msg}", flush=True)


def short(value, limit=110):
    text = value if isinstance(value, str) else json.dumps(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def kickoff_message(app, logged_in):
    docs = "\n".join(f"- {u}" for u in app["docs_urls"])
    mode = "logged_in" if logged_in else "public"
    return (
        f"Provider: {app['name']}\n"
        f"Console URL: {app['console_url']}\n"
        f"Docs URLs:\n{docs}\n"
        f"Run mode: {mode}\n\n"
        "Record how a developer creates an OAuth app here, following your instructions. "
        "Write the outputs to /mnt/session/outputs/."
    )


def stream_session(client, session_id, app, logged_in, events_file):
    """Stream events until the agent settles. Returns the final stop reason."""
    slug = app["slug"]
    started = time.monotonic()
    stop = "unknown"
    with client.beta.sessions.events.stream(session_id=session_id) as stream:
        # Stream first, then send, so no early events are missed.
        client.beta.sessions.events.send(
            session_id=session_id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": kickoff_message(app, logged_in)}]}],
        )
        for event in stream:
            events_file.write(event.model_dump_json() + "\n")
            events_file.flush()

            if event.type == "agent.tool_use":
                detail = event.input.get("command") or event.input.get("url") or event.input.get("file_path") or event.input
                log(slug, f"tool {event.name}: {short(detail)}")
                if event.evaluated_permission == "ask":
                    # Nobody is watching approvals in this experiment: deny anything the server flags.
                    log(slug, "  -> paused for approval; denying (unattended run)")
                    client.beta.sessions.events.send(
                        session_id=session_id,
                        events=[{"type": "user.tool_confirmation", "tool_use_id": event.id, "result": "deny"}],
                    )
                elif event.evaluated_permission == "deny":
                    log(slug, "  -> denied by the server's auto policy")
            elif event.type == "agent.message":
                text = "".join(b.text for b in event.content if b.type == "text")
                if text.strip():
                    log(slug, f"says: {short(text, 200)}")
            elif event.type == "session.error":
                log(slug, f"ERROR: {short(event.model_dump(), 300)}")
            elif event.type == "session.status_idle":
                stop = event.stop_reason.type
                if stop != "requires_action":
                    break
            elif event.type == "session.status_terminated":
                stop = "terminated"
                break

            if time.monotonic() - started > MAX_WALL_SECONDS:
                log(slug, "wall-clock cap reached; interrupting")
                client.beta.sessions.events.send(session_id=session_id, events=[{"type": "user.interrupt"}])
                stop = "wall_clock_cap"
                break
    return stop


def download_outputs(client, session_id, out_dir):
    names = []
    for attempt in range(4):
        files = list(client.beta.files.list(scope_id=session_id, betas=["managed-agents-2026-04-01"]))
        if files:
            for f in files:
                client.beta.files.download(f.id).write_to_file(out_dir / Path(f.filename).name)
                names.append(f.filename)
            return names
        time.sleep(2 + attempt * 2)  # outputs appear a few seconds after the session goes idle
    return names


def run_app(client, state, app, budget_cents, storage_state, run_dir):
    slug = app["slug"]
    out_dir = run_dir / slug
    out_dir.mkdir(parents=True)

    resources = []
    if storage_state:
        with open(storage_state, "rb") as fh:
            uploaded = client.beta.files.upload(file=fh)
        resources.append({"type": "file", "file_id": uploaded.id, "mount_path": "/storage_state.json"})

    session = client.beta.sessions.create(
        agent={"type": "agent", "id": state["agent_id"], "version": state["agent_version"]},
        environment_id=state["environment_id"],
        title=f"OAuth capture: {app['name']}",
        budget={"type": "limit", "max_list_cost": {"amount": str(budget_cents), "currency": "USD"}},
        resources=resources,
    )
    log(slug, f"session {session.id}")
    log(slug, f"trace: https://platform.claude.com/workspaces/default/sessions/{session.id}")

    started = time.monotonic()
    with open(out_dir / "events.jsonl", "w") as events_file:
        try:
            stop = stream_session(client, session.id, app, bool(storage_state), events_file)
        except anthropic.APIConnectionError as exc:
            log(slug, f"stream dropped ({exc}); polling until idle")
            stop = "stream_dropped"
            while time.monotonic() - started < MAX_WALL_SECONDS:
                if client.beta.sessions.retrieve(session.id).status in ("idle", "terminated"):
                    break
                time.sleep(5)

    files = download_outputs(client, session.id, out_dir)
    final = client.beta.sessions.retrieve(session.id)
    summary = {
        "app": slug,
        "session_id": session.id,
        "stop_reason": stop,
        "seconds": round(time.monotonic() - started),
        "files": files,
        "usage": final.usage.model_dump() if getattr(final, "usage", None) else None,
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    log(slug, f"done: stop={stop}, {len(files)} files, {summary['seconds']}s")
    return summary


def write_index(run_dir, summaries):
    lines = [f"# OAuth capture run {run_dir.name}", "", "| App | Stop | Seconds | Files | Guide | Findings |", "|---|---|---|---|---|---|"]
    for s in summaries:
        slug = s["app"]
        guide = f"[guide]({slug}/guide.md)" if "guide.md" in [Path(f).name for f in s["files"]] else "missing"
        findings = f"[findings]({slug}/findings.md)" if "findings.md" in [Path(f).name for f in s["files"]] else "missing"
        lines.append(f"| {slug} | {s['stop_reason']} | {s['seconds']} | {len(s['files'])} | {guide} | {findings} |")
    (run_dir / "index.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apps", help="comma-separated slugs from apps.json (default: all)")
    parser.add_argument("--budget-usd", type=float, default=4.0, help="hard spend cap per session")
    parser.add_argument("--storage-state", action="append", default=[], metavar="SLUG=PATH",
                        help="signed-in browser state for an app (see login_capture.py)")
    args = parser.parse_args()

    if not STATE_FILE.exists():
        raise SystemExit("No .state.json yet. Run provision.py first.")
    state = json.loads(STATE_FILE.read_text())

    apps = json.loads((HERE / "apps.json").read_text())
    if args.apps:
        wanted = set(args.apps.split(","))
        apps = [a for a in apps if a["slug"] in wanted]
    storage = dict(item.split("=", 1) for item in args.storage_state)

    run_dir = HERE / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True)

    client = anthropic.Anthropic()
    budget_cents = int(args.budget_usd * 100)
    with ThreadPoolExecutor(max_workers=len(apps)) as pool:
        futures = [pool.submit(run_app, client, state, app, budget_cents, storage.get(app["slug"]), run_dir) for app in apps]
        summaries = []
        for app, fut in zip(apps, futures):
            try:
                summaries.append(fut.result())
            except Exception as exc:  # keep the other apps' results
                log(app["slug"], f"FAILED: {exc!r}")
                summaries.append({"app": app["slug"], "stop_reason": f"error: {exc!r}", "seconds": 0, "files": []})

    write_index(run_dir, summaries)
    print(f"\nResults: {run_dir / 'index.md'}")


if __name__ == "__main__":
    main()
