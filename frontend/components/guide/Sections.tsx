"use client";

import { ArrowRight, ExternalLink } from "lucide-react";
import { cn } from "cn";
import type { Fact, Guide, PreparedScope, Review, Source, WallProbe } from "@/types/guide";
import { Chip, CopyButton, Eyebrow, Section, fmtDate } from "./shared";
import { Cite, CiteList, collectEvidence, markerFor } from "./Cite";

/** Row list used by every "list of facts" section: text with its citation marker(s) inline. */
function FactList({ facts, sources }: { facts: Fact[]; sources: Source[] }) {
  return (
    <ul className="divide-y rounded-lg border bg-card">
      {facts.map((f, i) => (
        <li key={i} className="px-3.5 py-3 text-sm leading-relaxed">
          {f.text}
          <Cite evidence={f.evidence} sources={sources} fact={f.text} />
        </li>
      ))}
    </ul>
  );
}

export function StartSection({ guide }: { guide: Guide }) {
  const facts = guide.before_you_start ?? [];
  if (!guide.byo_advice && facts.length === 0) return null;
  return (
    <>
      {guide.byo_advice && (
        <Section id="byo" title="Should you bring your own app?">
          <div className="rounded-lg border bg-muted/40 px-3.5 py-3 text-sm leading-relaxed">{guide.byo_advice}</div>
        </Section>
      )}
      {facts.length > 0 && (
        <Section id="before" title="Before you start">
          <FactList facts={facts} sources={guide.sources} />
        </Section>
      )}
    </>
  );
}

const LIMIT_GRID = "sm:grid sm:grid-cols-[minmax(0,1.25fr)_minmax(0,0.9fr)_minmax(0,1.15fr)] sm:gap-x-4";

export function LimitsSection({ guide }: { guide: Guide }) {
  const limits = guide.limits ?? [];
  if (limits.length === 0) return null;
  return (
    <Section id="limits" title="Limits">
      <div className="overflow-hidden rounded-lg border bg-card">
        <div className={cn("hidden border-b bg-muted/50 px-3.5 py-2 text-xs font-medium text-muted-foreground", LIMIT_GRID)}>
          <span>What</span>
          <span>Value</span>
          <span>Applies to</span>
        </div>
        <ul className="divide-y">
          {limits.map((l, i) => (
            <li key={i} className={cn("space-y-1 px-3.5 py-3 text-sm sm:space-y-0", LIMIT_GRID)}>
              <span className="block font-medium sm:font-normal">{l.what}</span>
              <span className="block font-mono text-xs leading-6 sm:text-[13px]">
                {l.value == null ? "unknown" : `${l.value.toLocaleString("en-US")} ${l.unit ?? ""}`.trim()}
                <Cite evidence={l.evidence} sources={guide.sources} fact={`${l.what}: ${l.value ?? "unknown"} ${l.unit ?? ""}`.trim()} />
              </span>
              <span className="block text-muted-foreground">{l.scope}</span>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

const REQUIRED: Record<Review["required"], { label: string; cls: string }> = {
  yes: { label: "Review required", cls: "border-danger-border bg-danger-soft text-danger" },
  no: { label: "No review", cls: "border-success-border bg-success-soft text-success" },
  conditional: { label: "Review depends on scopes or usage", cls: "border-warning-border bg-warning-soft text-warning" },
};

function KV({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-0.5 sm:grid-cols-[7rem_minmax(0,1fr)] sm:gap-3">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="min-w-0">{children}</dd>
    </div>
  );
}

export function ReviewSection({ guide }: { guide: Guide }) {
  const r = guide.review;
  if (!r) return null;
  const req = REQUIRED[r.required] ?? REQUIRED.conditional;
  return (
    <Section id="review" title="Review and approval">
      <div className="space-y-4 rounded-lg border bg-card p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Chip className={cn("px-2.5 py-1 text-xs", req.cls)}>{req.label}</Chip>
          <span className="text-sm">
            <CiteList evidence={r.evidence} sources={guide.sources} fact="Review and approval" />
          </span>
        </div>
        {(r.trigger || r.cost || r.reviewer) && (
          <dl className="space-y-1.5 text-sm leading-relaxed">
            {r.trigger && <KV k="Triggered by">{r.trigger}</KV>}
            {r.cost && <KV k="Cost">{r.cost}</KV>}
            {r.reviewer && <KV k="Reviewer">{r.reviewer}</KV>}
          </dl>
        )}
        {(r.wait_official || r.wait_community) && (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-info-border bg-info-soft p-3">
              <div className="text-[11px] font-medium tracking-wide text-info uppercase">Official wait time</div>
              <div className="mt-1 text-sm leading-snug">{r.wait_official ?? "Not published by the provider"}</div>
            </div>
            <div className="rounded-lg border border-warning-border bg-warning-soft p-3">
              <div className="text-[11px] font-medium tracking-wide text-warning uppercase">Community-reported wait</div>
              <div className="mt-1 text-sm leading-snug">{r.wait_community ?? "No community reports found"}</div>
            </div>
          </div>
        )}
        {r.submit?.length > 0 && (
          <div className="space-y-1.5">
            <Eyebrow>What to submit</Eyebrow>
            <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed marker:text-muted-foreground/60">
              {r.submit.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Section>
  );
}

export function GatesSection({ guide }: { guide: Guide }) {
  const gates = guide.customer_gates ?? [];
  const gotchas = guide.gotchas ?? [];
  if (gates.length === 0 && gotchas.length === 0) return null;
  return (
    <>
      {gates.length > 0 && (
        <Section id="gates" title="Customer gates" description="Things your end users' accounts or organizations can block, outside your control.">
          <FactList facts={gates} sources={guide.sources} />
        </Section>
      )}
      {gotchas.length > 0 && (
        <Section id="gotchas" title="Gotchas">
          <FactList facts={gotchas} sources={guide.sources} />
        </Section>
      )}
    </>
  );
}

export function BlockersSection({ guide }: { guide: Guide }) {
  const blockers = guide.blockers ?? [];
  if (blockers.length === 0) return null;
  return (
    <Section id="blocked" title="When you're blocked">
      <div className="grid gap-3">
        {blockers.map((b, i) => (
          <div key={i} className="break-inside-avoid space-y-3 rounded-lg border bg-card p-4 text-sm leading-relaxed">
            <div>
              <div className="text-[11px] font-medium tracking-wide text-danger uppercase">Symptom</div>
              <p className="mt-0.5 font-medium">
                {b.symptom}
                <Cite evidence={b.evidence} sources={guide.sources} fact={b.symptom} />
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 sm:gap-6">
              <div>
                <Eyebrow>Cause</Eyebrow>
                <p className="mt-0.5">{b.cause}</p>
              </div>
              <div>
                <div className="text-[11px] font-medium tracking-wide text-success uppercase">Fix</div>
                <p className="mt-0.5">{b.fix}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

const REVIEW_CLASS: Record<PreparedScope["review_class"], string> = {
  none: "border-success-border bg-success-soft text-success",
  sensitive: "border-warning-border bg-warning-soft text-warning",
  restricted: "border-danger-border bg-danger-soft text-danger",
  unknown: "border-dashed border-muted-foreground/60 text-muted-foreground",
};
const REVIEW_CLASS_LABEL: Record<PreparedScope["review_class"], string> = {
  none: "no review",
  sensitive: "sensitive",
  restricted: "restricted",
  unknown: "unknown",
};

const SCOPE_GRID = "sm:grid sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1.6fr)_7rem] sm:gap-x-4";

export function PreparedSection({ guide }: { guide: Guide }) {
  const p = guide.prepared;
  if (!p) return null;
  const consent = Object.entries(p.consent_screen ?? {});
  const hasAny = p.scopes?.length || p.privacy_policy_outline?.length || consent.length || p.review_text;
  if (!hasAny) return null;
  return (
    <Section id="prepared" title="Prepared for you" description="Drafts and values to paste, so you are not writing them from scratch.">
      {p.scopes?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Scopes</h3>
          <div className="overflow-hidden rounded-lg border bg-card">
            <div className={cn("hidden border-b bg-muted/50 px-3.5 py-2 text-xs font-medium text-muted-foreground", SCOPE_GRID)}>
              <span>Scope</span>
              <span>Why you would ask for it</span>
              <span>Review class</span>
            </div>
            <ul className="divide-y">
              {p.scopes.map((s, i) => (
                <li key={i} className={cn("space-y-1.5 px-3.5 py-3 text-sm sm:space-y-0 sm:items-start", SCOPE_GRID)}>
                  <code className="block font-mono text-xs leading-6 break-all">{s.scope}</code>
                  <span className="block leading-relaxed">{s.why}</span>
                  <span className="block">
                    <Chip className={REVIEW_CLASS[s.review_class] ?? REVIEW_CLASS.unknown}>{REVIEW_CLASS_LABEL[s.review_class] ?? s.review_class}</Chip>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {p.privacy_policy_outline?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Privacy policy outline</h3>
          <ul className="list-disc space-y-1 rounded-lg border bg-card py-3 pr-4 pl-8 text-sm leading-relaxed marker:text-muted-foreground/60">
            {p.privacy_policy_outline.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </div>
      )}

      {consent.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Consent screen fields</h3>
          <dl className="divide-y rounded-lg border bg-card">
            {consent.map(([k, v]) => (
              <div key={k} className="grid gap-1.5 px-3.5 py-2.5 text-sm sm:grid-cols-[11rem_minmax(0,1fr)_auto] sm:items-start sm:gap-3">
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="min-w-0 font-mono text-xs leading-6 break-all">{v}</dd>
                <CopyButton text={v} ariaLabel={`Copy ${k}`} className="justify-self-start sm:justify-self-end" />
              </div>
            ))}
          </dl>
        </div>
      )}

      {p.review_text && (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">Text for the review submission</h3>
            <CopyButton text={p.review_text} label="Copy text" />
          </div>
          <pre className="max-h-80 overflow-auto rounded-lg border bg-muted/40 p-3.5 font-mono text-xs leading-relaxed whitespace-pre-wrap">{p.review_text}</pre>
        </div>
      )}
    </Section>
  );
}

const OUTCOME: Record<WallProbe["outcome"], { label: string; cls: string }> = {
  login_wall: { label: "login wall", cls: "border-warning-border bg-warning-soft text-warning" },
  console_reachable: { label: "console reachable", cls: "border-success-border bg-success-soft text-success" },
  blocked: { label: "blocked", cls: "border-danger-border bg-danger-soft text-danger" },
  error: { label: "error", cls: "border-border bg-muted text-muted-foreground" },
};

function hostPath(u: string): string {
  try {
    const x = new URL(u);
    return x.host + (x.pathname === "/" ? "" : x.pathname);
  } catch {
    return u;
  }
}

export function WallCard({ wall }: { wall: WallProbe | null }) {
  return (
    <div className="space-y-3 rounded-lg border bg-card p-4 text-sm">
      {!wall ? (
        <p className="text-muted-foreground">Not probed. We did not try to open the provider&apos;s developer console for this guide.</p>
      ) : (
        <>
          <p className="text-xs leading-relaxed text-muted-foreground">
            What happens when an unauthenticated visitor opens the console. Observed with a read-only {wall.method === "browser" ? "browser" : "HTTP"} request;
            nothing was typed or submitted.
          </p>
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <Chip className={(OUTCOME[wall.outcome] ?? OUTCOME.error).cls}>{(OUTCOME[wall.outcome] ?? OUTCOME.error).label}</Chip>
            {wall.bot_check && <Chip className="border-danger-border bg-danger-soft text-danger">bot check</Chip>}
            <Chip className="border-border text-muted-foreground">method: {wall.method}</Chip>
            <span className="text-muted-foreground">observed {fmtDate(wall.observed_at)}</span>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
            <a href={wall.console_url} target="_blank" rel="noopener noreferrer" className="rounded border bg-muted/50 px-1.5 py-0.5 break-all hover:underline">
              {hostPath(wall.console_url)}
            </a>
            {(wall.redirect_chain ?? []).map((u, i) => (
              <span key={i} className="inline-flex items-center gap-1.5">
                <ArrowRight className="size-3 text-muted-foreground" aria-hidden />
                <span className="rounded border bg-muted/50 px-1.5 py-0.5 break-all" title={u}>
                  {hostPath(u).split("?")[0]}
                </span>
              </span>
            ))}
          </div>
          <dl className="grid gap-x-4 gap-y-1 text-xs sm:grid-cols-[auto_1fr]">
            {wall.wall_host && (
              <>
                <dt className="text-muted-foreground">Wall host</dt>
                <dd className="font-mono">{wall.wall_host}</dd>
              </>
            )}
            <dt className="text-muted-foreground">Asks for</dt>
            <dd>{wall.asks_for || "unknown"}</dd>
          </dl>
        </>
      )}
    </div>
  );
}

export function OpenSection({ guide }: { guide: Guide }) {
  const qs = guide.open_questions ?? [];
  const conflicts = guide.conflicts ?? [];
  return (
    <>
      {qs.length > 0 && (
        <Section id="open" title="Open questions" description="What we could not settle. Check these yourself.">
          <ul className="list-disc space-y-1.5 rounded-lg border bg-card py-3 pr-4 pl-8 text-sm leading-relaxed marker:text-muted-foreground/60">
            {qs.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </Section>
      )}
      <Section id="wall" title="Developer console access">
        <WallCard wall={guide.wall_probe} />
      </Section>
      {conflicts.length > 0 && (
        <Section id="conflicts" title="Conflicting evidence" description="Sources disagree. Both claims are shown with their evidence.">
          <div className="grid gap-3">
            {conflicts.map((c, i) => (
              <div key={i} className="break-inside-avoid space-y-3 rounded-lg border border-warning-border bg-warning-soft p-4 text-sm">
                <div className="font-mono text-xs text-warning">{c.field}</div>
                <p className="leading-relaxed text-foreground">{c.description}</p>
                <ul className="space-y-2">
                  {(c.evidence ?? []).map((e, j) => (
                    <li key={j} className="flex items-start gap-2 text-xs leading-relaxed text-foreground/80">
                      <span className="mt-1.5 shrink-0">
                        <Cite evidence={e} sources={guide.sources} fact={c.field} />
                      </span>
                      <span className="min-w-0">{e.quote ? `“${e.quote}”` : (e.note ?? "No quote")}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

const KIND: Record<Source["kind"], { label: string; cls: string }> = {
  official_docs: { label: "official docs", cls: "border-info-border bg-info-soft text-info" },
  composio_docs: { label: "Composio docs", cls: "border-brand/30 bg-brand-soft text-brand" },
  community: { label: "community", cls: "border-warning-border bg-warning-soft text-warning" },
  observation: { label: "our observation", cls: "border-success-border bg-success-soft text-success" },
};

export function SourcesSection({ guide }: { guide: Guide }) {
  const sources = guide.sources ?? [];
  if (sources.length === 0) return null;
  return (
    <Section id="sources" title="Sources" description="The number matches the small marker next to each claim.">
      <ol className="divide-y rounded-lg border bg-card">
        {sources.map((s, i) => {
          const k = KIND[s.kind] ?? KIND.community;
          return (
            <li key={s.id} id={`source-${s.id}`} className="flex items-start gap-3 px-3.5 py-3 text-sm">
              <span className="mt-px inline-flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full border bg-muted px-1 text-[11px] font-semibold tabular-nums">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1 space-y-1">
                <a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-start gap-1.5 font-medium underline-offset-2 hover:underline">
                  <span className="min-w-0">{s.title}</span>
                  <ExternalLink className="mt-1 size-3 shrink-0 text-muted-foreground print:hidden" aria-hidden />
                </a>
                <div className="font-mono text-[11px] leading-snug break-all text-muted-foreground">{s.url}</div>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1 pt-0.5">
                  <Chip className={k.cls}>{k.label}</Chip>
                  <span className="text-xs text-muted-foreground">accessed {fmtDate(s.accessed)}</span>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </Section>
  );
}

/** Print only: the exact quote behind every numbered marker, since hover cards do not exist on paper. */
export function PrintEvidence({ guide }: { guide: Guide }) {
  const all = collectEvidence(guide);
  if (all.length === 0) return null;
  const sources = guide.sources ?? [];
  const bySource = sources
    .map((s, i) => {
      const seen = new Set<string>();
      const rows = all.filter(({ evidence: e }) => e.source_id === s.id && e.quote && !seen.has(e.quote) && seen.add(e.quote));
      return { s, n: i + 1, rows };
    })
    .filter((x) => x.rows.length > 0);
  const tested = all.filter(({ evidence: e }) => markerFor(e, sources) === "T" && e.note);
  const loose = all.filter(({ evidence: e }) => !e.source_id && e.label !== "TESTED");
  return (
    <section className="hidden space-y-3 print:block" aria-label="Evidence quotes">
      <h2 className="text-lg font-semibold">Evidence quotes</h2>
      {bySource.map(({ s, n, rows }) => (
        <div key={s.id} className="break-inside-avoid text-xs leading-snug">
          <div className="font-semibold">
            [{n}] {s.title}
          </div>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {rows.map(({ evidence: e, fact }, i) => (
              <li key={i}>
                &ldquo;{e.quote}&rdquo; <span className="text-muted-foreground">({e.label}, {e.found_in === "hidden_section" ? "found in a hidden section" : "visible page text"}; {fact})</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
      {tested.length > 0 && (
        <div className="break-inside-avoid text-xs leading-snug">
          <div className="font-semibold">[T] Observed by our own tooling</div>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {tested.map(({ evidence: e, fact }, i) => (
              <li key={i}>
                {e.note} <span className="text-muted-foreground">({fact})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {loose.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {loose.length} claim{loose.length === 1 ? "" : "s"} marked [?] have no linked source and should be checked before relying on them.
        </p>
      )}
    </section>
  );
}
