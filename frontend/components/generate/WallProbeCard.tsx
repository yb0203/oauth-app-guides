"use client";

import { ChevronRightIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/guide/shared";
import type { WallProbe } from "@/types/guide";
import { Panel, PanelEmpty } from "./Panel";

const OUTCOME: Record<WallProbe["outcome"], { label: string; classes: string }> = {
  login_wall: { label: "Login wall", classes: "bg-warning-soft text-warning border-warning-border" },
  console_reachable: { label: "Console reachable", classes: "bg-success-soft text-success border-success-border" },
  blocked: { label: "Blocked", classes: "bg-danger-soft text-danger border-danger-border" },
  error: { label: "Probe error", classes: "bg-muted text-muted-foreground border-border" },
};

function shortUrl(url: string) {
  try {
    const u = new URL(url);
    const path = u.pathname === "/" ? "" : u.pathname;
    return `${u.hostname.replace(/^www\./, "")}${path}`;
  } catch {
    return url;
  }
}

function formatWhen(iso: string) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function WallProbeCard({
  wall,
  probeStatus,
  finished,
}: {
  wall: WallProbe | null;
  probeStatus: "pending" | "running" | "done" | "error" | "skipped";
  finished: boolean;
}) {
  const outcome = wall ? (OUTCOME[wall.outcome] ?? OUTCOME.error) : null;
  return (
    <Panel title="Console probe" bodyClassName="min-h-56">
      {!wall || !outcome ? (
        <PanelEmpty>
          {(probeStatus === "pending" || probeStatus === "running") && !finished
            ? "Waiting for the console probe."
            : "The console was not probed."}
        </PanelEmpty>
      ) : (
        <div className="animate-in fade-in space-y-3 duration-300 motion-reduce:animate-none">
          <div className="flex flex-wrap items-center gap-1.5">
            <Chip className={cn("px-2.5 py-1 text-xs", outcome.classes)}>{outcome.label}</Chip>
            {wall.bot_check && (
              <Chip className="border-danger-border bg-danger-soft px-2.5 py-1 text-xs text-danger">Bot check</Chip>
            )}          </div>

          <ol aria-label="Redirect path" className="flex flex-wrap items-center gap-1 text-xs">
            {(wall.redirect_chain.length ? wall.redirect_chain : [wall.console_url]).map((u, i, arr) => (
              <li key={`${u}-${i}`} className="flex min-w-0 items-center gap-1">
                <span
                  title={u}
                  className="max-w-[16rem] truncate rounded-md border bg-muted/50 px-1.5 py-0.5 font-mono text-xs text-foreground"
                >
                  {shortUrl(u)}
                </span>
                {i < arr.length - 1 && (
                  <ChevronRightIcon className="size-3 shrink-0 text-muted-foreground" aria-label="redirects to" />
                )}
              </li>
            ))}
          </ol>

          <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-1.5 text-sm">
            <dt className="text-muted-foreground">Asks for</dt>
            <dd className="min-w-0 break-words text-foreground">{wall.asks_for || "Nothing recorded"}</dd>
            <dt className="text-muted-foreground">Bot check</dt>
            <dd className="text-foreground">{wall.bot_check ? "Yes" : "None seen"}</dd>
            <dt className="text-muted-foreground">Method</dt>
            <dd className="text-foreground">{wall.method === "browser" ? "Headless browser" : "Plain HTTP request"}</dd>
            <dt className="text-muted-foreground">Observed</dt>
            <dd className="text-foreground">{formatWhen(wall.observed_at)}</dd>
          </dl>
        </div>
      )}
    </Panel>
  );
}
