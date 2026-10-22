"use client";

import { CitationChip } from "./CitationChip";
import type { Evidence, Guide, Source } from "@/types/guide";

/** Marker text: 1-based index of the source in guide.sources; "T" for tested observations without a source, "?" otherwise. */
export function markerFor(e: Evidence, sources: Source[]): string {
  if (e.source_id) {
    const i = (sources ?? []).findIndex((s) => s.id === e.source_id);
    if (i >= 0) return String(i + 1);
  }
  if (e.label === "TESTED") return "T";
  if (e.label === "UNCERTAIN") return "?";
  return "•";
}

/** One inline numbered citation marker for one evidence object. */
export function Cite({ evidence, sources, fact }: { evidence: Evidence | null | undefined; sources: Source[]; fact?: string | null }) {
  if (!evidence) return null;
  const source = evidence.source_id ? (sources ?? []).find((s) => s.id === evidence.source_id) : undefined;
  return (
    <CitationChip
      marker={markerFor(evidence, sources)}
      label={evidence.label}
      quote={evidence.quote}
      foundIn={evidence.found_in}
      sourceTitle={source?.title ?? null}
      sourceUrl={source?.url ?? null}
      note={evidence.note}
      fact={fact ?? null}
    />
  );
}

/** Several markers for an array of evidence. Same source and label are shown once, so a long list stays a short row of numbers. */
export function CiteList({ evidence, sources, fact }: { evidence: Evidence[] | null | undefined; sources: Source[]; fact?: string | null }) {
  if (!evidence || evidence.length === 0) return null;
  const seen = new Set<string>();
  const uniq = evidence.filter((e) => {
    const k = `${e.label}|${markerFor(e, sources)}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
  return (
    <>
      {uniq.map((e, i) => (
        <Cite key={i} evidence={e} sources={sources} fact={fact} />
      ))}
    </>
  );
}

/** Walk the whole guide and collect every evidence object (used by the print appendix). */
export function collectEvidence(guide: Guide): { evidence: Evidence; fact: string }[] {
  const out: { evidence: Evidence; fact: string }[] = [];
  const add = (e: Evidence | null | undefined, fact: string) => e && out.push({ evidence: e, fact });
  guide.before_you_start?.forEach((f) => add(f.evidence, f.text));
  guide.limits?.forEach((l) => add(l.evidence, `${l.what}${l.value != null ? `: ${l.value} ${l.unit ?? ""}` : ""}`));
  guide.steps?.forEach((s) => add(s.evidence, `Step ${s.n}: ${s.title}`));
  guide.review?.evidence?.forEach((e) => add(e, "Review and approval"));
  guide.customer_gates?.forEach((f) => add(f.evidence, f.text));
  guide.gotchas?.forEach((f) => add(f.evidence, f.text));
  guide.blockers?.forEach((b) => add(b.evidence, b.symptom));
  guide.conflicts?.forEach((c) => c.evidence?.forEach((e) => add(e, c.field)));
  return out;
}
