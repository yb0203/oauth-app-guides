"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { RotateCcwIcon, SquareIcon } from "lucide-react";
import { GuideView } from "@/components/guide/GuideView";
import { Chip } from "@/components/guide/shared";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GENERATE_URL } from "@/lib/api";
import { deriveRun, type GenerateMessage } from "@/lib/chat-types";
import { cn } from "@/lib/utils";
import { STAGE_ORDER, type StageData, type StageId } from "@/types/guide";
import { GuideReadyBanner } from "./GuideReadyBanner";
import { NarrationLog } from "./NarrationLog";
import { Panel } from "./Panel";
import { RunErrorPanel } from "./RunErrorPanel";
import { SourcesPanel } from "./SourcesPanel";
import { StageStepper, type StageTiming } from "./StageStepper";
import { VerificationCard } from "./VerificationCard";
import { WallProbeCard } from "./WallProbeCard";

type RunState = "running" | "done" | "failed" | "stopped";

const CHIP: Record<RunState, { label: string; classes: string; dot: string }> = {
  running: { label: "Running", classes: "border-info-border bg-info-soft text-info", dot: "bg-info animate-pulse motion-reduce:animate-none" },
  done: { label: "Done", classes: "border-success-border bg-success-soft text-success", dot: "bg-success" },
  failed: { label: "Failed", classes: "border-danger-border bg-danger-soft text-danger", dot: "bg-danger" },
  stopped: { label: "Stopped", classes: "border-border bg-muted text-muted-foreground", dot: "bg-muted-foreground" },
};

function useNow(active: boolean) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const t = setInterval(() => setNow(Date.now()), 200);
    return () => clearInterval(t);
  }, [active]);
  return now;
}

/** One run of the generation. Remount (new key) to start a fresh run. */
function GenerateRun({ app, onRestart }: { app: string; onRestart: () => void }) {
  const transport = useMemo(
    () =>
      new DefaultChatTransport<GenerateMessage>({
        api: GENERATE_URL,
        prepareSendMessagesRequest: () => ({ body: { app } }),
      }),
    [app],
  );

  // Client-side timestamps: the stream carries no timing, so note when each stage is first seen
  // and when it first reaches a terminal status.
  const [timings, setTimings] = useState<Partial<Record<StageId, StageTiming>>>({});
  const [stopped, setStopped] = useState(false);

  const { messages, sendMessage, status, error, stop } = useChat<GenerateMessage>({
    transport,
    onData: (part) => {
      if (part.type !== "data-stage" || !part.data) return;
      const { stage, status: st } = part.data;
      const t = Date.now();
      setTimings((prev) => {
        const cur = prev[stage] ?? { start: t };
        const terminal = st !== "running";
        if (prev[stage] && (!terminal || cur.end !== undefined)) return prev;
        return { ...prev, [stage]: { ...cur, end: terminal ? t : cur.end } };
      });
    },
  });

  // Start exactly once. useChat aborts its request in an effect cleanup, and React strict mode
  // simulates an unmount/remount in development, which would kill a request sent synchronously
  // from the first pass. Deferring the send by a tick (cleared by cleanup) means only the
  // surviving mount starts the run; the ref is a second guard against double starts.
  const startedRef = useRef(false);
  useEffect(() => {
    const t = setTimeout(() => {
      if (startedRef.current) return;
      startedRef.current = true;
      void sendMessage({ text: app });
    }, 0);
    return () => clearTimeout(t);
  }, [app, sendMessage]);

  const run = useMemo(() => deriveRun(messages), [messages]);

  const busy = status === "submitted" || status === "streaming";
  const starting = !busy && messages.length === 0 && !error && !stopped;
  const running = busy || starting;
  const state: RunState = run.guide ? "done" : running ? "running" : stopped ? "stopped" : "failed";

  const now = useNow(running);

  // A stage still marked running after the stream has ended was interrupted.
  const viewStages = useMemo(() => {
    if (running) return run.stages;
    const out: Partial<Record<StageId, StageData>> = {};
    for (const id of STAGE_ORDER) {
      const s = run.stages[id];
      if (!s) continue;
      out[id] =
        s.status === "running"
          ? {
              ...s,
              status: "error",
              detail: stopped ? "Stopped before this finished" : "The stream ended before this finished",
            }
          : s;
    }
    return out;
  }, [run.stages, running, stopped]);

  const guideRef = useRef<HTMLDivElement>(null);
  const scrolled = useRef(false);
  const hasGuide = Boolean(run.guide);
  useEffect(() => {
    if (!hasGuide || scrolled.current) return;
    scrolled.current = true;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Wait a frame so the inline guide has laid out before measuring.
    requestAnimationFrame(() =>
      guideRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" }),
    );
  }, [hasGuide]);

  const stageError = STAGE_ORDER.map((id) => viewStages[id]).find((s) => s?.status === "error");
  const errorMessage =
    error?.message ||
    (stageError ? `${stageError.label}${stageError.detail ? `: ${stageError.detail}` : ""}` : "") ||
    "The run ended without producing a guide.";

  const name = run.guide?.guide.app_name ?? app;
  const chip = CHIP[state];

  return (
    <div className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6">
      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <h1 className="min-w-0 text-2xl leading-tight font-semibold tracking-tight break-words">{name}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
            <span role="status">
              <Chip className={cn("px-2.5 py-1 text-xs", chip.classes)}>
                <span className={cn("size-1.5 rounded-full", chip.dot)} aria-hidden />
                {chip.label}
              </Chip>
            </span>
            {(state === "running" || state === "done") && (
              <Chip className="border-dashed border-muted-foreground/60 text-muted-foreground">
                <Sparkles className="size-3" aria-hidden /> Agent-generated
              </Chip>
            )}
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Link
              href="/"
              className="rounded text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
            >
              All apps
            </Link>
            {running ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setStopped(true);
                  stop();
                }}
              >
                <SquareIcon aria-hidden /> Stop
              </Button>
            ) : (
              state !== "failed" && (
                <Button variant="outline" size="sm" onClick={onRestart}>
                  <RotateCcwIcon aria-hidden /> Run again
                </Button>
              )
            )}
          </div>
        </div>
        <p className="max-w-2xl text-sm text-muted-foreground">
          {state === "done"
            ? "Done. The guide is below the run log, which stays here so you can see how it was built."
            : state === "failed"
              ? "The run stopped before a guide was produced. Everything it gathered is kept below."
              : state === "stopped"
                ? "You stopped the run. Everything gathered so far is kept below."
                : "An agent is finding the official docs, probing the developer console and re-checking every claim against the live pages. Each step shows up below as it happens."}
        </p>
      </header>

      {state === "failed" && (
        <div className="mt-6">
          <RunErrorPanel
            message={errorMessage}
            stages={viewStages}
            sourcesCount={run.sources.length}
            hasWall={Boolean(run.wall)}
            hasVerification={Boolean(run.verification)}
            onRetry={onRestart}
          />
        </div>
      )}
      {/* One column on small screens (pipeline, narration, sources, probe, verification); two columns from lg.
          `contents` lets the order utilities interleave the two columns' panels on small screens. */}
      <div className="mt-8 grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start print:hidden">
        <div className="contents lg:block lg:space-y-6">
          <div className="order-1">
            <Panel title="Pipeline">
              <StageStepper stages={viewStages} timings={timings} now={now} />
            </Panel>
          </div>
          <div className="order-4">
            <WallProbeCard wall={run.wall} probeStatus={viewStages.probe?.status ?? "pending"} finished={!running} />
          </div>
          <div className="order-5">
            <VerificationCard
              v={run.verification}
              verifyStatus={viewStages.verify?.status ?? "pending"}
              finished={!running}
            />
          </div>
        </div>
        <div className="contents lg:block lg:space-y-6">
          <div className="order-2">
            <Panel title="Agent narration">
              <NarrationLog lines={run.narration} active={running} />
            </Panel>
          </div>
          <div className="order-3">
            <SourcesPanel sources={run.sources} active={running} />
          </div>
        </div>
      </div>

      {run.guide && (
        <div ref={guideRef} className="mt-12 max-w-[760px] scroll-mt-20 space-y-6">
          <GuideReadyBanner permalink={run.guide.permalink} appName={run.guide.guide.app_name} />
          <GuideView guide={run.guide.guide} variant="inline" />
        </div>
      )}
    </div>
  );
}

export function GenerateView({ app }: { app: string }) {
  const [runId, setRunId] = useState(0);
  return <GenerateRun key={`${app}:${runId}`} app={app} onRestart={() => setRunId((n) => n + 1)} />;
}
