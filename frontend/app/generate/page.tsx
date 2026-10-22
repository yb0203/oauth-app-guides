import { Suspense } from "react";
import { GenerateView } from "@/components/generate/GenerateView";
import { TargetForm } from "@/components/generate/TargetForm";

export const metadata = { title: "Generating guide · OAuth app guides" };

export default async function GeneratePage({
  searchParams,
}: {
  searchParams: Promise<{ app?: string | string[] }>;
}) {
  const raw = (await searchParams).app;
  const app = (Array.isArray(raw) ? raw[0] : raw)?.trim();
  return (
    <Suspense fallback={<div className="mx-auto max-w-[1200px] px-4 py-8 text-sm text-muted-foreground">Loading</div>}>
      {app ? <GenerateView app={app} /> : <TargetForm />}
    </Suspense>
  );
}
