"use client";

import { CheckIcon, MinusIcon, XIcon } from "lucide-react";
import { Eyebrow } from "@/components/guide/shared";
import { cn } from "@/lib/utils";
import { STAGE_DEFAULT_LABEL, STAGE_SHORT_NAME } from "@/lib/chat-types";
import { STAGE_ORDER, type StageData, type StageId } from "@/types/guide";

export interface StageTiming {
  start: number;
  end?: number;
}

type RowStatus = StageData["status"] | "pending";

const STATUS_TEXT: Record<RowStatus, string> = {
  pending: "Pending",
  running: "Running",
  done: "Done",
  error: "Failed",
  skipped: "Skipped",
};

export function formatElapsed(ms: number): string {
  const s = Math.max(0, ms) / 1000;
  if (s < 10) return `${s.toFixed(1)}s`;
  if (s < 60) return `${Math.round(s)}s`;
  return `${Math.floor(s / 60)}m ${String(Math.round(s % 60)).padStart(2, "0")}s`;
}

function StatusIcon({ status }: { status: RowStatus }) {
  return (
    <span
      className={cn(
        "relative z-10 flex size-5 shrink-0 items-center justify-center rounded-full border bg-background",
        status === "done" && "border-success bg-success text-background",
        status === "error" && "border-danger bg-danger text-background",
        status === "running" && "border-foreground",
        status === "skipped" && "border-border text-muted-foreground",
        status === "pending" && "border-border",
      )}
    >
      {status === "done" && <CheckIcon className="size-3" strokeWidth={3} aria-hidden />}
      {status === "error" && <XIcon className="size-3" strokeWidth={3} aria-hidden />}
      {status === "skipped" && <MinusIcon className="size-3" aria-hidden />}
      {status === "running" && (
        <span
          className="size-3 animate-spin rounded-full border-2 border-border border-t-foreground"
          aria-hidden
        />
      )}
      {status === "pending" && <span className="size-1.5 rounded-full bg-muted-foreground/40" aria-hidden />}
      <span className="sr-only">{STATUS_TEXT[status]}</span>
    </span>
  );
}

function countLabel(key: string, value: number) {
  return `${value} ${key.replace(/_/g, " ")}`;
}

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
        return (
          <li
            key={id}
            className={cn("relative flex gap-3", !last && "pb-6")}
            data-stage={id}
            data-status={status}
          >
            {!last && (
              <span
                aria-hidden
                className={cn(
                  "absolute top-5 bottom-0 left-2.5 -ml-px w-px",
                  status === "done" ? "bg-success-border" : "bg-border",
                )}
              />
            )}
            <StatusIcon status={status} />
            <div className="min-w-0 flex-1 pt-px">
              <div className="flex items-center justify-between gap-3">
                <Eyebrow>{STAGE_SHORT_NAME[id]}</Eyebrow>
                {elapsed !== null && (
                  <span className="font-mono text-xs tabular-nums text-muted-foreground">
                    {formatElapsed(elapsed)}
                  </span>
                )}
              </div>
              <p
                className={cn(
                  "text-sm leading-snug",
                  status === "pending" || status === "skipped"
                    ? "text-muted-foreground"
                    : "font-medium text-foreground",
                  status === "error" && "text-danger",
                )}
              >
                {s?.label || STAGE_DEFAULT_LABEL[id]}
              </p>
              {s?.detail && <p className="mt-0.5 text-xs leading-snug text-muted-foreground">{s.detail}</p>}
              {counts.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {counts.map(([k, v]) => (
                    <span
                      key={k}
                      className="rounded-md border bg-muted/50 px-1.5 py-0.5 font-mono text-xs tabular-nums text-foreground"
                    >
                      {countLabel(k, v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
