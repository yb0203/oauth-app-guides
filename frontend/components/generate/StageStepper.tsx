"use client";

import { CheckIcon, MinusIcon, XIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { STAGE_DEFAULT_LABEL } from "@/lib/chat-types";
import { STAGE_ORDER, type StageData, type StageId } from "@/types/guide";
import { AnimatedNumber } from "./AnimatedNumber";
import { formatDuration, STAGE_WHY, humanize } from "./run-info";

export interface StageTiming {
  start: number;
  end?: number;
}

type RowStatus = StageData["status"] | "pending";

const STATUS_TEXT: Record<RowStatus, string> = {
  pending: "Waiting",
  running: "In progress",
  done: "Done",
  error: "Failed",
  skipped: "Skipped",
};

function StatusIcon({ status }: { status: RowStatus }) {
  return (
    <span
      className={cn(
        "relative z-10 flex size-5 shrink-0 items-center justify-center rounded-full border bg-background transition-colors duration-300",
        status === "done" && "border-success bg-success text-background",
        status === "error" && "border-danger bg-danger text-background",
        status === "running" && "border-info",
        status === "skipped" && "border-dashed border-muted-foreground/60 text-muted-foreground",
        status === "pending" && "border-border",
      )}
    >
      {status === "done" && <CheckIcon className="size-3" strokeWidth={3} aria-hidden />}
      {status === "error" && <XIcon className="size-3" strokeWidth={3} aria-hidden />}
      {status === "skipped" && <MinusIcon className="size-3" aria-hidden />}
      {status === "running" && (
        <span className="size-3 animate-spin rounded-full border-2 border-info-border border-t-info motion-reduce:animate-none" aria-hidden />
      )}
      {status === "pending" && <span className="size-1.5 rounded-full bg-muted-foreground/40" aria-hidden />}
    </span>
  );
}

const COUNT_LABEL: Record<string, string> = {
  candidates: "candidates",
  kept: "kept",
  pages: "pages",
  claims: "claims noted",
  steps: "steps",
  limits: "limits",
  checked: "quotes checked",
  downgraded: "downgraded",
};
const countLabel = (k: string) => COUNT_LABEL[k] ?? k.replace(/_/g, " ");

export function StageStepper({
  stages,
  timings,
  now,
}: {
  stages: Partial<Record<StageId, StageData>>;
  timings: Partial<Record<StageId, StageTiming>>;
  now: number;
}) {
  return (
    <ol className="relative" aria-label="Pipeline stages">
      {STAGE_ORDER.map((id, idx) => {
        const s = stages[id];
        const status: RowStatus = s?.status ?? "pending";
        const t = timings[id];
        const elapsed = t && status !== "skipped" ? (t.end ?? now) - t.start : null;
        const last = idx === STAGE_ORDER.length - 1;
        const counts = s?.counts ? Object.entries(s.counts) : [];
        const active = status === "running";
        return (
          <li key={id} className="relative flex gap-3" data-stage={id} data-status={status}>
            {!last && (
              <span
                aria-hidden
                className={cn(
                  "absolute top-6 -bottom-1 left-2.5 -ml-px w-px transition-colors duration-500",
                  status === "done" ? "bg-success-border" : "bg-border",
                )}
              />
            )}
            <StatusIcon status={status} />
            <div
              className={cn(
                "-mt-1 min-w-0 flex-1 rounded-lg px-2.5 py-1.5 transition-colors duration-300",
                !last && "mb-1",
                active && "bg-info-soft",
                status === "error" && "bg-danger-soft",
              )}
            >
              <div className="flex items-baseline justify-between gap-3">
                <p
                  className={cn(
                    "text-sm leading-snug font-medium",
                    status === "pending" && "text-muted-foreground",
                    status === "skipped" && "text-muted-foreground line-through decoration-muted-foreground/40",
                    status === "error" && "text-danger",
                  )}
                >
                  {s?.label || STAGE_DEFAULT_LABEL[id]}
                  <span className="sr-only">, {STATUS_TEXT[status]}</span>
                </p>
                <span className="font-mono text-xs tabular-nums text-muted-foreground" aria-hidden={elapsed === null}>
                  {elapsed !== null ? formatDuration(elapsed) : status === "skipped" ? "skipped" : ""}
                </span>
              </div>
              <p
                className={cn(
                  "mt-0.5 text-xs leading-snug text-muted-foreground",
                  // On small screens only the live row explains itself; the full list would be a wall of text.
                  !active && status !== "error" && "max-sm:hidden",
                )}
              >
                {STAGE_WHY[id]}
              </p>
              {/* Reserved even while empty, so details and counts arriving never push the stages below. */}
              <div className="mt-1.5 flex min-h-6 flex-wrap items-center gap-1.5">
                  {s?.detail && (
                    <span className={cn("text-xs first-letter:uppercase", status === "error" ? "text-danger" : "text-foreground")}>
                      {humanize(s.detail)}
                    </span>
                  )}
                  {active && !s?.detail && counts.length === 0 && (
                    <span className="text-xs text-info">Working…</span>
                  )}
                  {counts.map(([k, v]) => (
                    <span
                      key={k}
                      className="animate-in fade-in rounded-md border bg-background px-1.5 py-0.5 font-mono text-xs tabular-nums text-foreground duration-300 motion-reduce:animate-none"
                    >
                      <AnimatedNumber value={v} /> {countLabel(k)}
                    </span>
                  ))}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
