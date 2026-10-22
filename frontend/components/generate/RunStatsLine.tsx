import { cn } from "@/lib/utils";
import type { RunStats } from "@/types/guide";
import { formatDuration } from "./run-info";

const compact = (n: number) => (n >= 10000 ? `${(n / 1000).toFixed(n >= 100000 ? 0 : 1)}k` : n.toLocaleString("en-US"));

/** Honest cost line: free models report $0, anything else shows the amount the backend measured. */
function costText(stats: RunStats): string {
  if (stats.cost_usd === undefined || stats.cost_usd === null) return "cost not reported";
  return stats.cost_usd === 0 ? "$0.00 (free models)" : `$${stats.cost_usd.toFixed(stats.cost_usd < 0.01 ? 4 : 2)}`;
}

/** One quiet line of run statistics from data-run-stats. Every part is optional; missing ones are skipped. */
export function RunStatsLine({ stats, className }: { stats: RunStats; className?: string }) {
  const parts: string[] = [];
  if (typeof stats.total_seconds === "number") parts.push(formatDuration(stats.total_seconds * 1000));
  const llm = stats.llm;
  if (llm && typeof llm.calls === "number") {
    parts.push(`${llm.calls} LLM ${llm.calls === 1 ? "call" : "calls"}${llm.failed_calls ? ` (${llm.failed_calls} failed)` : ""}`);
    if (typeof llm.input_tokens === "number" || typeof llm.output_tokens === "number") {
      parts.push(
        `${typeof llm.input_tokens === "number" ? compact(llm.input_tokens) : "n/a"} tokens in / ${typeof llm.output_tokens === "number" ? compact(llm.output_tokens) : "n/a"} out`,
      );
    }
  }
  if (typeof stats.pages_fetched === "number") parts.push(`${stats.pages_fetched} pages read`);
  parts.push(costText(stats));

  return (
    <p
      aria-label="Run stats"
      className={cn("flex flex-wrap items-baseline gap-x-2 gap-y-1 rounded-lg border bg-card px-3 py-2 text-xs text-muted-foreground print:hidden", className)}
    >
      <span className="font-medium tracking-wide text-foreground uppercase">Run stats</span>
      {parts.map((p, i) => (
        <span key={i} className="font-mono tabular-nums">
          <span aria-hidden className="mr-2 text-border">
            ·
          </span>
          {p}
        </span>
      ))}
    </p>
  );
}
