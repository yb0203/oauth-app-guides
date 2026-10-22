import { cn } from "@/lib/utils";
import { Eyebrow } from "@/components/guide/shared";

/**
 * One block of the run page: an eyebrow heading over a card. Every panel on /generate uses this so
 * radius, padding and heading style match the guide below it. `empty` panels keep a minimum height so
 * the page does not jump when the first real data arrives.
 */
export function Panel({
  title,
  aside,
  children,
  className,
  bodyClassName,
}: {
  title: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section aria-label={title} className={className}>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Eyebrow>
          <h2>{title}</h2>
        </Eyebrow>
        {aside && <span className="text-xs text-muted-foreground tabular-nums">{aside}</span>}
      </div>
      <div className={cn("rounded-xl border bg-card p-4 text-card-foreground", bodyClassName)}>{children}</div>
    </section>
  );
}

/** Muted placeholder line inside a panel while its data has not arrived (or never will). */
export function PanelEmpty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>;
}
