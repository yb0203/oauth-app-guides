"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { NarrationLine } from "@/lib/chat-types";

export function NarrationLog({ lines, active }: { lines: NarrationLine[]; active: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const lastText = lines[lines.length - 1]?.text;

  // Scroll the log itself (not the page) to the newest line.
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [lines.length, lastText]);

  return (
    <div
      ref={ref}
      role="log"
      aria-live="polite"
      aria-label="Agent narration"
      className="h-52 overflow-y-auto pr-1"
    >
      {lines.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {active ? "The agent has not said anything yet." : "No narration was recorded for this run."}
        </p>
      ) : (
        <ul className="space-y-1.5">
          {lines.map((l, i) => {
            const latest = i === lines.length - 1;
            return (
              <li
                key={l.id}
                className={cn(
                  "animate-in fade-in flex gap-2.5 text-sm leading-snug duration-300 motion-reduce:animate-none",
                  latest && active ? "text-foreground" : "text-muted-foreground",
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "mt-2 size-1.5 shrink-0 rounded-full",
                    latest && active ? "bg-brand" : "bg-muted-foreground/40",
                  )}
                />
                <span className="min-w-0 break-words">{l.text}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
