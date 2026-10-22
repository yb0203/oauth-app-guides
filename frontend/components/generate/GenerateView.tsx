"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { ChevronDownIcon } from "lucide-react";
import { GuideView } from "@/components/guide/GuideView";
import { GENERATE_URL, getGuide } from "@/lib/api";
import { apiFetch, ApiError } from "@/lib/http-error";
import { configToBody, configToQuery, type GenConfig, type ModelsInfo } from "@/lib/models";
import { RecoveryNotice } from "./RecoveryNotice";
import { useRunRecovery, type RecoveryOutcome } from "./useRunRecovery";
import { RunStatsLine } from "./RunStatsLine";
import { configSummary, SettingsPopover } from "./SettingsPopover";
import { deriveRun, STAGE_DEFAULT_LABEL, type GenerateMessage } from "@/lib/chat-types";
import { cn } from "@/lib/utils";
import { STAGE_ORDER, type GuideDataPart, type StageData, type StageId, type VerificationProgress } from "@/types/guide";
import { GuideReadyBanner } from "./GuideReadyBanner";
import { ReplayBanner } from "./ReplayBanner";
import { NarrationLog } from "./NarrationLog";
import { Panel } from "./Panel";
import { RunErrorPanel } from "./RunErrorPanel";
import { RunSummary, type RunState } from "./RunSummary";
import { formatDuration, verifiedClaims } from "./run-info";
import { SourcesPanel } from "./SourcesPanel";
import { StageStepper, type StageTiming } from "./StageStepper";
import { VerificationCard } from "./VerificationCard";
import { WallProbeCard } from "./WallProbeCard";

function useNow(active: boolean) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const t = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(t);
  }, [active]);
  return now;
}

/** 0 to 1. Finished stages count fully; the stage in flight counts half, or its real fraction while verifying. */
function runProgress(stages: Partial<Record<StageId, StageData>>, v: VerificationProgress | null): number {
  let sum = 0;
  for (const id of STAGE_ORDER) {
    const st = stages[id]?.status;
    if (st === "done" || st === "skipped") sum += 1;
    else if (st === "running") sum += id === "verify" && v && v.total > 0 ? Math.min(1, v.checked / v.total) * 0.9 : 0.5;
  }
  return sum / STAGE_ORDER.length;
}

/** One run of the generation. Remount (new key) to start a fresh run. */
function GenerateRun({
  app,
  config: initialConfig,
  models,
  onRestart,
  onBadModel,
  onConfigChange,
}: {
  app: string;
  config: GenConfig;
  models: ModelsInfo | null;
  onRestart: () => void;
  /** the backend rejected the model in the request (HTTP 400): parent falls back to the default and re-runs */
  onBadModel: () => void;
  /** settings edited after the run: they apply to the next run */
  onConfigChange: (c: GenConfig) => void;
}) {
  // Frozen per run: changing settings afterwards must not touch a run in flight or rebuild its transport.
  const [config] = useState(initialConfig);
  const transport = useMemo(
    () =>
      new DefaultChatTransport<GenerateMessage>({
        api: GENERATE_URL,
        fetch: apiFetch("guides"),
        prepareSendMessagesRequest: () => ({ body: { app, config: configToBody(config) } }),
      }),
    [app, config],
  );

  // Client-side timestamps: the stream carries no timing, so note when each stage is first seen
  // and when it first reaches a terminal status.
  const [timings, setTimings] = useState<Partial<Record<StageId, StageTiming>>>({});
  const [stopped, setStopped] = useState(false);
  const [startedAt] = useState(() => Date.now());
  const [endedAt, setEndedAt] = useState<number | null>(null);
  const markEnded = () => setEndedAt((t) => t ?? Date.now());

  const { messages, sendMessage, status, error, stop } = useChat<GenerateMessage>({
    transport,
    onFinish: markEnded,
    onError: markEnded,
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

  // Stale link or removed model: the backend answers 400. Fall back to the default model once, with a notice.
  const badModel = error instanceof ApiError && error.status === 400 && Boolean(config.model);
  useEffect(() => {
    if (badModel) onBadModel();
  }, [badModel, onBadModel]);

  // The stream can go silent while the server carries on. Recovery asks GET /api/runs/{run_id} and, when the
  // server says done, loads the published guide from its permalink and hands off exactly like a streamed one.
  const [recovered, setRecovered] = useState<GuideDataPart | null>(null);
  const [recoverError, setRecoverError] = useState<string | null>(null);
  const runId = useMemo(() => messages.find((m) => m.role === "assistant")?.id ?? null, [messages]);

  const run = useMemo(() => deriveRun(messages), [messages]);
  const guidePart = run.guide ?? recovered;

  const busy = status === "submitted" || status === "streaming";
  const starting = !busy && messages.length === 0 && !error && !stopped;
  const running = busy || starting;

  const recovery = useRunRecovery({
    active: running && !run.guide,
    runId,
    activityKey: messages,
    onOutcome: async (o: RecoveryOutcome) => {
      if (o.kind === "done") {
        const g = await getGuide(o.slug).catch(() => null);
        if (g) setRecovered({ slug: o.slug, permalink: o.permalink ?? `/guides/${o.slug}`, guide: g });
        else setRecoverError("The run finished on the server, but the guide could not be loaded. Open it from the catalog or retry.");
      } else {
        setRecoverError(o.message);
      }
      markEnded();
      void stop(); // drop the stalled stream
    },
  });
  const state: RunState = guidePart ? "done" : running ? "running" : stopped ? "stopped" : "failed";

  const now = useNow(running);
  const elapsedMs = (endedAt ?? now) - startedAt;

  // A stage still marked running after the stream has ended was interrupted.
  const viewStages = useMemo(() => {
    if (running) return run.stages;
    if (recovered) {
      // The live feed dropped but the server finished: show every step as done, and say why.
      const all: Partial<Record<StageId, StageData>> = {};
      for (const id of STAGE_ORDER) {
        const st = run.stages[id];
        all[id] =
          st && (st.status === "done" || st.status === "skipped")
            ? st
            : { stage: id, status: "done", label: st?.label || STAGE_DEFAULT_LABEL[id], detail: "Finished on the server; the live feed had dropped" };
      }
      return all;
    }
    const out: Partial<Record<StageId, StageData>> = {};
    for (const id of STAGE_ORDER) {
      const s = run.stages[id];
      if (!s) continue;
      out[id] =
        s.status === "running"
          ? {
              ...s,
              status: "error",
              detail: stopped
                ? "Stopped before this finished"
                : error
                  ? "Failed here"
                  : "The connection ended before this finished",
            }
          : s;
    }
    return out;
  }, [run.stages, running, stopped, error, recovered]);

  const hasGuide = Boolean(guidePart);

  // Hand-off: let the finished pipeline sit for a beat, fold the run log away, then bring the guide into view.
  const [logOpen, setLogOpen] = useState(true);
  const guideRef = useRef<HTMLDivElement>(null);
  const handedOff = useRef(false);
  useEffect(() => {
    if (!hasGuide || handedOff.current) return;
    handedOff.current = true;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const fold = setTimeout(() => setLogOpen(false), reduce ? 0 : 1100);
    const reveal = setTimeout(
      () => {
        const el = guideRef.current;
        if (!el) return;
        el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
        el.focus({ preventScroll: true });
      },
      reduce ? 50 : 1500,
    );
    return () => {
      clearTimeout(fold);
      clearTimeout(reveal);
    };
  }, [hasGuide]);

  const stageError = STAGE_ORDER.map((id) => viewStages[id]).find((s) => s?.status === "error");
  const errorMessage =
    recoverError ||
    error?.message ||
    (stageError ? `${stageError.label}${stageError.detail ? `: ${stageError.detail}` : ""}` : "") ||
    "The run ended without producing a guide.";

  const replay = run.replay;
  // What the run actually used: the backend's report when it sent one, otherwise what we asked for.
  const sc = run.stats?.config;
  const effective: GenConfig = {
    model: sc?.model ?? config.model,
    pages: sc?.max_pages ?? config.pages,
    probe: sc?.probe_console ?? config.probe,
  };
  // A replay is always the recorded GitHub run; keep the heading on what the user asked for.
  const name = replay ? app : (guidePart?.guide.app_name ?? app);
  const currentStage =
    STAGE_ORDER.find((id) => viewStages[id]?.status === "running") ??
    [...STAGE_ORDER].reverse().find((id) => viewStages[id]) ??
    null;
  const progress = state === "done" ? 1 : runProgress(viewStages, run.verification);
  const latest = run.narration[run.narration.length - 1]?.text;
  const sourcesSeen = run.sources.length;
  const claims = guidePart ? verifiedClaims(guidePart.guide) : null;
  const logId = "run-log";

  return (
    <div className="mx-auto w-full max-w-[1200px] px-4 py-6 sm:px-6 sm:py-8">
      <RunSummary
        app={name}
        state={state}
        currentStage={currentStage}
        progress={progress}
        elapsedMs={elapsedMs}
        latest={latest}
        replay={replay}
        settings={
          running ? (
            <span className="text-xs text-muted-foreground">{configSummary(effective, models)}</span>
          ) : (
            <SettingsPopover value={effective} onChange={onConfigChange} models={models} className="bg-background" />
          )
        }
        stageElapsedMs={currentStage && viewStages[currentStage]?.status === "running" && timings[currentStage] ? now - timings[currentStage]!.start : 0}
        onStop={() => {
          setStopped(true);
          markEnded();
          stop();
        }}
        onRestart={onRestart}
      />

      {recovery.quiet && running && <RecoveryNotice status={recovery.status} canPoll={recovery.canPoll} />}

      {replay && <ReplayBanner app={name} />}

      {run.stats && state !== "running" && <RunStatsLine stats={run.stats} className="mt-4" />}

      {(state === "failed" || state === "stopped") && (
        <div className="mt-6">
          <RunErrorPanel
            app={name}
            message={errorMessage}
            stopped={state === "stopped"}
            stages={viewStages}
            sourcesCount={sourcesSeen}
            hasWall={Boolean(run.wall)}
            hasVerification={Boolean(run.verification)}
            onRetry={onRestart}
            rateLimited={error instanceof ApiError && error.rateLimited}
            retryAfter={error instanceof ApiError ? error.retryAfter : null}
          />
        </div>
      )}

      {state === "done" && (
        <button
          type="button"
          aria-expanded={logOpen}
          aria-controls={logId}
          onClick={() => setLogOpen((o) => !o)}
          className="mt-4 flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg border bg-card px-4 py-2.5 text-left text-sm transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none print:hidden"
        >
          <span className="min-w-0">
            <span className="font-medium text-foreground">How the agent built this</span>
            <span className="text-muted-foreground">
              {" "}
              · {formatDuration(elapsedMs)} · {sourcesSeen} {sourcesSeen === 1 ? "source" : "sources"}
              {claims ? ` · ${claims.n} of ${claims.total} claims verified` : ""}
            </span>
          </span>
          <ChevronDownIcon
            className={cn("size-4 shrink-0 text-muted-foreground transition-transform duration-300 motion-reduce:transition-none", logOpen && "rotate-180")}
            aria-hidden
          />
        </button>
      )}

      {/* The run log folds away (grid-rows 1fr to 0fr) once the guide arrives. One column on small screens
          (pipeline, narration, sources, probe, verification); two columns from lg. `contents` lets the order
          utilities interleave the two columns' panels on small screens. */}
      <div
        id={logId}
        inert={!logOpen}
        className={cn(
          "grid transition-[grid-template-rows,opacity] duration-500 ease-out motion-reduce:transition-none print:hidden",
          logOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="grid grid-cols-[minmax(0,1fr)] gap-6 pt-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start">
            <div className="contents lg:block lg:space-y-6">
              <div className="order-1">
                <Panel title="Pipeline" aside={`${currentStage ? STAGE_ORDER.indexOf(currentStage) + 1 : 0} of ${STAGE_ORDER.length}`}>
                  <StageStepper stages={viewStages} timings={timings} now={now} />
                </Panel>
              </div>
              {run.wall && (
                <div className="order-4">
                  <WallProbeCard wall={run.wall} />
                </div>
              )}
            </div>
            <div className="contents lg:block lg:space-y-6">
              <div className="order-2">
                <Panel title="What the agent is saying" aside="newest first">
                  <NarrationLog lines={run.narration} active={running} className="h-52" />
                </Panel>
              </div>
              {(running || sourcesSeen > 0) && (
                <div className="order-3">
                  <SourcesPanel sources={run.sources} active={running} />
                </div>
              )}
              {run.verification && (
                <div className="order-5">
                  <VerificationCard v={run.verification} running={running} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {guidePart && (
        <div ref={guideRef} tabIndex={-1} aria-label={`${name} guide`} className="mt-8 max-w-[760px] scroll-mt-14 space-y-6 outline-none">
          <GuideReadyBanner permalink={guidePart.permalink} guide={guidePart.guide} replay={replay} />
          <GuideView guide={guidePart.guide} variant="inline" replay={replay} />
        </div>
      )}
    </div>
  );
}

export function GenerateView({ app, initialConfig, models }: { app: string; initialConfig: GenConfig; models: ModelsInfo | null }) {
  const [runId, setRunId] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);

  // A model that is not on the allow-list (stale URL) is dropped up front, with a notice.
  const [config, setConfig] = useState<GenConfig>(() => {
    if (models && initialConfig.model && !models.models.some((m) => m.id === initialConfig.model)) return { ...initialConfig, model: undefined };
    return initialConfig;
  });
  const [startedWith] = useState(() => (models && initialConfig.model && !models.models.some((m) => m.id === initialConfig.model) ? initialConfig.model : null));
  const noticeText = notice ?? (startedWith ? `The model in this link (${startedWith}) isn't available. Using the default model instead.` : null);

  // The URL mirrors the settings, so a run can be shared and reproduced. Passive: keeps Next's history state.
  useEffect(() => {
    const url = new URL(window.location.href);
    for (const [k, v] of Object.entries({ model: "", ...configToQuery(config) })) {
      if (v) url.searchParams.set(k, v);
      else url.searchParams.delete(k);
    }
    window.history.replaceState(window.history.state, "", url);
  }, [config]);

  const onBadModel = useMemo(
    () => () => {
      setNotice(`The model in this link (${config.model}) was rejected by the server. Using the default model instead.`);
      setConfig((c) => ({ ...c, model: undefined }));
      setRunId((n) => n + 1);
    },
    [config.model],
  );

  return (
    <>
      {noticeText && (
        <div className="mx-auto w-full max-w-[1200px] px-4 pt-6 sm:px-6">
          <div role="status" className="flex items-start justify-between gap-3 rounded-lg border border-warning-border bg-warning-soft px-3 py-2 text-sm text-warning">
            <span>{noticeText}</span>
            <button type="button" onClick={() => setNotice("")} className="shrink-0 cursor-pointer text-xs underline underline-offset-2">
              Dismiss
            </button>
          </div>
        </div>
      )}
      <GenerateRun
        key={`${app}:${runId}`}
        app={app}
        config={config}
        models={models}
        onRestart={() => setRunId((n) => n + 1)}
        onBadModel={onBadModel}
        onConfigChange={setConfig}
      />
    </>
  );
}
