import type { Guide, SituationOption } from "@/types/guide";

/** Short, readable form of an option label for use inside a question. */
function shortLabel(label: string): string {
  const t = label.replace(/\s*\(.*?\)\s*$/, "").trim();
  return t.length > 56 ? `${t.slice(0, 53).trimEnd()}...` : t;
}

/**
 * Up to three deterministic starter questions derived from the guide itself:
 * a situation question, review timing, what the agent cannot do, then limits.
 */
export function starterQuestions(guide: Guide): string[] {
  const out: string[] = [];

  const { questions, variants } = guide.situations;
  // Prefer an option that a variant keys on by itself: that is the choice that changes the verdict most.
  let pick: SituationOption | null = null;
  for (const v of variants) {
    const keys = Object.keys(v.when);
    if (keys.length !== 1) continue;
    const q = questions.find((x) => x.id === keys[0]);
    const o = q?.options.find((x) => x.id === v.when[keys[0]]);
    if (o) {
      pick = o;
      break;
    }
  }
  if (!pick && questions[0]?.options[0]) pick = questions[0].options[0];
  if (pick) out.push(`What changes if I choose "${shortLabel(pick.label)}"?`);

  if (guide.review && guide.review.required !== "no") out.push("How long does review take?");
  if (guide.steps.some((s) => s.actor === "human")) out.push("What can't the agent do for me?");
  const limit = guide.limits[0];
  if (limit) out.push(`What are the limits on ${limit.what.toLowerCase()}?`);

  return out.slice(0, 3);
}
