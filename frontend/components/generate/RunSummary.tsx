"use client";

import Link from "next/link";
import { CheckIcon, FlaskConicalIcon, RotateCcwIcon, SparklesIcon, SquareIcon, TriangleAlertIcon } from "lucide-react";
import { Chip } from "@/components/guide/shared";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { STAGE_SHORT_NAME } from "@/lib/chat-types";
import { STAGE_ORDER, type StageId } from "@/types/guide";
import { formatDuration, QUIET_AFTER_MS, SLOW_AFTER_MS, STAGE_NOW, TYPICAL_RUN } from "./run-info";

export type RunState = "running" | "done" | "failed" | "stopped";

const CHIP: Record<RunState, { label: string; classes: string; dot: string }> = {
  running: { label: "Running", classes: "border-info-border bg-info-soft text-info", dot: "bg-info animate-pulse motion-reduce:animate-none" },
  done: { label: "Done", classes: "border-success-border bg-success-soft text-success", dot: "bg-success" },
  failed: { label: "Failed", classes: "border-danger-border bg-danger-soft text-danger", dot: "bg-danger" },
  stopped: { label: "Stopped", classes: "border-border bg-muted text-muted-foreground", dot: "bg-muted-foreground" },
};

/**
 * The first thing on the page: which app, what the agent is doing right now in plain words, one progress
 * bar, elapsed time against the usual range. Text that changes is not a live region itself (a stage
 * change is announced once by the hidden status line below), so screen readers are not flooded.
 */
export function RunSummary({
  app,
  state,
  currentStage,
  progress,
  elapsedMs,
  latest,
  replay = false,
  settings,
  stageElapsedMs = 0,
  onStop,
  onRestart,
}: {
  app: string;
  state: RunState;
  currentStage: StageId | null;
  /** 0 to 1 */
  progress: number;
  elapsedMs: number;
  latest?: string;
  /** recorded demo run: say so instead of claiming research for `app` */
  replay?: boolean;
  /** effective model and settings: static text while running, an editor once the run has ended */
  settings?: React.ReactNode;
  /** how long the current stage has been running, to explain quiet stretches */
  stageElapsedMs?: number;
  onStop: () => void;
  onRestart: () => void;
}) {
  const chip = CHIP[state];
  const stageNo = currentStage ? STAGE_ORDER.indexOf(currentStage) + 1 : 0;
  const slow = state === "running" && elapsedMs > SLOW_AFTER_MS;
  const pct = Math.round(progress * 100);

  const now =
    state === "running"
      ? replay
        ? currentStage
          ? `Replaying a recorded GitHub run (${STAGE_SHORT_NAME[currentStage].toLowerCase()})`
          : "Starting a recorded demo replay"
        : currentStage
          ? STAGE_NOW[currentStage](app)
          : `Starting the agent for ${app}`
      : state === "done"
        ? replay
          ? "Replay finished: this is the recorded GitHub guide"
          : `Guide ready for ${app}`
        : state === "stopped"
          ? "Stopped before the guide was finished"
          : "The run stopped before a guide was produced";

  const announce =
    state === "running"
      ? currentStage
        ? `Step ${stageNo} of ${STAGE_ORDER.length}: ${replay ? "demo replay of a recorded GitHub run" : STAGE_NOW[currentStage](app)}`
        : "Starting"
      : now;

  return (
    <header
      className={cn(
        "rounded-xl border p-4 transition-colors duration-500 sm:p-5",
        state === "done" ? "border-success-border bg-success-soft" : "bg-card",
      )}
    >
      <p role="status" className="sr-only">
        {announce}
      </p>
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3">
        <div className="min-w-0 flex-1 basis-64">
          <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
            <h1 className="min-w-0 text-2xl leading-tight font-semibold tracking-tight break-words">{app}</h1>
            <Chip className={cn("px-2.5 py-1 text-xs", chip.classes)}>
              <span className={cn("size-1.5 rounded-full", chip.dot)} aria-hidden />
              {chip.label}
            </Chip>
            {replay ? (
              <Chip className="border-warning-border bg-warning-soft text-warning" title="Recorded GitHub run, not research for this app">
                <FlaskConicalIcon className="size-3" aria-hidden /> Demo replay
              </Chip>
            ) : (
              state !== "done" && (
                <Chip className="border-dashed border-muted-foreground/60 bg-background/60 text-muted-foreground">
                  <SparklesIcon className="size-3" aria-hidden /> Agent-generated
                </Chip>
              )
            )}
          </div>
          <p className="mt-2 flex items-center gap-2 text-base font-medium text-foreground" aria-hidden>
            {state === "done" ? (
              <CheckIcon className="size-4 shrink-0 text-success" strokeWidth={3} />
            ) : state === "failed" ? (
              <TriangleAlertIcon className="size-4 shrink-0 text-danger" />
            ) : null}
            <span className="min-w-0 break-words">
              {now}
              {state === "running" && <span className="text-muted-foreground">…</span>}
            </span>
          </p>
          <p className={cn("mt-1 text-sm break-words text-muted-foreground", state === "running" && "min-h-5")} aria-hidden>
            {state === "running"
              ? !replay && stageElapsedMs > QUIET_AFTER_MS
                ? `Still on this step after ${formatDuration(stageElapsedMs)}. Free models can take a minute or two here; nothing is stuck.`
                : latest || "The agent will narrate each step below."
              : null}
            {state === "stopped" && "Everything gathered so far is kept below."}
            {state === "failed" && "What it found is kept below. Nothing has been published."}
          </p>
        </div>
        <div className="flex items-center gap-2 print:hidden">
          <Link
            href="/"
            className="rounded px-1 text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
          >
            All apps
          </Link>
          {state === "running" ? (
            <Button variant="outline" size="sm" onClick={onStop} className="bg-background">
              <SquareIcon aria-hidden /> Stop
            </Button>
          ) : (
            state !== "failed" && (
              <Button variant="outline" size="sm" onClick={onRestart} className="bg-background">
                <RotateCcwIcon aria-hidden /> Run again
              </Button>
            )
          )}
        </div>
      </div>

      {settings && <div className="mt-3 flex min-w-0 flex-wrap items-center gap-2 print:hidden">{settings}</div>}

      <div className="mt-4">
        <div
          role="progressbar"
          aria-label="Run progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={pct}
          aria-valuetext={`${pct} percent, step ${Math.max(stageNo, 1)} of ${STAGE_ORDER.length}`}
          className="h-2 overflow-hidden rounded-full bg-foreground/10"
        >
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-700 ease-out motion-reduce:transition-none",
              state === "done" ? "bg-success" : state === "failed" ? "bg-danger" : state === "stopped" ? "bg-muted-foreground" : "bg-info",
            )}
            style={{ width: `${Math.max(pct, state === "running" ? 3 : 0)}%` }}
          />
        </div>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span className="font-mono tabular-nums">
            {state === "done" ? "Finished in" : state === "running" ? "Elapsed" : "Ran for"} {formatDuration(elapsedMs)}
          </span>
          <span>
            {state === "running"
              ? replay
                ? "Demo replay, about 15 seconds"
                : slow
                  ? "Taking longer than the usual range. Still working."
                  : `Usually about ${TYPICAL_RUN}`
              : `${Math.min(Math.max(stageNo, 0), STAGE_ORDER.length)} of ${STAGE_ORDER.length} steps reached`}
          </span>
        </div>
      </div>
    </header>
  );
}
