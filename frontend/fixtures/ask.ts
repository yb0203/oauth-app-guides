// Dev-only mock logic for POST /api/guides/{slug}/ask (CONTRACT section 4b). Deterministic keyword retrieval over the
// guide JSON, no LLM. Used by app/api/dev-ask/[slug]/route.ts when NEXT_PUBLIC_USE_MOCK=1.
import type { AskAction, AskCitation } from "@/types/ask";
import type { Evidence, Guide } from "@/types/guide";

export interface AskRequestBody {
  question: string;
  situation: Record<string, string>;
  history: { role: "user" | "assistant"; text: string }[];
}

export type AskEvent = { delay: number; event: Record<string, unknown> | "[DONE]" };

interface Fact {
  text: string;
  evidence: Evidence;
  tokens: Set<string>;
  human?: boolean;
  step?: boolean;
}

const STOP = new Set(
  "a an and are as at be but by can could did do does for from get got had has have how i if in into is it its me my of on or our so than that the their them then there these they this to us was we were what when where which who why will with would you your should need needs want just about also any all not no yes there".split(
    " ",
  ),
);

// Question words that stand in for words the guide uses.
const SYNONYMS: Record<string, string[]> = {
  avoid: ["internal", "exempt"],
  skip: ["internal", "exempt"],
  bypass: ["internal", "exempt"],
  without: ["internal", "exempt"],
  long: ["wait", "days", "weeks"],
  time: ["wait", "days", "weeks"],
  fast: ["wait", "days"],
  slow: ["wait", "weeks"],
  price: ["cost", "paid", "fee"],
  pay: ["cost", "paid", "fee"],
  cost: ["paid", "fee"],
  fee: ["cost", "paid"],
  expensive: ["cost", "paid"],
  customer: ["customers", "outside"],
  user: ["users"],
  approval: ["review", "verification"],
  approve: ["review", "verification"],
  verify: ["verification"],
};

function stem(w: string): string {
  if (w.length > 5 && w.endsWith("ing")) return w.slice(0, -3);
  if (w.length > 4 && w.endsWith("ed")) return w.slice(0, -2);
  if (w.length > 3 && w.endsWith("s") && !w.endsWith("ss")) return w.slice(0, -1);
  return w;
}

function tokenize(text: string, expand = false): Set<string> {
  const out = new Set<string>();
  for (const raw of text.toLowerCase().match(/[a-z][a-z0-9.]+|[a-z]/g) ?? []) {
    const w = raw.replace(/\.+$/, "");
    if (w.length < 3 || STOP.has(w)) continue;
    out.add(stem(w));
    if (expand) for (const s of SYNONYMS[w] ?? []) out.add(stem(s));
  }
  return out;
}

/** The leading sentence(s) of `text`, within `max` characters, without a trailing full stop. */
function firstSentences(text: string, max = 230, prefer?: Set<string>): string {
  const clean = text.replace(/\s+/g, " ").trim();
  let sentences = clean.split(/(?<=[.!?])\s+(?=[A-Z0-9"'(])/);
  if (prefer && sentences.length > 1) {
    // lead with the sentence that overlaps the question most
    const score = (x: string) => [...tokenize(x)].filter((t) => prefer.has(t)).length;
    const best = sentences.reduce((bi, x, i) => (score(x) > score(sentences[bi]) ? i : bi), 0);
    sentences = [sentences[best]];
  }
  let out = "";
  for (const s of sentences) {
    if (out && (out + " " + s).length > max) break;
    out += (out ? " " : "") + s;
    if (out.length >= max * 0.5) break;
  }
  if (out.length > max) {
    const cut = out.slice(0, max);
    const clause = Math.max(cut.lastIndexOf("; "), cut.lastIndexOf(", "), cut.lastIndexOf(" ("));
    out = clause > max * 0.5 ? cut.slice(0, clause) : cut.replace(/\s+\S*$/, "") + "...";
  }
  return out.replace(/[.;:,]+$/, "").replace(/\.\.\.$/, "...");
}

function collectFacts(g: Guide): Fact[] {
  const facts: Fact[] = [];
  const add = (text: string | null | undefined, evidence: Evidence | undefined, human = false, step = false) => {
    if (!text || !evidence) return;
    facts.push({ text, evidence, tokens: tokenize(text), human, step });
  };
  for (const f of g.before_you_start ?? []) add(f.text, f.evidence);
  for (const f of g.customer_gates ?? []) add(f.text, f.evidence);
  for (const f of g.gotchas ?? []) add(f.text, f.evidence);
  for (const l of g.limits ?? []) {
    add(`${l.what}: ${l.value ?? "no fixed number"} ${l.unit} (${l.scope})`.replace(/\s+/g, " "), l.evidence);
  }
  for (const b of g.blockers ?? []) add(`${b.symptom} ${b.cause} ${b.fix}`, b.evidence);
  const r = g.review;
  if (r) {
    const ev = r.evidence?.[0];
    add(r.trigger, ev);
    add(r.wait_official, r.evidence?.find((e) => e.quote?.match(/week|day/i)) ?? ev);
    add(r.wait_community, r.evidence?.[r.evidence.length - 1] ?? ev);
    add(r.cost, ev);
    add(r.reviewer, ev);
  }
  for (const s of g.steps ?? []) add(`${s.title}. ${s.detail}`, s.evidence, s.actor === "human", true);
  return facts;
}

export function buildAnswer(guide: Guide, body: AskRequestBody) {
  const question = (body.question ?? "").trim();
  const qTokens = tokenize(question, true);
  const facts = collectFacts(guide);

  // idf-weighted overlap
  const df = new Map<string, number>();
  for (const f of facts) for (const t of f.tokens) df.set(t, (df.get(t) ?? 0) + 1);
  const idf = (t: string) => Math.log(1 + facts.length / (df.get(t) ?? facts.length));
  const scored = facts
    .map((f) => {
      let score = 0;
      for (const t of qTokens) if (f.tokens.has(t)) score += idf(t);
      return { f, score: f.step ? score * 0.7 : score };
    })
    .filter((x) => x.score >= 2.5)
    .sort((a, b) => b.score - a.score);
  const top = scored[0]?.score ?? 0;
  const relevant = scored.filter((x) => x.score >= top * 0.6);

  // which situation option does the question point at?
  const appTokens = tokenize(`${guide.app_name} ${guide.slug}`);
  const actions: AskAction[] = [];
  let variantSentence = "";
  for (const q of guide.situations.questions) {
    let best: { id: string; label: string; score: number } | null = null;
    for (const o of q.options) {
      const idTokens = tokenize(o.id.replace(/[-_]/g, " "));
      const labelTokens = tokenize(o.label);
      let score = 0;
      for (const t of qTokens) {
        if (appTokens.has(t)) continue;
        if (idTokens.has(t)) score += 2;
        else if (labelTokens.has(t)) score += 1;
      }
      if (score >= 2 && (!best || score > best.score)) best = { id: o.id, label: o.label, score };
    }
    if (best && body.situation?.[q.id] !== best.id) {
      actions.push({ kind: "set_situation", question_id: q.id, option_id: best.id, label: `Apply: ${best.label}` });
    }
  }
  if (actions.length) {
    const first = actions[0];
    const v = guide.situations.variants.find((x) => {
      const keys = Object.keys(x.when);
      return keys.length === 1 && x.when[first.question_id] === first.option_id;
    });
    if (v) variantSentence = firstSentences(v.summary, 260);
  }

  // "What can't the agent do for me?"
  const humanSteps = guide.steps.filter((s) => s.actor === "human");
  const asksHuman = /\b(agent|human|myself|by hand|manual|can'?t|cannot)\b/i.test(question) && /\bagent|human|myself|manual\b/i.test(question);

  const citations: AskCitation[] = [];
  const markerFor = (ev: Evidence, fact: string): string => {
    const existing = citations.find((c) => c.fact === fact);
    if (existing) return existing.marker;
    const src = guide.sources.find((s) => s.id === ev.source_id);
    const marker = String(citations.length + 1);
    citations.push({
      marker,
      label: ev.label,
      source_id: ev.source_id,
      url: src?.url ?? null,
      title: src?.title ?? null,
      quote: ev.quote,
      found_in: ev.found_in,
      fact,
    });
    return marker;
  };

  const sentences: string[] = [];
  if (asksHuman && humanSteps.length) {
    const reasons = Array.from(new Set(humanSteps.map((s) => s.human_reason).filter(Boolean))).map((r) =>
      String(r).replace(/_/g, " "),
    );
    sentences.push(
      `The agent can't do ${humanSteps.length} of the ${guide.steps.length} steps for you. They need a person for ${reasons.slice(0, 4).join(", ")}.`,
    );
    for (const s of humanSteps.slice(0, 2)) {
      const why = s.human_reason ? ` (${s.human_reason.replace(/_/g, " ")})` : "";
      sentences.push(`Step ${s.n}, ${s.title.charAt(0).toLowerCase()}${s.title.slice(1).replace(/\.$/, "")}${why}. [${markerFor(s.evidence, `${s.title}. ${s.detail}`)}]`);
    }
  } else {
    if (variantSentence) sentences.push(`${variantSentence}.`);
    const seen = new Set<string>();
    for (const { f } of relevant) {
      if (sentences.length >= 3 + (variantSentence ? 1 : 0)) break;
      const k = f.text.slice(0, 40);
      if (seen.has(k)) continue;
      seen.add(k);
      if (variantSentence && variantSentence.toLowerCase().includes(f.text.slice(0, 30).toLowerCase())) continue;
      sentences.push(`${firstSentences(f.text, 230, qTokens)}. [${markerFor(f.evidence, f.text)}]`);
      if (sentences.length - (variantSentence ? 1 : 0) >= 3) break;
    }
  }

  const covered = sentences.length > 0;
  const text = covered
    ? sentences.join(" ")
    : `This guide doesn't cover that, so I can't answer it from its evidence. It covers setting up and getting approval for the ${guide.app_name} OAuth app: scopes, limits, review and the steps to follow.`;

  return { text, citations: covered ? citations : [], actions: covered ? actions : [], covered };
}

export function buildAskEvents(guide: Guide, body: AskRequestBody): AskEvent[] {
  const { text, citations, actions, covered } = buildAnswer(guide, body);
  const id = `ask-${Date.now().toString(36)}`;
  const ev: AskEvent[] = [{ delay: 350, event: { type: "start", messageId: id } }];
  ev.push({ delay: 250, event: { type: "text-start", id: "t1" } });
  // Small chunks on purpose: markers like "[12]" get split across deltas.
  for (let i = 0; i < text.length; i += 7) {
    ev.push({ delay: 28, event: { type: "text-delta", id: "t1", delta: text.slice(i, i + 7) } });
  }
  ev.push({ delay: 20, event: { type: "text-end", id: "t1" } });
  if (citations.length) ev.push({ delay: 120, event: { type: "data-citations", id: "citations", data: citations } });
  actions.forEach((a, i) => ev.push({ delay: 80, event: { type: "data-action", id: `action-${i + 1}`, data: a } }));
  ev.push({
    delay: 60,
    event: { type: "data-answer-meta", id: "meta", data: { covered, suggest: covered ? null : "regenerate" } },
  });
  ev.push({ delay: 20, event: { type: "finish" } });
  ev.push({ delay: 10, event: "[DONE]" });
  return ev;
}
