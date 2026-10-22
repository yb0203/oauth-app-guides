"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRightIcon, CheckIcon, RotateCcwIcon, SearchIcon, TriangleAlertIcon, XIcon } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { API_URL } from "@/lib/api";
import { STAGE_DEFAULT_LABEL } from "@/lib/chat-types";
import { cn } from "@/lib/utils";
import { STAGE_ORDER, type GuideListEntry, type StageData, type StageId } from "@/types/guide";

const TRY_NEXT: Partial<Record<StageId, string>> = {
  resolve: "Check the spelling, or use the name the provider uses for its developer platform.",
  find_docs: "Try the exact product name, or paste the address of its developer docs.",
  research: "The docs may be slow or blocked right now. Retrying usually works.",
  probe: "The console may block automated visits. Retrying is safe; the guide can be written without it.",
  synthesize: "Retrying is safe. Nothing partial was published.",
  verify: "Retrying is safe. Nothing unverified was published.",
  publish: "The guide was written but could not be saved. Retrying is safe.",
};

function useCuratedGuides() {
  const [guides, setGuides] = useState<GuideListEntry[]>([]);
  useEffect(() => {
    const ctl = new AbortController();
    fetch(`${API_URL}/api/guides`, { signal: ctl.signal })
      .then((r) => (r.ok ? (r.json() as Promise<GuideListEntry[]>) : []))
      .then((list) => setGuides(list.filter((g) => g.guide_type === "curated").slice(0, 4)))
      .catch(() => {});
    return () => ctl.abort();
  }, []);
  return guides;
}

/** What succeeded, what failed, what to try, and a way out that is never a dead end. */
export function RunErrorPanel({
  app,
  message,
  stopped,
  stages,
  sourcesCount,
  hasWall,
  hasVerification,
  onRetry,
}: {
  app: string;
  message: string;
  stopped: boolean;
  stages: Partial<Record<StageId, StageData>>;
  sourcesCount: number;
  hasWall: boolean;
  hasVerification: boolean;
  onRetry: () => void;
}) {
  const curated = useCuratedGuides();
  const completed = STAGE_ORDER.filter((id) => stages[id]?.status === "done");
  const failedId =
    STAGE_ORDER.find((id) => stages[id]?.status === "error") ?? STAGE_ORDER.find((id) => stages[id]?.status === "running") ?? null;
  const kept: string[] = [];
  if (sourcesCount > 0) kept.push(`${sourcesCount} ${sourcesCount === 1 ? "source" : "sources"}`);
  if (hasWall) kept.push("the console probe");
  if (hasVerification) kept.push("partial verification");
  const label = (id: StageId) => stages[id]?.label || STAGE_DEFAULT_LABEL[id];

  return (
    <section role={stopped ? undefined : "alert"} aria-labelledby="run-error-title" className="rounded-xl border border-danger-border bg-danger-soft p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <TriangleAlertIcon className="mt-0.5 size-5 shrink-0 text-danger" aria-hidden />
        <div className="min-w-0 flex-1">
          <h2 id="run-error-title" className="text-base font-semibold text-danger">
            {stopped ? `Stopped before the ${app} guide was finished` : `Couldn't finish the ${app} guide`}
          </h2>
          {!stopped && <p className="mt-1 text-sm break-words text-foreground">{message}</p>}
        </div>
      </div>

      <dl className="mt-4 grid gap-4 border-t border-danger-border pt-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="flex items-center gap-1.5 text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            <CheckIcon className="size-3 text-success" strokeWidth={3} aria-hidden /> Worked
          </dt>
          <dd className="mt-1 text-foreground">
            {completed.length === 0 ? "Nothing finished before the stop." : completed.map(label).join(", ") + "."}
            {kept.length > 0 && <span className="mt-1 block text-muted-foreground">Kept below: {kept.join(", ")}.</span>}
          </dd>
        </div>
        <div>
          <dt className="flex items-center gap-1.5 text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            <XIcon className="size-3 text-danger" strokeWidth={3} aria-hidden /> {stopped ? "Stopped at" : "Failed at"}
          </dt>
          <dd className="mt-1 text-foreground">
            {failedId ? label(failedId) : "The request, before the first step started."}
            {failedId && stages[failedId]?.detail && stages[failedId]?.status === "error" && (
              <span className="mt-1 block text-muted-foreground">{stages[failedId]?.detail}</span>
            )}
          </dd>
        </div>
        <div>
          <dt className="flex items-center gap-1.5 text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            <SearchIcon className="size-3" aria-hidden /> Try next
          </dt>
          <dd className="mt-1 text-foreground">
            {(failedId && TRY_NEXT[failedId]) || "Retrying is safe. Nothing partial was published."}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-danger-border pt-4">
        <Button size="sm" onClick={onRetry}>
          <RotateCcwIcon aria-hidden /> Retry
        </Button>
        <Link href="/generate" className={cn(buttonVariants({ variant: "outline", size: "sm" }), "bg-background")}>
          Try a different app
        </Link>
        {curated.length > 0 && (
          <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-sm sm:ml-auto">
            <span className="text-muted-foreground">Or read a curated guide:</span>
            {curated.map((g) => (
              <Link
                key={g.slug}
                href={`/guides/${g.slug}`}
                className="inline-flex items-center gap-0.5 rounded font-medium text-foreground underline-offset-4 hover:underline focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
              >
                {g.app_name} <ArrowRightIcon className="size-3" aria-hidden />
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
