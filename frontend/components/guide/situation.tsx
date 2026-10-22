"use client";

// Shared "your situation" state for one guide. The answers drive the verdict header and are mirrored in the
// URL (?question_id=option_id) so a shared link keeps the developer's decision. The Ask panel reads/sets them too.
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { Guide, SituationVariant, Tier, Verdict } from "@/types/guide";

export type Answers = Record<string, string>;

export interface ResolvedSituation {
  answers: Answers;
  /** first variant whose `when` entries are all selected; null = base verdict */
  variant: SituationVariant | null;
  tier: Tier;
  summary: string;
  calendarLabel: string;
  notes: string[];
  /** labels of the selected options, in question order */
  selectedLabels: string[];
  /** true when a variant (not the base verdict) is showing */
  changed: boolean;
  verdict: Verdict;
}

export function sanitizeAnswers(guide: Guide, raw: Answers | undefined): Answers {
  const out: Answers = {};
  for (const q of guide.situations.questions) {
    const v = raw?.[q.id];
    if (v && q.options.some((o) => o.id === v)) out[q.id] = v;
  }
  return out;
}

export function resolveSituation(guide: Guide, answers: Answers): ResolvedSituation {
  const variant =
    guide.situations.variants.find((v) => {
      const keys = Object.keys(v.when);
      return keys.length > 0 && keys.every((k) => answers[k] === v.when[k]);
    }) ?? null;
  const selectedLabels = guide.situations.questions
    .map((q) => q.options.find((o) => o.id === answers[q.id])?.label)
    .filter((l): l is string => !!l);
  return {
    answers,
    variant,
    tier: variant?.tier ?? guide.verdict.tier,
    summary: variant?.summary ?? guide.verdict.summary,
    calendarLabel: variant?.calendar_label ?? guide.verdict.calendar.label,
    notes: variant?.notes ?? [],
    selectedLabels,
    changed: !!variant,
    verdict: guide.verdict,
  };
}

interface Ctx extends ResolvedSituation {
  guide: Guide;
  setAnswer: (questionId: string, optionId: string | null) => void;
  reset: () => void;
}

const SituationContext = createContext<Ctx | null>(null);

/** Returns null when rendered outside a provider (e.g. GuideView standalone wraps itself in one). */
export const useSituationOptional = () => useContext(SituationContext);

export function useSituation(): Ctx {
  const c = useContext(SituationContext);
  if (!c) throw new Error("useSituation must be used inside <SituationProvider>");
  return c;
}

export function SituationProvider({
  guide,
  initialAnswers,
  syncUrl = false,
  children,
}: {
  guide: Guide;
  initialAnswers?: Answers;
  /** mirror answers into the URL query with history.replaceState (guide page only; off for the inline run view) */
  syncUrl?: boolean;
  children: React.ReactNode;
}) {
  const [answers, setAnswers] = useState<Answers>(() => sanitizeAnswers(guide, initialAnswers));

  const commit = useCallback(
    (next: Answers) => {
      setAnswers(next);
      if (syncUrl && typeof window !== "undefined") {
        const url = new URL(window.location.href);
        for (const q of guide.situations.questions) url.searchParams.delete(q.id);
        for (const [k, v] of Object.entries(next)) url.searchParams.set(k, v);
        // Passive mirror only: pass the existing history state through (it carries Next's __NA marker), so the
        // App Router does not treat this as a navigation, re-fetch the page, or re-key the segment. The React
        // state in this provider is the single source of truth; the URL is just for sharing and reloads.
        window.history.replaceState(window.history.state, "", url);
      }
    },
    [guide, syncUrl],
  );

  const setAnswer = useCallback(
    (qid: string, oid: string | null) => {
      const next = { ...answers };
      if (oid === null || next[qid] === oid) delete next[qid]; // clicking the selected pill again clears it
      else next[qid] = oid;
      commit(sanitizeAnswers(guide, next));
    },
    [answers, commit, guide],
  );
  const reset = useCallback(() => commit({}), [commit]);

  const value = useMemo<Ctx>(
    () => ({ ...resolveSituation(guide, answers), guide, setAnswer, reset }),
    [guide, answers, setAnswer, reset],
  );
  return <SituationContext.Provider value={value}>{children}</SituationContext.Provider>;
}
