"use client";

import type { VerificationProgress } from "@/types/guide";
import { Panel, PanelEmpty } from "./Panel";

function Counter({ value, label, hint }: { value: number; label: string; hint: string }) {
  return (
    <div className="min-w-0 rounded-lg border bg-background px-3 py-2.5">
      <p className="text-lg leading-none font-semibold tabular-nums text-foreground">{value}</p>
      <p className="mt-1.5 text-xs leading-tight font-medium text-foreground">{label}</p>
      <p className="mt-0.5 text-xs leading-tight text-muted-foreground">{hint}</p>
    </div>
  );
}

export function VerificationCard({
  v,
  verifyStatus,
  finished,
}: {
  v: VerificationProgress | null;
  verifyStatus: "pending" | "running" | "done" | "error" | "skipped";
  finished: boolean;
}) {
  const pct = v && v.total > 0 ? Math.min(100, Math.round((v.checked / v.total) * 100)) : 0;
  return (
    <Panel title="Claim verification" aside={v ? `${v.checked} of ${v.total}` : undefined} bodyClassName="min-h-44">
      {!v ? (
        <PanelEmpty>
          {(verifyStatus === "pending" || verifyStatus === "running") && !finished
            ? "Waiting for verification to start."
            : "Verification did not run."}
        </PanelEmpty>
      ) : (
        <div className="animate-in fade-in duration-300 motion-reduce:animate-none">
          <p className="text-sm text-foreground">Claims re-checked against the live pages</p>
          <div
            role="progressbar"
            aria-label="Claims checked"
            aria-valuemin={0}
            aria-valuemax={v.total}
            aria-valuenow={v.checked}
            className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"
          >
            <div
              className="h-full rounded-full bg-brand transition-[width] duration-500 ease-out motion-reduce:transition-none"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
            <Counter value={v.docs_verified} label="Confirmed in docs" hint="quote found on the page" />
            <Counter value={v.hidden} label="In hidden sections" hint="collapsed or tabbed" />
            <Counter value={v.downgraded} label="Downgraded" hint="marked uncertain" />
          </div>
        </div>
      )}
    </Panel>
  );
}
