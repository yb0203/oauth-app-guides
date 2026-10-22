"use client";

import { useState } from "react";
import { ArrowUpRightIcon, GlobeIcon } from "lucide-react";
import { Source } from "@/components/ai-elements/sources";
import { Chip } from "@/components/guide/shared";
import type { RunSource } from "@/lib/chat-types";
import { cn } from "@/lib/utils";
import { Panel, PanelEmpty } from "./Panel";
import { classifySource, hostOf, SOURCE_KIND_LABEL, type SourceKind } from "./run-info";

const KIND_STYLE: Record<SourceKind, string> = {
  official: "border-success-border bg-success-soft text-success",
  composio: "border-info-border bg-info-soft text-info",
  community: "border-warning-border bg-warning-soft text-warning",
  observation: "border-border bg-muted text-muted-foreground",
  other: "border-border bg-muted text-muted-foreground",
};

function Favicon({ host }: { host: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <GlobeIcon className="size-4 shrink-0 text-muted-foreground" aria-hidden />;
  return (
    // eslint-disable-next-line @next/next/no-img-element -- tiny third-party icon, nothing to optimise
    <img
      src={`https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=64`}
      alt=""
      width={16}
      height={16}
      loading="lazy"
      onError={() => setFailed(true)}
      className="size-4 shrink-0 rounded-sm"
    />
  );
}

interface Group {
  host: string;
  kind: SourceKind;
  items: RunSource[];
}

function groupByHost(sources: RunSource[]): Group[] {
  const groups = new Map<string, Group>();
  for (const s of sources) {
    const host = hostOf(s.url);
    const g = groups.get(host);
    if (g) g.items.push(s);
    else groups.set(host, { host, kind: classifySource(s.url, s.title), items: [s] });
  }
  return [...groups.values()];
}

export function SourcesPanel({ sources, active }: { sources: RunSource[]; active: boolean }) {
  const groups = groupByHost(sources);
  const official = groups.filter((g) => g.kind === "official" || g.kind === "composio").length;
  const community = groups.filter((g) => g.kind === "community").length;
  const aside =
    sources.length > 0
      ? `${sources.length} ${sources.length === 1 ? "page" : "pages"} · ${groups.length} ${groups.length === 1 ? "site" : "sites"}`
      : undefined;

  return (
    <Panel title="Sources read" aside={aside}>
      {sources.length === 0 ? (
        <PanelEmpty>{active ? "Pages the agent reads will be listed here, grouped by site." : "No sources were cited."}</PanelEmpty>
      ) : (
        <>
          <p className="mb-3 text-xs text-muted-foreground">
            {official} official or Composio {official === 1 ? "site" : "sites"}
            {community > 0 && `, ${community} community`}. Official docs carry the guide; community reports are labelled as such.
          </p>
          <ul className="-mx-1 max-h-72 space-y-3 overflow-y-auto px-1">
            {groups.map((g) => (
              <li key={g.host} className="animate-in fade-in duration-300 motion-reduce:animate-none">
                <div className="flex items-center gap-2">
                  <Favicon host={g.host} />
                  <span className="min-w-0 truncate font-mono text-xs text-foreground">{g.host}</span>
                  <Chip className={cn("ml-auto", KIND_STYLE[g.kind])}>{SOURCE_KIND_LABEL[g.kind]}</Chip>
                </div>
                <ul className="mt-1 ml-6 border-l pl-3">
                  {g.items.map((s) => (
                    <li key={s.sourceId}>
                      <Source
                        href={s.url}
                        title={s.title}
                        className="group flex items-start justify-between gap-2 rounded-sm py-1 text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
                      >
                        <span className="min-w-0 truncate">{s.title}</span>
                        <ArrowUpRightIcon className="mt-0.5 size-3.5 shrink-0 opacity-60 group-hover:opacity-100" aria-hidden />
                        <span className="sr-only">(opens in a new tab)</span>
                      </Source>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </>
      )}
    </Panel>
  );
}
