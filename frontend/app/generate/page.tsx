import { Suspense } from "react";
import { GenerateView } from "@/components/generate/GenerateView";
import { TargetForm } from "@/components/generate/TargetForm";
import { getModels, parseConfig } from "@/lib/models";

export const metadata = { title: "Generating guide · OAuth app guides" };

export default async function GeneratePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const raw = sp.app;
  const app = (Array.isArray(raw) ? raw[0] : raw)?.trim();
  const config = parseConfig(sp);
  const models = await getModels();
  return (
    <Suspense fallback={<div className="mx-auto max-w-[1200px] px-4 py-8 text-sm text-muted-foreground">Loading</div>}>
      {app ? <GenerateView app={app} initialConfig={config} models={models} /> : <TargetForm models={models} initialConfig={config} />}
    </Suspense>
  );
}
