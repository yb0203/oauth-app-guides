"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDown, RotateCcw } from "lucide-react";
import { cn } from "cn";
import { TIER_LADDER, TIER_LADDER_BG, tierMeta } from "@/lib/tiers";
import type { Guide, SituationVariant, Verdict } from "@/types/guide";
import { Cite } from "./Cite";
import { ActorBadge } from "./ActorBadge";
import { LABEL_META } from "./CitationChip";
import { Chip, Eyebrow, formatEffort, variantEffort } from "./shared";
import { useSituation } from "./situation";

/* ------------------------------------------------------------------ helpers */

/**
 * Height that eases to its content instead of jumping. Server render and print use natural height; after mount the
 * wrapper follows the measured height of its child with a short transition, so changing the situation moves
 * everything below it smoothly rather than snapping.
 */
function AutoHeight({ children, className }: { children: React.ReactNode; className?: string }) {
  const inner = useRef<HTMLDivElement>(null);
  const [h, setH] = useState<number | undefined>(undefined);
  useEffect(() => {
    const el = inner.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setH(el.offsetHeight));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return (
    <div
      style={{ height: h }}
      className={cn("overflow-hidden transition-[height] duration-200 ease-out motion-reduce:transition-none print:!h-auto print:overflow-visible", className)}
    >
      <div ref={inner}>{children}</div>
    </div>
  );
}

const FADE = "animate-in fade-in-0 duration-200 motion-reduce:animate-none";

/** Fade class for content keyed by the active variant; nothing on first paint, so page load stays still. */
function useFade(key: number): string {
  const [initial] = useState(key);
  return key === initial ? "" : FADE;
}

/** Calendar label to rough days (max). Null when the text has no usable number (for example "Not available to individuals"). */
function parseWaitDays(label: string): number | null {
  const l = label.toLowerCase();
  const re = /(\d+(?:\.\d+)?)(?:\s*(?:to|-|–)\s*(\d+(?:\.\d+)?))?\+?\s*(day|week|month|year)s?/g;
  const unit = { day: 1, week: 7, month: 30, year: 365 } as const;
  let best: number | null = null;
  for (const m of l.matchAll(re)) {
    const v = Number(m[2] ?? m[1]) * unit[m[3] as keyof typeof unit];
    best = best == null ? v : Math.max(best, v);
  }
  if (best != null) return best;
  if (/same day|under an hour|minutes|hours?\b|instant/.test(l)) return 0;
  return null;
}

/** Log-ish length so ten minutes and fourteen weeks both stay visible. Input in hours. */
const g = (hours: number) => Math.log10(1 + hours * 6);

type WaitSpec = { days: number | null; open: boolean };

function waitFor(v: Verdict, variantLabel: string | null): WaitSpec {
  if (variantLabel != null) {
    const d = parseWaitDays(variantLabel);
    return { days: d, open: d == null };
  }
  const max = v.calendar?.max_days;
  if (max == null) return { days: v.calendar?.min_days ?? null, open: true };
  return { days: max, open: false };
}

function WorkWaitBar({ verdict, appName, variantLabel, calendarLabel }: { verdict: Verdict; appName: string; variantLabel: string | null; calendarLabel: string }) {
  const work = verdict.effort_hours?.max ?? 0;
  const wait = waitFor(verdict, variantLabel);
  const gw = g(work);
  const gk = wait.days != null ? g(wait.days * 24) : 0;
  let workPct: number;
  if (wait.open) workPct = gk > 0 ? Math.min(65, Math.max(6, (gw / (gw + gk)) * 100)) : 60; // open-ended wait: always show the striped part
  else if (gk === 0) workPct = 100;
  else workPct = Math.min(94, Math.max(6, (gw / (gw + gk)) * 100));
  const label = `Your work ${formatEffort(verdict.effort_hours)} against waiting on ${appName}: ${calendarLabel}. Decorative bar on a log scale, not to scale.`;
  return (
    <div className="space-y-1.5">
      <div role="img" aria-label={label} title="Log scale: long waits are compressed, so this is a rough picture, not a measurement." className="flex h-1.5 w-full gap-px overflow-hidden rounded-full bg-muted">
        <div className="keep-bg bg-brand transition-[width] duration-300 motion-reduce:transition-none" style={{ width: `${workPct}%` }} />
        {workPct < 100 && (
          <div
            className={cn("keep-bg min-w-0 flex-1 transition-[width] duration-300 motion-reduce:transition-none", wait.open ? "bg-[repeating-linear-gradient(135deg,var(--muted-foreground)_0_3px,transparent_3px_6px)] opacity-60" : "bg-muted-foreground/45")}
          />
        )}
      </div>
    </div>
  );
}

const BASIS = {
  official: { label: "Official docs", cls: "border-info-border bg-info-soft text-info", title: "Wait time stated by the provider" },
  community: { label: "Community reports", cls: "border-warning-border bg-warning-soft text-warning", title: "Wait time reported by developers; not official" },
  estimate: { label: "Our estimate", cls: "border-dashed border-muted-foreground/60 text-muted-foreground", title: "No published figure; this is an estimate" },
} as const;

const CONFIDENCE = {
  high: "border-success-border bg-success-soft text-success",
  medium: "border-warning-border bg-warning-soft text-warning",
  low: "border-danger-border bg-danger-soft text-danger",
} as const;

function variantLabels(guide: Guide, v: SituationVariant): string {
  return Object.entries(v.when)
    .map(([qid, oid]) => guide.situations.questions.find((q) => q.id === qid)?.options.find((o) => o.id === oid)?.label ?? oid)
    .join(" · ");
}

function Tile({ eyebrow, dot, aside, children }: { eyebrow: React.ReactNode; dot: string; aside?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="min-w-0 rounded-lg border bg-background p-3">
      <div className="flex items-center justify-between gap-2">
        <Eyebrow className="flex min-w-0 items-center gap-1.5">
          <span aria-hidden className={cn("keep-bg size-2 shrink-0 rounded-[3px]", dot)} />
          <span className="min-w-0 truncate">{eyebrow}</span>
        </Eyebrow>
        {aside}
      </div>
      <div className="mt-2 min-w-0">{children}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ verdict */

export function VerdictCard({ guide }: { guide: Guide }) {
  const { tier: tierId, summary, calendarLabel, variant, reset } = useSituation();
  const v = guide.verdict;
  const eff = variantEffort(variant?.notes);
  const tier = tierMeta(tierId);
  const variants = guide.situations?.variants ?? [];
  const variantIdx = variant ? variants.indexOf(variant) : -1;
  const fade = useFade(variantIdx);
  const ladderIdx = TIER_LADDER.indexOf(tierId); // -1 for "unknown"
  const basis = BASIS[v.calendar_basis] ?? BASIS.estimate;

  return (
    <section aria-label="Verdict" className="rounded-xl border bg-card p-4 text-card-foreground shadow-xs" data-testid="verdict-card">
      <p className="sr-only" aria-live="polite">
        {tier.label}. {summary}
      </p>

      {/* tier + confidence */}
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
            <span className={cn("text-2xl leading-tight font-semibold tracking-tight", tier.text)} data-testid="tier-badge">
              {tier.label}
            </span>
            <span className="text-sm text-muted-foreground">{tier.hint}</span>
          </div>
        </div>
        <Chip className={cn("mt-0.5 px-2.5 py-1 text-xs", CONFIDENCE[v.confidence] ?? CONFIDENCE.medium)} title="How sure we are about this verdict">
          {v.confidence[0].toUpperCase() + v.confidence.slice(1)} confidence
        </Chip>
      </div>

      {/* difficulty ladder */}
      <ol className="mt-3.5 grid grid-cols-4 gap-1.5" aria-label={ladderIdx >= 0 ? `Difficulty: step ${ladderIdx + 1} of 4, ${tier.label}` : "Difficulty: unknown"}>
        {TIER_LADDER.map((t, i) => {
          const filled = ladderIdx >= 0 && i <= ladderIdx;
          const current = i === ladderIdx;
          return (
            <li key={t} aria-current={current ? "step" : undefined} className="min-w-0 space-y-1.5">
              <div className={cn("keep-bg h-1.5 rounded-full transition-colors duration-200", filled ? TIER_LADDER_BG[i] : "bg-muted")} />
              <div className={cn("text-[11px] leading-tight", current ? "font-semibold text-foreground" : "text-muted-foreground")}>
                {tierMeta(t).short}
                {current && <span className="sr-only"> (current)</span>}
              </div>
            </li>
          );
        })}
      </ol>

      {/* summary and "Changed because" callout: one block whose height eases between situations */}
      <AutoHeight className="mt-3.5">
        <div key={variantIdx} className={fade}>
          <p className="text-base leading-relaxed text-foreground" data-testid="verdict-summary">
            {summary}
          </p>
          {variant && (
            <div className="mt-3.5 rounded-lg border border-brand/25 bg-brand-soft p-3 text-sm" data-testid="variant-callout">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="font-medium text-brand">Changed because:</span>
                <span className="min-w-0 text-foreground">{variantLabels(guide, variant)}</span>
                <button
                  type="button"
                  onClick={reset}
                  className="ml-auto inline-flex cursor-pointer items-center gap-1 rounded text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none print:hidden"
                >
                  <RotateCcw className="size-3" aria-hidden /> Reset
                </button>
              </div>
              {variant.notes?.length > 0 && (
                <ul className="mt-2 list-disc space-y-1 pl-5 text-foreground/90 marker:text-brand/60">
                  {variant.notes.map((n, j) => (
                    <li key={j}>{n}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </AutoHeight>

      {/* metrics */}
      <AutoHeight className="mt-3.5">
        <div className="grid gap-3 sm:grid-cols-2">
          <Tile eyebrow="Your work" dot="bg-brand" aside={<span className="text-[11px] text-muted-foreground">{eff ? "for this situation" : variant ? "base estimate, all situations" : "hands-on time"}</span>}>
            <div className="text-xl leading-tight font-semibold tracking-tight tabular-nums" data-testid="effort">
              {formatEffort(eff ?? v.effort_hours)}
            </div>
          </Tile>
          <Tile
            eyebrow={`Waiting on ${guide.app_name}`}
            dot="bg-muted-foreground/45"
            aside={
              <Chip className={cn("shrink-0", basis.cls)} title={basis.title}>
                {basis.label}
              </Chip>
            }
          >
            <div key={variantIdx} className={cn("text-sm leading-snug font-medium", fade)} data-testid="calendar-label">
              {calendarLabel || "Unknown"}
            </div>
          </Tile>
        </div>
      </AutoHeight>
      <div className="mt-3">
        <WorkWaitBar verdict={eff ? { ...v, effort_hours: eff } : v} appName={guide.app_name} variantLabel={variant ? variant.calendar_label : null} calendarLabel={calendarLabel} />
      </div>

      <TrustLine guide={guide} />
    </section>
  );
}

/* ------------------------------------------------------------------ trust line */

/**
 * "51 claims: 46 docs-verified (8 in hidden sections) · 2 tested · 2 community · 1 uncertain".
 * Per the schema, docs_verified already includes docs_hidden and total = tested + docs_verified + community + uncertain,
 * so hidden is shown as a subset in parentheses, never added again.
 */
export function TrustLine({ guide, className }: { guide: Guide; className?: string }) {
  const s = guide.verification_summary;
  if (!s || !s.total) return null;
  const hiddenIsSubset = s.docs_hidden > 0 && s.docs_hidden <= s.docs_verified;
  const parts: { key: string; dot: string; text: string }[] = [];
  if (s.docs_verified > 0 || (s.docs_hidden > 0 && !hiddenIsSubset)) {
    parts.push({
      key: "docs",
      dot: LABEL_META.DOCS.dot,
      text: `${s.docs_verified} docs-verified${hiddenIsSubset ? ` (${s.docs_hidden} in hidden sections)` : ""}`,
    });
  }
  if (s.docs_hidden > 0 && !hiddenIsSubset) {
    parts.push({ key: "hidden", dot: LABEL_META.DOCS.dot, text: `${s.docs_hidden} docs-verified in hidden sections` });
  }
  if (s.tested > 0) parts.push({ key: "tested", dot: LABEL_META.TESTED.dot, text: `${s.tested} tested` });
  if (s.community > 0) parts.push({ key: "community", dot: LABEL_META.COMMUNITY.dot, text: `${s.community} community` });
  if (s.uncertain > 0) parts.push({ key: "uncertain", dot: LABEL_META.UNCERTAIN.dot, text: `${s.uncertain} uncertain` });

  return (
    <p className={cn("mt-4 flex flex-wrap items-center gap-x-3.5 gap-y-1 border-t pt-3.5 text-xs text-muted-foreground", className)} data-testid="trust-line">
      <span className="font-semibold text-foreground">{s.total} claims:</span>
      {parts.map((p) => (
        <span key={p.key} className="inline-flex items-center gap-1.5">
          <span aria-hidden className={cn("keep-bg size-1.5 rounded-full", p.dot)} />
          {p.text}
        </span>
      ))}
    </p>
  );
}

/* ------------------------------------------------------------------ start here */

export function StartHere({ guide }: { guide: Guide }) {
  const first = [...(guide.steps ?? [])].sort((a, b) => a.n - b.n)[0];
  if (!first) return null;
  return (
    <section aria-label="Start here" className="rounded-xl border bg-muted/40 px-4 py-3.5 sm:px-5">
      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
        <span className="text-[11px] font-semibold tracking-wide text-brand uppercase">Start here</span>
        <span aria-hidden className="text-muted-foreground/50">
          ·
        </span>
        <span className="text-xs text-muted-foreground">Step {first.n}</span>
        <ActorBadge actor={first.actor} reason={first.human_reason} />
        <a href="#steps" className="ml-auto inline-flex items-center gap-1 text-xs font-medium text-brand underline-offset-2 hover:underline print:hidden">
          All {guide.steps.length} steps <ArrowDown className="size-3" aria-hidden />
        </a>
      </div>
      <h2 className="mt-2 text-base leading-snug font-semibold">{first.title}</h2>
      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
        {first.detail}
        <Cite evidence={first.evidence} sources={guide.sources} />
      </p>
    </section>
  );
}
