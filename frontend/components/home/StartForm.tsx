"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { CatalogEntry } from "@/types/guide";

const EXAMPLES = ["Xero", "Notion", "Zoom"];

export function StartForm({ catalog }: { catalog: CatalogEntry[] }) {
  const router = useRouter();
  const [value, setValue] = useState("");

  function go(raw: string) {
    const app = raw.trim();
    if (!app) return;
    const hit = catalog.find(
      (c) => c.has_guide && (c.name.toLowerCase() === app.toLowerCase() || c.slug === app.toLowerCase()),
    );
    router.push(hit ? `/guides/${hit.guide_slug ?? hit.slug}` : `/generate?app=${encodeURIComponent(app)}`);
  }

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          go(value);
        }}
        className="flex items-center gap-2 rounded-xl border bg-background p-1.5 shadow-xs focus-within:ring-2 focus-within:ring-ring/60"
      >
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Enter an app name or website"
          aria-label="App name or website"
          autoFocus
          className="h-10 min-w-0 flex-1 bg-transparent px-3 text-base outline-none placeholder:text-muted-foreground"
        />
        <Button type="submit" size="lg" disabled={!value.trim()} className="shrink-0">
          Generate<span className="hidden sm:inline"> guide</span> <ArrowRight className="size-4" aria-hidden />
        </Button>
      </form>
      <p className="mt-2 text-xs text-muted-foreground">
        Try an app we have not covered:{" "}
        {EXAMPLES.map((ex, i) => (
          <span key={ex}>
            <button type="button" className="cursor-pointer rounded underline underline-offset-2 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none" onClick={() => go(ex)}>
              {ex}
            </button>
            {i < EXAMPLES.length - 1 ? ", " : ""}
          </span>
        ))}
        . The agent reads the docs, probes the console, and cites every claim.
      </p>
    </div>
  );
}
