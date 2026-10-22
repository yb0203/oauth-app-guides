"use client";

import { AlertTriangleIcon, RotateCcwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { STAGE_DEFAULT_LABEL } from "@/lib/chat-types";
import { STAGE_ORDER, type StageData, type StageId } from "@/types/guide";

/** Pure panel: what succeeded, what failed, and a retry. */
export function RunErrorPanel({
  message,
  stages,
  sourcesCount,
  hasWall,
  hasVerification,
  onRetry,
}: {
  message: string;
  stages: Partial<Record<StageId, StageData>>;
  sourcesCount: number;
  hasWall: boolean;
  hasVerification: boolean;
  onRetry: () => void;
}) {
  const completed = STAGE_ORDER.filter((id) => stages[id]?.status === "done");
  const failedId =
    STAGE_ORDER.find((id) => stages[id]?.status === "error") ??
    STAGE_ORDER.find((id) => stages[id]?.status === "running") ??
    null;
  const failedStage = failedId ? stages[failedId] : undefined;
  const kept: string[] = [];
  if (sourcesCount > 0) kept.push(`${sourcesCount} ${sourcesCount === 1 ? "source" : "sources"}`);
  if (hasWall) kept.push("the console probe");
  if (hasVerification) kept.push("partial verification");

  return (
    <section
      role="alert"
      className="rounded-lg border border-danger-border bg-danger-soft p-4"
      aria-labelledby="run-error-title"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 gap-3">
          <AlertTriangleIcon className="mt-0.5 size-4 shrink-0 text-danger" aria-hidden />
          <div className="min-w-0">
            <h2 id="run-error-title" className="text-sm font-semibold text-danger">
              The run did not finish
            </h2>
            <p className="mt-1 text-sm break-words text-foreground">{message}</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={onRetry} className="shrink-0 bg-background">
          <RotateCcwIcon aria-hidden /> Retry
        </Button>
      </div>

      <dl className="mt-4 grid gap-3 border-t border-danger-border pt-3 text-xs sm:grid-cols-2">
        <div>
          <dt className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">What succeeded</dt>
          <dd className="mt-1 text-foreground">
            {completed.length === 0 && kept.length === 0 ? (
              "Nothing completed before the failure."
            ) : (
              <>
                {completed.length > 0 && (
                  <span className="block">
                    {completed.map((id) => stages[id]?.label || STAGE_DEFAULT_LABEL[id]).join("; ")}.
                  </span>
                )}
                {kept.length > 0 && <span className="block">Kept below: {kept.join(", ")}.</span>}
              </>
            )}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">What failed</dt>
          <dd className="mt-1 text-foreground">
            {failedId
              ? `${failedStage?.label || STAGE_DEFAULT_LABEL[failedId]}${
                  failedStage?.detail ? ` (${failedStage.detail})` : ""
                }`
              : "The request failed before the first stage started."}
          </dd>
        </div>
      </dl>
    </section>
  );
}
