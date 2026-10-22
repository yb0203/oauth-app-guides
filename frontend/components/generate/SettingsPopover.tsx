"use client";

import { CheckIcon, SlidersHorizontalIcon } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { DEFAULT_PAGE_OPTIONS, formatContext, modelLabel, type GenConfig, type ModelsInfo } from "@/lib/models";
import { cn } from "@/lib/utils";

const PAGE_HINT: Record<number, string> = {
  3: "Quickest, but may miss review details. More pages are slower but more thorough.",
  5: "Balanced: registration, scopes and review. More pages are slower but more thorough.",
  8: "Most thorough, and the slowest. Fewer pages are faster.",
};

/** One-line summary used on the trigger and in the run header. */
export function configSummary(config: GenConfig, models: ModelsInfo | null): string {
  const parts: string[] = [];
  if (models) parts.push(modelLabel(models, config.model ?? models.defaultModel ?? undefined));
  parts.push(`${config.pages} pages`);
  parts.push(config.probe ? "console probe on" : "console probe off");
  return parts.join(" · ");
}

/**
 * Compact "Settings" disclosure: model (free models only), docs depth, console probe. Controlled; the parent
 * decides where the value lives (home form state, or the /generate URL).
 */
export function SettingsPopover({
  value,
  onChange,
  models,
  align = "start",
  className,
}: {
  value: GenConfig;
  onChange: (next: GenConfig) => void;
  models: ModelsInfo | null;
  align?: "start" | "center" | "end";
  className?: string;
}) {
  const pageOptions = models?.pageOptions ?? DEFAULT_PAGE_OPTIONS;
  const selectedModel = value.model ?? models?.defaultModel ?? undefined;

  return (
    <Popover>
      <PopoverTrigger
        className={cn(
          "inline-flex min-w-0 max-w-full cursor-pointer items-center gap-1.5 rounded-lg border bg-background px-2.5 py-1.5 text-xs text-muted-foreground transition-colors outline-none hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 data-popup-open:bg-muted data-popup-open:text-foreground",
          className,
        )}
      >
        <SlidersHorizontalIcon className="size-3.5 shrink-0" aria-hidden />
        <span className="font-medium text-foreground">Settings</span>
        <span className="min-w-0 truncate">{configSummary(value, models)}</span>
      </PopoverTrigger>
      <PopoverContent
        align={align}
        sideOffset={6}
        // stay below the trigger and scroll inside the panel instead of flipping to the side of it
        collisionAvoidance={{ side: "none", align: "shift" }}
        className="z-50 max-h-[min(var(--available-height),36rem)] w-[min(24rem,calc(100vw-2rem))] gap-3.5 overflow-y-auto border border-border bg-popover p-3.5 opacity-100 shadow-lg data-open:animate-none data-closed:animate-none"
      >
        {models && (
          <fieldset className="min-w-0">
            <legend className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">Model</legend>
            <div role="radiogroup" aria-label="Model" className="space-y-1">
              {models.models.map((m) => {
                const active = m.id === selectedModel;
                const ctx = formatContext(m.contextLength);
                return (
                  <button
                    key={m.id}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    disabled={!m.available}
                    onClick={() => onChange({ ...value, model: m.id === models.defaultModel ? undefined : m.id })}
                    className={cn(
                      "flex w-full items-start gap-2.5 rounded-lg border px-2.5 py-2 text-left outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
                      !m.available ? "cursor-not-allowed opacity-55" : "cursor-pointer",
                      active ? "border-brand/50 bg-brand-soft" : m.available && "hover:bg-muted",
                    )}
                  >
                    <span
                      aria-hidden
                      className={cn(
                        "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full border",
                        active ? "border-brand bg-brand text-background" : "border-border",
                      )}
                    >
                      {active && <CheckIcon className="size-3" strokeWidth={3} />}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
                        <span className="text-sm font-medium text-foreground">{m.label}</span>
                        {m.free && (
                          <span className="rounded border border-success-border bg-success-soft px-1 text-[10px] leading-4 font-medium text-success">Free</span>
                        )}
                        {m.id === models.defaultModel && (
                          <span className="rounded border border-brand/30 bg-background px-1 text-[10px] leading-4 font-medium text-brand">Recommended</span>
                        )}
                      </span>
                      {m.available ? (
                        (ctx || m.notes) && (
                          <span className="mt-0.5 block text-xs text-muted-foreground">{[m.notes, ctx].filter(Boolean).join(" · ")}</span>
                        )
                      ) : (
                        <span className="mt-0.5 block text-xs text-muted-foreground">Unavailable right now{ctx ? ` · ${ctx}` : ""}</span>
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          </fieldset>
        )}

        <fieldset className="min-w-0">
          <legend className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">Docs depth</legend>
          <div role="radiogroup" aria-label="Docs depth" className="grid grid-flow-col auto-cols-fr gap-1 rounded-lg bg-muted p-0.5">
            {pageOptions.map((n) => (
              <button
                key={n}
                type="button"
                role="radio"
                aria-checked={value.pages === n}
                onClick={() => onChange({ ...value, pages: n })}
                className={cn(
                  "cursor-pointer rounded-md px-2 py-1 text-sm tabular-nums outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
                  value.pages === n ? "bg-background font-medium text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {n} pages
              </button>
            ))}
          </div>
          <p className="mt-1.5 text-xs text-muted-foreground">
            {PAGE_HINT[value.pages] ?? "More pages are slower but more thorough."}
          </p>
        </fieldset>

        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <label htmlFor="probe-toggle" className="text-sm font-medium text-foreground">
              Probe the developer console
            </label>
            <p className="mt-0.5 text-xs text-muted-foreground">Opens the real sign-in page to see what a new developer hits. Adds a few seconds.</p>
          </div>
          <Switch id="probe-toggle" checked={value.probe} onCheckedChange={(probe) => onChange({ ...value, probe })} aria-label="Probe the developer console" />
        </div>

        <p className="border-t pt-3 text-xs text-muted-foreground">Demo uses free models via OpenRouter only.</p>
      </PopoverContent>
    </Popover>
  );
}
