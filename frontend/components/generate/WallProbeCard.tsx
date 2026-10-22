"use client";

import { ChevronRightIcon, LockKeyholeIcon, ShieldCheckIcon, ShieldAlertIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Chip, fmtDate } from "@/components/guide/shared";
import type { WallProbe } from "@/types/guide";
import { Panel } from "./Panel";
import { hostOf } from "./run-info";

const OUTCOME = {
  login_wall: { label: "Sign-in wall", Icon: LockKeyholeIcon, classes: "border-warning-border bg-warning-soft text-warning" },
  console_reachable: { label: "Console reachable", Icon: ShieldCheckIcon, classes: "border-success-border bg-success-soft text-success" },
  blocked: { label: "Blocked", Icon: ShieldAlertIcon, classes: "border-danger-border bg-danger-soft text-danger" },
  error: { label: "Couldn't reach", Icon: ShieldAlertIcon, classes: "border-border bg-muted text-muted-foreground" },
} as const;

function shortUrl(url: string) {
  try {
    const u = new URL(url);
    return `${u.hostname.replace(/^www\./, "")}${u.pathname === "/" ? "" : u.pathname}`;
  } catch {
    return url;
  }
}

/** First clause of "GitHub account: username or email and password, Google" is the account the console needs. */
function headline(w: WallProbe): string {
  const host = w.wall_host ? hostOf(`https://${w.wall_host}`) : hostOf(w.console_url);
  const who = w.asks_for.split(":")[0]?.trim();
  switch (w.outcome) {
    case "login_wall":
      return who ? `Console needs a ${who.replace(/^an? /i, "")}` : `Console needs a sign-in at ${host}`;
    case "console_reachable":
      return "Console opens without signing in";
    case "blocked":
      return `Console blocked the probe at ${host}`;
    default:
      return "The console could not be probed";
  }
}

/** The sign-in wall observation as one compact card. Hidden until the probe has something to show. */
export function WallProbeCard({ wall }: { wall: WallProbe }) {
  const o = OUTCOME[wall.outcome] ?? OUTCOME.error;
  const seen = fmtDate(wall.observed_at);
  const chain = wall.redirect_chain.length ? wall.redirect_chain : [wall.console_url];
  return (
    <Panel title="Console probe">
      <div className="animate-in fade-in space-y-3 duration-300 motion-reduce:animate-none">
        <div className="flex items-start gap-3">
          <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-lg border", o.classes)}>
            <o.Icon className="size-4" aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="text-sm leading-snug font-medium text-foreground">{headline(wall)}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Seen {seen} · {wall.method === "browser" ? "headless browser" : "plain request"} ·{" "}
              {wall.bot_check ? "bot check present" : "no bot check"}
            </p>
          </div>
          <Chip className={cn("ml-auto hidden sm:inline-flex", o.classes)}>{o.label}</Chip>
        </div>
        {wall.asks_for && <p className="text-sm break-words text-muted-foreground">Asks for: {wall.asks_for}</p>}
        <ol aria-label="Redirect path" className="flex flex-wrap items-center gap-1 text-xs">
          {chain.map((u, i) => (
            <li key={`${u}-${i}`} className="flex min-w-0 items-center gap-1">
              <span title={u} className="max-w-[14rem] truncate rounded-md border bg-muted/50 px-1.5 py-0.5 font-mono text-foreground">
                {shortUrl(u)}
              </span>
              {i < chain.length - 1 && <ChevronRightIcon className="size-3 shrink-0 text-muted-foreground" aria-label="redirects to" />}
            </li>
          ))}
        </ol>
      </div>
    </Panel>
  );
}
