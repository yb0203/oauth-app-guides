"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckIcon, CopyIcon } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function GuideReadyBanner({ permalink }: { permalink: string; appName?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${permalink}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard can be unavailable (insecure context); the link itself is still shown.
    }
  }

  return (
    <section
      aria-labelledby="guide-ready-title"
      className="animate-in fade-in flex flex-wrap items-center justify-between gap-3 rounded-xl border border-success-border bg-success-soft px-4 py-3 duration-300 motion-reduce:animate-none"
    >
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-success text-background">
          <CheckIcon className="size-3.5" strokeWidth={3} aria-hidden />
        </span>
        <div className="min-w-0">
          <h2 id="guide-ready-title" className="text-sm font-semibold text-success">
            Guide ready
          </h2>
          <p className="truncate text-xs text-muted-foreground">
            Published at{" "}
            <Link href={permalink} className="font-mono underline underline-offset-2">
              {permalink}
            </Link>
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 print:hidden">
        <Button variant="outline" size="sm" onClick={copy} className="bg-background">
          {copied ? <CheckIcon aria-hidden /> : <CopyIcon aria-hidden />}
          {copied ? "Copied" : "Copy link"}
        </Button>
        <Link href={permalink} className={cn(buttonVariants({ size: "sm" }))}>
          Open guide page
        </Link>
      </div>
    </section>
  );
}
