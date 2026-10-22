"use client";

import { useState } from "react";
import { BadgeCheck, Check, FileText, FlaskConical, Link2, Printer, Sparkles } from "lucide-react";
import { cn } from "cn";
import { markdownUrl } from "@/lib/api";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Guide } from "@/types/guide";
import { Chip, copyText, fmtDate } from "./shared";
import { SituationPills } from "./SituationPills";
import { SituationProvider, useSituationOptional } from "./situation";
import { StartHere, VerdictCard } from "./VerdictSection";
import { StepsSection } from "./Steps";
import {
  BlockersSection,
  GatesSection,
  LimitsSection,
  OpenSection,
  PreparedSection,
  PrintEvidence,
  ReviewSection,
  SourcesSection,
  StartSection,
} from "./Sections";

export { SituationPills } from "./SituationPills";
export { VerdictCard, StartHere, TrustLine } from "./VerdictSection";

const iconBtn =
  "inline-flex size-8 cursor-pointer items-center justify-center rounded-md border bg-background text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none";

function HeaderActions({ guide }: { guide: Guide }) {
  const [copied, setCopied] = useState(false);
  const link = () => `${window.location.origin}/guides/${encodeURIComponent(guide.slug)}${window.location.search}`;
  return (
    <div className="order-2 ml-auto flex items-center gap-1.5 sm:order-3 print:hidden">
      <Tooltip>
        <TooltipTrigger
          aria-label={copied ? "Link copied" : "Copy link to this guide"}
          className={cn(iconBtn, copied && "border-success-border bg-success-soft text-success hover:bg-success-soft hover:text-success")}
          onClick={async () => {
            await copyText(link());
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? <Check className="size-4" /> : <Link2 className="size-4" />}
        </TooltipTrigger>
        <TooltipContent>{copied ? "Link copied" : "Copy link (keeps your situation)"}</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger
          aria-label="Open Markdown export"
          className={iconBtn}
          render={<a href={markdownUrl(guide.slug)} target="_blank" rel="noopener noreferrer" />}
        >
          <FileText className="size-4" />
        </TooltipTrigger>
        <TooltipContent>Markdown export</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger aria-label="Print this guide" className={iconBtn} onClick={() => window.print()}>
          <Printer className="size-4" />
        </TooltipTrigger>
        <TooltipContent>Print</TooltipContent>
      </Tooltip>
    </div>
  );
}

const COMPOSIO = {
  managed: { label: "Composio: managed app", title: "Composio provides a ready-made OAuth app; bringing your own is optional" },
  byo: { label: "Composio: bring your own", title: "You must register your own OAuth app" },
  not_in_catalog: { label: "Composio: not in catalog", title: "Composio has no toolkit for this app yet" },
} as const;

function Header({ guide, isPage, replay = false }: { guide: Guide; isPage: boolean; replay?: boolean }) {
  const curated = guide.guide_type === "curated";
  const composio = COMPOSIO[guide.composio?.status] ?? COMPOSIO.managed;
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      {isPage ? (
        <h1 className="order-1 text-2xl leading-tight font-semibold tracking-tight">{guide.app_name}</h1>
      ) : (
        <h2 className="order-1 text-lg font-semibold tracking-tight">{guide.app_name} OAuth app guide</h2>
      )}
      <div className="order-3 flex basis-full flex-wrap items-center gap-x-3 gap-y-1.5 sm:order-2 sm:basis-auto">
        {replay ? (
          <Chip className="border-warning-border bg-warning-soft text-warning" title="Recorded GitHub run shown in demo mode; not research for the app you typed">
            <FlaskConical className="size-3" aria-hidden /> Demo replay
          </Chip>
        ) : (
          <Chip className={curated ? "border-brand/30 bg-brand-soft text-brand" : "border-dashed border-muted-foreground/60 text-muted-foreground"}>
            {curated ? <BadgeCheck className="size-3" aria-hidden /> : <Sparkles className="size-3" aria-hidden />}
            {curated ? "Curated" : "Agent-generated"}
          </Chip>
        )}
        <span className="text-sm text-muted-foreground">Last verified {fmtDate(guide.last_verified)}</span>
        <Chip className="border-border text-muted-foreground" title={composio.title}>
          {composio.label}
        </Chip>
      </div>
      {isPage && <HeaderActions guide={guide} />}
    </div>
  );
}

function SectionNav({ guide }: { guide: Guide }) {
  const items = [
    guide.byo_advice && { id: "byo", label: "Bring your own?" },
    guide.before_you_start?.length > 0 && { id: "before", label: "Before you start" },
    guide.limits?.length > 0 && { id: "limits", label: "Limits" },
    guide.steps?.length > 0 && { id: "steps", label: "Steps" },
    guide.review && { id: "review", label: "Review" },
    (guide.customer_gates?.length > 0 || guide.gotchas?.length > 0) && {
      id: guide.customer_gates?.length > 0 ? "gates" : "gotchas",
      label: "Gates & gotchas",
    },
    guide.blockers?.length > 0 && { id: "blocked", label: "If blocked" },
    guide.prepared && { id: "prepared", label: "Prepared for you" },
    { id: "wall", label: "Console access" },
    guide.sources?.length > 0 && { id: "sources", label: "Sources" },
  ].filter(Boolean) as { id: string; label: string }[];
  return (
    <nav
      aria-label="On this page"
      className="sticky top-12 z-20 -mx-1 border-b bg-background/90 px-1 backdrop-blur supports-[backdrop-filter]:bg-background/75 print:hidden"
    >
      <ul className="flex gap-1 overflow-x-auto py-1.5 text-[13px] whitespace-nowrap [mask-image:linear-gradient(to_right,#000_calc(100%-1.5rem),transparent)] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {items.map((t) => (
          <li key={t.id}>
            <a href={`#${t.id}`} className="block rounded-md px-2.5 py-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none">
              {t.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

function GuideBody({ guide, variant, replay }: { guide: Guide; variant: "page" | "inline"; replay: boolean }) {
  const isPage = variant === "page";
  return (
    <article className="min-w-0 space-y-8" data-guide-slug={guide.slug}>
      <header className="space-y-4">
        <Header guide={guide} isPage={isPage} replay={replay} />
        <SituationPills />
        <VerdictCard guide={guide} />
        <StartHere guide={guide} />
      </header>
      {isPage && <SectionNav guide={guide} />}
      <div className="space-y-10">
        <StartSection guide={guide} />
        <LimitsSection guide={guide} />
        <StepsSection guide={guide} />
        <ReviewSection guide={guide} />
        <GatesSection guide={guide} />
        <BlockersSection guide={guide} />
        <PreparedSection guide={guide} />
        <OpenSection guide={guide} />
        <SourcesSection guide={guide} />
        <PrintEvidence guide={guide} />
      </div>
    </article>
  );
}

/** The whole guide. Works inside a SituationProvider (shared with the Ask panel) or on its own. No outer <main>. */
export function GuideView({
  guide,
  variant = "page",
  replay = false,
}: {
  guide: Guide;
  variant?: "page" | "inline";
  /** the guide is a recorded demo replay, not research for the app that was asked about */
  replay?: boolean;
}) {
  const shared = useSituationOptional();
  const body = <GuideBody guide={guide} variant={variant} replay={replay} />;
  if (shared) return body;
  return <SituationProvider key={guide.slug} guide={guide}>{body}</SituationProvider>;
}
