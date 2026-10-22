"use client";

import { Fragment, type ReactNode } from "react";
import Link from "next/link";
import { ArrowUpRightIcon, CheckIcon, InfoIcon, PlusIcon } from "lucide-react";
import { CitationChip } from "@/components/guide/CitationChip";
import { useSituation } from "@/components/guide/situation";
import { deriveAnswer, splitAnswer, type AskMessage } from "@/lib/ask-types";
import { cn } from "@/lib/utils";
import type { AskAction } from "@/types/ask";

/** `code` and **bold** only; anything else is plain text. */
function Inline({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g);
  return (
    <>
      {parts.map((p, i) => {
        if (p.startsWith("**") && p.endsWith("**") && p.length > 4)
          return (
            <strong key={i} className="font-medium text-foreground">
              {p.slice(2, -2)}
            </strong>
          );
        if (p.startsWith("`") && p.endsWith("`") && p.length > 2)
          return (
            <code key={i} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
              {p.slice(1, -1)}
            </code>
          );
        return <Fragment key={i}>{p}</Fragment>;
      })}
    </>
  );
}

/** Marker whose citation has not arrived yet: same footprint as the final chip, so nothing jumps. */
function PendingMarker({ marker }: { marker: string }) {
  return (
    <sup className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded bg-muted px-1 align-baseline text-[10px] font-medium text-muted-foreground tabular-nums">
      {marker}
    </sup>
  );
}

function ActionButton({ action }: { action: AskAction }) {
  const { answers, setAnswer } = useSituation();
  const applied = answers[action.question_id] === action.option_id;
  const plain = action.label.replace(/^Apply:\s*/i, "");
  return (
    <button
      type="button"
      disabled={applied}
      onClick={() => setAnswer(action.question_id, action.option_id)}
      className={cn(
        "group flex w-full items-start gap-2.5 rounded-lg border px-3 py-2 text-left text-sm transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
        applied
          ? "cursor-default border-success-border bg-success-soft text-success"
          : "cursor-pointer border-border bg-background hover:border-brand/40 hover:bg-brand-soft",
      )}
    >
      <span
        className={cn(
          "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full",
          applied ? "bg-success text-background" : "bg-brand-soft text-brand group-hover:bg-background",
        )}
      >
        {applied ? <CheckIcon className="size-3" strokeWidth={3} /> : <PlusIcon className="size-3" strokeWidth={3} />}
      </span>
      <span className="min-w-0">
        <span className={cn("block font-medium", !applied && "text-foreground")}>
          {applied ? "Applied" : "Apply to your situation"}
        </span>
        <span className={cn("block text-xs", applied ? "text-success/80" : "text-muted-foreground")}>
          {plain}
          {applied ? ". The verdict updated." : ""}
        </span>
      </span>
    </button>
  );
}

export function AnswerBody({
  message,
  streaming,
  appName,
}: {
  message: AskMessage;
  streaming: boolean;
  appName: string;
}) {
  const a = deriveAnswer(message);
  const pending = streaming && a.citations.length === 0;
  const segments = splitAnswer(a.text, a.citations, pending);

  // Group segments into paragraphs on blank lines.
  const paragraphs: ReactNode[][] = [[]];
  segments.forEach((s, i) => {
    if (s.kind === "cite") {
      const c = s.citation;
      paragraphs[paragraphs.length - 1].push(
        c ? (
          <CitationChip
            key={`c${i}`}
            marker={s.marker}
            label={c.label}
            quote={c.quote}
            foundIn={c.found_in}
            sourceTitle={c.title}
            sourceUrl={c.url}
            fact={c.fact}
          />
        ) : (
          <PendingMarker key={`p${i}`} marker={s.marker} />
        ),
      );
      return;
    }
    s.text.split(/\n{2,}/).forEach((chunk, j) => {
      if (j > 0) paragraphs.push([]);
      if (chunk) paragraphs[paragraphs.length - 1].push(<Inline key={`t${i}-${j}`} text={chunk} />);
    });
  });

  const notCovered = a.meta?.covered === false;
  const empty = !a.text.trim();

  return (
    <div className="space-y-3">
      {!empty && (
        <div className="space-y-2.5 text-sm leading-relaxed text-foreground/90">
          {paragraphs
            .filter((p) => p.length > 0)
            .map((p, i) => (
              <p key={i} className="whitespace-pre-line">
                {p}
              </p>
            ))}
        </div>
      )}
      {a.actions.length > 0 && (
        <div className="space-y-1.5">
          {a.actions.map((act) => (
            <ActionButton key={`${act.question_id}:${act.option_id}`} action={act} />
          ))}
        </div>
      )}
      {notCovered && (
        <div className="flex items-start gap-2 rounded-lg border bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
          <InfoIcon className="mt-0.5 size-3.5 shrink-0" />
          <div className="min-w-0">
            <p className="font-medium text-foreground/80">Not covered by this guide</p>
            <p className="mt-0.5">
              It has no evidence on this.{" "}
              <Link
                href={`/generate?app=${encodeURIComponent(appName)}`}
                className="inline-flex items-center gap-0.5 font-medium text-brand underline-offset-2 hover:underline"
              >
                Regenerate guide
                <ArrowUpRightIcon className="size-3" />
              </Link>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
