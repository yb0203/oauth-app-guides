"use client";

import { Check, RotateCcw } from "lucide-react";
import { cn } from "cn";
import { Eyebrow } from "./shared";
import { useSituation } from "./situation";

/**
 * One row per situation question: the question as a label, the options as toggle pills.
 * Clicking the selected pill clears it. Answers live in the shared situation state (and the URL).
 */
export function SituationPills({ className }: { className?: string }) {
  const { guide, answers, setAnswer, reset } = useSituation();
  const questions = guide.situations?.questions ?? [];
  if (questions.length === 0) return null;
  const any = Object.keys(answers).length > 0;

  return (
    <div className={cn("space-y-2.5 print:hidden", className)} data-testid="situation-pills">
      <div className="flex min-h-5 items-center justify-between gap-3">
        <Eyebrow>Your situation</Eyebrow>
        <button
          type="button"
          onClick={reset}
          tabIndex={any ? 0 : -1}
          aria-hidden={!any}
          className={cn(
            "inline-flex cursor-pointer items-center gap-1 rounded text-xs text-muted-foreground underline-offset-2 transition-opacity hover:text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
            !any && "pointer-events-none opacity-0",
          )}
        >
          <RotateCcw className="size-3" aria-hidden /> Reset
        </button>
      </div>
      {questions.map((q) => (
        <div key={q.id} role="group" aria-labelledby={`q-${q.id}`} className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <span id={`q-${q.id}`} className="text-sm font-medium">
            {q.text}
          </span>
          <div className="flex flex-wrap gap-2">
            {q.options.map((o) => {
              const on = answers[q.id] === o.id;
              return (
                <button
                  key={o.id}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setAnswer(q.id, o.id)}
                  className={cn(
                    "inline-flex min-h-8 cursor-pointer items-center gap-2 rounded-full border py-1 pr-3.5 pl-2.5 text-left text-sm leading-snug transition-colors focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
                    on
                      ? "border-brand bg-brand-soft text-brand"
                      : "bg-background text-foreground hover:border-foreground/30 hover:bg-muted",
                  )}
                >
                  <span
                    aria-hidden
                    className={cn(
                      "flex size-3.5 shrink-0 items-center justify-center rounded-full border transition-colors",
                      on ? "border-brand bg-brand text-background" : "border-muted-foreground/50",
                    )}
                  >
                    {on && <Check className="size-2.5" strokeWidth={3} />}
                  </span>
                  {o.label}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
