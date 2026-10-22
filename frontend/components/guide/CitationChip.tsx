"use client";

// Small inline numbered citation marker. Opens a card on hover, keyboard focus and click/tap (click pins it open
// so it also works on touch; outside click or Escape closes it). The marker number matches the Sources list.
import { useCallback, useEffect, useRef, useState } from "react";
import { Eye, EyeOff, ExternalLink } from "lucide-react";
import { cn } from "cn";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import type { EvidenceLabel, FoundIn } from "@/types/guide";

export interface CitationChipProps {
  marker: string; // "1", "2"…
  label: EvidenceLabel;
  quote: string | null;
  foundIn: FoundIn;
  sourceTitle?: string | null;
  sourceUrl?: string | null;
  note?: string | null; // what our tooling observed (TESTED)
  fact?: string | null; // the guide fact being cited
}

/** Colour + wording per evidence label. Shared by the chip, the trust line and the legend. */
export const LABEL_META: Record<EvidenceLabel, { name: string; chip: string; pill: string; dot: string; meaning: string }> = {
  TESTED: {
    name: "Tested",
    chip: "border-success bg-success text-background",
    pill: "border-success-border bg-success-soft text-success",
    dot: "bg-success",
    meaning: "Our tooling observed this directly.",
  },
  DOCS: {
    name: "Docs",
    chip: "border-brand/30 bg-brand-soft text-brand",
    pill: "border-brand/30 bg-brand-soft text-brand",
    dot: "bg-brand",
    meaning: "Stated in the provider's docs; the quote was checked against the live page.",
  },
  COMMUNITY: {
    name: "Community",
    chip: "border-warning-border bg-warning-soft text-warning",
    pill: "border-warning-border bg-warning-soft text-warning",
    dot: "bg-warning",
    meaning: "Reported by developers, not confirmed by official docs.",
  },
  UNCERTAIN: {
    name: "Uncertain",
    chip: "border-dashed border-muted-foreground/60 bg-transparent text-muted-foreground",
    pill: "border-dashed border-muted-foreground/60 bg-transparent text-muted-foreground",
    dot: "bg-muted-foreground/60",
    meaning: "We could not verify this. Treat it as a best guess.",
  },
};

export function CitationChip({ marker, label, quote, foundIn, sourceTitle, sourceUrl, note, fact }: CitationChipProps) {
  const meta = LABEL_META[label] ?? LABEL_META.UNCERTAIN;
  const hidden = foundIn === "hidden_section";
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const close = useCallback(() => {
    setPinned(false);
    setOpen(false);
  }, []);

  // While open: Escape closes. While pinned: a press outside the chip and the card closes.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    const onDown = (e: PointerEvent) => {
      if (!pinned) return;
      const t = e.target as Node | null;
      if (t && (triggerRef.current?.contains(t) || (t as Element).closest?.("[data-citation-card]"))) return;
      close();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [open, pinned, close]);

  return (
    <HoverCard
      open={open}
      onOpenChange={(next) => {
        if (!next && pinned) return; // hover-out / blur must not close a card the reader pinned with a click
        setOpen(next);
      }}
    >
      <HoverCardTrigger
        delay={120}
        closeDelay={180}
        render={<button type="button" ref={triggerRef} />}
        aria-label={`Citation ${marker}: ${meta.name} evidence${hidden ? ", hidden section" : ""}`}
        aria-expanded={open}
        onClick={() => {
          if (pinned) close();
          else {
            setPinned(true);
            setOpen(true);
          }
        }}
        className={cn(
          "relative -top-[0.4em] mx-[1px] inline-flex h-[1.05rem] min-w-[1.05rem] cursor-pointer items-center justify-center rounded-full border px-[3px] align-baseline text-[10px] leading-none font-semibold tabular-nums no-underline transition-[filter,box-shadow] hover:brightness-95 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none data-popup-open:ring-2 data-popup-open:ring-ring/50 print:cursor-auto",
          meta.chip,
        )}
      >
        {marker}
      </HoverCardTrigger>
      <HoverCardContent
        data-citation-card
        side="top"
        align="center"
        sideOffset={8}
        className="flex w-[22rem] max-w-[calc(100vw-1.5rem)] flex-col gap-2.5 p-3 text-xs leading-snug"
      >
        <div className="flex items-start gap-2">
          <span className={cn("shrink-0 rounded-full border px-1.5 py-0.5 text-[10px] leading-none font-semibold tracking-wide uppercase", meta.pill)}>
            {label}
          </span>
          <span className="text-muted-foreground">{meta.meaning}</span>
        </div>

        {fact && <p className="text-[13px] font-medium text-foreground">{fact}</p>}

        {quote ? (
          <blockquote className="border-l-2 border-brand/40 bg-muted/60 py-1.5 pr-2 pl-2.5 text-[12px] leading-snug text-foreground/90">
            &ldquo;{quote}&rdquo;
          </blockquote>
        ) : (
          label !== "TESTED" && <p className="text-muted-foreground">No supporting quote is available for this claim.</p>
        )}

        {quote && foundIn && (
          <p className={cn("flex items-start gap-1.5", hidden ? "text-warning" : "text-muted-foreground")}>
            {hidden ? <EyeOff className="mt-px size-3.5 shrink-0" /> : <Eye className="mt-px size-3.5 shrink-0" />}
            <span>
              {hidden
                ? "Found in a hidden section of the page (a collapsed accordion or tab), not in the visible page text."
                : "Found in visible page text."}
            </span>
          </p>
        )}

        {note && (
          <p>
            <span className="font-medium">{label === "TESTED" ? "What our tooling observed: " : "Note: "}</span>
            {note}
          </p>
        )}

        {sourceUrl ? (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-start gap-1.5 border-t pt-2 font-medium text-brand underline-offset-2 hover:underline"
          >
            <ExternalLink className="mt-px size-3.5 shrink-0" />
            <span className="min-w-0 break-words">
              <span className="tabular-nums">[{marker}]</span> {sourceTitle || sourceUrl}
            </span>
          </a>
        ) : (
          <p className="border-t pt-2 text-muted-foreground">
            {label === "TESTED" ? "Observed by our own tooling; there is no page to link." : "No source is linked to this claim."}
          </p>
        )}
      </HoverCardContent>
    </HoverCard>
  );
}
