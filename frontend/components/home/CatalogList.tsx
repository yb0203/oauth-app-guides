"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Check, Search } from "lucide-react";
import { cn } from "cn";
import { TIER_META, tierMeta } from "@/lib/tiers";
import type { CatalogEntry, Tier } from "@/types/guide";

const TIER_FILTERS: Tier[] = ["instant", "verify_to_scale", "review_required", "partner_only", "unknown"];

function StatusChip({ status }: { status: string }) {
  const label = status === "managed" ? "Managed by Composio" : status === "byo" ? "Bring your own app" : "Not in catalog";
  return (
    <span className={cn("inline-flex items-center text-xs", status === "managed" ? "font-medium text-success" : "text-muted-foreground")}>
      {label}
    </span>
  );
}

/** Verified tier when a guide exists, otherwise the research guess. */
const effectiveTier = (c: CatalogEntry) => (c.has_guide && c.tier ? c.tier : c.tier_guess);

function TierChip({ entry }: { entry: CatalogEntry }) {
  const verified = entry.has_guide && !!entry.tier;
  const meta = tierMeta(effectiveTier(entry));
  if (verified) {
    return (
      <span
        title="Verified by a guide"
        className={cn("inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-xs font-medium", meta.classes)}
      >
        <Check aria-hidden className="size-3" />
        {meta.label}
      </span>
    );
  }
  return (
    <span
      title="Research-based guess; generate a guide to verify it"
      className="inline-flex items-center gap-1 rounded-md border border-dashed px-1.5 py-0.5 text-xs text-muted-foreground"
    >
      <span aria-hidden className={cn("size-1.5 rounded-full opacity-60", meta.dot)} />
      {meta.label}
      <span className="text-[10px] uppercase tracking-wide opacity-70">guess</span>
    </span>
  );
}

export function CatalogList({ catalog }: { catalog: CatalogEntry[] }) {
  const [q, setQ] = useState("");
  const [tier, setTier] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [onlyReady, setOnlyReady] = useState(false);

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return catalog
      .filter((c) => !needle || c.name.toLowerCase().includes(needle) || c.slug.includes(needle))
      .filter((c) => !tier || effectiveTier(c) === tier)
      .filter((c) => !status || c.composio_status === status)
      .filter((c) => !onlyReady || c.has_guide)
      .sort((a, b) => Number(b.has_guide) - Number(a.has_guide) || a.name.localeCompare(b.name));
  }, [catalog, q, tier, status, onlyReady]);

  const chip = (active: boolean) =>
    cn(
      "shrink-0 cursor-pointer rounded-full border px-2.5 py-1 text-xs whitespace-nowrap transition-colors focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
      active ? "border-foreground bg-foreground text-background" : "text-muted-foreground hover:bg-muted hover:text-foreground",
    );

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-56 flex-1">
          <Search aria-hidden className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Filter apps"
            aria-label="Filter apps"
            className="h-9 w-full rounded-lg border bg-background pl-8 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/60"
          />
        </div>
        <div className="flex w-full gap-2 -m-1 overflow-x-auto p-1 [scrollbar-width:none] sm:w-auto sm:overflow-visible [&::-webkit-scrollbar]:hidden">
        <button type="button" aria-pressed={onlyReady} className={chip(onlyReady)} onClick={() => setOnlyReady((v) => !v)}>
          Guide ready
        </button>
        <button type="button" aria-pressed={status === "managed"} className={chip(status === "managed")} onClick={() => setStatus(status === "managed" ? null : "managed")}>
          Managed
        </button>
        <button type="button" aria-pressed={status === "byo"} className={chip(status === "byo")} onClick={() => setStatus(status === "byo" ? null : "byo")}>
          Bring your own
        </button>
        </div>
      </div>
      <div className="mt-1 flex gap-1.5 -m-1 overflow-x-auto p-1 [scrollbar-width:none] sm:flex-wrap sm:overflow-visible [&::-webkit-scrollbar]:hidden">
        {TIER_FILTERS.map((t) => (
          <button key={t} type="button" aria-pressed={tier === t} className={chip(tier === t)} onClick={() => setTier(tier === t ? null : t)}>
            <span aria-hidden className={cn("mr-1.5 inline-block size-1.5 rounded-full", TIER_META[t].dot)} />
            {TIER_META[t].label}
          </button>
        ))}
      </div>

      <div className="mt-4 overflow-hidden rounded-xl border">
        <div className="grid grid-cols-[minmax(0,1fr)_6rem] items-center gap-3 border-b bg-muted/50 px-4 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_6rem]">
          <span>App</span>
          <span className="hidden sm:block">Tier</span>
          <span className="hidden sm:block">Composio</span>
          <span className="text-right">Guide</span>
        </div>
        {rows.length === 0 && <p className="px-4 py-8 text-center text-sm text-muted-foreground">No apps match these filters.</p>}
        <ul className="divide-y">
          {rows.map((c) => {
            const meta = tierMeta(effectiveTier(c));
            const verified = c.has_guide && !!c.tier;
            return (
              <li
                key={c.slug}
                className="grid grid-cols-[minmax(0,1fr)_6rem] items-center gap-3 px-4 py-2.5 text-sm sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_6rem]"
              >
                <span className="min-w-0">
                  <span className="block truncate font-medium">{c.name}</span>
                  <span className={cn("block text-xs sm:hidden", verified ? meta.text : "text-muted-foreground")}>
                    {meta.label}
                    {verified ? "" : " (guess)"}
                  </span>
                </span>
                <span className="hidden sm:block">
                  <TierChip entry={c} />
                </span>
                <span className="hidden sm:block">
                  <StatusChip status={c.composio_status} />
                </span>
                <span className="text-right">
                  {c.has_guide ? (
                    <Link
                      href={`/guides/${c.guide_slug ?? c.slug}`}
                      className="inline-flex items-center rounded-md border border-brand/30 bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand transition-colors hover:border-brand/50 focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
                    >
                      Read guide
                    </Link>
                  ) : (
                    <Link
                      href={`/generate?app=${encodeURIComponent(c.name)}`}
                      className="inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
                    >
                      Generate
                    </Link>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        {rows.length} of {catalog.length} apps. Tiers marked “guess” are research-based until a guide has verified them.
      </p>
    </div>
  );
}
