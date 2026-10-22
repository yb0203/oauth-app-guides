"""Timed batch of live generations against production, with token and cost accounting.

Usage: python3 evals/perf.py [App ...]     (defaults to a fixed 5-app set)
Writes evals/runs/perf-<slug>.sse and evals/PERF.json, and prints a Markdown table.

Cost is reported three ways:
  actual_usd       - what the run reports (`data-run-stats.cost_usd`; free models cost 0)
  account_delta    - the change in OpenRouter account usage across the whole batch (GET /api/v1/key)
  paid_equivalent  - the same tokens priced at the paid (non-":free") variant of each model, from
                     OpenRouter's public model list
The OpenRouter key is read from backend/.env and never printed.
"""

import json
import os
import pathlib
import ssl
import sys
import time
import urllib.request

try:  # python.org builds on macOS ship without CA certs; certifi fixes that
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _CTX = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "https://oauth-guides-api.vercel.app"
APPS = sys.argv[1:] or ["GitHub", "Gmail", "Spotify", "Asana", "Notion"]


def openrouter_key():
    for line in (ROOT / "backend" / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def account_usage(key):
    if not key:
        return None
    req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
        return json.load(r).get("data", {}).get("usage")


def paid_prices():
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60, context=_CTX) as r:
        models = json.load(r)["data"]
    return {m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"])) for m in models}


def run(app):
    slug = app.lower().replace(".", "-").replace(" ", "-")
    tag = os.getenv("PERF_MODEL", "default").split("/")[-1].replace(":free", "")
    out = ROOT / "evals" / "runs" / f"perf-{tag}-{slug}.sse"
    req = urllib.request.Request(f"{API}/api/generate", data=json.dumps({"app": app, **({"config": {"model": os.environ["PERF_MODEL"]}} if os.getenv("PERF_MODEL") else {})}).encode(),
                                 headers={"content-type": "application/json"})
    start = time.monotonic()
    stats, guide_ok = None, False
    with urllib.request.urlopen(req, timeout=330, context=_CTX) as r, open(out, "w") as fh:
        for raw in r:
            line = raw.decode()
            fh.write(line)
            if line.startswith("data:") and '"type":"data-run-stats"' in line:
                stats = json.loads(line[5:])["data"]
            if line.startswith("data:") and '"type":"data-guide"' in line:
                guide_ok = True
    return {"app": app, "client_seconds": round(time.monotonic() - start, 1), "guide": guide_ok, "stats": stats}


def main():
    key = openrouter_key()
    prices = paid_prices()
    before = account_usage(key)
    results = []
    for app in APPS:
        res = run(app)
        st = res["stats"] or {}
        paid, unpriced = 0.0, []
        for model, u in (st.get("llm", {}).get("by_model") or {}).items():
            p = prices.get(model.removesuffix(":free"))
            if p and u.get("input_tokens") is not None:
                paid += u["input_tokens"] * p[0] + (u.get("output_tokens") or 0) * p[1]
            else:  # free-only model with no paid variant, or no usage reported
                unpriced.append(model)
        res["paid_equivalent_usd"] = round(paid, 4)
        res["unpriced_models"] = unpriced
        results.append(res)
        print(f"{app}: {res['client_seconds']} s, guide={res['guide']}", file=sys.stderr)
    after = account_usage(key)
    summary = {"apps": results, "account_usage_before": before, "account_usage_after": after,
               "account_delta_usd": None if before is None or after is None else round(after - before, 6)}
    (ROOT / "evals" / f"PERF-{os.getenv('PERF_MODEL', 'default').split('/')[-1].replace(':free', '')}.json").write_text(json.dumps(summary, indent=2))

    print("| App | Total time | Slowest stage | LLM calls (failed) | Input tokens | Output tokens | Actual cost | Paid-model equivalent |")
    print("|---|---|---|---|---|---|---|---|")
    for r in results:
        st = r["stats"] or {}
        llm = st.get("llm", {})
        stages = st.get("stages") or {}
        slow = max(stages.items(), key=lambda kv: kv[1].get("seconds") or 0, default=(None, {}))
        print(f"| {r['app']} | {st.get('total_seconds', r['client_seconds'])} s | {slow[0]} ({slow[1].get('seconds')} s) | "
              f"{llm.get('calls')} ({llm.get('failed_calls')}) | {llm.get('input_tokens')} | {llm.get('output_tokens')} | "
              f"${st.get('cost_usd', 0):.2f} | ${r['paid_equivalent_usd']:.4f}" + (f" (excl. {', '.join(r['unpriced_models'])})" if r['unpriced_models'] else "") + " |")
    print(f"\nOpenRouter account usage change across the batch: {summary['account_delta_usd']}")


if __name__ == "__main__":
    main()
