"use client";

import { useState } from "react";
import Link from "next/link";
import { BadgeCheckIcon, CheckIcon, FileTextIcon, FlaskConicalIcon, LinkIcon, SparklesIcon } from "lucide-react";
import { Chip, copyText } from "@/components/guide/shared";
import { buttonVariants } from "@/components/ui/button";
import { markdownUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Guide } from "@/types/guide";
import { verifiedClaims } from "./run-info";

/**
 * Sticks under the site header while the guide is read, so the way to the permanent page, a shareable link
 * and the Markdown export stay one click away. The badge is the honest label: this guide was written by
 * the agent a moment ago, and the number is how many of its claims were checked.
 */
export function GuideReadyBanner({ permalink, guide, replay = false }: { permalink: string; guide: Guide; replay?: boolean }) {
  const [copied, setCopied] = useState(false);
  const { n, total } = verifiedClaims(guide);

  async function copy() {
    await copyText(`${window.location.origin}${permalink}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <section
      aria-label="Guide actions"
      className={cn("animate-in fade-in slide-in-from-top-2 z-20 -mx-4 sm:sticky sm:top-12 border-y px-4 py-2.5 backdrop-blur duration-500 motion-reduce:animate-none sm:mx-0 sm:rounded-xl sm:border", replay ? "border-warning-border bg-warning-soft/95" : "border-success-border bg-success-soft/95")}
    >
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        {replay ? (
          <Chip
            className="border-warning-border bg-background/70 px-2.5 py-1 text-xs text-warning"
            title="A recording of the GitHub run, shown for any input in demo mode. It is not research for the app you typed."
          >
            <FlaskConicalIcon className="size-3" aria-hidden />
            Demo replay
            <span aria-hidden className="text-warning/50">
              ·
            </span>
            Recorded GitHub run
          </Chip>
        ) : (
          <Chip
            className="border-success-border bg-background/70 px-2.5 py-1 text-xs text-success"
            title="Written by the agent a moment ago. The count is how many of the guide's claims carry checked evidence."
          >
            <SparklesIcon className="size-3" aria-hidden />
            Agent-generated
            <span aria-hidden className="text-success/50">
              ·
            </span>
            <BadgeCheckIcon className="size-3" aria-hidden />
            Verified {n} of {total} claims
          </Chip>
        )}
        <div className="flex flex-wrap items-center gap-1.5 print:hidden">
          <Link href={permalink} className={cn(buttonVariants({ size: "sm" }))}>
            <LinkIcon aria-hidden /> {replay ? "Open the GitHub guide" : "Open permanent link"}
          </Link>
          <button
            type="button"
            onClick={copy}
            className={cn(buttonVariants({ variant: "outline", size: "sm" }), "cursor-pointer bg-background")}
          >
            {copied ? <CheckIcon aria-hidden /> : null}
            <span aria-live="polite">{copied ? "Link copied" : "Copy link"}</span>
          </button>
          <a
            href={markdownUrl(guide.slug)}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }), "bg-background")}
          >
            <FileTextIcon aria-hidden /> Export Markdown
            <span className="sr-only">(opens in a new tab)</span>
          </a>
        </div>
      </div>
    </section>
  );
}
