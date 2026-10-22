"use client";

import { cn } from "@/lib/utils";
import type { NarrationLine } from "@/lib/chat-types";

/**
 * The agent's own commentary, newest first. The newest line always sits at the top of the box, so a
 * viewer never has to chase a scrolling log; older lines fade as they move down.
 */
export function NarrationLog({
  lines,
  active,
  className,
}: {
  lines: NarrationLine[];
  active: boolean;
  className?: string;
}) {
  const newestFirst = [...lines].reverse();
  return (
    <div
      role="log"
      aria-label="Agent narration, newest first"
      tabIndex={0}
      className={cn(
        "overflow-y-auto rounded-sm pr-1 focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
        className,
      )}
    >
      {lines.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {active ? "Waiting for the agent's first note." : "No narration was recorded for this run."}
        </p>
      ) : (
        <ul className="space-y-2">
          {newestFirst.map((l, i) => {
            const latest = i === 0 && active;
            return (
              <li
                key={l.id}
                className={cn(
                  "animate-in fade-in slide-in-from-top-1 flex gap-2.5 text-sm leading-snug duration-300 motion-reduce:animate-none",
                  latest ? "font-medium text-foreground" : i < 3 ? "text-foreground/80" : "text-muted-foreground",
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "mt-[7px] size-1.5 shrink-0 rounded-full",
                    latest ? "animate-pulse bg-info motion-reduce:animate-none" : "bg-muted-foreground/40",
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
