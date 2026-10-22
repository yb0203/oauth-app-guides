import { getCatalog } from "@/lib/api";
import { CatalogList } from "@/components/home/CatalogList";
import { StartForm } from "@/components/home/StartForm";
import type { CatalogEntry } from "@/types/guide";

export const dynamic = "force-dynamic";

export default async function Home() {
  let catalog: CatalogEntry[] = [];
  let error: string | null = null;
  try {
    catalog = await getCatalog();
  } catch (e) {
    error = e instanceof Error ? e.message : "Backend unreachable";
  }

  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-12 pb-16 sm:px-6">
      <section className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          How hard is it to get a provider&apos;s OAuth app approved?
        </h1>
        <p className="mt-3 text-base text-muted-foreground">
          Verified guides for creating, and getting approval for, the OAuth app behind every user connection: the steps,
          the wait, the cost, and the evidence for each claim. Missing an app? An agent writes the guide live.
        </p>
        <div className="mt-6">
          <StartForm catalog={catalog} />
        </div>
      </section>

      <section className="mt-12">
        <h2 className="mb-3 text-lg font-semibold tracking-tight">Catalog</h2>
        {error ? (
          <div className="rounded-xl border border-warning-border bg-warning-soft p-4 text-sm text-warning">
            Could not load the catalog from the backend ({error}). You can still enter an app name above once the
            backend is running.
          </div>
        ) : (
          <CatalogList catalog={catalog} />
        )}
      </section>
    </div>
  );
}
