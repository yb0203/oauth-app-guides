"use client";

import { useEffect, useRef, useState } from "react";
import { RUN_URL, USE_MOCK } from "@/lib/api";

/** No new stream parts for this long = the connection went quiet. */
export const QUIET_MS = 45_000;
const POLL_EVERY_MS = 5_000;
const GIVE_UP_MS = 4 * 60_000;

export interface RunStatus {
  run_id?: string;
  status: "running" | "done" | "error";
  stage?: string | null;
  slug?: string | null;
  permalink?: string | null;
  error?: string | null;
}

export type RecoveryOutcome =
  | { kind: "done"; slug: string; permalink: string | null }
  | { kind: "error"; message: string }
  | { kind: "lost"; message: string };

/** Mock runs can shorten the quiet window with ?quiet_s=5 (dev only). */
function quietMs(): number {
  if (USE_MOCK && typeof window !== "undefined") {
    const s = Number(new URLSearchParams(window.location.search).get("quiet_s"));
    if (s > 0) return s * 1000;
  }
  return QUIET_MS;
}

/**
 * Watches a generation stream for silence. If nothing new arrives for 45 s while the run is active, it reports
 * `quiet` and polls GET /api/runs/{runId} every 5 s for up to 4 minutes; the server keeps running and publishes
 * the guide even when the stream dies. `onOutcome` fires once when the server says done/error, or when the
 * run cannot be found or the time is up.
 */
export function useRunRecovery({
  active,
  runId,
  activityKey,
  onOutcome,
}: {
  active: boolean;
  runId: string | null;
  /** any value that changes whenever a stream part arrives (the messages array) */
  activityKey: unknown;
  onOutcome: (o: RecoveryOutcome) => void;
}) {
  const [quiet, setQuiet] = useState(false);
  const [status, setStatus] = useState<RunStatus | null>(null);
  const last = useRef(0);
  const quietSince = useRef<number | null>(null);
  const outcomeRef = useRef(onOutcome);
  const doneRef = useRef(false);

  useEffect(() => {
    outcomeRef.current = onOutcome;
  });
  useEffect(() => {
    last.current = Date.now();
  }, [activityKey]);

  // Watchdog. State is only set from the timer, never synchronously in an effect.
  useEffect(() => {
    if (!active) return;
    last.current = Date.now();
    const t = setInterval(() => {
      const isQuiet = Date.now() - last.current > quietMs();
      if (isQuiet && quietSince.current === null) quietSince.current = Date.now();
      if (!isQuiet) quietSince.current = null;
      setQuiet(isQuiet);
    }, 1000);
    return () => clearInterval(t);
  }, [active]);

  // Recovery polling while quiet.
  useEffect(() => {
    if (!active || !quiet || !runId || doneRef.current) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const finish = (o: RecoveryOutcome) => {
      if (cancelled || doneRef.current) return;
      doneRef.current = true;
      outcomeRef.current(o);
    };

    const poll = async () => {
      if (cancelled) return;
      const since = quietSince.current ?? Date.now();
      if (Date.now() - since > GIVE_UP_MS) {
        finish({ kind: "lost", message: "Lost contact with the run and could not recover it in 4 minutes." });
        return;
      }
      try {
        const res = await fetch(RUN_URL(runId), { cache: "no-store" });
        if (res.status === 404) {
          finish({ kind: "lost", message: "The server has no record of this run (it may have restarted)." });
          return;
        }
        if (res.ok) {
          const s = (await res.json()) as RunStatus;
          if (!cancelled) setStatus(s);
          if (s.status === "done" && s.slug) return finish({ kind: "done", slug: s.slug, permalink: s.permalink ?? null });
          if (s.status === "error") return finish({ kind: "error", message: s.error || "The run failed on the server." });
        }
      } catch {
        /* network blip: keep polling until the deadline */
      }
      if (!cancelled) timer = setTimeout(poll, POLL_EVERY_MS);
    };
    void poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [active, quiet, runId]);

  return { quiet: active && quiet, status, canPoll: Boolean(runId) };
}
