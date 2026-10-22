import type { UIMessage } from "ai";
import type { AskAction, AskAnswerMeta, AskCitation } from "@/types/ask";

/** The typed message for the ask stream (CONTRACT section 4b). Data part names: data-citations, data-action, data-answer-meta. */
export type AskMessage = UIMessage<
  never,
  {
    citations: AskCitation[];
    action: AskAction;
    "answer-meta": AskAnswerMeta;
  }
>;

export interface AskAnswer {
  text: string;
  citations: AskCitation[];
  actions: AskAction[];
  meta: AskAnswerMeta | null;
}

export function messageText(m: AskMessage): string {
  return m.parts
    .filter((p) => p.type === "text")
    .map((p) => p.text)
    .join("");
}

/** Fold an assistant message's parts into what the UI renders. */
export function deriveAnswer(m: AskMessage): AskAnswer {
  const out: AskAnswer = { text: "", citations: [], actions: [], meta: null };
  const seenActions = new Set<string>();
  for (const p of m.parts) {
    switch (p.type) {
      case "text":
        out.text += p.text;
        break;
      case "data-citations":
        if (Array.isArray(p.data)) out.citations = p.data;
        break;
      case "data-action": {
        const key = p.data ? `${p.data.question_id}:${p.data.option_id}` : "";
        if (p.data && !seenActions.has(key)) {
          seenActions.add(key);
          out.actions.push(p.data);
        }
        break;
      }
      case "data-answer-meta":
        if (p.data) out.meta = p.data;
        break;
    }
  }
  return out;
}

export type AnswerSegment =
  | { kind: "text"; text: string }
  | { kind: "cite"; marker: string; citation: AskCitation | null };

const MARKER = /\[(\d{1,2})\]/g;

/**
 * Split answer text into text and citation segments. While the citations part has not arrived yet
 * (`citations` is empty and `pending`), markers stay as unresolved cite segments; a trailing, still
 * incomplete marker such as "[" or "[1" is held back so it never flashes as raw text. Once citations
 * have arrived, markers that do not resolve are dropped.
 */
export function splitAnswer(text: string, citations: AskCitation[], pending: boolean): AnswerSegment[] {
  const byMarker = new Map(citations.map((c) => [String(c.marker), c]));
  const body = pending ? text.replace(/\[\d{0,2}$/, "") : text;
  const out: AnswerSegment[] = [];
  let last = 0;
  for (const m of body.matchAll(MARKER)) {
    const idx = m.index ?? 0;
    if (idx > last) out.push({ kind: "text", text: body.slice(last, idx) });
    const citation = byMarker.get(m[1]) ?? null;
    if (citation || pending) out.push({ kind: "cite", marker: m[1], citation });
    last = idx + m[0].length;
  }
  if (last < body.length) out.push({ kind: "text", text: body.slice(last) });
  return out;
}
