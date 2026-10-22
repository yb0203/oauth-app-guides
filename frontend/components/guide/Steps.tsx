"use client";

import { AlertTriangle, Info } from "lucide-react";
import { cn } from "cn";
import type { Guide, Step } from "@/types/guide";
import { CopyButton, Section } from "./shared";
import { Cite } from "./Cite";
import { ActorBadge } from "./ActorBadge";

/** A copyable monospace value. If it is the Composio callback URL, its note is shown right under it. */
function ValueRow({ label, value, guide }: { label: string; value: string; guide: Guide }) {
  const callbackUrl = guide.composio?.callback_url;
  const note = guide.composio?.callback_note;
  const isCallback = !!callbackUrl && value.includes(callbackUrl);
  return (
    <div className="space-y-1.5">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="flex items-start gap-2">
        <code className="min-w-0 flex-1 rounded-md border bg-muted/50 px-2.5 py-1.5 font-mono text-xs leading-relaxed break-all">{value}</code>
        <CopyButton text={value} ariaLabel={`Copy ${label}`} />
      </div>
      {isCallback && note && <CallbackNote note={note} />}
    </div>
  );
}

function CallbackNote({ note }: { note: string }) {
  return (
    <p className="flex items-start gap-2 rounded-md border border-info-border bg-info-soft px-2.5 py-2 text-xs leading-relaxed text-info">
      <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
      <span>{note}</span>
    </p>
  );
}

export function CallbackCard({ guide }: { guide: Guide }) {
  const c = guide.composio;
  if (!c?.callback_url) return null;
  return (
    <div className="space-y-2 rounded-lg border bg-card p-3.5" id="callback">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
        <h3 className="text-sm font-semibold">Composio callback URL</h3>
        <span className="text-xs text-muted-foreground">Use it as the redirect URL in the provider&apos;s app settings</span>
      </div>
      <div className="flex items-start gap-2">
        <code className="min-w-0 flex-1 rounded-md border bg-muted/50 px-2.5 py-1.5 font-mono text-xs leading-relaxed break-all">{c.callback_url}</code>
        <CopyButton text={c.callback_url} ariaLabel="Copy Composio callback URL" />
      </div>
      {c.callback_note && <CallbackNote note={c.callback_note} />}
    </div>
  );
}

function StepItem({ step, guide, last }: { step: Step; guide: Guide; last: boolean }) {
  return (
    <li className="relative flex gap-3 break-inside-avoid sm:gap-4" id={`step-${step.n}`}>
      <div className="flex flex-col items-center">
        <div className="keep-bg z-10 flex size-7 shrink-0 items-center justify-center rounded-full border bg-background text-xs font-semibold tabular-nums">
          {step.n}
        </div>
        {!last && <div className="mt-1 w-px flex-1 bg-foreground/15" />}
      </div>
      <div className={cn("min-w-0 flex-1", !last && "pb-7")}>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <h3 className="min-w-0 text-base leading-7 font-semibold">{step.title}</h3>
          <ActorBadge actor={step.actor} reason={step.human_reason} />
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-foreground/80">
          {step.detail}
          <Cite evidence={step.evidence} sources={guide.sources} fact={`Step ${step.n}: ${step.title}`} />
        </p>
        {step.values?.length > 0 && (
          <div className="mt-3 space-y-3 rounded-lg border bg-card p-3">
            {step.values.map((v, i) => (
              <ValueRow key={i} label={v.label} value={v.value} guide={guide} />
            ))}
          </div>
        )}
        {step.irreversible && (
          <div role="note" className="mt-3 flex items-start gap-2.5 rounded-lg border border-warning-border bg-warning-soft px-3 py-2.5 text-sm text-warning">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
            <div>
              <div className="font-semibold">Check before you click</div>
              <div className="text-xs leading-relaxed opacity-90">This step can&apos;t be undone once you confirm it.</div>
            </div>
          </div>
        )}
      </div>
    </li>
  );
}

export function StepsSection({ guide }: { guide: Guide }) {
  const steps = [...(guide.steps ?? [])].sort((a, b) => a.n - b.n);
  if (steps.length === 0) return null;
  return (
    <Section id="steps" title="Steps you can act on" description="In order. The chip on each step says who has to do it; the small number is the evidence.">
      <CallbackCard guide={guide} />
      <ol className="pt-1">
        {steps.map((s, i) => (
          <StepItem key={`${s.n}-${i}`} step={s} guide={guide} last={i === steps.length - 1} />
        ))}
      </ol>
    </Section>
  );
}
