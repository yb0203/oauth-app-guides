"use client";

import { ArrowUpRightIcon } from "lucide-react";
import { Source } from "@/components/ai-elements/sources";
import type { RunSource } from "@/lib/chat-types";
import { Panel, PanelEmpty } from "./Panel";

function hostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function SourcesPanel({ sources, active }: { sources: RunSource[]; active: boolean }) {
  return (
    <Panel title="Sources" aside={sources.length > 0 ? sources.length : undefined} bodyClassName="p-0">
      {sources.length === 0 ? (
        <div className="p-4">
          <PanelEmpty>{active ? "Pages the agent reads will appear here as they are used." : "No sources were cited."}</PanelEmpty>
        </div>
      ) : (
        <ul className="max-h-80 divide-y overflow-y-auto">
          {sources.map((s) => (
            <li key={s.sourceId} className="animate-in fade-in duration-300 motion-reduce:animate-none">
              <Source
                href={s.url}
                title={s.title}
                className="group flex items-start justify-between gap-3 px-4 py-2.5 transition-colors hover:bg-muted/60 focus-visible:bg-muted/60 focus-visible:outline-none"
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-foreground">{s.title}</span>
                  <span className="block truncate font-mono text-xs text-muted-foreground">{hostname(s.url)}</span>
                </span>
                <ArrowUpRightIcon
                  className="mt-0.5 size-3.5 shrink-0 text-muted-foreground group-hover:text-foreground"
                  aria-hidden
                />
                <span className="sr-only">(opens in a new tab)</span>
              </Source>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
