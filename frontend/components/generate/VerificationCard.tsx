"use client";

import { cn } from "@/lib/utils";
import type { VerificationProgress } from "@/types/guide";
import { AnimatedNumber } from "./AnimatedNumber";
import { Panel } from "./Panel";

function Tally({ value, label, hint, tone }: { value: number; label: string; hint: string; tone?: string }) {
  return (
    <div className="min-w-0 rounded-lg border bg-background px-3 py-2">
      <p className={cn("text-lg leading-none font-semibold text-foreground", tone)}>
        <AnimatedNumber value={value} />
      </p>
      <p className="mt-1.5 text-xs leading-tight font-medium text-foreground">{label}</p>
      <p className="mt-0.5 text-xs leading-tight text-muted-foreground">{hint}</p>
    </div>
  );
}

/** Live "quotes verified n of m" meter, fed by data-verification. Hidden until the first count arrives. */
export function VerificationCard({ v, running }: { v: VerificationProgress; running: boolean }) {
  const pct = v.total > 0 ? Math.min(100, Math.round((v.checked / v.total) * 100)) : 0;
  const complete = v.total > 0 && v.checked >= v.total;
  return (
    <Panel title="Quote verification">
      <div className="animate-in fade-in duration-300 motion-reduce:animate-none">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-sm text-foreground">
            <span className="text-2xl font-semibold tracking-tight tabular-nums">
              <AnimatedNumber value={v.checked} />
            </span>
            <span className="text-muted-foreground"> of {v.total} quotes re-checked on the live pages</span>
          </p>
          <span className="font-mono text-xs text-muted-foreground tabular-nums">{pct}%</span>
        </div>
        <div
          role="progressbar"
          aria-label="Quotes verified"
          aria-valuemin={0}
          aria-valuemax={v.total}
          aria-valuenow={v.checked}
          className="mt-2.5 h-2 overflow-hidden rounded-full bg-muted"
        >
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-500 ease-out motion-reduce:transition-none",
              complete || !running ? "bg-success" : "bg-info",
            )}
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2">
          <Tally value={v.docs_verified} label="Confirmed" hint="quote on the page" tone="text-success" />
          <Tally value={v.hidden} label="Hidden" hint="collapsed or tabbed" />
          <Tally value={v.downgraded} label="Downgraded" hint="marked uncertain" tone={v.downgraded > 0 ? "text-warning" : undefined} />
        </div>
      </div>
    </Panel>
  );
}
