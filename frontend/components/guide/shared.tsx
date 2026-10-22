"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "cn";

/** "6–10 min" for <1h, "2–4 h" otherwise. */
export function formatEffort(range: { min: number; max: number } | null | undefined): string {
  if (!range) return "Unknown";
  const { min, max } = range;
  if (max < 1) {
    const a = Math.max(1, Math.round(min * 60));
    const b = Math.max(1, Math.round(max * 60));
    return a === b ? `${a} min` : `${a}–${b} min`;
  }
  const a = Math.round(min * 10) / 10;
  const b = Math.round(max * 10) / 10;
  return a === b ? `${a} h` : `${a}–${b} h`;
}

/** Variants carry their effort only as prose ("Our effort estimate is 8 to 16 active hours"); read it when present. */
export function variantEffort(notes: string[] | null | undefined): { min: number; max: number } | null {
  for (const n of notes ?? []) {
    const m = /effort[^.\d]*(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*(?:active\s+)?(hours?|hrs?|h|minutes?|mins?)\b/i.exec(n);
    if (m) {
      const k = /^m/i.test(m[3]) ? 1 / 60 : 1;
      return { min: parseFloat(m[1]) * k, max: parseFloat(m[2]) * k };
    }
  }
  return null;
}

export function copyText(text: string): Promise<void> {
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
  }
  return fallbackCopy(text);
}
function fallbackCopy(text: string): Promise<void> {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand("copy");
  } catch {}
  document.body.removeChild(ta);
  return Promise.resolve();
}

export function CopyButton({
  text,
  label = "Copy",
  className,
  ariaLabel,
}: {
  text: string;
  label?: string;
  className?: string;
  ariaLabel?: string;
}) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      aria-label={ariaLabel ?? `Copy ${label}`}
      onClick={async () => {
        await copyText(text);
        setDone(true);
        setTimeout(() => setDone(false), 1500);
      }}
      className={cn(
        "inline-flex h-7 shrink-0 cursor-pointer items-center gap-1.5 rounded-md border bg-background px-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none print:hidden",
        done && "border-success-border bg-success-soft text-success hover:bg-success-soft hover:text-success",
        className,
      )}
    >
      {done ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      <span aria-live="polite" className="min-w-[2.6rem] text-left">
        {done ? "Copied" : label}
      </span>
    </button>
  );
}

/** Document section: h2 + optional one-line description. Spacing and type are set here once. */
export function Section({
  id,
  title,
  description,
  children,
  className,
}: {
  id: string;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={cn("scroll-mt-28 space-y-4", className)}>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {children}
    </section>
  );
}

export function Chip({ children, className, title }: { children: React.ReactNode; className?: string; title?: string }) {
  return (
    <span
      title={title}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] leading-none font-medium whitespace-nowrap",
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Small uppercase label used above values and in tiles. One style everywhere. */
export function Eyebrow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("text-[11px] font-medium tracking-wide text-muted-foreground uppercase", className)}>{children}</div>;
}

export function fmtDate(d: string | null | undefined): string {
  if (!d) return "unknown";
  const dt = new Date(d.length === 10 ? `${d}T00:00:00Z` : d);
  if (Number.isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}
