import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { GuidePageShell } from "@/components/guide/GuidePageShell";
import { API_URL, getGuide } from "@/lib/api";
import type { Guide } from "@/types/guide";

type Props = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

async function load(slug: string): Promise<{ guide: Guide | null; error: string | null }> {
  try {
    return { guide: await getGuide(slug), error: null };
  } catch (e) {
    return { guide: null, error: e instanceof Error ? e.message : "Unknown error" };
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const { guide } = await load(slug);
  if (!guide) return { title: "Guide · OAuth app guides" };
  return {
    title: `${guide.app_name} OAuth app guide · verified setup and approval`,
    description: guide.verdict?.summary,
  };
}

export default async function GuidePage({ params, searchParams }: Props) {
  const { slug } = await params;
  const query = await searchParams;
  // Only plain string values; the situation provider drops anything that is not a real question/option.
  const initialAnswers: Record<string, string> = {};
  for (const [k, v] of Object.entries(query)) {
    const value = Array.isArray(v) ? v[0] : v;
    if (typeof value === "string") initialAnswers[k] = value;
  }
  const { guide, error } = await load(slug);

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16">
        <div className="space-y-3 rounded-xl border border-warning-border bg-warning-soft p-6">
          <h1 className="text-lg font-semibold text-warning">Can&apos;t reach the guide service</h1>
          <p className="text-sm text-warning/90">
            The page tried to load the guide for <span className="font-mono">{slug}</span> from{" "}
            <span className="font-mono">{API_URL}</span> and did not get a usable response.
          </p>
          <p className="font-mono text-xs text-warning/80">{error}</p>
          <p className="text-sm text-warning/90">
            Start the backend (<span className="font-mono">uvicorn</span> on port 8000), or check{" "}
            <span className="font-mono">NEXT_PUBLIC_API_URL</span>, then reload.
          </p>
          <Link href="/" className="inline-block text-sm font-medium underline underline-offset-2">
            Back to all apps
          </Link>
        </div>
      </div>
    );
  }
  if (!guide) notFound();
  return <GuidePageShell guide={guide} initialAnswers={initialAnswers} />;
}
